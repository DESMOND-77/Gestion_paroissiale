import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.core.cache import cache
import redis
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, AccessToken

logger = logging.getLogger(__name__)


class TokenManager:
    """Gestion des tokens JWT avec Redis."""

    # Connexion Redis directe (pour les opérations avancées)
    _redis_client = None

    @classmethod
    def get_redis_client(cls):
        """Obtient un client Redis."""
        if cls._redis_client is None:
            try:
                cls._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                cls._redis_client = None
        return cls._redis_client

    @classmethod
    def check_redis_version(cls):
        """Vérifie la version de Redis et ajuste la compatibilité."""
        try:
            redis_client = cls.get_redis_client()
            if redis_client:
                info = redis_client.info()
                version = info["redis_version"]
                # Redis 4.0+ supporte HSET avec mapping, sinon utiliser l'ancienne syntaxe
                return version >= "4.0.0"
        except Exception as e:
            logger.warning(f"Impossible de vérifier la version Redis: {e}")
        return False

    @staticmethod
    def generate_token(user):
        """Génère un token JWT pour un utilisateur donné."""
        try:

            # Récupérer la configuration D'ABORD
            access_expiry = settings.SIMPLE_JWT.get(
                "ACCESS_TOKEN_LIFETIME", timedelta(days=3)
            )
            refresh_expiry = settings.SIMPLE_JWT.get(
                "REFRESH_TOKEN_LIFETIME", timedelta(days=14)
            )

            # Générer le refresh token
            refresh = RefreshToken.for_user(user)
            jti = str(uuid.uuid4())
            refresh["jti"] = jti
            refresh["username"] = user.username
            refresh["email"] = user.email
            refresh["is_staff"] = user.is_staff
            refresh["is_verified"] = user.is_verified
            refresh["type"] = "refresh"
            refresh["user_id"] = user.id

            # Configurer l'expiration du ACCESS token
            access_token = AccessToken()
            access_token["jti"] = str(uuid.uuid4())
            access_token["type"] = "access"
            access_token["user_id"] = user.id

            # Signer le token avec la clé secrète
            access_token_str = str(access_token)

            # Stocker le refresh token dans le cache
            TokenManager._store_token_metadata(
                user.id, jti, "refresh", refresh_expiry.total_seconds()
            )

            return {
                "access": access_token_str,
                "refresh": str(refresh),
                "token_type": "Bearer",
                "access_expires_in": int(access_expiry.total_seconds()),
                "refresh_expires_in": int(refresh_expiry.total_seconds()),
                "user_id": user.id,
                "issued_at": int(time.time()),
            }
        except Exception as e:
            logger.error(f"Error generating token for user {user.id}: {str(e)}")
            return None

    @staticmethod
    def refresh_token(refresh_token_str):
        """Rafraîchit un token JWT donné."""
        try:
            token = RefreshToken(refresh_token_str)

            jti = token.get("jti")
            if not jti or TokenManager.is_token_blacklisted(jti):
                logger.warning(
                    f"Attempt to refresh blacklisted or invalid token: {jti}"
                )
                raise TokenError("Token is blacklisted or invalid")
            user_id = token.get("user_id")
            from accounts.models import User

            try:
                user = User.objects.get(id=user_id)
            except:
                logger.warning(f"User not found for token refresh: {user_id}")
                raise TokenError("Invalid token ")

            if not user.is_active:
                logger.warning(
                    f"Inactive user attempted token refresh: {user.matricule}"
                )
                TokenManager.blacklist_token(jti)
                raise TokenError("User is inactive")
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", True):
                # Blacklist the old token
                TokenManager.blacklist_token(jti)
                # Generate a new token pair
                return TokenManager.generate_token(user)
        except TokenError as e:
            logger.error(f"TokenError while refreshing token: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"unexpected error during token refresh: {str(e)}")
            raise TokenError(f"Failed to refresh token: {str(e)}")

    @staticmethod
    def validate_token(token_str):
        """Valide un token JWT donné.
        return tuple ( is_valid, user_id, token_type)
        """
        try:
            """first use pyjwt to decode and verify the token"""
            unverified = jwt.decode(
                token_str,
                options={"verify_signature": False},
            )
            algorithms = unverified.get(
                "algorithms", settings.SIMPLE_JWT.get("ALGORITHM", "HS256")
            )
            # now properly decode
            decoded = jwt.decode(
                token_str,
                settings.SIMPLE_JWT.get("SIGNING_KEY", settings.SECRET_KEY),
                algorithms=[algorithms],
                options={"verify_signature": True},
            )
            # check token type

            token_type = decoded.get("token_type", decoded.get("type", "access"))
            user_id = decoded.get("user_id")
            jti = decoded.get("jti")

            # check if token is blacklisted
            if jti and TokenManager.is_token_blacklisted(jti):
                logger.warning(f"Attempt to use blacklisted token: {jti}")
                return False, None, None

            # check expiration
            exp_timestamp = decoded.get("exp", 0)

            if exp_timestamp < time.time():
                logger.debug(
                    f"Token has expired at : {datetime.fromtimestamp(exp_timestamp).isoformat()}"
                )
                return False, None, None
            return True, user_id, token_type
        except jwt.PyJWKError as e:
            logger.error(f"token validation error: {str(e)}")
            return False, None, None
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False, None, None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token error: {str(e)}")
            return False, None, None

    @staticmethod
    def _store_token_metadata(user_id, jti, token_type, expiry_seconds):
        """Stocke les métadonnées du token dans le cache pour la révocation."""
        try:
            # verifie si on utilise redis ou cache memoire
            if hasattr(cache, "client"):
                # redis implementation
                try:
                    redis_client = TokenManager.get_redis_client()
                    if not redis_client:
                        return False

                    user_tokens_key = f"user_tokens:{user_id}"
                    token_info_key = f"token_info:{jti}"

                    pipeline = redis_client.pipeline()
                    pipeline.sadd(user_tokens_key, jti)
                    pipeline.expire(user_tokens_key, int(expiry_seconds))

                    # Créer le dictionnaire token_info
                    token_info = {
                        "user_id": str(user_id),
                        "type": token_type,
                        "created_at": str(time.time()),  # Convertir en string
                        "expires_at": str(time.time() + expiry_seconds),
                    }

                    # Vérifier la compatibilité et utiliser la méthode appropriée
                    supports_mapping = TokenManager.check_redis_version()

                    if supports_mapping and hasattr(pipeline, "hset"):
                        # Méthode moderne (Redis 4.0+)
                        pipeline.hset(token_info_key, mapping=token_info)
                    else:
                        # Méthode compatible avec toutes les versions
                        for field, value in token_info.items():
                            pipeline.hset(token_info_key, field, value)

                    pipeline.expire(token_info_key, int(expiry_seconds))
                    pipeline.execute()

                    logger.debug(f"Token metadata stored in Redis: {jti}")
                    return True
                except Exception as e:
                    logger.error(f"Error storing token metadata in Redis: {e}")
                    return False
            else:
                # memory cache implementation
                user_tokens_key = f"user_tokens_{user_id}"
                existing_tokens = cache.get(user_tokens_key, set())

                if not isinstance(existing_tokens, set):
                    existing_tokens = set()
                existing_tokens.add(jti)
                cache.set(user_tokens_key, existing_tokens, timeout=int(expiry_seconds))
        except Exception as e:
            logger.error(f"Error storing token metadata: {str(e)}")

    @staticmethod
    def is_token_blacklisted(jti):
        """Vérifie si un token est dans la liste noire."""
        if not jti:
            return False
        blacklist_key = f"blacklisted_tokens:{jti}"
        if cache.get(blacklist_key) is not None:
            return True
        # Vérification supplémentaire via Redis direct
        try:
            redis_client = TokenManager.get_redis_client()
            if redis_client and redis_client.exists(blacklist_key):
                return True
        except Exception as e:
            logger.error(f"Error checking blacklist in Redis: {e}")

        return False

    @staticmethod
    def blacklist_token(jti):
        if not jti:
            return False
        blacklist_key = f"blacklisted_tokens:{jti}"
        cache.set(
            blacklist_key,
            True,
            timeout=settings.SIMPLE_JWT.get("BLACKLIST_TIMEOUT", 86400),
        )

    @staticmethod
    def blacklist_all_user_tokens(user_id):
        """Met tous les tokens d'un utilisateur dans la liste noire."""
        try:
            user_tokens_key = f"user_tokens:{user_id}"
            if hasattr(cache, "client"):
                # reddis implementation
                try:
                    redis_client = TokenManager.get_redis_client()
                    if not redis_client:
                        return False

                    user_tokens_key = f"user_tokens:{user_id}"
                    tokens = redis_client.smembers(user_tokens_key)

                    if tokens:
                        pipeline = redis_client.pipeline()
                        # Blacklister chaque token
                        for jti in tokens:
                            blacklist_key = f"blacklisted_tokens:{jti}"  # cohérent avec is_token_blacklisted
                            pipeline.setex(blacklist_key, 86400 * 14, 1)  # 14 jours

                        # Supprimer l'ensemble des tokens de l'utilisateur
                        pipeline.delete(user_tokens_key)
                        pipeline.execute()

                        logger.info(
                            f"Cleaned up {len(tokens)} tokens for user {user_id}"
                        )
                        return True
                except Exception as e:
                    logger.error(f"Error cleaning up user tokens: {e}")
            else:
                # implementation generic pour LocMemCache
                token_set = cache.get(user_tokens_key, set())
                if not token_set:
                    return 0
                for jti in token_set:
                    TokenManager.blacklist_token(jti)
                # supprime la liste des tokens actifs
                cache.delete(user_tokens_key)
                return len(token_set)
        except Exception as e:
            logger.error(f"Error blacklisting tokens for user {user_id}: {str(e)}")
            return 0

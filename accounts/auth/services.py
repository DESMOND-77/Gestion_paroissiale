import logging

from django.conf import settings
from django.conf import settings as pj_settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import UserSerializer
from core.jwt_utils import TokenManager

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service pour la gestion de l'authentification des utilisateurs."""

    @staticmethod
    def register(email, password, prenom, nom, request_meta=None):

        from accounts.verification.services import EmailVerificationService

        if not email or not password:
            return (
                False,
                {"success": False, "error": "Email et mot de passe sont requis."},
                400,
            )

        # Log registration attempt
        if request_meta:
            logger.info(
                f"Registration attempt from IP: {request_meta.get('REMOTE_ADDR')} "
            )
        try:

            if User.objects.filter(email=email).exists():
                return (
                    False,
                    {
                        "success": False,
                        "error": "Un utilisateur avec cet email existe déjà.",
                    },
                    400,
                )
            # valider la complexité du mot de passe
            try:
                validate_password(password)
            except ValidationError as e:
                return (
                    False,
                    {
                        "success": False,
                        "error": f"Mot de passe invalide: {'; '.join(e.messages)}",
                    },
                    400,
                )
            # créer l'utilisateur
            user = User.objects.create_user(
                email=email,
                password=password,
                prenom=prenom,
                nom=nom,
                is_verified=False,
            )

            # engage le processus de vérification par email ici si nécessaire
            if user.email and pj_settings.REQUIRE_EMAIL_VERIFICATION:
                # utiliser le cache pour marquer que l'email doit etre envoyé
                cache_key = f"send_verification_email_{user.id}"
                cache.set(cache_key, True, timeout=3600)  # 1 heure

                # lancer une tache asynchrone pour l'envoie de l'email
                try:
                    # rediriger au service de verification de l'email
                    EmailVerificationService.send_verification_email_background(user.id)
                    logger.info(f"Verification email queued for user {user.email}")
                except Exception as thread_error:
                    # log but don't fail registration if email queueing fail
                    logger.error(
                        f"Failed to queue verification email: {str(thread_error)}"
                    )

            # serialize user data
            serializer = UserSerializer(user)

            # Generate tokens
            tokens = TokenManager.generate_token(user)

            # Log successful registration
            logger.info(f"User registered successfully: {user.email}")

            # Return success response
            return (
                True,
                {
                    "success": True,
                    "data": {
                        "user": serializer.data,
                        "tokens": tokens,
                        "is_new_user": True,
                        "email_verified": user.is_verified,
                    },
                },
                201,
            )
        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}")
            return (
                False,
                {
                    "success": False,
                    "error": "Registration failed, please try again later.",
                },
                400,
            )

    @staticmethod
    def login(request, email, password, device_info=None, request_meta=None):
        """
        Handle user login with email and password.
        Args:
            email (str): User's email.
            password (str): User's password.
            device_info (dict, optional): Information about the user's device.
            request_meta (dict, optional): Request metadata for logging.

        Returns:
            tuple : (success,response_dict,status_code)
        """

        if not email or not password:
            return (
                False,
                {"success": False, "error": "Email et mot de passe requis."},
                400,
            )

        # Normalize email for cache keys
        safe_email = email.replace("@", "_at_").replace(".", "_")
        LOCK_KEY = f"account_lockout_{safe_email}"
        FAIL_KEY = f"failed_login_{safe_email}"

        # Log original attempt
        if request_meta:
            logger.info(
                f"Login attempt for {email} from IP: {request_meta.get('REMOTE_ADDR')} UA: {request_meta.get('HTTP_USER_AGENT')}"
            )

        try:
            # Check lockout
            if cache.get(LOCK_KEY):
                logger.warning(f"Login attempt for locked account: {email}")
                return (
                    False,
                    {
                        "success": False,
                        "error": "Compte temporairement verrouillé après plusieurs échecs de connexion. Réessayez plus tard.",
                        "lockout": True,
                    },
                    403,
                )

            # Authenticate
            user = authenticate(request=request, username=email, password=password)

            if not user:
                failed_attempts = cache.get(FAIL_KEY, 0) + 1
                cache.set(FAIL_KEY, failed_attempts, timeout=1800)

                # Lock after 5 attempts
                if failed_attempts >= 5:
                    cache.set(LOCK_KEY, True, timeout=900)
                    logger.warning(f"Account locked (5 failed attempts): {email}")
                    return (
                        False,
                        {
                            "success": False,
                            "error": "Compte verrouillé après plusieurs tentatives échouées. Réessayez dans 15 minutes.",
                            "lockout": True,
                        },
                        403,
                    )

                logger.warning(f"Failed login {failed_attempts} for {email}")
                return (
                    False,
                    {"success": False, "error": "Email ou mot de passe incorrect."},
                    401,
                )

            if not user.is_active:
                return (
                    False,
                    {"success": False, "error": "Ce compte est désactivé."},
                    403,
                )

            # Le compte doit être vérifié avant toute connexion.
            if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
                logger.warning(f"Login blocked (email not verified): {email}")
                return (
                    False,
                    {
                        "success": False,
                        "error": (
                            "Votre compte n'est pas encore vérifié. "
                            "Consultez l'email de vérification envoyé à votre adresse."
                        ),
                        "verification_needed": True,
                    },
                    403,
                )

            # SUCCESS → Reset failed attempts
            cache.delete(FAIL_KEY)
            serializer = UserSerializer(user)
            tokens = TokenManager.generate_token(user)

            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            logger.info(f"User logged in: {email}")

            return (
                True,
                {
                    "data": {
                        "user": serializer.data,
                        "tokens": tokens,
                        "email_verified": user.is_verified,
                        "verification_needed": not user.is_verified
                                               and settings.REQUIRE_EMAIL_VERIFICATION,
                    }
                },
                200,
            )

        except Exception as e:
            logger.error(f"Error during login for {email}: {str(e)}")
            return (
                False,
                {"success": False, "error": "Login failed, try again later."},
                401,
            )

    @staticmethod
    def RefreshToken(refresh_token):
        """
        Refresh an authentication token

        Args:
            refresh_token (str): the refresh token to use

        Returns:
            tuple: (success, response_dict, status_code)
        """
        if not refresh_token:
            return (
                False,
                {"success": False, "error": "Refresh token is required"},
                400,
            )
        try:
            # Use token manager to refresh the token
            tokens = TokenManager.refresh_token(refresh_token)

            # TokenManager.refresh_token() peut renvoyer None si la rotation des
            # refresh tokens est désactivée : on traite ce cas explicitement.
            if not tokens:
                return (
                    False,
                    {"success": False, "error": "Unable to refresh token"},
                    401,
                )

            # Return successful response data. On renvoie la structure native de
            # generate_token (access/refresh/access_expires_in/...) pour rester
            # cohérent avec login et register.
            return (
                True,
                {"success": True, "data": tokens},
                200,
            )

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return (
                False,
                {"success": False, "error": "An error during token refresh"},
                500,
            )

    @staticmethod
    def Validate_token(token, user):
        """
        Validate a token and check if it belongs to the user

        Args:
            token (str): the  token to validate
            user : The user to check against

        Returns:
            tuple: (success, response_dict, status_code)
        """
        is_valid, user_id, token_type = TokenManager.validate_token(token)
        # Comparaison en chaînes : user.id est un UUID (plus un entier), donc
        # int(user_id) lèverait ValueError.
        if not is_valid or str(user_id) != str(user.id):
            logger.warning(
                f"Token validation failed: expected user {user.id}, got {user_id}"
            )
            return False, {"success": False, "error": "Token validation failed"}, 400
        # access verification status through the service layer cache handling
        from accounts.verification.services import EmailVerificationService

        success, verification_response, _ = (
            EmailVerificationService.check_verification_status(user)
        )
        if not success:
            logger.warning(f"Error checking verification status for  user {user.id}")
            # fallback to provided user object
            is_verified = user.is_verified
        else:
            is_verified = verification_response.get("data", {}).get(
                "is_verified", user.is_verified
            )
        logger.info(
            f"Token validation retrieved verification status for user {user.id} : is_verified={is_verified}"
        )

        return (
            True,
            {
                "success": True,
                "data": {
                    "valid": True,
                    "user_id": user.id,
                    "email_verified": is_verified,
                },
            },
            200,
        )

    @staticmethod
    def logout(user, refresh_token=None):
        """
        Handle user logout invalidating as needed
        Args:
            user: The user object logging out
            refresh_token: (str, optional): the refresh token to invalidate

        Returns:
            tuple: (success, response_dict, status_code)

        """
        # Invalidate specific token if provided
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                jti = token.get("jti")
                if jti:
                    TokenManager.blacklist_token(jti)
                    logger.info(f"token blacklisted during logout : {jti}")
            except Exception as e:
                logger.warning(f"Error blacklisting token during logout {str(e)}")

        # log the logout event
        logger.info(f"User logged out: {user.id}")
        return True, {"success": True, "message": "Successfully logged out"}, 200

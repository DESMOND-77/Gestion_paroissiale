"""Classe de base et utilitaires partagés par les tests d'authentification."""
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APITestCase

from accounts.models import User
from core.jwt_utils import TokenManager

# Réglages hermétiques : pas de Redis, pas d'envoi réel d'email.
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "auth-tests",
    }
}


@override_settings(
    CACHES=TEST_CACHES,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    REQUIRE_EMAIL_VERIFICATION=True,
    JWT_AUTH_COOKIE_SECURE=False,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class BaseAuthTest(APITestCase):
    """Base commune : cache vidé, Redis neutralisé, helpers de fabrique."""

    # Mot de passe valide vis-à-vis des validateurs Django par défaut.
    VALID_PASSWORD = "Str0ngPass!2024"

    def setUp(self):
        super().setUp()
        # Chaque test part d'un cache propre (verrouillages / rate-limit / tokens).
        cache.clear()
        # Neutraliser le client Redis direct : force le chemin "cache mémoire".
        redis_patcher = mock.patch.object(
            TokenManager, "get_redis_client", return_value=None
        )
        redis_patcher.start()
        self.addCleanup(redis_patcher.stop)

    # ------------------------------------------------------------------ helpers
    def create_user(self, email="user@example.com", password=None, **extra):
        """Crée un utilisateur actif (vérifié par défaut sauf override)."""
        password = password or self.VALID_PASSWORD
        extra.setdefault("prenom", "Jean")
        extra.setdefault("nom", "Dupont")
        extra.setdefault("is_verified", True)
        return User.objects.create_user(email=email, password=password, **extra)

    def auth(self, user):
        """Authentifie le client via un vrai access token JWT (header Bearer)."""
        tokens = TokenManager.generate_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return tokens

    @staticmethod
    def make_uid_token(user):
        """Génère (uid base64, token) comme dans les emails de vérification/reset."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token

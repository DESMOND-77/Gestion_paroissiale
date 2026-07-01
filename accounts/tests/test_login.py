"""Tests de la connexion (login), y compris le verrouillage de compte."""
from django.urls import reverse

from .base import BaseAuthTest


class LoginViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("login")
        self.user = self.create_user(email="login@example.com")

    def test_login_success(self):
        resp = self.client.post(
            self.url,
            {"email": "login@example.com", "password": self.VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertIn("tokens", resp.data["data"])
        self.assertEqual(resp.data["data"]["user"]["email"], "login@example.com")
        self.assertTrue(resp.data["data"]["email_verified"])

    def test_login_updates_last_login(self):
        self.assertIsNone(self.user.last_login)
        self.client.post(
            self.url,
            {"email": "login@example.com", "password": self.VALID_PASSWORD},
            format="json",
        )
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(resp.data["success"])

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            self.url,
            {"email": "ghost@example.com", "password": self.VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(resp.data["success"])

    def test_login_missing_fields(self):
        resp = self.client.post(self.url, {"email": "login@example.com"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_login_inactive_user_is_rejected(self):
        # ModelBackend refuse d'authentifier un compte inactif -> identifiants invalides
        self.create_user(email="inactive@example.com", is_active=False)
        resp = self.client.post(
            self.url,
            {"email": "inactive@example.com", "password": self.VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(resp.data["success"])

    def test_account_lockout_after_five_failed_attempts(self):
        creds = {"email": "login@example.com", "password": "bad"}
        # 4 premières tentatives -> 401
        for _ in range(4):
            resp = self.client.post(self.url, creds, format="json")
            self.assertEqual(resp.status_code, 401)
        # 5e tentative -> verrouillage (403)
        resp = self.client.post(self.url, creds, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(resp.data.get("lockout"))

    def test_locked_account_blocks_even_with_correct_password(self):
        creds = {"email": "login@example.com", "password": "bad"}
        for _ in range(5):
            self.client.post(self.url, creds, format="json")
        # Même avec le bon mot de passe, le compte reste verrouillé.
        resp = self.client.post(
            self.url,
            {"email": "login@example.com", "password": self.VALID_PASSWORD},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(resp.data.get("lockout"))

"""Tests de l'inscription (register)."""
from unittest import mock

from django.urls import reverse

from accounts.models import User, UserActivity
from .base import BaseAuthTest

# On neutralise l'envoi d'email de vérification déclenché par l'inscription.
PATCH_BG = "accounts.verification.services.EmailVerificationService.send_verification_email_background"


class RegistrationViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("register")
        self.payload = {
            "email": "new@example.com",
            "password": self.VALID_PASSWORD,
            "prenom": "Alice",
            "nom": "Martin",
        }

    @mock.patch(PATCH_BG)
    def test_register_success(self, mock_bg):
        resp = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data["success"])
        self.assertIn("data", resp.data)
        self.assertEqual(resp.data["data"]["user"]["email"], "new@example.com")
        self.assertIn("tokens", resp.data["data"])
        self.assertTrue(resp.data["data"]["is_new_user"])

        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.is_verified)
        # L'email de vérification a bien été mis en file d'attente.
        mock_bg.assert_called_once_with(user.id)

    @mock.patch(PATCH_BG)
    def test_register_logs_activity(self, _mock_bg):
        self.client.post(self.url, self.payload, format="json")
        user = User.objects.get(email="new@example.com")
        self.assertTrue(
            UserActivity.objects.filter(user=user, action="Register").exists()
        )

    @mock.patch(PATCH_BG)
    def test_register_supports_legacy_first_last_name(self, _mock_bg):
        payload = {
            "email": "legacy@example.com",
            "password": self.VALID_PASSWORD,
            "first_name": "Bob",
            "last_name": "Legacy",
        }
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(email="legacy@example.com")
        self.assertEqual(user.prenom, "Bob")
        self.assertEqual(user.nom, "Legacy")

    @mock.patch(PATCH_BG)
    def test_register_duplicate_email(self, _mock_bg):
        self.create_user(email="new@example.com")
        resp = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_register_missing_email(self):
        payload = dict(self.payload)
        payload.pop("email")
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_register_missing_password(self):
        payload = dict(self.payload)
        payload.pop("password")
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_register_weak_password_rejected(self):
        payload = dict(self.payload, password="123")
        resp = self.client.post(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])
        self.assertFalse(User.objects.filter(email=payload["email"]).exists())

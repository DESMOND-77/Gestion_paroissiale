"""Tests de la réinitialisation du mot de passe (demande + confirmation)."""
from unittest import mock

from django.urls import reverse

from .base import BaseAuthTest

# On neutralise l'envoi réel de l'email de réinitialisation (thread daemon).
PATCH_SEND = "accounts.verification.emails.EmailService.send_password_reset_email"


class PasswordResetRequestViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("password_reset")
        self.user = self.create_user(email="reset@example.com")

    @mock.patch(PATCH_SEND, return_value=True)
    def test_request_reset_existing_email(self, mock_send):
        resp = self.client.post(self.url, {"email": "reset@example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])

    @mock.patch(PATCH_SEND, return_value=True)
    def test_request_reset_unknown_email_does_not_leak(self, mock_send):
        # Anti-énumération : même réponse générique pour un email inconnu.
        resp = self.client.post(self.url, {"email": "ghost@example.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        mock_send.assert_not_called()

    def test_request_reset_missing_email(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])


class ConfirmPasswordResetViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("confirm_password_reset")
        self.user = self.create_user(email="confirm@example.com")
        self.new_password = "Brand-N3w!Pass"

    def test_confirm_reset_success(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {"uid": uid, "token": token, "new_password": self.new_password},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_confirm_reset_invalid_token(self):
        uid, _ = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {"uid": uid, "token": "bad-token", "new_password": self.new_password},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_confirm_reset_missing_fields(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(self.url, {"uid": uid, "token": token}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_confirm_reset_weak_password(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {"uid": uid, "token": token, "new_password": "123"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

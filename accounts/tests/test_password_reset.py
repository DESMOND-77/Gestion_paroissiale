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


# La confirmation du reset (token + nouveau mot de passe) est désormais assurée
# par la page HTML : voir accounts/tests/test_web_pages.PasswordResetPageTests.

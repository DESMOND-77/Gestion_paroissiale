"""Tests de la vérification d'email (verify, send, status)."""

from unittest import mock

from django.urls import reverse

from .base import BaseAuthTest

# Cible du thread d'envoi : on la neutralise pour éviter tout envoi réel.
PATCH_BG = "accounts.verification.services.EmailVerificationService.send_verification_email_background"


class SendVerificationEmailViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("send_verification")
        self.user = self.create_user(email="send@example.com", is_verified=False)

    @mock.patch(PATCH_BG)
    def test_send_verification_success(self, mock_bg):
        self.auth(self.user)
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        mock_bg.assert_called_once_with(self.user.id)

    @mock.patch(PATCH_BG)
    def test_send_verification_rate_limited_on_second_call(self, _mock_bg):
        self.auth(self.user)
        self.client.post(self.url, {}, format="json")
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 429)
        self.assertFalse(resp.data["success"])

    @mock.patch(PATCH_BG)
    def test_send_verification_already_verified(self, mock_bg):
        verified = self.create_user(email="already@example.com", is_verified=True)
        self.auth(verified)
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        mock_bg.assert_not_called()

    def test_send_verification_requires_authentication(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 401)


class CheckVerificationStatusViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("check_verification")

    def test_status_reports_verified(self):
        user = self.create_user(email="v@example.com", is_verified=True)
        self.auth(user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertTrue(resp.data["data"]["is_verified"])

    def test_status_reports_unverified(self):
        user = self.create_user(email="nv@example.com", is_verified=False)
        self.auth(user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["data"]["is_verified"])

    def test_status_requires_authentication(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

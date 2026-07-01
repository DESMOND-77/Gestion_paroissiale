"""Tests des endpoints de tokens : refresh et validation."""
from django.urls import reverse

from core.jwt_utils import TokenManager
from .base import BaseAuthTest


class TokenRefreshViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("token_refresh")
        self.user = self.create_user(email="refresh@example.com")

    def test_refresh_success_returns_new_tokens(self):
        tokens = TokenManager.generate_token(self.user)
        resp = self.client.post(
            self.url, {"refresh_token": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertIn("access", resp.data["data"])

    def test_refresh_missing_token(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_refresh_invalid_token(self):
        resp = self.client.post(
            self.url, {"refresh_token": "not-a-real-token"}, format="json"
        )
        self.assertGreaterEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])


class ValidateTokenViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("validate_token")
        self.user = self.create_user(email="validate@example.com")

    def test_validate_token_success(self):
        # auth() pose le header Bearer avec un access token valide.
        self.auth(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertTrue(resp.data["data"]["valid"])
        self.assertEqual(resp.data["data"]["user_id"], self.user.id)

    def test_validate_token_requires_authentication(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

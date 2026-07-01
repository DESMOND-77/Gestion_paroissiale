"""Tests déconnexion, profil courant (me) et changement de mot de passe."""
from django.urls import reverse

from accounts.models import UserActivity
from core.jwt_utils import TokenManager
from .base import BaseAuthTest


class LogoutViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("logout")
        self.user = self.create_user(email="logout@example.com")

    def test_logout_success(self):
        tokens = self.auth(self.user)
        resp = self.client.post(
            self.url, {"refresh_token": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertTrue(
            UserActivity.objects.filter(user=self.user, action="logout").exists()
        )

    def test_logout_requires_authentication(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 401)


class MeViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("me")
        self.user = self.create_user(email="me@example.com")

    def test_me_returns_current_user(self):
        self.auth(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["email"], "me@example.com")

    def test_me_requires_authentication(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)


class ChangePasswordViewTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("change_password")
        self.user = self.create_user(email="change@example.com")
        self.new_password = "N3w-Str0ng!Pass"

    def test_change_password_success(self):
        self.auth(self.user)
        resp = self.client.post(
            self.url,
            {
                "old_password": self.VALID_PASSWORD,
                "new_password": self.new_password,
                "confirm_password": self.new_password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_change_password_wrong_old_password(self):
        self.auth(self.user)
        resp = self.client.post(
            self.url,
            {
                "old_password": "totally-wrong",
                "new_password": self.new_password,
                "confirm_password": self.new_password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_change_password_confirmation_mismatch(self):
        self.auth(self.user)
        resp = self.client.post(
            self.url,
            {
                "old_password": self.VALID_PASSWORD,
                "new_password": self.new_password,
                "confirm_password": "different",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data["success"])

    def test_change_password_requires_authentication(self):
        resp = self.client.post(self.url, {}, format="json")
        self.assertEqual(resp.status_code, 401)

"""Tests des pages HTML conviviales : vérification d'email et réinitialisation."""
from django.urls import reverse

from .base import BaseAuthTest


class EmailVerifyPageTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("web_verify_email")
        self.user = self.create_user(email="verifpage@example.com", is_verified=False)

    def test_valid_link_confirms_and_renders_success(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.get(self.url, {"uid": uid, "token": token})
        self.assertContains(resp, "Adresse e-mail confirmée", status_code=200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_missing_params_renders_error(self):
        resp = self.client.get(self.url, {"uid": "abc"})
        self.assertContains(resp, "Vérification impossible", status_code=400)

    def test_invalid_token_renders_error(self):
        uid, _ = self.make_uid_token(self.user)
        resp = self.client.get(self.url, {"uid": uid, "token": "bad-token"})
        self.assertContains(resp, "Vérification impossible", status_code=400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)


class PasswordResetPageTests(BaseAuthTest):
    def setUp(self):
        super().setUp()
        self.url = reverse("web_password_reset")
        self.user = self.create_user(email="resetpage@example.com")
        self.new_password = "Nouveau-P4ss!2026"

    def test_get_renders_form(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.get(self.url, {"uid": uid, "token": token})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'name="new_password"')
        self.assertContains(resp, 'name="confirm_password"')

    def test_get_missing_params_invalid_link(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Réinitialisation impossible", status_code=400)

    def test_post_success_changes_password(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": self.new_password,
                "confirm_password": self.new_password,
            },
        )
        self.assertContains(resp, "Mot de passe mis à jour", status_code=200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))

    def test_post_password_mismatch(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": token,
                "new_password": self.new_password,
                "confirm_password": "different",
            },
        )
        self.assertContains(resp, "ne correspondent pas", status_code=400)

    def test_post_weak_password_rejected(self):
        uid, token = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {"uid": uid, "token": token, "new_password": "123", "confirm_password": "123"},
        )
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("123"))

    def test_post_invalid_token(self):
        uid, _ = self.make_uid_token(self.user)
        resp = self.client.post(
            self.url,
            {
                "uid": uid,
                "token": "bad-token",
                "new_password": self.new_password,
                "confirm_password": self.new_password,
            },
        )
        self.assertContains(resp, "Réinitialisation impossible", status_code=400)

"""Tests unitaires de la couche service (sans passer par HTTP)."""
from unittest import mock

from accounts.models import User
from accounts.auth.services import AuthenticationService
from accounts.verification.services import EmailVerificationService
from accounts.verification.password_reset_service import PasswordResetService
from core.jwt_utils import TokenManager
from .base import BaseAuthTest

PATCH_BG = "accounts.verification.services.EmailVerificationService.send_verification_email_background"
PATCH_RESET_SEND = "accounts.verification.emails.EmailService.send_password_reset_email"


class AuthenticationServiceTests(BaseAuthTest):
    @mock.patch(PATCH_BG)
    def test_register_creates_user(self, _mock_bg):
        success, data, code = AuthenticationService.register(
            email="svc@example.com",
            password=self.VALID_PASSWORD,
            prenom="Svc",
            nom="Test",
        )
        self.assertTrue(success)
        self.assertEqual(code, 201)
        self.assertTrue(User.objects.filter(email="svc@example.com").exists())

    def test_register_missing_credentials(self):
        success, data, code = AuthenticationService.register(
            email="", password="", prenom="A", nom="B"
        )
        self.assertFalse(success)
        self.assertEqual(code, 400)

    @mock.patch(PATCH_BG)
    def test_register_duplicate_email(self, _mock_bg):
        self.create_user(email="dup@example.com")
        success, data, code = AuthenticationService.register(
            email="dup@example.com",
            password=self.VALID_PASSWORD,
            prenom="A",
            nom="B",
        )
        self.assertFalse(success)
        self.assertEqual(code, 400)

    def test_login_success(self):
        self.create_user(email="svclogin@example.com")
        success, data, code = AuthenticationService.login(
            request=None,
            email="svclogin@example.com",
            password=self.VALID_PASSWORD,
        )
        self.assertTrue(success)
        self.assertEqual(code, 200)
        self.assertIn("tokens", data["data"])

    def test_login_invalid_credentials(self):
        self.create_user(email="svclogin2@example.com")
        success, data, code = AuthenticationService.login(
            request=None, email="svclogin2@example.com", password="wrong"
        )
        self.assertFalse(success)
        self.assertEqual(code, 401)

    def test_refresh_token_missing(self):
        success, data, code = AuthenticationService.RefreshToken(None)
        self.assertFalse(success)
        self.assertEqual(code, 400)

    def test_refresh_token_rotation(self):
        user = self.create_user(email="rot@example.com")
        tokens = TokenManager.generate_token(user)
        success, data, code = AuthenticationService.RefreshToken(tokens["refresh"])
        self.assertTrue(success)
        self.assertEqual(code, 200)
        self.assertIn("access", data["data"])

    def test_logout_returns_success(self):
        user = self.create_user(email="svclogout@example.com")
        success, data, code = AuthenticationService.logout(user=user)
        self.assertTrue(success)
        self.assertEqual(code, 200)


class EmailVerificationServiceTests(BaseAuthTest):
    def test_verify_email_valid(self):
        user = self.create_user(email="ev@example.com", is_verified=False)
        uid, token = self.make_uid_token(user)
        success, data, code = EmailVerificationService.verify_email(uid, token)
        self.assertTrue(success)
        self.assertEqual(code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_verify_email_invalid(self):
        user = self.create_user(email="ev2@example.com", is_verified=False)
        uid, _ = self.make_uid_token(user)
        success, data, code = EmailVerificationService.verify_email(uid, "bad")
        self.assertFalse(success)
        self.assertEqual(code, 400)

    def test_check_status_already_verified(self):
        user = self.create_user(email="ev3@example.com", is_verified=True)
        success, data, code = EmailVerificationService.check_verification_status(user)
        self.assertTrue(success)
        self.assertTrue(data["data"]["is_verified"])


class PasswordResetServiceTests(BaseAuthTest):
    @mock.patch(PATCH_RESET_SEND, return_value=True)
    def test_request_reset_generic_response(self, _mock_send):
        self.create_user(email="pr@example.com")
        success, data, code = PasswordResetService.request_reset("pr@example.com")
        self.assertTrue(success)
        self.assertEqual(code, 200)

    def test_confirm_reset_valid(self):
        user = self.create_user(email="pr2@example.com")
        uid, token = self.make_uid_token(user)
        success, data, code = PasswordResetService.confirm_reset(
            uid, token, "An0ther-Str0ng!Pass"
        )
        self.assertTrue(success)
        self.assertEqual(code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("An0ther-Str0ng!Pass"))

    def test_confirm_reset_invalid_token(self):
        user = self.create_user(email="pr3@example.com")
        uid, _ = self.make_uid_token(user)
        success, data, code = PasswordResetService.confirm_reset(uid, "bad", "x" * 12)
        self.assertFalse(success)
        self.assertEqual(code, 400)

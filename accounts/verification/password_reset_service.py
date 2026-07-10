import logging
import threading

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError

from accounts.verification.tokens import TokenVerifier
from core.jwt_utils import TokenManager
from .emails import EmailService

User = get_user_model()
logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service class to handle password reset operations"""

    def request_reset(email):
        """Request password reset for email
        Args:
            email (str): user email
        Returns:
            tuple: (success,response_dict,status_code)
        """
        try:
            if not email:
                return False, {"success": False, "error": "Email is required"}, 400
            # Rate limiting by email to prevent abuse
            rate_key = f"password_reset_{email}"
            if cache.get(rate_key):
                return (
                    True,
                    {
                        "success": True,
                        "message": "If an account exist with this email,a password rest link will be sent.",
                    },
                    200,
                )
            # find user by email
            try:
                user = User.objects.get(email=email)

                # send email in background thread
                threading.Thread(
                    target=EmailService.send_password_reset_email,
                    args=(user,),
                    daemon=True,
                ).start()
            except User.DoesNotExist:
                pass

            # rate limit regardless of result ( to prevent enumeration attacks)
            cache.set(rate_key, True, timeout=300)

            # for security, return success message regardless of actual result
            return (
                True,
                {
                    "success": True,
                    "message": "If an account exist with this email,a password reset link will be sent.",
                },
                200,
            )

        except Exception as e:
            logger.error(f"Password reset Error i {str(e)}")

            # for security, don't expose error details
            return (
                True,
                {
                    "success": True,
                    "message": "If an account exist with this email,a password reset link will be sent.",
                },
                200,
            )

    @staticmethod
    def confirm_reset(uidb64, token, new_password):
        """Complete password reset with token and new password

        Args:
            uidb64 (str): Base 64 user ID
            token (str): Reset token
            new_password (str): New password
        Returns:
            tuple : (success,response_dic,status_code)
        """
        is_valid, user, error = TokenVerifier.verify_token(uidb64, token)

        if not is_valid:
            return (
                False,
                {
                    "success": False,
                    "error": "Invalid password reset link, please request a new one",
                },
                400,
            )
        # Validate the new password
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return False, {"success": False, "error": ", ".join(e.messages)}, 400

        # Update password
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Log password reset for security audit
        logger.info(f"Password reset completed for user {user.id} via link")

        # Invalidate all existing refresh tokens for security
        TokenManager.blacklist_all_user_tokens(user.id)

        return (
            True,
            {
                "success": True,
                "message": "Mot de passe réinitialisé avec succès, vous pouvez maintenant vous connecter.",
            },
            200,
        )

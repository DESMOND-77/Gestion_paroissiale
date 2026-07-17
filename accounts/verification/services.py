import logging
import threading
import traceback

from django.contrib.auth import get_user_model
from django.core.cache import cache

from accounts.verification.tokens import TokenVerifier

from .emails import EmailService

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailVerificationService:
    """service pour la gestion de la vérification des emails"""

    @staticmethod
    def get_verification_cache_key(user_id):
        """get standardized cache key for user verification status"""
        return f"user_verified_status{user_id}"

    @staticmethod
    def verify_email(uidb64, token):
        """
        verify email with token
        Args:
            uidb64 ( str): Base64 encoded user ID
            token (str): verification token
        Returns:
            tuple : (success,response_dict,status_code)
        """

        is_valid, user, error = TokenVerifier.verify_token(uidb64, token)

        if not is_valid:
            logger.warning(f"Invalid token verification attempt with uidb64: {uidb64}")
            return (
                False,
                {
                    "success": False,
                    "error": error
                    or "Invalid verification link. Please request a new one",
                },
                400,
            )
        try:
            # ensure we use an atomic transaction
            from django.db import transaction

            with transaction.atomic():
                # Update user verification status if not verified
                if not user.is_verified:
                    user.is_verified = True
                    user.is_active = True
                    user.save(update_fields=["is_verified", "is_active"])
                    logger.info(
                        f"Email verified for user {user.id} {user.email} via link"
                    )
                else:
                    logger.info(
                        f"Email verification attempt for already verified user {user.id} {user.email}"
                    )

            # Explicitly clear any related cache using our standardized key
            cache_key = EmailVerificationService.get_verification_cache_key(user.id)

            # set the verified status to true in cache
            cache.set(
                cache_key, True, timeout=86400
            )  # 24h - aligné avec le cycle de token

            logger.info(f"Updated verification cache for user {user.id} set to True")

            return (
                True,
                {"success": True, "message": "Email verification successful"},
                200,
            )
        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}")
            return (
                False,
                {
                    "success": False,
                    "error": "An error occurred during verification. Please try again",
                },
                500,
            )

    @staticmethod
    def send_verification_email(user):
        """Envoie un email de vérification à l'utilisateur.

        Args:
            user (User): L'utilisateur à qui envoyer l'email.

        Returns:
            tuple : (success,response_dict,status_code)
        """
        try:
            if user.is_verified:
                return (
                    True,
                    {"success": True, "message": "L'utilisateur est déjà vérifié."},
                    200,
                )
            # Rate imite per user
            rate_key = f"email_verification_rate_{user.id}"
            if cache.get(rate_key):
                # get timeout remaining ( in seconds)
                timeout_value = 300
                return (
                    False,
                    {
                        "success": False,
                        "error": "Veuillez patienter avant de renvoyer l'email de vérification.",
                        "retry_after": timeout_value,
                    },
                    429,
                )

            # queue verification email to be sent on background
            try:
                # Queue verification email to be sent in background
                threading.Thread(
                    target=EmailVerificationService.send_verification_email_background,
                    args=(user.id,),
                    daemon=True,
                ).start()
                # set rate limiting after background thread launch
                cache.set(rate_key, True, timeout=300)  # 5 minutes rate limit
                logger.info(f"Queued verification email for user {user.email}")
                return (
                    True,
                    {
                        "success": True,
                        "message": "L'email de vérification a été envoyé, veuillez consulter votre boîte de réception.",
                    },
                    200,
                )
            except Exception as thread_error:
                logger.error(
                    f"Error starting background thread for verification email: {str(thread_error)}"
                )
                return (
                    False,
                    {
                        "success": False,
                        "error": "Failed to send verification email,please retry later.",
                    },
                    500,
                )
        except Exception as e:
            logger.error(f"Error in send_verification_email service: {str(e)}")
            logger.error(traceback.format_exc())
            return (
                False,
                {
                    "success": False,
                    "error": "An error occurred while sending verification email.",
                },
                400,
            )

    @staticmethod
    def send_verification_email_background(user_id):
        """Background task to send verification email.
        Args:
            user_id (int): ID de l'utilisateur.

        # forward to EmailService

        """
        try:
            # Queue verification email with retry
            EmailService.send_verification_email_background_with_retry(user_id, 3)
            logger.info(f"Verification email queued for user {user_id}")
        except Exception as e:
            logger.error(
                f"Failed to sent background verification email for user {user_id}, {str(e)}"
            )
            logger.error(traceback.format_exc())

    @staticmethod
    def check_verification_status(user):
        """
        check email verification status
        Args:
          user: user object
        Returns:
          tuple: (success, response_dict, status_code)
        """
        try:
            # first try to get status from cache
            cache_key = EmailVerificationService.get_verification_cache_key(user.pk)
            cached_status = cache.get(cache_key)

            # If we have a cache ststus, use it
            if cached_status is not None:
                logger.info(
                    f"Using cached verification status for user: {user.pk}: {cached_status}"
                )
                return (
                    True,
                    {"success": True, "data": {"is_verified": cached_status}},
                    200,
                )
            # if not in cache, query the database
            try:
                # Get fresh user data from DB
                fresh_user = User.objects.get(pk=user.pk)
                is_verified = fresh_user.is_verified

                # cache the result for future queries
                cache.set(
                    cache_key, is_verified, timeout=86400
                )  # 24h - aligné avec le cycle de token

                logger.info(
                    f"fetched verification status from DB for user: {user.pk}: {is_verified}"
                )
                return (
                    True,
                    {"success": True, "data": {"is_verified": is_verified}},
                    200,
                )
            except User.DoesNotExist:
                logger.error("User not found in database")
                return False, {"success": False, "error": "User not found"}, 404
        except Exception as e:
            logger.error(f"Check verification status error: {str(e)}")

            # return last know status from DB to degrade gracefully
            return (
                True,
                {
                    "success": True,
                    "data": {"is_verified": user.is_verified},
                    "message": "Could not check latest status using existing information",
                },
                200,
            )

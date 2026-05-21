import logging
import threading
import traceback
import time
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending user verification emails
    Args:
        user (User): The user to send email to
    Returns:
        bool: success status
    """

    @staticmethod
    def send_verification_email(user):
        """send verification email with both link and code"""
        try:
            # generate verification token for link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verify_url = (
                f"{settings.FRONTEND_URL}/auth/email-verify?uid={uid}&token={token}"
            )
            # compose email
            subject = f"{settings.APP_NAME} - Verify your email address"

            # template context
            context = {
                "user": user,
                "verify_url": verify_url,
                "App_name": settings.APP_NAME,
                "code_expiry": "1 hour",
            }

            try:
                # HTML message
                html_message = render_to_string("emails/verify_email.html", context)
                # plain text fallback
                plain_message = f"""
                    Hello {user.email},
                    Please verify your email address by clicking the link below:
                    
                    {verify_url}
                    Thanks you,
                    {settings.APP_NAME} Team"""
            except Exception as template_error:
                logger.error(f"Error rendering email template: {str(template_error)}")
                html_message = None
                plain_message = f"""
                    Hello {user.email},
                    Please verify your email address by clicking the link below:
                    
                    {verify_url}
                    Thanks you,
                    {settings.APP_NAME} Team"""
            # verify smtp settings
            try:
                # check if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set
                if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                    logger.error(
                        "Email credentials  not configured properly in settings."
                    )
                    return False
                from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
                send_mail(
                    subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"Verification email sent to user {user.email}")
                return True
            except Exception as send_error:
                logger.error(
                    f"SMTP Error sending verification email: {str(send_error)}"
                )
                return False
        except Exception as e:
            logger.error(f"Error in send_verification_email: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    @staticmethod
    def _send_verification_email_with_retry(user_id, max_attempts=3):
        """Internal method to send verification email with retries (runs in background thread)"""
        try:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.error(
                    f"Background verification email: User with id {user_id} not found."
                )
                return

            # check if already verified
            if user.is_verified:
                logger.info(
                    f"Background verification email: User {user.email} is already verified."
                )
                return
            # make multiple attempts with backoff
            for attempt in range(1, max_attempts + 1):
                try:
                    success = EmailService.send_verification_email(user)
                    if success:
                        logger.info(
                            f"Background verification email sent to user {user.email} on attempt {attempt}."
                        )
                        return
                    else:
                        logger.warning(
                            f"Background verification email attempt {attempt} failed for user {user.email}."
                        )
                except Exception as e:
                    logger.error(
                        f"Error sending background verification email to user {user.email} on attempt {attempt}: {str(e)}"
                    )
                # exponential backoff before next attempt
                backoff_time = 2**attempt + random.uniform(0, 1)
                if attempt < max_attempts:
                    time.sleep(backoff_time)
            logger.error(
                f"{max_attempts} attempts to send background verification email to user {user.email} have failed."
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in send_verification_email_background_with_retry: {str(e)}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")

    @staticmethod
    def send_verification_email_background_with_retry(user_id, max_attempts=3):
        """Sends verification email in background thread (non-blocking)"""
        thread = threading.Thread(
            target=EmailService._send_verification_email_with_retry,
            args=(user_id, max_attempts),
            daemon=True
        )
        thread.start()

    @staticmethod
    def send_password_reset_email(user):
        """Send password reset email to user
        Args:
            user (str): user object
        Returns:
            tuple: (bool, reset_code) - success_status
        """
        try:
            # generate verification token for link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = f"{settings.FRONTEND_URL}/auth/password-reset-confirm?uid={uid}&token={token}"
            # compose email
            subject = f"{settings.APP_NAME} - Reset your password"

            # template context
            context = {
                "user": user,
                "reset_url": reset_url,
                "App_name": settings.APP_NAME,
                "code_expiry": "1 hour",
            }

            try:
                # HTML message
                html_message = render_to_string("emails/password_reset.html", context)
                # plain text fallback
                plain_message = f"""
                    Hello {user.email},
                    Your requested to reset your password for your {settings.APP_NAME} account
                    Please the link below to reset your password:
                    
                    {reset_url}

                    If you didn't request this,please ignore this email
                    Thanks you,
                    {settings.APP_NAME} Team"""
            except Exception as template_error:
                logger.error(f"Error rendering email template: {str(template_error)}")
                html_message = None
                plain_message = f"""
                    Hello {user.email},
                    Your requested to reset your password for your {settings.APP_NAME} account
                    Please the link below to reset your password:
                    
                    {reset_url}

                    If you didn't request this,please ignore this email
                    Thanks you,
                    {settings.APP_NAME} Team"""
            # verify smtp settings
            try:
                # check if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set
                if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                    logger.error(
                        "Email credentials  not configured properly in settings."
                    )
                    return False
                from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
                send_mail(
                    subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"password reset email sent to user {user.email}")
                return True
            except Exception as send_error:
                logger.error(
                    f"SMTP Error sending password reset email: {str(send_error)}"
                )
                return False
        except Exception as e:
            logger.error(f"Error in send_password_reset_email: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

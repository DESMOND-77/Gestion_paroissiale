import logging
import threading
import traceback
import time
import random
import os
from email.mime.image import MIMEImage
from django.core.mail import get_connection, EmailMultiAlternatives
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

    # Content-ID du logo embarqué, référencé par src="cid:logo" dans les templates.
    INLINE_LOGO_CID = "logo"

    @staticmethod
    def _attach_inline_logo(message):
        """Embarque le logo en image inline (CID) pour qu'il s'affiche toujours.

        Sans effet si aucun logo n'est configuré/trouvé : l'email part quand même
        (le template affiche alors le texte alternatif).
        """
        logo_path = getattr(settings, "EMAIL_LOGO_PATH", None)
        if not logo_path or not os.path.exists(logo_path):
            if logo_path:
                logger.warning(f"Email logo introuvable: {logo_path}")
            return
        try:
            # Sous-type déduit de l'extension (évite toute détection implicite).
            ext = os.path.splitext(logo_path)[1].lower().lstrip(".")
            subtype = {"jpg": "jpeg"}.get(ext, ext) or "png"
            with open(logo_path, "rb") as f:
                image = MIMEImage(f.read(), _subtype=subtype)
            image.add_header("Content-ID", f"<{EmailService.INLINE_LOGO_CID}>")
            image.add_header(
                "Content-Disposition", "inline", filename=os.path.basename(logo_path)
            )
            # Le sous-type "related" lie l'image au HTML qui la référence via CID.
            # message.mixed_subtype = "related"
            message.attach(image)
        except Exception as e:
            logger.warning(f"Impossible d'embarquer le logo inline: {str(e)}")

    @staticmethod
    def _build_message(
        subject, plain_message, html_message, recipient_list, from_email, connection=None
    ):
        """Construit un EmailMultiAlternatives (texte + HTML + logo inline)."""
        message = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=recipient_list,
            connection=connection,
        )
        if html_message:
            message.attach_alternative(html_message, "text/html")
            EmailService._attach_inline_logo(message)
        return message

    @staticmethod
    def _send_with_fallback(subject, plain_message, html_message, recipient_list):
        """Envoie un email via le backend principal, avec repli SMTP.

        1. Tente l'envoi via le backend par défaut (Resend/Anymail).
        2. En cas d'échec, ré-essaie via une connexion SMTP explicite
           (paramètres EMAIL_HOST/EMAIL_HOST_USER/...).

        Le message est un multipart avec le logo embarqué en inline (CID).

        Args:
            subject (str): Sujet de l'email.
            plain_message (str): Corps texte brut.
            html_message (str | None): Corps HTML (optionnel).
            recipient_list (list[str]): Destinataires.

        Returns:
            bool: True si l'un des backends a réussi, False sinon.
        """
        primary_from = settings.FROM_EMAIL or settings.EMAIL_HOST_USER

        # 1) Backend principal (Resend/Anymail via EMAIL_BACKEND)
        try:
            message = EmailService._build_message(
                subject, plain_message, html_message, recipient_list, primary_from
            )
            message.send(fail_silently=False)
            logger.info(f"Email sent via primary backend to {recipient_list}")
            return True
        except Exception as primary_error:
            logger.error(
                f"Primary email backend failed for {recipient_list}: {str(primary_error)}"
            )

        # 2) Repli SMTP
        fallback_backend = getattr(settings, "EMAIL_FALLBACK_BACKEND", None)
        if not fallback_backend:
            logger.error("No SMTP fallback backend configured; giving up.")
            return False
        if not (
            settings.EMAIL_HOST
            and settings.EMAIL_HOST_USER
            and settings.EMAIL_HOST_PASSWORD
        ):
            logger.error(
                "SMTP fallback credentials incomplete (EMAIL_HOST/USER/PASSWORD); giving up."
            )
            return False

        try:
            use_ssl = str(getattr(settings, "EMAIL_USE_SSL", "False")).lower() in (
                "true",
                "1",
                "yes",
            )
            connection = get_connection(
                backend=fallback_backend,
                host=settings.EMAIL_HOST,
                port=int(settings.EMAIL_PORT),
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_ssl=use_ssl,
                use_tls=not use_ssl,
                timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
                fail_silently=False,
            )
            # En SMTP (Gmail), l'expéditeur doit être l'utilisateur authentifié.
            message = EmailService._build_message(
                subject,
                plain_message,
                html_message,
                recipient_list,
                settings.EMAIL_HOST_USER,
                connection=connection,
            )
            message.send(fail_silently=False)
            logger.info(f"Email sent via SMTP fallback to {recipient_list}")
            return True
        except Exception as fallback_error:
            logger.error(
                f"SMTP fallback also failed for {recipient_list}: {str(fallback_error)}"
            )
            return False

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
            subject = f"{settings.APP_NAME} — Confirmez votre adresse e-mail"

            # template context
            context = {
                "user": user,
                "verify_url": verify_url,
                "app_name": settings.APP_NAME,
                "code_expiry": "2 heures",
            }

            # Corps texte brut (repli si le client n'affiche pas le HTML)
            plain_message = (
                f"Bonjour {user.prenom or user.email},\n\n"
                f"Votre compte {settings.APP_NAME} a bien été créé. "
                f"Confirmez votre adresse e-mail pour l'activer en ouvrant le lien ci-dessous :\n\n"
                f"{verify_url}\n\n"
                f"Ce lien est valable {context['code_expiry']}. "
                f"Si vous n'êtes pas à l'origine de cette inscription, ignorez ce message.\n\n"
                f"— L'équipe {settings.APP_NAME}"
            )

            try:
                # Version HTML
                html_message = render_to_string("emails/verify_email.html", context)
            except Exception as template_error:
                logger.error(f"Error rendering email template: {str(template_error)}")
                html_message = None
            # Envoi avec repli SMTP automatique si le backend principal échoue
            sent = EmailService._send_with_fallback(
                subject=subject,
                plain_message=plain_message,
                html_message=html_message,
                recipient_list=[user.email],
            )
            if sent:
                logger.info(f"Verification email sent to user {user.email}")
            else:
                logger.error(
                    f"All email backends failed for verification email to {user.email}"
                )
            return sent
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
            subject = f"{settings.APP_NAME} — Réinitialisez votre mot de passe"

            # template context
            context = {
                "user": user,
                "reset_url": reset_url,
                "app_name": settings.APP_NAME,
                "code_expiry": "2 heures",
            }

            # Corps texte brut (repli si le client n'affiche pas le HTML)
            plain_message = (
                f"Bonjour {user.prenom or user.email},\n\n"
                f"Nous avons reçu une demande de réinitialisation du mot de passe de votre "
                f"compte {settings.APP_NAME}. Ouvrez le lien ci-dessous pour en choisir un nouveau :\n\n"
                f"{reset_url}\n\n"
                f"Ce lien expire dans {context['code_expiry']}. "
                f"Si vous n'avez pas fait cette demande, ignorez ce message : votre mot de passe reste inchangé.\n\n"
                f"— L'équipe {settings.APP_NAME}"
            )

            try:
                # Version HTML
                html_message = render_to_string("emails/password_reset.html", context)
            except Exception as template_error:
                logger.error(f"Error rendering email template: {str(template_error)}")
                html_message = None
            # Envoi avec repli SMTP automatique si le backend principal échoue
            sent = EmailService._send_with_fallback(
                subject=subject,
                plain_message=plain_message,
                html_message=html_message,
                recipient_list=[user.email],
            )
            if sent:
                logger.info(f"password reset email sent to user {user.email}")
            else:
                logger.error(
                    f"All email backends failed for password reset email to {user.email}"
                )
            return sent
        except Exception as e:
            logger.error(f"Error in send_password_reset_email: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

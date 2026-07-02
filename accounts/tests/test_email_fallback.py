"""Tests du repli SMTP de EmailService._send_with_fallback."""
from unittest import mock

from django.test import SimpleTestCase, override_settings

from accounts.verification.emails import EmailService

SEND_MAIL = "accounts.verification.emails.send_mail"
GET_CONNECTION = "accounts.verification.emails.get_connection"

SMTP_SETTINGS = dict(
    FROM_EMAIL="noreply@example.com",
    EMAIL_FALLBACK_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="smtp.gmail.com",
    EMAIL_PORT=587,
    EMAIL_USE_SSL="False",
    EMAIL_HOST_USER="fallback@gmail.com",
    EMAIL_HOST_PASSWORD="app-password",
    EMAIL_TIMEOUT=10,
)


@override_settings(**SMTP_SETTINGS)
class EmailFallbackTests(SimpleTestCase):
    def _call(self):
        return EmailService._send_with_fallback(
            subject="Sujet",
            plain_message="corps",
            html_message="<b>corps</b>",
            recipient_list=["dest@example.com"],
        )

    @mock.patch(SEND_MAIL)
    def test_primary_success_no_fallback(self, mock_send):
        # Le backend principal réussit : pas de repli.
        self.assertTrue(self._call())
        self.assertEqual(mock_send.call_count, 1)

    @mock.patch(GET_CONNECTION)
    @mock.patch(SEND_MAIL)
    def test_falls_back_to_smtp_on_primary_failure(self, mock_send, mock_conn):
        # 1er appel (principal) échoue, 2e appel (SMTP) réussit.
        mock_send.side_effect = [Exception("Resend 403"), None]
        self.assertTrue(self._call())
        self.assertEqual(mock_send.call_count, 2)
        mock_conn.assert_called_once()
        # La connexion de repli utilise bien le backend SMTP configuré.
        self.assertEqual(
            mock_conn.call_args.kwargs["backend"],
            "django.core.mail.backends.smtp.EmailBackend",
        )
        # L'expéditeur SMTP est l'utilisateur authentifié (contrainte Gmail).
        self.assertEqual(
            mock_send.call_args.kwargs["from_email"], "fallback@gmail.com"
        )

    @mock.patch(GET_CONNECTION)
    @mock.patch(SEND_MAIL)
    def test_returns_false_when_both_backends_fail(self, mock_send, _mock_conn):
        mock_send.side_effect = Exception("boom")
        self.assertFalse(self._call())
        self.assertEqual(mock_send.call_count, 2)

    @override_settings(EMAIL_FALLBACK_BACKEND="")
    @mock.patch(SEND_MAIL)
    def test_no_fallback_when_disabled(self, mock_send):
        mock_send.side_effect = Exception("Resend 403")
        self.assertFalse(self._call())
        # Pas de second envoi puisque le repli est désactivé.
        self.assertEqual(mock_send.call_count, 1)

    @override_settings(EMAIL_HOST_USER="")
    @mock.patch(SEND_MAIL)
    def test_no_fallback_when_smtp_credentials_missing(self, mock_send):
        mock_send.side_effect = Exception("Resend 403")
        self.assertFalse(self._call())
        self.assertEqual(mock_send.call_count, 1)

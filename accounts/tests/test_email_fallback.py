"""Tests du repli SMTP et de l'embarquement du logo (CID) de EmailService."""
import os
import tempfile
from unittest import mock

from django.test import SimpleTestCase, override_settings

from accounts.verification.emails import EmailService

# Patch au niveau de l'envoi du message (EmailMultiAlternatives.send).
SEND = "accounts.verification.emails.EmailMultiAlternatives.send"
GET_CONNECTION = "accounts.verification.emails.get_connection"

# Un PNG 1x1 valide, pour tester l'embarquement inline sans dépendre d'un asset.
_PNG_1x1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

SMTP_SETTINGS = dict(
    FROM_EMAIL="noreply@example.com",
    EMAIL_FALLBACK_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="smtp.gmail.com",
    EMAIL_PORT=587,
    EMAIL_USE_SSL="False",
    EMAIL_HOST_USER="fallback@gmail.com",
    EMAIL_HOST_PASSWORD="app-password",
    EMAIL_TIMEOUT=10,
    EMAIL_LOGO_PATH=None,  # pas de logo par défaut dans ces tests d'envoi
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

    @mock.patch(SEND, autospec=True)
    def test_primary_success_no_fallback(self, mock_send):
        self.assertTrue(self._call())
        self.assertEqual(mock_send.call_count, 1)

    @mock.patch(GET_CONNECTION)
    @mock.patch(SEND, autospec=True)
    def test_falls_back_to_smtp_on_primary_failure(self, mock_send, mock_conn):
        # 1er envoi (principal) échoue, 2e envoi (SMTP) réussit.
        mock_send.side_effect = [Exception("Resend 403"), None]
        self.assertTrue(self._call())
        self.assertEqual(mock_send.call_count, 2)
        mock_conn.assert_called_once()
        self.assertEqual(
            mock_conn.call_args.kwargs["backend"],
            "django.core.mail.backends.smtp.EmailBackend",
        )
        # Le message de repli part avec l'expéditeur SMTP authentifié (Gmail).
        fallback_message = mock_send.call_args_list[1].args[0]
        self.assertEqual(fallback_message.from_email, "fallback@gmail.com")

    @mock.patch(GET_CONNECTION)
    @mock.patch(SEND, autospec=True)
    def test_returns_false_when_both_backends_fail(self, mock_send, _mock_conn):
        mock_send.side_effect = Exception("boom")
        self.assertFalse(self._call())
        self.assertEqual(mock_send.call_count, 2)

    @override_settings(EMAIL_FALLBACK_BACKEND="")
    @mock.patch(SEND, autospec=True)
    def test_no_fallback_when_disabled(self, mock_send):
        mock_send.side_effect = Exception("Resend 403")
        self.assertFalse(self._call())
        self.assertEqual(mock_send.call_count, 1)

    @override_settings(EMAIL_HOST_USER="")
    @mock.patch(SEND, autospec=True)
    def test_no_fallback_when_smtp_credentials_missing(self, mock_send):
        mock_send.side_effect = Exception("Resend 403")
        self.assertFalse(self._call())
        self.assertEqual(mock_send.call_count, 1)


class InlineLogoTests(SimpleTestCase):
    def _build(self):
        return EmailService._build_message(
            subject="Sujet",
            plain_message="corps",
            html_message='<img src="cid:logo">',
            recipient_list=["dest@example.com"],
            from_email="noreply@example.com",
        )

    def test_logo_embedded_as_inline_cid(self):
        with tempfile.TemporaryDirectory() as d:
            logo = os.path.join(d, "logo.png")
            with open(logo, "wb") as f:
                f.write(_PNG_1x1)
            with override_settings(EMAIL_LOGO_PATH=logo):
                message = self._build()

        # Le message porte bien une image inline avec le Content-ID "logo".
        payloads = message.message().get_payload()
        cids = [
            p.get("Content-ID")
            for p in _walk(message.message())
            if p.get("Content-ID")
        ]
        self.assertIn("<logo>", cids)
        # Structure "related" pour lier l'image au HTML.
        self.assertEqual(message.mixed_subtype, "related")
        self.assertTrue(payloads)

    def test_missing_logo_does_not_break_send(self):
        with override_settings(EMAIL_LOGO_PATH="/chemin/inexistant/logo.png"):
            message = self._build()
        # Pas d'image embarquée, mais le message reste valide (HTML présent).
        self.assertTrue(any(
            part.get_content_type() == "text/html"
            for part in _walk(message.message())
        ))


def _walk(msg):
    """Aplati récursivement toutes les parties MIME d'un message."""
    if msg.is_multipart():
        for part in msg.get_payload():
            yield from _walk(part)
    else:
        yield msg

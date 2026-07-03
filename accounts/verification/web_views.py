"""Pages HTML conviviales (rendues par Django) pour les liens des emails :
vérification d'adresse e-mail et réinitialisation du mot de passe.

Ces vues servent de vraies pages web (pas des réponses JSON de l'API). Elles
réutilisent la logique métier des services existants.
"""
import logging

from django.conf import settings
from django.shortcuts import render
from django.views import View

from accounts.verification.services import EmailVerificationService
from accounts.verification.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)

# Message de secours en français pour le lien invalide (le service renvoie un
# texte en anglais que l'on ne veut pas exposer tel quel à l'utilisateur).
_INVALID_LINK_FR = (
    "Ce lien est invalide ou a expiré. Veuillez relancer la procédure pour en "
    "obtenir un nouveau."
)


class EmailVerifyPageView(View):
    """Page affichant le résultat de la vérification d'adresse e-mail."""

    template_name = "auth/verify_email_result.html"

    def get(self, request):
        uid = request.GET.get("uid")
        token = request.GET.get("token")
        ctx = {"app_name": settings.APP_NAME, "login_url": settings.PUBLIC_BASE_URL}

        if not uid or not token:
            ctx.update(status="error", message=_INVALID_LINK_FR)
            return render(request, self.template_name, ctx, status=400)

        success, _, code = EmailVerificationService.verify_email(uid, token)
        if success:
            ctx.update(
                status="success",
                message="Votre adresse e-mail a été confirmée. Votre compte est "
                "désormais actif — vous pouvez fermer cette page et retourner à l'application.",
            )
            return render(request, self.template_name, ctx)

        ctx.update(status="error", message=_INVALID_LINK_FR)
        return render(request, self.template_name, ctx, status=code or 400)


class PasswordResetPageView(View):
    """Formulaire de choix d'un nouveau mot de passe (deux champs) + résultat."""

    template_name = "auth/password_reset_form.html"

    def _ctx(self, uid, token, **extra):
        base = {
            "app_name": settings.APP_NAME,
            "login_url": settings.PUBLIC_BASE_URL,
            "uid": uid,
            "token": token,
        }
        base.update(extra)
        return base

    def get(self, request):
        uid = request.GET.get("uid")
        token = request.GET.get("token")
        if not uid or not token:
            ctx = self._ctx(uid, token, state="invalid_link", error=_INVALID_LINK_FR)
            return render(request, self.template_name, ctx, status=400)
        return render(request, self.template_name, self._ctx(uid, token, state="form"))

    def post(self, request):
        uid = request.POST.get("uid")
        token = request.POST.get("token")
        new_password = request.POST.get("new_password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if not uid or not token:
            ctx = self._ctx(uid, token, state="invalid_link", error=_INVALID_LINK_FR)
            return render(request, self.template_name, ctx, status=400)

        if new_password != confirm_password:
            ctx = self._ctx(
                uid, token, state="form",
                error="Les deux mots de passe ne correspondent pas.",
            )
            return render(request, self.template_name, ctx, status=400)

        success, response, code = PasswordResetService.confirm_reset(
            uid, token, new_password
        )
        if success:
            ctx = self._ctx(
                uid, token, state="success",
                message="Votre mot de passe a été réinitialisé. Vous pouvez "
                "maintenant vous connecter avec vos nouveaux identifiants. Fermez cette page et retournez à l'application.",
            )
            return render(request, self.template_name, ctx)

        # Échec : lien invalide (message anglais du service) ou mot de passe rejeté
        # par les validateurs (messages déjà en français).
        raw_error = response.get("error") if isinstance(response, dict) else None
        if not raw_error or "Invalid password reset link" in raw_error:
            error = _INVALID_LINK_FR
            state = "invalid_link"
        else:
            error = raw_error
            state = "form"
        ctx = self._ctx(uid, token, state=state, error=error)
        return render(request, self.template_name, ctx, status=code or 400)

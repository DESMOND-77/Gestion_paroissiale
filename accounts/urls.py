from django.urls import path

from accounts.verification.web_views import EmailVerifyPageView, PasswordResetPageView
from .auth.views import (
    ChangePasswordView,
    CheckPermissionView,
    MeView,
    UserActivityView,
    UserDetailView,
    UserListView,
    UserLoginView,
    UserRegistrationView,
    TokenRefreshView,
    ValidateTokenView,
    LogOutView,
)
from .profile.views import UserProfileView
from .verification.views import (
    SendVerificationEmailView,
    CheckVerificationStatusView,
    PasswordResetView,
)

urlpatterns = [
    # Auth
    path("auth/register/", UserRegistrationView.as_view(), name="register"),
    path("auth/login/", UserLoginView.as_view(), name="login"),
    path("auth/logout/", LogOutView.as_view(), name="logout"),
    # token
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/validate/", ValidateTokenView.as_view(), name="validate_token"),
    path("auth/me/", MeView.as_view(), name="me"),
    # Profile routes
    path("user/profile/", UserProfileView.as_view(), name="profile"),
    path("user/change-password/", ChangePasswordView.as_view(), name="change_password"),
    # User management (admin only)
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="user_detail"),
    # Activity logs (admin only)
    path("activities/", UserActivityView.as_view(), name="user_activities"),
    # Permission check
    path("check-permission/", CheckPermissionView.as_view(), name="check_permission"),
    # Vérification d'email : la vérification par lien est gérée par la page HTML
    # `web_verify_email` .
    # Pages HTML conviviales (liens des emails)
    path("verify-email/", EmailVerifyPageView.as_view(), name="web_verify_email"),
    path("reset-password/", PasswordResetPageView.as_view(), name="web_password_reset"),
    path(
        "auth/send-verification/",
        SendVerificationEmailView.as_view(),
        name="send_verification",
    ),
    path(
        "auth/verification-status/",
        CheckVerificationStatusView.as_view(),
        name="check_verification",
    ),
    # Réinitialisation : demande d'envoi du lien ici ; la confirmation (nouveau mot
    # de passe) est gérée par la page HTML `web_password_reset` (ci-dessus).
    path("auth/password-reset/", PasswordResetView.as_view(), name="password_reset"),
]

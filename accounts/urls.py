from django.urls import path, include
from rest_framework.routers import DefaultRouter


from rest_framework_simplejwt.views import TokenRefreshView


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
    VerifyEmailView,
    SendVerificationEmailView,
    CheckVerificationStatusView,
    PasswordResetView,
    ConfirmPasswordResetView,
)

urlpatterns = [
    # path("us", include(router.urls)),
    # Auth
    path("auth/register/", UserRegistrationView.as_view(), name="register"),
    path("auth/login/", UserLoginView.as_view(), name="login"),
    path("auth/logout/", LogOutView.as_view(), name="logout"),
    # token
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/validate/", ValidateTokenView.as_view(), name="validate_token"),
    path("auth/me/", MeView.as_view(), name="me"),
    # password reset
    path("auth/password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "auth/password-reset-confirm/",
        ConfirmPasswordResetView.as_view(),
        name="confirm_password_reset",
    ),
    # Profile routes
    path("user/profile/", UserProfileView.as_view(), name="profile"),
    path("user/change-password/", ChangePasswordView.as_view(), name="change_password"),
    # User management (admin only)
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    # Activity logs (admin only)
    path("activities/", UserActivityView.as_view(), name="user_activities"),
    # Permission check
    path("check-permission/", CheckPermissionView.as_view(), name="check_permission"),
    # verification routes
    path("auth/email-verify/", VerifyEmailView.as_view(), name="verify_email"),
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
]

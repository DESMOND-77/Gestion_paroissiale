from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class AccountLockedException(APIException):
    status_code = 403
    default_detail = _("Your account has been locked. Please contact support.")
    default_code = "account_locked"


class EmailNotVerifiedException(APIException):
    status_code = 401
    default_detail = _("Email address not verified. Please verify your email to proceed.")
    default_code = "email_not_verified"


class InvalidTokenException(APIException):
    status_code = 400
    default_detail = _("The provided token is invalid or has expired.")
    default_code = "invalid_token"


class PermissionDeniedException(APIException):
    status_code = 403
    default_detail = _("You do not have permission to perform this action.")
    default_code = "permission_denied"


class RateLimitExceededException(APIException):
    status_code = 429
    default_detail = _("Rate limit exceeded. Please try again later.")
    default_code = "rate_limit_exceeded"

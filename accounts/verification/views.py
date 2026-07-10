import logging
import traceback

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import status

from accounts.serializers import PasswordResetSerializer
from accounts.verification.password_reset_service import PasswordResetService
from core.base_view import BaseAPIView
from core.response import standardized_response
from .services import EmailVerificationService

logger = logging.getLogger(__name__)


class SendVerificationEmailView(BaseAPIView):
    """
    Endpoint for sending verification email
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        # use service layer for sending verification email
        try:
            success, response_data, status_code = (
                EmailVerificationService.send_verification_email(request.user)
            )
            return Response(standardized_response(**response_data), status=status_code)
        except Exception as e:
            logger.error(f"Send verification email error : {str(e)}")
            logger.error(traceback.format_exc)
            return Response(
                standardized_response(
                    success=False,
                    error="Failed to send verification email. Please try again later",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )


class CheckVerificationStatusView(BaseAPIView):
    """Endpoint for checking verification status"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        try:
            success, response_data, status_code = (
                EmailVerificationService.check_verification_status(request.user)
            )
            # Log the verification status
            logger.info(
                f"Verification status check for user: {request.user.pk}: {response_data.get('data', {}).get('is_verified')}"
            )
            return Response(
                standardized_response(**response_data),
                status=status_code,
            )
        except Exception as e:
            logger.error(f"Check verification status error: {str(e)}")
            logger.error(traceback.format_exc())

            # Fallback to request.user if all else fails
            return Response(
                standardized_response(
                    success=True,
                    data={"is_verified": request.user.is_verified},
                    message="Could not check status using, existing information",
                ),
                status=status.HTTP_200_OK,
            )


class PasswordResetView(BaseAPIView):
    """
    Endpoint for requesting password reset
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @swagger_auto_schema(
        operation_description="Demander la réinitialisation du mot de passe",
        request_body=PasswordResetSerializer,
        responses={
            200: openapi.Response(
                description="Demande traitée avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(description="Email invalide ou manquant"),
        },
        tags=["Password Reset"],
    )
    def post(self, request):
        try:
            email = request.data.get("email")

            if not email:
                return Response(
                    standardized_response(success=False, error="Email is required"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # use service layer for password reset logic
            success, response_data, status_code = PasswordResetService.request_reset(
                email
            )

            return Response(
                standardized_response(**response_data),
                status=status_code,
            )

        except Exception as e:
            logger.error(f"Password reset  error: {str(e)}")
            logger.error(traceback.format_exc())

            # Fallback
            return Response(
                standardized_response(
                    success=True,
                    message="If an account exist with this email,a password reset link will be sent.",
                ),
                status=status.HTTP_200_OK,
            )

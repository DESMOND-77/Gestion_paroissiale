import logging
import traceback

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import status

from accounts.models import UserActivity
from core.base_view import BaseAPIView
from core.response import standardized_response
from .services import ProfileService

logger = logging.getLogger(__name__)


class UserProfileView(BaseAPIView):
    """API endpoint for user profile operations"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """get User profile data"""
        try:
            # use service layer to get user profile data
            user_data = ProfileService.get_profile(request.user, request=request)
            return Response(standardized_response(success=True, data=user_data))
        except Exception as e:
            logger.error(f"Profile fetch error: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                standardized_response(
                    success=False, error="Failed to retrieve profile"
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _log_profile_update(self, request):
        UserActivity.objects.create(
            user=request.user,
            action="update",
            details="Mise à jour du profil",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

    def put(self, request):
        """Update full user profile"""
        try:
            success, response_data, status_code = ProfileService.update_profile(
                user=request.user, data=request.data, files=request.FILES, request=request
            )
            if success:
                self._log_profile_update(request)
            return Response(standardized_response(**response_data), status=status_code)
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                standardized_response(success=False, error="Profile update failed"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        """Partial user profile update"""
        try:
            success, response_data, status_code = ProfileService.update_profile(
                user=request.user, data=request.data, files=request.FILES, request=request
            )
            if success:
                self._log_profile_update(request)
            return Response(standardized_response(**response_data), status=status_code)
        except Exception as e:
            logger.error(f"Profile patch error: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                standardized_response(success=False, error="Profile update failed"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

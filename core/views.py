from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.response import standardized_response
from .health import get_health_status


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring application status.

    Returns status of Redis cache and Database.
    Accessible without authentication.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        health = get_health_status()
        is_healthy = all(health.values())

        return Response(
            standardized_response(
                success=is_healthy,
                data=health,
                message=(
                    "Application health check"
                    if is_healthy
                    else "One or more services are down"
                ),
            ),
            status=(
                status.HTTP_200_OK
                if is_healthy
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )

import logging
import traceback

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .response import standardized_response

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Vue de base pour toutes les vues APIView.
    Centralise la gestion des erreurs et fournit check_extra_permission().
    """

    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response(
                standardized_response(success=False, message=str(exc)),
                status=status.HTTP_401_UNAUTHORIZED,
            )
        logger.error(f"Exception in {self.__class__.__name__}: {str(exc)}")
        traceback_str = "".join(traceback.format_tb(exc.__traceback__))
        logger.error(f"Traceback: {traceback_str}")
        return super().handle_exception(exc)

    def check_extra_permission(self, request, permission):
        """Assert a single permission instance; raises PermissionDenied if it fails."""
        if not permission.has_permission(request, self):
            self.permission_denied(
                request, message=getattr(permission, "message", None)
            )

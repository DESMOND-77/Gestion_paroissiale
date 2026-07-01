import logging
import traceback

from rest_framework import status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .response import standardized_response

logger = logging.getLogger(__name__)


class _ExceptionHandlerMixin:
    """Shared error handling for all base view classes."""

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


class BaseAPIView(_ExceptionHandlerMixin, APIView):
    """Base view for APIView subclasses with centralised error handling."""
    pass


class BaseModelViewSet(_ExceptionHandlerMixin, viewsets.ModelViewSet):
    """Base ModelViewSet with centralised error handling."""
    pass


class BaseViewSet(_ExceptionHandlerMixin, viewsets.ViewSet):
    """Base ViewSet with centralised error handling."""
    pass

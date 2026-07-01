"""
Custom exception handler for DRF to handle unsupported media types gracefully.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.response import Response
from rest_framework import status
from .response import standardized_response


def custom_exception_handler(exc, context):
    """
    Custom exception handler that catches UnsupportedMediaType errors
    and returns a standardized response.
    """
    # Handle UnsupportedMediaType exception
    if isinstance(exc, UnsupportedMediaType):
        media_type = exc.media_type or "unknown"
        return Response(
            standardized_response(
                success=False,
                error=f"Type de média « {media_type} » non supporté. Utilisez 'application/json'."
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Call the default exception handler first to get the standard error response
    response = exception_handler(exc, context)
    
    # If the response is None, it means the exception was not handled by DRF
    if response is None:
        return None
    
    # Wrap other exceptions with our standardized response format
    return response

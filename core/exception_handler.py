"""
Gestionnaire d'exceptions personnalisé pour DRF.

Garantit que TOUTES les réponses d'erreur respectent le format Core
(`standardized_response`) : {success, data, error, message}.
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.response import Response
from rest_framework import status

from .response import standardized_response


def _extract_error(data):
    """Transforme le corps d'erreur par défaut de DRF en (error, message).

    DRF renvoie selon le cas :
      - {"detail": "..."} pour auth / permission / 404 / throttling
      - {"champ": ["err1", "err2"], ...} pour les erreurs de validation
      - une liste de messages
      - une chaîne
    """
    if isinstance(data, dict):
        # Cas standard : clé "detail"
        if "detail" in data and len(data) == 1:
            return str(data["detail"]), None
        # Erreurs de validation par champ : on garde le détail structuré
        return data, "Erreur de validation des données."
    if isinstance(data, list):
        return data, "Erreur de validation des données."
    return str(data), None


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions qui enveloppe toutes les réponses d'erreur
    DRF dans le format standardisé Core.
    """
    # Type de média non supporté
    if isinstance(exc, UnsupportedMediaType):
        media_type = exc.media_type or "unknown"
        return Response(
            standardized_response(
                success=False,
                error=f"Type de média « {media_type} » non supporté. Utilisez 'application/json'.",
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Laisser DRF produire la réponse standard d'abord
    response = exception_handler(exc, context)

    # None => exception non gérée par DRF (sera une 500 non standardisée,
    # traitée en amont par BaseAPIView / middleware)
    if response is None:
        return None

    # Si déjà au format Core (vue qui a levé une erreur avec ce format), ne rien changer
    if isinstance(response.data, dict) and "success" in response.data:
        return response

    error, message = _extract_error(response.data)
    response.data = standardized_response(
        success=False,
        error=error,
        message=message,
    )
    return response

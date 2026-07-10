from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.base_view import BaseAPIView
from core.response import standardized_response
from core.sync import run_sync
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


class SyncView(BaseAPIView):
    """Synchronisation bidirectionnelle offline → serveur central.

    Corps de requête (JSON) ::

        {
          "since": "2026-07-10T08:00:00Z",   // curseur (null au premier appel)
          "changes": {                        // modifications locales à pousser
            "membres": [ { "id": "<uuid>", "nom": "...", "updated_at": "...",
                           "is_deleted": false }, ... ],
            "transactions": [ ... ]
          }
        }

    Réponse : `server_time` (nouveau curseur à conserver), `results`
    (applied / conflicts / errors par collection) et `changes` (ce que le
    client doit intégrer). Cf. `core.sync`.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data or {}
        since = payload.get("since")
        changes = payload.get("changes") or {}

        if not isinstance(changes, dict):
            return Response(
                standardized_response(
                    success=False,
                    error="`changes` doit être un objet { collection: [...] }.",
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = run_sync(changes, since)
        return Response(
            standardized_response(success=True, data=result),
            status=status.HTTP_200_OK,
        )

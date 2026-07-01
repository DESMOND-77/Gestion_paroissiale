import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.base_view import BaseAPIView
from core.permissions import IsAdmin
from core.response import standardized_response
from .models import Groupe
from .serializers import GroupeSerializer
from .services import GroupeService

logger = logging.getLogger(__name__)


class GroupeListView(BaseAPIView):
    """
    GET  /api/groupes/          — liste (filtrable via ?nom=)
    POST /api/groupes/          — création (admin uniquement)
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        nom = request.query_params.get("nom", "")
        qs = GroupeService.search_groupes(nom=nom).select_related("responsable")
        logger.info(f"Retrieved {qs.count()} groupes for user {request.user}")
        return Response(standardized_response(data=GroupeSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating groupe by user {request.user}: {request.data.get('nom', 'Unknown')}")
        serializer = GroupeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        groupe = GroupeService.create_groupe(
            nom=validated["nom"],
            responsable=validated.get("responsable"),
            **{k: v for k, v in validated.items() if k not in ("nom", "responsable")},
        )
        logger.info(f"Groupe created successfully: {groupe.id} ({groupe.nom})")
        return Response(
            standardized_response(data=GroupeSerializer(groupe).data, message="Groupe créé avec succès"),
            status=status.HTTP_201_CREATED,
        )


class GroupeDetailView(BaseAPIView):
    """
    GET    /api/groupes/<pk>/   — détail
    PUT    /api/groupes/<pk>/   — mise à jour complète (admin)
    PATCH  /api/groupes/<pk>/   — mise à jour partielle (admin)
    DELETE /api/groupes/<pk>/   — suppression (admin)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdmin()]

    def _get_groupe(self, pk):
        return get_object_or_404(Groupe.objects.select_related("responsable"), pk=pk)

    def get(self, request, pk):
        groupe = self._get_groupe(pk)
        logger.debug(f"Retrieving groupe {pk} for user {request.user}")
        return Response(standardized_response(data=GroupeSerializer(groupe).data))

    def put(self, request, pk):
        groupe = self._get_groupe(pk)
        logger.info(f"Updating groupe {pk} by user {request.user}")
        serializer = GroupeSerializer(groupe, data=request.data)
        serializer.is_valid(raise_exception=True)
        groupe = GroupeService.update_groupe(groupe, **serializer.validated_data)
        logger.info(f"Groupe {pk} updated successfully")
        return Response(standardized_response(data=GroupeSerializer(groupe).data, message="Groupe modifié"))

    def patch(self, request, pk):
        groupe = self._get_groupe(pk)
        logger.info(f"Partial update groupe {pk} by user {request.user}")
        serializer = GroupeSerializer(groupe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        groupe = GroupeService.update_groupe(groupe, **serializer.validated_data)
        logger.info(f"Groupe {pk} updated successfully")
        return Response(standardized_response(data=GroupeSerializer(groupe).data, message="Groupe modifié"))

    def delete(self, request, pk):
        groupe = self._get_groupe(pk)
        logger.warning(f"Deleting groupe {pk} ({groupe.nom}) by user {request.user}")
        groupe.delete()
        logger.info(f"Groupe {pk} deleted successfully")
        return Response(standardized_response(message="Groupe supprimé"), status=status.HTTP_204_NO_CONTENT)


class GroupeMembresView(BaseAPIView):
    """
    GET /api/groupes/<pk>/membres/  — liste des membres du groupe avec statistiques
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from membres.serializers import MembreSerializer
        groupe = get_object_or_404(Groupe, pk=pk)
        logger.debug(f"Retrieving membres for groupe {pk}")

        count = GroupeService.get_groupe_membres_count(groupe)
        membres = groupe.membres.select_related("user").all()
        logger.info(f"Retrieved {count} membres for groupe {pk}")
        return Response(standardized_response(
            data={
                "groupe": groupe.nom,
                "total_membres": count,
                "membres": MembreSerializer(membres, many=True).data,
            }
        ))

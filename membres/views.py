import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from core.base_view import BaseAPIView
from core.permissions import IsAdmin, IsSecretaryOrAbove
from core.response import standardized_response
from .models import Membre
from .serializers import MembreSerializer, MembreDetailSerializer, SacrementSerializer
from .services import MembreService

logger = logging.getLogger(__name__)


class MembreListView(BaseAPIView):
    """
    GET  /api/membres/          — liste (filtrable via ?nom=&prenom=&groupe=)
    POST /api/membres/          — création
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request):
        nom = request.query_params.get("nom", "")
        prenom = request.query_params.get("prenom", "")
        groupe = request.query_params.get("groupe")

        qs = MembreService.search_membres(nom=nom, prenom=prenom, groupe=groupe)
        qs = qs.select_related("groupe", "user")
        logger.info(f"Retrieved {qs.count()} membres for user {request.user}")
        return Response(standardized_response(data=MembreSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating membre by user {request.user}: {request.data}")
        serializer = MembreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membre = MembreService.create_membre(**serializer.validated_data)
        logger.info(f"Membre created successfully: {membre.id}")
        return Response(
            standardized_response(data=MembreSerializer(membre).data, message="Membre créé avec succès"),
            status=status.HTTP_201_CREATED,
        )


class MembreDetailView(BaseAPIView):
    """
    GET    /api/membres/<pk>/   — détail + statistiques
    PUT    /api/membres/<pk>/   — mise à jour complète
    PATCH  /api/membres/<pk>/   — mise à jour partielle
    DELETE /api/membres/<pk>/   — suppression (admin uniquement)
    """

    permission_classes = [IsSecretaryOrAbove]

    def _get_membre(self, pk):
        return get_object_or_404(Membre.objects.select_related("groupe", "user"), pk=pk)

    def get(self, request, pk):
        membre = self._get_membre(pk)
        logger.debug(f"Retrieving membre {pk} for user {request.user}")
        stats = MembreService.get_membre_statistics(membre)
        data = MembreDetailSerializer(membre).data
        data["statistiques"] = stats
        return Response(standardized_response(data=data))

    def put(self, request, pk):
        membre = self._get_membre(pk)
        logger.info(f"Updating membre {pk} by user {request.user}")
        serializer = MembreSerializer(membre, data=request.data)
        serializer.is_valid(raise_exception=True)
        membre = MembreService.update_membre(membre, **serializer.validated_data)
        logger.info(f"Membre {pk} updated successfully")
        return Response(standardized_response(data=MembreSerializer(membre).data, message="Membre modifié"))

    def patch(self, request, pk):
        membre = self._get_membre(pk)
        logger.info(f"Partial update membre {pk} by user {request.user}")
        serializer = MembreSerializer(membre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        membre = MembreService.update_membre(membre, **serializer.validated_data)
        logger.info(f"Membre {pk} updated successfully")
        return Response(standardized_response(data=MembreSerializer(membre).data, message="Membre modifié"))

    def delete(self, request, pk):
        self.check_extra_permission(request, IsAdmin())
        membre = self._get_membre(pk)
        logger.warning(f"Deleting membre {pk} by user {request.user}")
        membre.delete()
        logger.info(f"Membre {pk} deleted successfully")
        return Response(standardized_response(message="Membre supprimé"), status=status.HTTP_204_NO_CONTENT)


class MembreSacrementsView(BaseAPIView):
    """
    GET  /api/membres/<pk>/sacrements/  — liste des sacrements
    POST /api/membres/<pk>/sacrements/  — ajout d'un sacrement
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request, pk):
        membre = get_object_or_404(Membre, pk=pk)
        logger.debug(f"Retrieving sacrements for membre {pk}")
        sacrements = membre.sacrements.all()
        logger.info(f"Retrieved {sacrements.count()} sacrements for membre {pk}")
        return Response(standardized_response(data=SacrementSerializer(sacrements, many=True).data))

    def post(self, request, pk):
        membre = get_object_or_404(Membre, pk=pk)
        logger.info(f"Adding sacrement to membre {pk} by user {request.user}")
        serializer = SacrementSerializer(data={**request.data, "membre": membre.id})
        serializer.is_valid(raise_exception=True)
        sacrement = serializer.save(membre=membre)
        logger.info(f"Sacrement {sacrement.id} added to membre {pk}")
        return Response(
            standardized_response(data=SacrementSerializer(sacrement).data, message="Sacrement enregistré"),
            status=status.HTTP_201_CREATED,
        )

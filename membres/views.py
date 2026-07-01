import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.base_view import BaseModelViewSet
from core.permissions import IsAdmin, IsSecretaryOrAbove
from core.response import standardized_response
from .models import Membre, Sacrement
from .serializers import MembreSerializer, MembreDetailSerializer, SacrementSerializer
from .services import MembreService

logger = logging.getLogger(__name__)


class MembreViewSet(BaseModelViewSet):
    queryset = Membre.objects.select_related("groupe", "user").all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MembreDetailSerializer
        return MembreSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]
        if self.action in ("list", "retrieve"):
            return [IsSecretaryOrAbove()]
        return [IsSecretaryOrAbove()]

    def list(self, request, *args, **kwargs):
        logger.debug(f"Listing membres for user {request.user}")
        qs = self.get_queryset()
        logger.info(f"Retrieved {qs.count()} membres")
        serializer = self.get_serializer(qs, many=True)
        return Response(standardized_response(data=serializer.data))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.debug(f"Retrieving membre {instance.id} for user {request.user}")
        serializer = self.get_serializer(instance)
        return Response(standardized_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating membre by user {request.user}: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membre = serializer.save()
        logger.info(f"Membre created successfully: {membre.id}")
        return Response(
            standardized_response(data=serializer.data, message="Membre créé avec succès"),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        logger.info(f"Updating membre {instance.id} by user {request.user} (partial={partial})")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Membre {instance.id} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Membre modifié"))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.warning(f"Deleting membre {instance.id} by user {request.user}")
        instance.delete()
        logger.info(f"Membre {instance.id} deleted successfully")
        return Response(standardized_response(message="Membre supprimé"), status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], permission_classes=[IsSecretaryOrAbove])
    def sacrements(self, request, pk=None):
        membre = self.get_object()
        logger.debug(f"Retrieving sacrements for membre {membre.id}")
        sacrements = membre.sacrements.all()
        logger.info(f"Retrieved {sacrements.count()} sacrements for membre {membre.id}")
        serializer = SacrementSerializer(sacrements, many=True)
        return Response(standardized_response(data=serializer.data))

    @action(detail=True, methods=["post"], permission_classes=[IsSecretaryOrAbove])
    def ajouter_sacrement(self, request, pk=None):
        membre = self.get_object()
        logger.info(f"Adding sacrement to membre {membre.id} by user {request.user}")
        serializer = SacrementSerializer(data={**request.data, "membre": membre.id})
        serializer.is_valid(raise_exception=True)
        sacrement = serializer.save(membre=membre)
        logger.info(f"Sacrement {sacrement.id} added to membre {membre.id}")
        return Response(
            standardized_response(data=serializer.data, message="Sacrement enregistré"),
            status=status.HTTP_201_CREATED,
        )

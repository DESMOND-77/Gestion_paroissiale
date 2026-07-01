import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.base_view import BaseModelViewSet
from core.permissions import IsAdmin, IsSecretaryOrAbove
from core.response import standardized_response
from .models import Evenement, Participation
from .serializers import EvenementSerializer, ParticipationSerializer
from .services import EvenementService
from membres.models import Membre

logger = logging.getLogger(__name__)


class EvenementViewSet(BaseModelViewSet):
    queryset = Evenement.objects.select_related("createur").prefetch_related("participations").all()
    serializer_class = EvenementSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]
        if self.action in ("create", "update", "partial_update", "inscrire"):
            return [IsSecretaryOrAbove()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        logger.debug(f"Listing evenements for user {request.user}")
        qs = self.get_queryset()
        logger.info(f"Retrieved {qs.count()} evenements")
        serializer = self.get_serializer(qs, many=True)
        return Response(standardized_response(data=serializer.data))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.debug(f"Retrieving evenement {instance.id} for user {request.user}")
        serializer = self.get_serializer(instance)
        return Response(standardized_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating evenement by user {request.user}: {request.data.get('titre', 'Unknown')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evenement = serializer.save(createur=request.user)
        logger.info(f"Evenement created successfully: {evenement.id} ({evenement.titre})")
        return Response(
            standardized_response(data=serializer.data, message="Événement créé"),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        logger.info(f"Updating evenement {instance.id} by user {request.user} (partial={partial})")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Evenement {instance.id} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Événement modifié"))

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.warning(f"Deleting evenement {instance.id} ({instance.titre}) by user {request.user}")
        instance.delete()
        logger.info(f"Evenement {instance.id} deleted successfully")
        return Response(standardized_response(message="Événement supprimé"), status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsSecretaryOrAbove])
    def inscrire(self, request, pk=None):
        evenement = self.get_object()
        membre_id = request.data.get("membre")
        logger.info(f"Inscribing membre {membre_id} to evenement {evenement.id} by user {request.user}")

        if not membre_id:
            logger.warning(f"Inscription attempt without membre ID to evenement {evenement.id}")
            return Response(
                standardized_response(success=False, error="Champ 'membre' requis"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get membre and use service to register
            membre = Membre.objects.get(id=membre_id)
            participation = EvenementService.inscrire_membre(evenement, membre)
            serializer = ParticipationSerializer(participation)
            return Response(
                standardized_response(data=serializer.data, message="Membre inscrit"),
                status=status.HTTP_201_CREATED,
            )
        except Membre.DoesNotExist:
            logger.error(f"Membre {membre_id} not found")
            return Response(
                standardized_response(success=False, error="Membre introuvable"),
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error inscribing membre: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"], permission_classes=[IsSecretaryOrAbove])
    def participants(self, request, pk=None):
        evenement = self.get_object()
        logger.debug(f"Retrieving participants for evenement {evenement.id}")
        participations = evenement.participations.select_related("membre").all()
        logger.info(f"Retrieved {participations.count()} participants for evenement {evenement.id}")
        serializer = ParticipationSerializer(participations, many=True)
        return Response(standardized_response(data=serializer.data))

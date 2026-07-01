import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.base_view import BaseAPIView
from core.permissions import IsAdmin, IsSecretaryOrAbove
from core.response import standardized_response
from .models import Evenement, Participation
from .serializers import EvenementSerializer, ParticipationSerializer
from .services import EvenementService
from membres.models import Membre

logger = logging.getLogger(__name__)


class EvenementListView(BaseAPIView):
    """
    GET  /api/evenements/           — liste (filtres: ?upcoming=true, ?type=)
    POST /api/evenements/           — création
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSecretaryOrAbove()]
        return [IsAuthenticated()]

    def get(self, request):
        upcoming = request.query_params.get("upcoming", "").lower() == "true"
        type_event = request.query_params.get("type")

        if upcoming:
            qs = EvenementService.get_upcoming_evenements(type_event=type_event)
            logger.debug(f"Listing upcoming evenements for user {request.user}")
        else:
            qs = Evenement.objects.select_related("createur").prefetch_related("participations").all()
            if type_event:
                qs = qs.filter(type=type_event)

        logger.info(f"Retrieved {qs.count()} evenements for user {request.user}")
        return Response(standardized_response(data=EvenementSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating evenement by user {request.user}: {request.data.get('titre', 'Unknown')}")
        serializer = EvenementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        evenement = EvenementService.create_evenement(
            titre=validated["titre"],
            type_event=validated["type"],
            date_debut=validated["date_debut"],
            createur=request.user,
            **{k: v for k, v in validated.items() if k not in ("titre", "type", "date_debut")},
        )
        logger.info(f"Evenement created successfully: {evenement.id} ({evenement.titre})")
        return Response(
            standardized_response(data=EvenementSerializer(evenement).data, message="Événement créé"),
            status=status.HTTP_201_CREATED,
        )


class EvenementDetailView(BaseAPIView):
    """
    GET    /api/evenements/<pk>/    — détail
    PUT    /api/evenements/<pk>/    — mise à jour complète
    PATCH  /api/evenements/<pk>/    — mise à jour partielle
    DELETE /api/evenements/<pk>/    — suppression (admin)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        if self.request.method == "DELETE":
            return [IsAdmin()]
        return [IsSecretaryOrAbove()]

    def _get_evenement(self, pk):
        return get_object_or_404(
            Evenement.objects.select_related("createur").prefetch_related("participations"),
            pk=pk,
        )

    def get(self, request, pk):
        evenement = self._get_evenement(pk)
        logger.debug(f"Retrieving evenement {pk} for user {request.user}")
        return Response(standardized_response(data=EvenementSerializer(evenement).data))

    def put(self, request, pk):
        evenement = self._get_evenement(pk)
        logger.info(f"Updating evenement {pk} by user {request.user}")
        serializer = EvenementSerializer(evenement, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Evenement {pk} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Événement modifié"))

    def patch(self, request, pk):
        evenement = self._get_evenement(pk)
        logger.info(f"Partial update evenement {pk} by user {request.user}")
        serializer = EvenementSerializer(evenement, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Evenement {pk} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Événement modifié"))

    def delete(self, request, pk):
        evenement = self._get_evenement(pk)
        logger.warning(f"Deleting evenement {pk} ({evenement.titre}) by user {request.user}")
        evenement.delete()
        logger.info(f"Evenement {pk} deleted successfully")
        return Response(standardized_response(message="Événement supprimé"), status=status.HTTP_204_NO_CONTENT)


class EvenementInscrireView(BaseAPIView):
    """
    POST   /api/evenements/<pk>/inscrire/   — inscription d'un membre (?membre=<id>)
    DELETE /api/evenements/<pk>/inscrire/   — désinscription d'un membre (?membre=<id>)
    """

    permission_classes = [IsSecretaryOrAbove]

    def _get_membre(self, membre_id, evenement_pk):
        if not membre_id:
            return None, Response(
                standardized_response(success=False, error="Champ 'membre' requis"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return Membre.objects.get(id=membre_id), None
        except Membre.DoesNotExist:
            logger.error(f"Membre {membre_id} not found for evenement {evenement_pk}")
            return None, Response(
                standardized_response(success=False, error="Membre introuvable"),
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request, pk):
        evenement = get_object_or_404(Evenement, pk=pk)
        membre_id = request.data.get("membre")
        logger.info(f"Inscribing membre {membre_id} to evenement {pk} by user {request.user}")

        membre, error_response = self._get_membre(membre_id, pk)
        if error_response:
            return error_response

        try:
            participation = EvenementService.inscrire_membre(evenement, membre)
            logger.info(f"Membre {membre_id} successfully inscribed to evenement {pk}")
            return Response(
                standardized_response(data=ParticipationSerializer(participation).data, message="Membre inscrit"),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error inscribing membre: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, pk):
        evenement = get_object_or_404(Evenement, pk=pk)
        membre_id = request.query_params.get("membre") or request.data.get("membre")
        logger.info(f"Desincribing membre {membre_id} from evenement {pk} by user {request.user}")

        membre, error_response = self._get_membre(membre_id, pk)
        if error_response:
            return error_response

        try:
            EvenementService.desinscrire_membre(evenement, membre)
            logger.info(f"Membre {membre_id} successfully desinscribed from evenement {pk}")
            return Response(standardized_response(message="Membre désinscrit"))
        except Exception as e:
            logger.error(f"Error desincribing membre: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )


class EvenementParticipantsView(BaseAPIView):
    """
    GET /api/evenements/<pk>/participants/  — liste des participants
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request, pk):
        evenement = get_object_or_404(Evenement, pk=pk)
        logger.debug(f"Retrieving participants for evenement {pk}")
        participations = EvenementService.get_participations(evenement)
        logger.info(f"Retrieved {participations.count()} participants for evenement {pk}")
        return Response(standardized_response(data=ParticipationSerializer(participations, many=True).data))

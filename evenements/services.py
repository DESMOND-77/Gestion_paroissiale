import logging
from datetime import datetime

from django.db.models import Q

from .models import Evenement, Participation

logger = logging.getLogger(__name__)


class EvenementService:
    """Service layer for Evenement business logic"""

    @staticmethod
    def create_evenement(titre, type_event, date_debut, createur, **kwargs):
        """Create a new event"""
        try:
            evenement = Evenement.objects.create(
                titre=titre,
                type=type_event,
                date_debut=date_debut,
                createur=createur,
                **kwargs,
            )
            logger.info(f"Evenement created: {evenement.id} ({titre})")
            return evenement
        except Exception as e:
            logger.error(f"Error creating evenement: {e}")
            raise

    @staticmethod
    def inscrire_membre(evenement, membre):
        """Register a member for an event"""
        try:
            participation, created = Participation.objects.get_or_create(
                evenement=evenement, membre=membre
            )
            if created:
                logger.info(
                    f"Membre {membre.id} registered for evenement {evenement.id}"
                )
            else:
                logger.debug(
                    f"Membre {membre.id} already registered for evenement {evenement.id}"
                )
            return participation
        except Exception as e:
            logger.error(f"Error registering membre: {e}")
            raise

    @staticmethod
    def desinscrire_membre(evenement, membre):
        """Unregister a member from an event"""
        try:
            Participation.objects.filter(evenement=evenement, membre=membre).delete()
            logger.info(
                f"Membre {membre.id} unregistered from evenement {evenement.id}"
            )
        except Exception as e:
            logger.error(f"Error unregistering membre: {e}")
            raise

    @staticmethod
    def get_participations(evenement):
        """Get all participants for an event"""
        return evenement.participations.select_related("membre", "membre__user").all()

    @staticmethod
    def get_evenements_for_user(user):
        """Événements auxquels `user` est convié (ou qu'il a créés).

        Convié si : invite_tous, OU son rôle ∈ roles_invites, OU sa fiche membre
        appartient à un groupe convié, OU sa fiche est conviée nommément. Le
        créateur voit toujours ses propres événements (pour les gérer).
        """
        q = (
            Q(invite_tous=True)
            | Q(createur=user)
            | Q(roles_invites__contains=user.role)
        )
        membre = getattr(user, "membre", None)
        if membre is not None:
            q |= Q(membres_invites=membre)
            if membre.groupe_id:
                q |= Q(groupes_invites=membre.groupe_id)

        return (
            Evenement.objects.filter(q)
            .select_related("createur")
            .prefetch_related("participations", "groupes_invites", "membres_invites")
            .distinct()
        )

    @staticmethod
    def get_upcoming_evenements(type_event=None):
        """Get upcoming events"""
        queryset = Evenement.objects.filter(date_debut__gte=datetime.now())

        if type_event:
            queryset = queryset.filter(type=type_event)

        return queryset.order_by("date_debut")

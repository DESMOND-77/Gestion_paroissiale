import logging

from django.db.models import Q

from .models import Membre

logger = logging.getLogger(__name__)


class MembreService:
    """Service layer for Membre business logic"""

    @staticmethod
    def create_membre(user=None, nom="", prenom="", **kwargs):
        """Create a new member with validation"""
        try:
            membre = Membre.objects.create(user=user, nom=nom, prenom=prenom, **kwargs)
            logger.info(f"Membre created: {membre.id} ({prenom} {nom})")
            return membre
        except Exception as e:
            logger.error(f"Error creating membre: {e}")
            raise

    @staticmethod
    def update_membre(membre, **kwargs):
        """Update member information"""
        try:
            for key, value in kwargs.items():
                if hasattr(membre, key):
                    setattr(membre, key, value)
            membre.save()
            logger.info(f"Membre {membre.id} updated")
            return membre
        except Exception as e:
            logger.error(f"Error updating membre {membre.id}: {e}")
            raise

    @staticmethod
    def search_membres(nom="", prenom="", groupe=None, sexe=None, search=None):
        """Search members by name and/or group and/or sexe.

        `search` matches nom OR prenom (used by the single search box in the
        app) and takes precedence over the separate `nom`/`prenom` filters.
        """
        queryset = Membre.objects.all()
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | Q(prenom__icontains=search)
            )
        else:
            if nom:
                queryset = queryset.filter(nom__icontains=nom)
            if prenom:
                queryset = queryset.filter(prenom__icontains=prenom)
        if groupe:
            queryset = queryset.filter(groupe=groupe)
        if sexe:
            queryset = queryset.filter(sexe=sexe)
        logger.debug(f"Search membres: {queryset.count()} results")
        return queryset

    @staticmethod
    def get_membre_statistics(membre):
        """Get statistics for a member"""
        return {
            "total_transactions": membre.transactions.count(),
            "total_participations": membre.participations.count(),
            "sacrements": membre.sacrements.count(),
        }

import logging

from .models import Groupe

logger = logging.getLogger(__name__)


class GroupeService:
    """Service layer for Groupe business logic"""

    @staticmethod
    def create_groupe(nom, responsable=None, **kwargs):
        """Create a new group"""
        try:
            groupe = Groupe.objects.create(
                nom=nom,
                responsable=responsable,
                **kwargs
            )
            logger.info(f"Groupe created: {groupe.id} ({nom})")
            return groupe
        except Exception as e:
            logger.error(f"Error creating groupe: {e}")
            raise

    @staticmethod
    def update_groupe(groupe, **kwargs):
        """Update group information"""
        try:
            for key, value in kwargs.items():
                if hasattr(groupe, key):
                    setattr(groupe, key, value)
            groupe.save()
            logger.info(f"Groupe {groupe.id} updated")
            return groupe
        except Exception as e:
            logger.error(f"Error updating groupe {groupe.id}: {e}")
            raise

    @staticmethod
    def get_groupe_membres_count(groupe):
        """Get the number of members in a group"""
        count = groupe.membres.count()
        logger.debug(f"Groupe {groupe.id} has {count} membres")
        return count

    @staticmethod
    def search_groupes(nom=""):
        """Search groups by name"""
        queryset = Groupe.objects.all()
        if nom:
            queryset = queryset.filter(nom__icontains=nom)
        logger.debug(f"Search groupes: {queryset.count()} results")
        return queryset

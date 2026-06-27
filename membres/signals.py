import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Membre

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_membre_for_user(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un Membre quand un User est créé.
    """
    if created:
        # Vérifier que le Membre n'existe pas déjà
        try:
            membre = instance.membre
        except Membre.DoesNotExist:
            membre = None
        
        if membre is None:
            try:
                Membre.objects.create(
                    user=instance,
                    nom=instance.nom,
                    prenom=instance.prenom
                )
                logger.info(f"Membre créé automatiquement pour l'utilisateur: {instance.email}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du Membre pour {instance.email}: {str(e)}")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def update_membre_for_user(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les informations du User vers le Membre.
    """
    if not created:
        try:
            membre = instance.membre
            # Mettre à jour les infos du membre à partir du user
            if membre.nom != instance.nom or membre.prenom != instance.prenom:
                membre.nom = instance.nom
                membre.prenom = instance.prenom
                membre.save()
                logger.debug(f"Infos du Membre synchronisées pour: {instance.email}")
        except Membre.DoesNotExist:
            # Si le Membre n'existe pas, le créer
            try:
                Membre.objects.create(
                    user=instance,
                    nom=instance.nom,
                    prenom=instance.prenom
                )
                logger.info(f"Membre créé (rattrappage) pour l'utilisateur: {instance.email}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du Membre pour {instance.email}: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du Membre pour {instance.email}: {str(e)}")

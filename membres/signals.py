import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

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
                    user=instance, nom=instance.nom, prenom=instance.prenom
                )
                logger.info(
                    f"Membre créé automatiquement pour l'utilisateur: {instance.email}"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la création du Membre pour {instance.email}: {str(e)}"
                )


@receiver(post_save, sender=Membre)
def update_user_for_membre(sender, instance, **kwargs):
    """Synchro inverse Membre → User (nom/prénom).

    Si la fiche est liée à un compte et que nom/prénom y ont été modifiés
    (ex : édition par le secrétariat), on les répercute sur le `User` — source
    de vérité de l'identité quand un compte existe.

    Anti-récursion : la sauvegarde n'a lieu **que si les valeurs diffèrent**.
    Après une propagation dans un sens, le signal réciproque
    (`update_membre_for_user`) constate l'égalité et ne re-sauvegarde pas —
    la boucle s'arrête d'elle-même. Ne pas retirer cette garde d'égalité.
    """
    user = instance.user
    if user is None:
        return
    if user.nom != instance.nom or user.prenom != instance.prenom:
        try:
            user.nom = instance.nom
            user.prenom = instance.prenom
            user.save(update_fields=["nom", "prenom", "updated_at"])
            logger.debug(f"Infos du User synchronisées depuis le Membre: {user.email}")
        except Exception as e:
            logger.error(
                f"Erreur lors de la synchro User depuis Membre {instance.pk}: {str(e)}"
            )


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
                    user=instance, nom=instance.nom, prenom=instance.prenom
                )
                logger.info(
                    f"Membre créé (rattrappage) pour l'utilisateur: {instance.email}"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la création du Membre pour {instance.email}: {str(e)}"
                )
        except Exception as e:
            logger.error(
                f"Erreur lors de la synchronisation du Membre pour {instance.email}: {str(e)}"
            )

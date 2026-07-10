import uuid

from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    """Clé primaire UUID (au lieu d'un entier auto-incrémenté).

    Indispensable pour une architecture offline-first : chaque appareil peut
    générer l'identifiant d'un nouvel enregistrement hors ligne (côté client)
    sans risque de collision au moment de la synchronisation vers le serveur
    central. Si le client ne fournit pas d'`id`, le serveur en génère un.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SyncableModel(UUIDPrimaryKeyModel):
    """Socle des modèles synchronisables (offline → serveur central).

    - ``created_at`` / ``updated_at`` : horodatage technique. ``updated_at`` sert
      de base à la résolution de conflits (stratégie *last-write-wins* : la
      version la plus récente l'emporte lors de la synchro).
    - ``is_deleted`` : suppression logique (*soft delete*). Un enregistrement créé
      hors ligne ne peut pas être « dé-créé » proprement ; on le marque supprimé
      pour propager l'état lors de la prochaine synchronisation plutôt que de le
      retirer physiquement.

    Ces champs sont une métadonnée technique distincte des dates métier
    (``date`` d'une transaction, ``date_ajout`` d'un article, etc.).
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True

"""Moteur de synchronisation offline → serveur central.

Un unique endpoint (`POST /api/v1/sync/`) échange un lot bidirectionnel :

- **push** : le client envoie ses créations/modifications/suppressions locales.
  Chaque enregistrement est appliqué en *upsert* par `id` (UUID). La résolution
  de conflits est *last-write-wins* basée sur `updated_at` : si la version
  serveur est plus récente que celle du client, le serveur gagne et
  l'enregistrement est renvoyé comme conflit (non écrasé).
- **pull** : le serveur renvoie tout ce qui a changé depuis `since` (y compris
  les enregistrements marqués supprimés `is_deleted`), pour que le client se
  mette à jour.

Le format d'un enregistrement transporte, en plus des champs métier, les
métadonnées de synchro `updated_at` (ISO 8601) et `is_deleted`.
"""

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def get_sync_registry():
    """Registre { nom_collection: (Model, Serializer) }.

    Construit à l'appel (et non à l'import) pour éviter tout import circulaire
    au chargement de `core`.
    """
    from membres.models import Membre, Sacrement
    from membres.serializers import MembreSerializer, SacrementSerializer
    from groupes.models import Groupe
    from groupes.serializers import GroupeSerializer
    from evenements.models import Evenement, Participation
    from evenements.serializers import EvenementSerializer, ParticipationSerializer
    from finances.models import Transaction
    from finances.serializers import TransactionSerializer
    from librairie.models import Article, Vente
    from librairie.serializers import ArticleSerializer, VenteSerializer

    return {
        "groupes": (Groupe, GroupeSerializer),
        "membres": (Membre, MembreSerializer),
        "sacrements": (Sacrement, SacrementSerializer),
        "evenements": (Evenement, EvenementSerializer),
        "participations": (Participation, ParticipationSerializer),
        "transactions": (Transaction, TransactionSerializer),
        "articles": (Article, ArticleSerializer),
        "ventes": (Vente, VenteSerializer),
    }


def _serialize(serializer_cls, obj):
    """Sérialise un objet en ajoutant les métadonnées de synchro."""
    data = serializer_cls(obj).data
    data["updated_at"] = obj.updated_at.isoformat()
    data["created_at"] = obj.created_at.isoformat()
    data["is_deleted"] = obj.is_deleted
    return data


def _apply_record(model, serializer_cls, record):
    """Applique un enregistrement entrant (upsert + last-write-wins).

    Retourne un tuple (statut, payload) où statut ∈
    {"applied", "conflict", "error"}.
    """
    rid = record.get("id")
    client_updated = record.get("updated_at")
    client_updated_dt = parse_datetime(client_updated) if client_updated else None

    instance = model.objects.filter(id=rid).first() if rid else None

    # Résolution de conflit : la version serveur, plus récente, l'emporte.
    if instance and client_updated_dt and instance.updated_at > client_updated_dt:
        return "conflict", _serialize(serializer_cls, instance)

    serializer = serializer_cls(instance, data=record, partial=bool(instance))
    if not serializer.is_valid():
        return "error", {"id": rid, "errors": serializer.errors}

    obj = serializer.save()

    # Suppression logique propagée depuis le client.
    wants_deleted = bool(record.get("is_deleted", False))
    if wants_deleted != obj.is_deleted:
        obj.is_deleted = wants_deleted
        obj.save(update_fields=["is_deleted", "updated_at"])

    return "applied", str(obj.id)


def push_changes(changes):
    """Applique le lot entrant. `changes` = { collection: [records] }.

    Chaque enregistrement est traité dans son propre point de sauvegarde : une
    erreur sur un enregistrement n'annule pas les autres.
    """
    registry = get_sync_registry()
    results = {}

    for collection, records in changes.items():
        if collection not in registry:
            results[collection] = {"error": "collection inconnue"}
            continue

        model, serializer_cls = registry[collection]
        applied, conflicts, errors = [], [], []

        for record in records:
            try:
                with transaction.atomic():
                    status_, payload = _apply_record(model, serializer_cls, record)
            except Exception as exc:  # noqa: BLE001 - on isole chaque enregistrement
                errors.append({"id": record.get("id"), "errors": str(exc)})
                continue

            if status_ == "applied":
                applied.append(payload)
            elif status_ == "conflict":
                conflicts.append(payload)
            else:
                errors.append(payload)

        results[collection] = {
            "applied": applied,
            "conflicts": conflicts,
            "errors": errors,
        }

    return results


def pull_changes(since):
    """Renvoie tout ce qui a changé depuis `since` (ISO 8601) ou tout si None."""
    registry = get_sync_registry()
    since_dt = parse_datetime(since) if since else None

    out = {}
    for collection, (model, serializer_cls) in registry.items():
        qs = model.objects.all()
        if since_dt:
            qs = qs.filter(updated_at__gt=since_dt)
        out[collection] = [_serialize(serializer_cls, obj) for obj in qs]
    return out


def run_sync(changes, since):
    """Point d'entrée : push puis pull, avec l'horodatage serveur de référence.

    `server_time` doit être renvoyé au client et réutilisé comme prochain
    `since` (curseur de synchronisation).
    """
    server_time = timezone.now()
    results = push_changes(changes or {})
    server_changes = pull_changes(since)
    return {
        "server_time": server_time.isoformat(),
        "results": results,
        "changes": server_changes,
    }

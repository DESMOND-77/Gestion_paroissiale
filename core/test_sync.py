import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from groupes.models import Groupe
from membres.models import Membre

User = get_user_model()


class SyncEndpointTests(APITestCase):
    """Vérifie le endpoint /api/v1/sync/ : push (upsert + UUID client),
    résolution de conflit last-write-wins, soft delete et pull."""

    def setUp(self):
        self.url = reverse("sync")
        self.user = User.objects.create_user(
            email="secretaire@paroisse.ga",
            password="Secret123!",
            nom="Ndong",
            prenom="Paul",
            role="secretaire",
        )
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post(self.url, {"changes": {}}, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_push_honours_client_generated_uuid(self):
        gid = str(uuid.uuid4())
        resp = self.client.post(
            self.url,
            {"changes": {"groupes": [{"id": gid, "nom": "Chorale"}]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["results"]["groupes"]["applied"], [gid])
        # L'enregistrement existe bien avec l'UUID fourni par le client.
        self.assertTrue(Groupe.objects.filter(id=gid, nom="Chorale").exists())

    def test_conflict_server_wins_when_server_is_newer(self):
        gid = str(uuid.uuid4())
        # État serveur (updated_at ~ maintenant).
        Groupe.objects.create(id=gid, nom="Serveur")
        stale = (timezone.now() - timedelta(hours=1)).isoformat()
        resp = self.client.post(
            self.url,
            {"changes": {"groupes": [{"id": gid, "nom": "Client", "updated_at": stale}]}},
            format="json",
        )
        result = resp.json()["data"]["results"]["groupes"]
        self.assertEqual(result["applied"], [])
        self.assertEqual(len(result["conflicts"]), 1)
        # La valeur serveur n'a pas été écrasée.
        self.assertEqual(Groupe.objects.get(id=gid).nom, "Serveur")

    def test_client_wins_when_client_is_newer(self):
        gid = str(uuid.uuid4())
        Groupe.objects.create(id=gid, nom="Serveur")
        newer = (timezone.now() + timedelta(hours=1)).isoformat()
        resp = self.client.post(
            self.url,
            {"changes": {"groupes": [{"id": gid, "nom": "Client", "updated_at": newer}]}},
            format="json",
        )
        self.assertEqual(resp.json()["data"]["results"]["groupes"]["applied"], [gid])
        self.assertEqual(Groupe.objects.get(id=gid).nom, "Client")

    def test_soft_delete_is_propagated(self):
        gid = str(uuid.uuid4())
        Groupe.objects.create(id=gid, nom="A supprimer")
        newer = (timezone.now() + timedelta(hours=1)).isoformat()
        resp = self.client.post(
            self.url,
            {"changes": {"groupes": [
                {"id": gid, "nom": "A supprimer", "is_deleted": True, "updated_at": newer}
            ]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Groupe.objects.get(id=gid).is_deleted)

    def test_invalid_record_reported_without_aborting_batch(self):
        good = str(uuid.uuid4())
        resp = self.client.post(
            self.url,
            {"changes": {"groupes": [
                {"id": good, "nom": "Valide"},
                {"id": str(uuid.uuid4())},  # nom manquant → invalide
            ]}},
            format="json",
        )
        result = resp.json()["data"]["results"]["groupes"]
        self.assertEqual(result["applied"], [good])
        self.assertEqual(len(result["errors"]), 1)
        self.assertTrue(Groupe.objects.filter(id=good).exists())

    def test_pull_returns_changes_since_cursor(self):
        # Le signal a déjà créé un Membre pour self.user ; on filtre via `since`.
        cursor = timezone.now().isoformat()
        gid = str(uuid.uuid4())
        Groupe.objects.create(id=gid, nom="Nouveau")
        resp = self.client.post(
            self.url, {"since": cursor, "changes": {}}, format="json"
        )
        changes = resp.json()["data"]["changes"]
        returned_ids = [g["id"] for g in changes["groupes"]]
        self.assertIn(gid, returned_ids)
        # Métadonnées de synchro présentes.
        self.assertIn("updated_at", changes["groupes"][0])
        self.assertIn("is_deleted", changes["groupes"][0])

    def test_server_time_cursor_is_returned(self):
        resp = self.client.post(self.url, {"changes": {}}, format="json")
        self.assertIn("server_time", resp.json()["data"])

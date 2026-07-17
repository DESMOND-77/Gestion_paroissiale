from rest_framework import serializers

from accounts.models import User
from core.serializers import WritableIDModelSerializer
from groupes.models import Groupe
from membres.models import Membre

from .models import Evenement, Participation


class ParticipationSerializer(WritableIDModelSerializer):
    membre_nom = serializers.SerializerMethodField()

    class Meta:
        model = Participation
        fields = ["id", "evenement", "membre", "membre_nom", "date_inscription"]
        read_only_fields = ["date_inscription"]

    def get_membre_nom(self, obj):
        return str(obj.membre)


class EvenementSerializer(WritableIDModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    createur_nom = serializers.SerializerMethodField()
    nb_participants = serializers.SerializerMethodField()

    # Conviés (écriture par ids/codes ; noms fournis en lecture pour l'affichage).
    roles_invites = serializers.ListField(
        child=serializers.ChoiceField(choices=User.ROLES_CHOICES),
        required=False,
    )
    groupes_invites = serializers.PrimaryKeyRelatedField(
        queryset=Groupe.objects.all(), many=True, required=False
    )
    membres_invites = serializers.PrimaryKeyRelatedField(
        queryset=Membre.objects.all(), many=True, required=False
    )
    groupes_invites_noms = serializers.SerializerMethodField()
    membres_invites_noms = serializers.SerializerMethodField()
    est_passe = serializers.BooleanField(read_only=True)

    class Meta:
        model = Evenement
        fields = [
            "id",
            "titre",
            "type",
            "type_display",
            "description",
            "date_debut",
            "date_fin",
            "lieu",
            "est_inscription_requise",
            "createur",
            "createur_nom",
            "nb_participants",
            "invite_tous",
            "roles_invites",
            "groupes_invites",
            "membres_invites",
            "groupes_invites_noms",
            "membres_invites_noms",
            "est_passe",
        ]
        read_only_fields = [
            "type_display",
            "createur_nom",
            "nb_participants",
            "groupes_invites_noms",
            "membres_invites_noms",
            "est_passe",
        ]

    def get_createur_nom(self, obj):
        if obj.createur:
            return obj.createur.full_name or obj.createur.email
        return None

    def get_nb_participants(self, obj):
        return obj.participations.count()

    def get_groupes_invites_noms(self, obj):
        return {str(g.id): g.nom for g in obj.groupes_invites.all()}

    def get_membres_invites_noms(self, obj):
        return {str(m.id): m.nom_complet for m in obj.membres_invites.all()}

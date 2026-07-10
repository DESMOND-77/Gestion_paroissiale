from rest_framework import serializers

from core.serializers import WritableIDModelSerializer

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
        ]
        read_only_fields = ["type_display", "createur_nom", "nb_participants"]

    def get_createur_nom(self, obj):
        if obj.createur:
            return obj.createur.full_name or obj.createur.email
        return None

    def get_nb_participants(self, obj):
        return obj.participations.count()

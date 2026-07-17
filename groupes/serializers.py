from rest_framework import serializers

from accounts.models import User
from core.serializers import WritableIDModelSerializer

from .models import Groupe


class GroupeSerializer(WritableIDModelSerializer):
    responsable_nom = serializers.SerializerMethodField()
    responsables = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    responsables_noms = serializers.SerializerMethodField()

    class Meta:
        model = Groupe
        fields = [
            "id",
            "nom",
            "description",
            "responsable",
            "responsable_nom",
            "responsables",
            "responsables_noms",
            "date_creation",
        ]
        read_only_fields = ["date_creation", "responsables_noms"]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return obj.responsable.full_name or obj.responsable.email
        return None

    def get_responsables_noms(self, obj):
        return {str(u.id): (u.full_name or u.email) for u in obj.responsables.all()}

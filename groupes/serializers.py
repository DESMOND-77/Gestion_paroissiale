from rest_framework import serializers

from .models import Groupe


class GroupeSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.SerializerMethodField()

    class Meta:
        model = Groupe
        fields = ["id", "nom", "description", "responsable", "responsable_nom", "date_creation"]
        read_only_fields = ["date_creation"]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return obj.responsable.full_name or obj.responsable.email
        return None

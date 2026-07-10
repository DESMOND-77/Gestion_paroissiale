from rest_framework import serializers

from core.serializers import WritableIDModelSerializer

from .models import Transaction


class TransactionSerializer(WritableIDModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    categorie_display = serializers.CharField(source="get_categorie_display", read_only=True)
    enregistre_par_nom = serializers.SerializerMethodField()
    membre_nom = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id", "type", "type_display", "categorie", "categorie_display",
            "montant", "description", "date", "membre", "membre_nom",
            "enregistre_par", "enregistre_par_nom",
        ]
        read_only_fields = ["type_display", "categorie_display", "membre_nom", "enregistre_par_nom"]

    def get_enregistre_par_nom(self, obj):
        if obj.enregistre_par:
            return obj.enregistre_par.full_name or obj.enregistre_par.email
        return None

    def get_membre_nom(self, obj):
        return str(obj.membre) if obj.membre else None

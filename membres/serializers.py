from rest_framework import serializers
from .models import Membre, Sacrement


class SacrementSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    officiant_nom = serializers.SerializerMethodField()

    class Meta:
        model = Sacrement
        fields = [
            "id", "type", "type_display", "membre", "date",
            "officiant", "officiant_nom", "observations",
        ]
        read_only_fields = ["type_display", "officiant_nom"]

    def get_officiant_nom(self, obj):
        if obj.officiant:
            return obj.officiant.full_name or obj.officiant.email
        return None


class MembreSerializer(serializers.ModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    groupe_nom = serializers.SerializerMethodField()

    class Meta:
        model = Membre
        fields = [
            "id", "user", "nom", "prenom", "nom_complet", "date_naissance",
            "sexe", "telephone", "email", "quartier", "date_inscription",
            "est_baptise", "est_confirme", "groupe", "groupe_nom",
        ]
        read_only_fields = ["date_inscription", "nom_complet"]

    def get_groupe_nom(self, obj):
        return obj.groupe.nom if obj.groupe else None


class MembreDetailSerializer(MembreSerializer):
    sacrements = SacrementSerializer(many=True, read_only=True)

    class Meta(MembreSerializer.Meta):
        fields = MembreSerializer.Meta.fields + ["sacrements"]

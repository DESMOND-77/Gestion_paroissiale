from rest_framework import serializers

from core.serializers import WritableIDModelSerializer

from .models import Membre, Sacrement


class SacrementSerializer(WritableIDModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    officiant_nom = serializers.SerializerMethodField()

    class Meta:
        model = Sacrement
        fields = [
            "id",
            "type",
            "type_display",
            "membre",
            "date",
            "officiant",
            "officiant_nom",
            "observations",
        ]
        read_only_fields = ["type_display", "officiant_nom"]

    def get_officiant_nom(self, obj):
        if obj.officiant:
            return obj.officiant.full_name or obj.officiant.email
        return None


class MembreSerializer(WritableIDModelSerializer):
    nom_complet = serializers.ReadOnlyField()
    groupe_nom = serializers.SerializerMethodField()
    # Informations utilisateur associé
    email = serializers.CharField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = Membre
        fields = [
            "id",
            "user",
            "nom",
            "prenom",
            "nom_complet",
            "date_naissance",
            "sexe",
            "email",
            "phone_number",
            "profile_picture_url",
            "quartier",
            "est_baptise",
            "est_confirme",
            "groupe",
            "groupe_nom",
        ]
        read_only_fields = [
            "nom_complet",
            "email",
            "phone_number",
            "profile_picture_url",
        ]

    def get_groupe_nom(self, obj):
        return obj.groupe.nom if obj.groupe else None

    def get_profile_picture_url(self, obj):
        # Photo de profil du compte `user` associé au membre. `request` peut ne
        # pas être dans le contexte (repli sur l'URL relative MEDIA_URL).
        user = obj.user
        if not user or not user.profile_picture:
            return None
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(user.profile_picture.url)
        return user.profile_picture.url


class MembreDetailSerializer(MembreSerializer):
    sacrements = SacrementSerializer(many=True, read_only=True)

    class Meta(MembreSerializer.Meta):
        fields = MembreSerializer.Meta.fields + ["sacrements"]


class MembreSelfSerializer(serializers.ModelSerializer):
    """Auto-service : un membre ne peut modifier que ses propres
    date_naissance / sexe / quartier - tout le reste (identité, sacrements,
    groupe) reste réservé au personnel via MembreSerializer."""

    nom_complet = serializers.ReadOnlyField()
    groupe_nom = serializers.SerializerMethodField()
    email = serializers.CharField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = Membre
        fields = [
            "id",
            "nom",
            "prenom",
            "nom_complet",
            "date_naissance",
            "sexe",
            "email",
            "phone_number",
            "quartier",
            "est_baptise",
            "est_confirme",
            "groupe",
            "groupe_nom",
        ]
        read_only_fields = [
            "id",
            "nom",
            "prenom",
            "nom_complet",
            "email",
            "phone_number",
            "est_baptise",
            "est_confirme",
            "groupe",
            "groupe_nom",
        ]

    def get_groupe_nom(self, obj):
        return obj.groupe.nom if obj.groupe else None

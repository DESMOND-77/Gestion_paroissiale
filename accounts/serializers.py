# apps/accounts/serializers.py
from rest_framework import serializers

from .models import User, UserActivity


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""

    email = serializers.EmailField(required=True, help_text="Email de l'utilisateur")
    password = serializers.CharField(
        required=True, min_length=8, help_text="Mot de passe (minimum 8 caractères)"
    )
    prenom = serializers.CharField(required=True, help_text="Prénom de l'utilisateur")
    nom = serializers.CharField(required=True, help_text="Nom de l'utilisateur")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec cet email existe déjà."
            )
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    email = serializers.EmailField(required=True, help_text="Email de l'utilisateur")
    password = serializers.CharField(required=True, help_text="Mot de passe")


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""

    email = serializers.EmailField(
        required=True,
        help_text="Email de l'utilisateur pour réinitialiser le mot de passe",
    )


class ConfirmPasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""

    token = serializers.CharField(
        required=True, help_text="Token de réinitialisation reçu par email"
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        help_text="Nouveau mot de passe (minimum 8 caractères)",
    )
    confirm_password = serializers.CharField(
        required=True, help_text="Confirmation du nouveau mot de passe"
    )

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"new_password": "Les mots de passe ne correspondent pas."}
            )
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""

    refresh_token = serializers.CharField(
        required=True, help_text="Token de rafraîchissement JWT"
    )


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout"""

    refresh_token = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Token de rafraîchissement (optionnel)",
    )


class UserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "prenom",
            "nom",
            "phone_number",
            "role",
            "username",
            "profile_picture",
            "profile_picture_url",
            "is_active",
            "is_verified",
            "created_at",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "last_login",
            "profile_picture_url",
        ]

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture:
            return None
        # `request` n'est pas toujours dans le contexte (services login/register/
        # profil qui instancient le serializer sans le passer). On renvoie alors
        # l'URL relative (MEDIA_URL) au lieu de lever KeyError.
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.profile_picture.url)
        return obj.profile_picture.url


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["prenom", "nom", "phone_number"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"new_password": "Les mots de passe ne correspondent pas."}
            )
        return data


class UserActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            "id",
            "user_email",
            "user_full_name",
            "action",
            "action_display",
            "details",
            "ip_address",
            "timestamp",
        ]
        read_only_fields = fields

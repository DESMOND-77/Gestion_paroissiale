import logging
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models

from django.core.validators import RegexValidator

from membres.models import Membre

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def create_superuser(self, email, password, **extra_fields):
        """
        Crée un superuser.
        """
        if not password:
            logger.error(f"Attempt to create superuser {email} without password")
            raise ValueError("mot de passe non definit pour le superUser")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")  # Ajouté

        if extra_fields.get("is_staff") is not True:
            logger.error(f"Superuser creation failed for {email}: is_staff not True")
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            logger.error(f"Superuser creation failed for {email}: is_superuser not True")
            raise ValueError("Superuser must have is_superuser=True.")

        logger.info(f"Creating superuser: {email}")
        return self.create_user(email, password, **extra_fields)

    def create_user(self, email, password=None, **extra_fields):
        """Créer un utilisateur"""
        if not email:
            logger.error("Attempt to create user without email")
            raise ValueError("Email obligatoire")
        if not password:
            logger.error(f"Attempt to create user {email} without password")
            raise ValueError("Mot de passe obligatoire")

        if not extra_fields.get("username"):
            extra_fields["username"] = email.split("@")[0]

        email = self.normalize_email(email)
        logger.debug(f"Creating user with email: {email}, username: {extra_fields.get('username')}")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        logger.info(f"User created successfully: {email} (role: {extra_fields.get('role', 'not set')})")
        return user


class User(AbstractBaseUser, PermissionsMixin,Membre):
    ROLES_CHOICES = [
        ("fidele", "Fidèle"),
        ("responsable", "Responsable"),
        ("secretaire", "Secrétaire"),
        ("tresorier", "Trésorier"),
        ("pretre", "Prêtre"),
        ("admin", "Administrateur"),
    ]

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=191, unique=True)


    # Changé le default à "admin" pour correspondre à vos choix
    role = models.CharField(
        max_length=20, choices=ROLES_CHOICES, default="fidele", verbose_name="Rôle"
    )

    is_active = models.BooleanField(
        default=True, verbose_name="Actif"
    )  # Changé à True par défaut
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )
    last_login = models.DateTimeField(blank=True, null=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Format de téléphone invalide"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name="Téléphone",
    )
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True, verbose_name="Photo de profil"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom", "role"]

    class Meta:

        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.nom} ({self.email})"

    @property
    def full_name(self):
        return f"{self.nom_complet}"

    def get_short_name(self):
        return self.prenom 

    def get_role_display_name(self):
        return dict(self.ROLES_CHOICES).get(self.role, self.role)

    # Permissions métier basées sur le rôle
    ROLE_PERMISSIONS = {
        "admin": {
            "admin_access", "manage_users", "manage_finances", "manage_events",
            "manage_groups", "manage_membres", "view_activities", "manage_librairie",
        },
        "pretre": {
            "manage_finances", "manage_events", "manage_groups",
            "manage_membres", "manage_librairie",
        },
        "tresorier": {"manage_finances", "manage_membres", "view_activities"},
        "secretaire": {
            "manage_events", "manage_groups", "manage_membres", "manage_librairie",
        },
        "responsable": {"manage_membres", "manage_groups"},
        "fidele": set(),
    }

    def has_permission(self, permission_name: str) -> bool:
        """
        Vérifie si l'utilisateur possède une permission métier par son nom.
        
        Args:
            permission_name: Nom de la permission à vérifier
            
        Returns:
            True si l'utilisateur a la permission, False sinon
        """
        has_perm = permission_name in self.ROLE_PERMISSIONS.get(self.role, set())
        logger.debug(f"User {self.email} permission check for '{permission_name}': {has_perm}")
        return has_perm

    # Méthode importante pour l'admin Django
    def has_module_perms(self, app_label):
        """Retourne True si l'utilisateur a les permissions pour l'app donnée."""
        can_access = self.is_staff or self.is_superuser
        logger.debug(f"User {self.email} module access check for '{app_label}': {can_access}")
        return can_access


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ("login", "Connexion"),
        ("logout", "Déconnexion"),
        ("create", "Création"),
        ("update", "Mise à jour"),
        ("delete", "Suppression"),
        ("view", "Consultation"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True,)

    class Meta:
        verbose_name = "Activité utilisateur"
        verbose_name_plural = "Activités utilisateur"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"

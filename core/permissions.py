"""Classes de permission DRF - Gestion Paroissiale.

Deux styles, tous deux adossés à la source de vérité `core/rbac.py` :

1. Basées sur la **hiérarchie de rôles** (`IsAdmin`, `IsSecretaryOrAbove`,
   `IsTreasurerOrAbove`) - pratiques et rétro-compatibles.
2. Basées sur les **permissions métier granulaires** (`HasPermission`,
   `HasAnyPermission`, `HasAllPermissions`) - à privilégier dans le code neuf,
   elles suivent automatiquement toute évolution de `ROLE_PERMISSIONS`.

Exemples :
    permission_classes = [HasPermission("manage_membres")]
    permission_classes = [HasAnyPermission("view_membres", "manage_membres")]
"""

from rest_framework.permissions import BasePermission

from core import rbac

SECRETARY_ROLES = {"secretaire", "tresorier", "responsable", "pretre", "admin"}
TREASURER_ROLES = {"tresorier", "pretre", "admin"}
ADMIN_ROLES = {"admin"}


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ADMIN_ROLES
        )


class IsSecretaryOrAbove(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in SECRETARY_ROLES
        )


class IsTreasurerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in TREASURER_ROLES
        )


# ---------------------------------------------------------------------------
# Permissions métier granulaires (adossées à core/rbac.py)
# ---------------------------------------------------------------------------


class _BasePermissionCheck(BasePermission):
    """Base commune : exige un utilisateur authentifié avant tout contrôle."""

    #: permissions métier requises, renseignées par les fabriques ci-dessous.
    required_permissions: tuple[str, ...] = ()
    #: True → il suffit d'UNE permission ; False → il les faut TOUTES.
    require_any: bool = True

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        role = getattr(user, "role", None)
        if role is None:
            return False
        if self.require_any:
            return rbac.has_any_permission(role, *self.required_permissions)
        return rbac.has_all_permissions(role, *self.required_permissions)


def HasPermission(permission: str) -> type[BasePermission]:
    """Fabrique une classe de permission exigeant `permission`.

    Usage : ``permission_classes = [HasPermission("manage_membres")]``.
    """
    if permission not in rbac.PERMISSIONS_CATALOGUE:
        raise ValueError(f"Permission inconnue : {permission!r}")
    return type(
        f"HasPermission_{permission}",
        (_BasePermissionCheck,),
        {
            "required_permissions": (permission,),
            "require_any": True,
            "message": f"Permission requise : {permission}",
        },
    )


def HasAnyPermission(*permissions: str) -> type[BasePermission]:
    """Autorise si l'utilisateur possède AU MOINS UNE des permissions."""
    _validate(permissions)
    return type(
        "HasAnyPermission",
        (_BasePermissionCheck,),
        {
            "required_permissions": tuple(permissions),
            "require_any": True,
            "message": f"Une de ces permissions est requise : {', '.join(permissions)}",
        },
    )


def HasAllPermissions(*permissions: str) -> type[BasePermission]:
    """Autorise si l'utilisateur possède TOUTES les permissions."""
    _validate(permissions)
    return type(
        "HasAllPermissions",
        (_BasePermissionCheck,),
        {
            "required_permissions": tuple(permissions),
            "require_any": False,
            "message": f"Toutes ces permissions sont requises : {', '.join(permissions)}",
        },
    )


def _validate(permissions: tuple[str, ...]) -> None:
    unknown = [p for p in permissions if p not in rbac.PERMISSIONS_CATALOGUE]
    if unknown:
        raise ValueError(f"Permissions inconnues : {unknown}")

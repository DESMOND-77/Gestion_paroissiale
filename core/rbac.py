"""
Système centralisé de gestion des permissions (RBAC) — Gestion Paroissiale.

Source de vérité UNIQUE pour :
  - le catalogue exhaustif des permissions métier (`PERMISSIONS_CATALOGUE`) ;
  - l'attribution des permissions à chaque rôle (`ROLE_PERMISSIONS`).

Le modèle `accounts.User` et les classes de permission DRF de
`core/permissions.py` délèguent à ce module — ne dupliquez pas ces tables
ailleurs.

Rôles (hiérarchie) : fidele < responsable < secretaire < tresorier < pretre < admin
"""

# ---------------------------------------------------------------------------
# 1. CATALOGUE EXHAUSTIF DES PERMISSIONS (par domaine fonctionnel)
# ---------------------------------------------------------------------------

PERMISSIONS_CATALOGUE: dict[str, str] = {
    # ── Administration générale ──────────────────────────────────────────
    "admin_access": "Accès au panneau d'administration complet.",
    # ── Utilisateurs (comptes de l'application) ──────────────────────────
    "manage_users": "Créer, modifier, désactiver et supprimer des comptes utilisateurs.",
    "view_users": "Consulter la liste et les détails des comptes utilisateurs.",
    # ── Finances ─────────────────────────────────────────────────────────
    "manage_finances": (
        "Créer, modifier, supprimer des écritures comptables, gérer les "
        "budgets, dons, quêtes, offrandes et dépenses."
    ),
    "view_finances": "Consulter les écritures comptables, rapports financiers et soldes.",
    "export_finances": "Exporter les rapports financiers (PDF, Excel).",
    "approve_expenses": "Valider ou rejeter des demandes de dépenses.",
    # ── Événements ───────────────────────────────────────────────────────
    "manage_events": (
        "Créer, modifier, annuler des événements paroissiaux "
        "(messes, baptêmes, mariages, retraites, etc.)."
    ),
    "view_events": "Consulter le calendrier et les détails des événements.",
    "manage_event_registrations": "Gérer les inscriptions aux événements.",
    # ── Groupes / mouvements ─────────────────────────────────────────────
    "manage_groups": "Créer, modifier, dissoudre tout groupe ou mouvement paroissial.",
    "view_groups": "Consulter la liste et les détails de tous les groupes.",
    "manage_owned_group": "Modifier les informations du groupe dont on est responsable.",
    "add_membres_to_group": "Ajouter des membres dans son propre groupe.",
    "remove_membres_from_group": "Retirer des membres de son propre groupe.",
    "view_owned_group_members": "Consulter les membres de son propre groupe.",
    # ── Membres / paroissiens ────────────────────────────────────────────
    "manage_membres": (
        "Créer, modifier, archiver des fiches paroissiens "
        "(coordonnées, sacrements, historique pastoral)."
    ),
    "view_membres": "Consulter la liste et les fiches des paroissiens.",
    "export_membres": "Exporter l'annuaire paroissial (PDF, Excel, CSV).",
    "record_sacraments": (
        "Enregistrer un sacrement (baptême, confirmation, mariage) "
        "dans la fiche d'un paroissien."
    ),
    # ── Activités / Journal de bord ──────────────────────────────────────
    "manage_activities": (
        "Créer, modifier, supprimer des entrées dans le journal "
        "d'activités paroissiales."
    ),
    "view_activities": "Consulter le journal des activités.",
    # ── Librairie / Bibliothèque ─────────────────────────────────────────
    "manage_librairie": (
        "Ajouter, modifier, retirer des ouvrages de la librairie "
        "paroissiale, gérer les emprunts et les stocks."
    ),
    "view_librairie": "Consulter le catalogue de la librairie.",
    "borrow_books": "Emprunter un ouvrage.",
    "manage_borrowings": "Gérer les emprunts (retours, relances, réservations).",
    # ── Communication ────────────────────────────────────────────────────
    "send_announcements": (
        "Envoyer des annonces/communications à tout ou partie des "
        "paroissiens (email, SMS, notifications)."
    ),
    "manage_website": "Modifier le contenu du site web paroissial.",
}


# ---------------------------------------------------------------------------
# 2. ATTRIBUTION DES PERMISSIONS AUX RÔLES
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[str, set[str]] = {
    # ── ADMINISTRATEUR : tous les droits sans exception ──────────────────
    "admin": {
        "admin_access",
        "manage_users",
        "view_users",
        "manage_finances",
        "view_finances",
        "export_finances",
        "approve_expenses",
        "manage_events",
        "view_events",
        "manage_event_registrations",
        "manage_groups",
        "view_groups",
        "manage_owned_group",
        "add_membres_to_group",
        "remove_membres_from_group",
        "view_owned_group_members",
        "manage_membres",
        "view_membres",
        "export_membres",
        "record_sacraments",
        "manage_activities",
        "view_activities",
        "manage_librairie",
        "view_librairie",
        "borrow_books",
        "manage_borrowings",
        "send_announcements",
        "manage_website",
    },
    # ── PRÊTRE : regard transversal (consultation) + ministère ───────────
    "pretre": {
        "view_users",
        "view_finances",
        "export_finances",
        "view_events",
        "manage_event_registrations",
        "view_groups",
        "view_owned_group_members",
        "view_membres",
        "export_membres",
        "record_sacraments",
        "view_activities",
        "manage_activities",
        "view_librairie",
        "borrow_books",
        "manage_borrowings",
        "send_announcements",
    },
    # ── TRÉSORIER : gestion financière complète ──────────────────────────
    "tresorier": {
        "manage_finances",
        "view_finances",
        "export_finances",
        "approve_expenses",
        "view_activities",
    },
    # ── SECRÉTAIRE : gestion opérationnelle (hors finances/système) ──────
    "secretaire": {
        "view_users",
        "view_events",
        "view_groups",
        "view_membres",
        "view_activities",
        "view_librairie",
        "manage_events",
        "manage_event_registrations",
        "manage_groups",
        "manage_membres",
        "export_membres",
        "record_sacraments",
        "manage_activities",
        "manage_librairie",
        "manage_borrowings",
        "borrow_books",
        "send_announcements",
    },
    # ── RESPONSABLE DE GROUPE : son groupe uniquement ────────────────────
    "responsable": {
        "manage_owned_group",
        "add_membres_to_group",
        "remove_membres_from_group",
        "view_owned_group_members",
        "view_events",
        "view_groups",
        "view_membres",
        "borrow_books",
        "view_librairie",
    },
    # ── FIDÈLE : consultation grand public ───────────────────────────────
    "fidele": {
        "view_events",
        "view_librairie",
        "borrow_books",
    },
}


# Garde-fou : au chargement du module, vérifier qu'aucun rôle ne référence
# une permission absente du catalogue (typo = échec explicite au démarrage).
_unknown = {
    perm
    for perms in ROLE_PERMISSIONS.values()
    for perm in perms
    if perm not in PERMISSIONS_CATALOGUE
}
if _unknown:
    raise ValueError(
        f"ROLE_PERMISSIONS référence des permissions hors catalogue : {sorted(_unknown)}"
    )
del _unknown


# ---------------------------------------------------------------------------
# 3. FONCTIONS UTILITAIRES
# ---------------------------------------------------------------------------


def get_permissions(role: str) -> set[str]:
    """Retourne l'ensemble (copie) des permissions d'un rôle, ou set() si inconnu."""
    return set(ROLE_PERMISSIONS.get(role, set()))


def has_permission(role: str, permission: str) -> bool:
    """Vrai si le rôle possède la permission donnée."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: str, *permissions: str) -> bool:
    """Vrai si le rôle possède au moins une des permissions spécifiées."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return any(p in role_perms for p in permissions)


def has_all_permissions(role: str, *permissions: str) -> bool:
    """Vrai si le rôle possède toutes les permissions spécifiées."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return all(p in role_perms for p in permissions)


def roles_with_permission(permission: str) -> set[str]:
    """Retourne tous les rôles possédant la permission donnée (audit/debug)."""
    return {role for role, perms in ROLE_PERMISSIONS.items() if permission in perms}


def missing_permissions(role: str) -> set[str]:
    """Retourne les permissions du catalogue qu'un rôle NE possède PAS."""
    return set(PERMISSIONS_CATALOGUE.keys()) - ROLE_PERMISSIONS.get(role, set())

# Référence de l'API

La documentation interactive fait foi : **Swagger** (`/docs/`) et **ReDoc**
(`/redoc/`). Cette page résume les conventions et la liste des endpoints.

## Conventions

- **Versionnage** : toutes les routes métier sont sous `/api/v1/`
  (DRF `URLPathVersioning`). Exception : `/api/health/` (infra, non versionné).
- **Authentification** : en-tête `Authorization: Bearer <access_token>`.
  Access token : 15 min ; refresh token : 7 jours, avec rotation.
- **Identifiants** : UUID partout (`/api/v1/membres/<uuid>/`).
- **Pagination** : `PageNumberPagination`, 50 éléments par page (`?page=N`).
- **Format de réponse** (les clés à `None` sont omises) :

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": "..."
}
```

## Santé

| Méthode | Endpoint       | Auth | Description      |
| ------- | -------------- | ---- | ---------------- |
| GET     | `/api/health/` | —    | État BDD + Redis |

## Authentification & comptes

| Méthode  | Endpoint                            | Auth  | Description                                                        |
| -------- | ----------------------------------- | ----- | ------------------------------------------------------------------ |
| POST     | `/api/v1/auth/register/`            | —     | Inscription (rôle `fidele` par défaut)                             |
| POST     | `/api/v1/auth/login/`               | —     | Connexion (e-mail vérifié requis ; 5 échecs → verrouillage 15 min) |
| POST     | `/api/v1/auth/logout/`              | ✅    | Déconnexion (liste noire des jetons)                               |
| POST     | `/api/v1/auth/token/refresh/`       | —     | Rafraîchir le jeton (rotation)                                     |
| POST     | `/api/v1/auth/token/validate/`      | —     | Valider un jeton                                                   |
| GET      | `/api/v1/auth/me/`                  | ✅    | Utilisateur courant                                                |
| POST     | `/api/v1/auth/password-reset/`      | —     | Demander l'e-mail de réinitialisation                              |
| POST     | `/api/v1/auth/send-verification/`   | —     | Renvoyer l'e-mail de vérification                                  |
| GET      | `/api/v1/auth/verification-status/` | —     | Statut de vérification                                             |
| GET      | `/api/v1/verify-email/`             | —     | **Page HTML** : vérifie l'e-mail (lien reçu)                       |
| GET/POST | `/api/v1/reset-password/`           | —     | **Page HTML** : formulaire de réinitialisation                     |
| GET/PUT  | `/api/v1/user/profile/`             | ✅    | Lire / modifier son profil                                         |
| POST     | `/api/v1/user/change-password/`     | ✅    | Changer le mot de passe (invalide tous les jetons)                 |
| GET      | `/api/v1/users/`                    | admin | Liste des utilisateurs                                             |
| GET      | `/api/v1/users/<uuid>/`             | admin | Détail d'un utilisateur                                            |
| GET      | `/api/v1/activities/`               | admin | Journal d'activités                                                |
| POST     | `/api/v1/check-permission/`         | ✅    | Vérifier une permission RBAC (+ liste complète)                    |

> Les liens envoyés par e-mail pointent vers les **pages HTML**
> (`verify-email/`, `reset-password/`), pas vers des endpoints JSON.

## Membres

| Méthode              | Endpoint                             | Description                                |
| -------------------- | ------------------------------------ | ------------------------------------------ |
| GET/POST             | `/api/v1/membres/`                   | Liste / création (avec ou sans compte lié) |
| GET                  | `/api/v1/membres/me/`                | Fiche du membre courant                    |
| GET/PUT/PATCH/DELETE | `/api/v1/membres/<uuid>/`            | Détail / modification / suppression        |
| GET/POST             | `/api/v1/membres/<uuid>/sacrements/` | Sacrements d'un membre                     |

## Groupes

| Méthode              | Endpoint                          | Description                         |
| -------------------- | --------------------------------- | ----------------------------------- |
| GET/POST             | `/api/v1/groupes/`                | Liste / création                    |
| GET/PUT/PATCH/DELETE | `/api/v1/groupes/<uuid>/`         | Détail / modification / suppression |
| GET                  | `/api/v1/groupes/<uuid>/membres/` | Membres d'un groupe                 |

## Événements

| Méthode              | Endpoint                                  | Description                                                    |
| -------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| GET/POST             | `/api/v1/evenements/`                     | Liste / création (invitations : tous, rôles, groupes, membres) |
| GET/PUT/PATCH/DELETE | `/api/v1/evenements/<uuid>/`              | Détail / modification / suppression                            |
| POST                 | `/api/v1/evenements/<uuid>/inscrire/`     | S'inscrire à un événement                                      |
| GET                  | `/api/v1/evenements/<uuid>/participants/` | Liste des participants                                         |

## Finances

| Méthode              | Endpoint                                | Description                                  |
| -------------------- | --------------------------------------- | -------------------------------------------- |
| GET/POST             | `/api/v1/finances/transactions/`        | Transactions (entrées / sorties, catégories) |
| GET/PUT/PATCH/DELETE | `/api/v1/finances/transactions/<uuid>/` | Détail d'une transaction                     |
| GET                  | `/api/v1/finances/rapport/`             | Rapport financier                            |
| GET                  | `/api/v1/finances/membre/<uuid>/dons/`  | Dons d'un membre                             |

## Librairie

| Méthode              | Endpoint                             | Description                              |
| -------------------- | ------------------------------------ | ---------------------------------------- |
| GET/POST             | `/api/v1/librairie/articles/`        | Articles                                 |
| GET/PUT/PATCH/DELETE | `/api/v1/librairie/articles/<uuid>/` | Détail d'un article                      |
| GET                  | `/api/v1/librairie/alertes/`         | Articles sous le seuil d'alerte de stock |
| GET/POST             | `/api/v1/librairie/ventes/`          | Ventes                                   |
| GET                  | `/api/v1/librairie/ventes/rapport/`  | Rapport des ventes                       |

## Synchronisation hors ligne

| Méthode | Endpoint        | Description                                                                                                         |
| ------- | --------------- | ------------------------------------------------------------------------------------------------------------------- |
| POST    | `/api/v1/sync/` | Batch bidirectionnel : _push_ (upsert par UUID, last-write-wins, soft-delete) + _pull_ (delta depuis `server_time`) |

## Erreurs

Toutes les erreurs suivent le format standardisé, par exemple :

```json
{
  "success": false,
  "error": "Identifiants invalides.",
  "message": "Échec de l'authentification"
}
```

| Code | Signification                                      |
| ---- | -------------------------------------------------- |
| 400  | Erreur de validation                               |
| 401  | Non authentifié / jeton invalide ou en liste noire |
| 403  | Permission insuffisante (rôle / RBAC)              |
| 404  | Ressource introuvable                              |
| 429  | Limitation de débit (throttling)                   |
| 500  | Erreur serveur interne                             |

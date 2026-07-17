# Architecture

Vue d'ensemble de l'architecture de **Gestion Paroissiale API**.

## Flux d'une requête

```text
Requête HTTP → gestion_p/urls.py → Vue/ViewSet (app/views.py) → Service / Modèle → MySQL
                                                              ↘ Redis (jetons, sessions, rate limiting)
```

1. **Routage** : `gestion_p/urls.py` monte les apps sous `/api/v1/<module>/`
   (DRF `URLPathVersioning`, `DEFAULT_VERSION="v1"`). `/api/health/` reste non
   versionné (endpoint d'infrastructure).
2. **Authentification** : JWT (`djangorestframework-simplejwt`) ; la validité du
   jeton est vérifiée contre la liste noire Redis (par `jti`).
3. **Permissions** : classes DRF (hiérarchie de rôles ou RBAC granulaire).
4. **Vue** : validation via serializer, appel du service ou de l'ORM, réponse
   standardisée.

## Couches

| Couche | Emplacement | Rôle |
| --- | --- | --- |
| Views | `app/views.py` | Gestion HTTP, validation, réponses standardisées |
| Services | `accounts/{auth,profile,verification}/`, `app/services.py` | Logique métier complexe |
| Serializers | `app/serializers.py` | Validation / transformation des données |
| Models | `app/models.py` | Modèles UUID + managers personnalisés |
| Transverse | `core/` (racine) | Réponses, exceptions, JWT, RBAC, sync, santé |

## Le module transverse `core/`

- `core/response.py` — `standardized_response()` : format unique
  `{"success", "data", "error", "message"}` ; les clés à `None` sont **omises**.
- `core/exception_handler.py` — convertit **toutes** les erreurs DRF
  (validation, 401, 403, 404, throttling) dans le format standardisé
  (branché via `REST_FRAMEWORK["EXCEPTION_HANDLER"]`).
- `core/base_view.py` — `BaseAPIView` : classe mère des vues (gestion
  centralisée des exceptions, `check_extra_permission()`).
- `core/jwt_utils.py` — `TokenManager` : émission des paires de jetons, suivi
  dans Redis par `jti`, liste noire (logout, changement de mot de passe), repli
  `LocMemCache` sans Redis.
- `core/rbac.py` — **source de vérité unique** des permissions métier :
  `PERMISSIONS_CATALOGUE` + `ROLE_PERMISSIONS` + helpers. Validation à l'import.
- `core/permissions.py` — classes DRF : hiérarchie de rôles (`IsAdmin`,
  `IsSecretaryOrAbove`, `IsTreasurerOrAbove`) et fabriques granulaires
  (`HasPermission`, `HasAnyPermission`, `HasAllPermissions`).
- `core/models.py` — `UUIDPrimaryKeyModel` et `SyncableModel` (UUID +
  `created_at`/`updated_at`/`is_deleted`).
- `core/sync.py` + `SyncView` — synchronisation hors ligne (voir plus bas).
- `core/health.py` — `HealthCheckView` (état Redis + BDD, non authentifié).

## `User` vs `Membre` — séparation volontaire

Deux modèles pour deux concepts distincts (fusionner est un **anti-objectif**) :

- **`accounts.User`** : l'identité d'authentification — `email` (unique,
  `USERNAME_FIELD`), mot de passe, `role`, `phone_number`, `profile_picture`.
- **`membres.Membre`** : la fiche pastorale — `nom`, `prenom`,
  `date_naissance`, `sexe`, `quartier`, `est_baptise`, `est_confirme`,
  `groupe`, sacrements. Lien `OneToOneField(user, null=True)` : une paroisse
  suit des personnes **sans compte** (enfants, personnes âgées…).

Synchronisation (signaux dans `membres/signals.py`) :

- `create_membre_for_user` — chaque nouveau `User` reçoit automatiquement sa
  fiche `Membre` (copie de `nom`/`prenom`).
- `update_membre_for_user` / `update_user_for_membre` — synchronisation
  bidirectionnelle de `nom`/`prenom`, avec **garde d'égalité avant sauvegarde**
  (empêche la récursion infinie — ne pas retirer ces gardes).
- `Membre` ne stocke ni e-mail, ni téléphone, ni photo : dérivés en lecture
  seule du `User` lié dans `MembreSerializer`.

## Architecture offline-first

- **Clés primaires UUID** générées côté client (`SyncableModel`), donc pas de
  collision hors ligne. Conséquences : routes en `<uuid:pk>`, `str()` sur tout
  id mis dans un JWT/JSON, détection de création via `self._state.adding`.
- **`POST /api/v1/sync/`** (`core/sync.py`) : endpoint batch bidirectionnel —
  *push* (upsert par UUID, *last-write-wins* sur `updated_at`, suppression
  logique via `is_deleted`) + *pull* (delta depuis un curseur `server_time`).
- Les serializers synchronisables héritent de
  `core.serializers.WritableIDModelSerializer` (sinon DRF rend la PK read-only).
- Nouvelles collections synchronisables : à enregistrer dans le registre de
  `core/sync.py`.

## Infrastructure

| Composant | Rôle |
| --- | --- |
| MySQL/MariaDB (ou PostgreSQL via `DATABASE_URL`) | Persistance |
| Redis 7 | Jetons JWT (`jti`), verrouillage de compte, throttling, cache, sessions |
| Resend (Anymail) | Envoi d'e-mails (repli SMTP en dev ; SMTP bloqué sur Render) |
| WhiteNoise | Fichiers statiques en production |
| Gunicorn | Serveur WSGI |
| Docker / Render | Conteneurisation et déploiement (voir [deployment.md](deployment.md)) |

> Sans Redis, l'application fonctionne en mode dégradé : `TokenManager` bascule
> sur une sémantique `LocMemCache` (non partagée entre processus).

## Documents liés

- [installation.md](installation.md) — installation locale
- [development.md](development.md) — conventions et tests
- [deployment.md](deployment.md) — Docker et Render
- [api.md](api.md) — référence des endpoints
- [database.md](database.md) — modèle de données

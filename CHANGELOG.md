# Changelog

Toutes les modifications notables de **Gestion Paroissiale API** sont documentées
dans ce fichier.

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et le projet suit le [versionnage sémantique](https://semver.org/lang/fr/).

> Le journal détaillé des correctifs (en français, avec Problème / Cause /
> Solution / Fichiers) reste tenu dans [`fixs.md`](./fixs.md). Ce CHANGELOG en
> est la synthèse orientée versions.

## [Non publié]

### Ajouté

- Outillage qualité : `pyproject.toml` (métadonnées du projet, groupe de
  dépendances `dev`) + linter/formateur **ruff** (règles E, W, F, I, DJ, B, UP)
  branché dans la CI ; base de code reformatée et corrigée en conséquence
  (`except` nu typé, `raise … from`, variable inutilisée, imports triés).
- Standardisation open source du dépôt : README refondu (badges, roadmap, FAQ),
  `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `SECURITY.md`,
  `.env.example`, dossier `.github/` (modèles d'issues et de PR, workflows CI /
  release / CodeQL, Dependabot, CODEOWNERS) et documentation technique `docs/`
  (architecture, installation, développement, déploiement, API, base de données).
- Versionnage de l'API sous le préfixe `/api/v1/` (DRF `URLPathVersioning`,
  `DEFAULT_VERSION="v1"`). Le health check `/api/health/` reste non versionné.
- Headers de sécurité HTTP : `SECURE_CONTENT_TYPE_NOSNIFF`,
  `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = "DENY"` (toujours actifs) ;
  `SECURE_SSL_REDIRECT` + HSTS (`SECURE_HSTS_*`) en production.
- Fichiers de gouvernance projet : `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`
  (MIT).

### Corrigé

- Build Docker : remplacement du paquet runtime introuvable
  `default-libmysqlclient21` par `libmariadb3` (image de base Debian trixie).

## [1.0.0] - 2026-07-08

Première version consolidée après l'audit technique (20 problèmes traités sur
3 phases).

### Sécurité

- Rôle par défaut d'un nouvel utilisateur ramené de `admin` à `fidele`
  (le plus restrictif).
- Durée de vie des JWT alignée sur OWASP : access token 15 min, refresh token
  7 jours, avec rotation.
- Rate limiting (throttling DRF) appliqué aux endpoints sensibles : connexion,
  réinitialisation de mot de passe, renvoi de vérification d'email.
- Suppression des `print()` de debug exposant des données de requête.

### Performance & Architecture

- Pagination globale (`PageNumberPagination`, `PAGE_SIZE = 50`).
- Index base de données sur les champs fréquemment filtrés
  (transactions, événements, membres, activités utilisateur).
- Optimisation des requêtes N+1 via `select_related` / `prefetch_related` dans
  tous les modules.
- Couche service (`services.py`) introduite dans `membres`, `groupes`,
  `evenements`, `finances`, `librairie`.
- Déploiement conteneurisé via `Dockerfile` (Gunicorn) + `docker-compose`
  (build, healthcheck) au lieu du serveur de développement.
- Suppression de la configuration `CHANNEL_LAYERS` / `ASGI_APPLICATION`
  inutilisée (pas de WebSockets).
- Configuration email via Resend (Anymail) avec repli SMTP.

### Corrigé

- Test Redis (`ping`) retiré du chargement de `settings.py` ; état de Redis
  exposé via `GET /api/health/` (`core/health.py`).
- Divers doublons et code mort : `BASE_DIR`, import `admin`, docstring
  `TokenManager`, import non idiomatique de `settings`.
- Ajout de `REQUIRED_FIELDS` au modèle `User` personnalisé.
- Trailing slash ajouté sur `auth/token/refresh/`.

[Non publié]: https://github.com/DESMOND-77/Gestion_paroissiale/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/DESMOND-77/Gestion_paroissiale/releases/tag/v1.0.0

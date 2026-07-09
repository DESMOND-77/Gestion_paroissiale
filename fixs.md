# Journal des correctifs (fixs.md)

Ce fichier documente les correctifs apportés au projet. Chaque entrée décrit le
problème, la cause, la solution et les fichiers touchés. Entrées les plus
récentes en haut.

---

## 2026-07-10 — Correctifs audit P3.8 (headers sécurité) & P3.10 (gouvernance)

**Problème** : deux points de l'audit restaient ouverts :
- P3.8 : aucun header de sécurité HTTP configuré.
- P3.10 : absence de `CHANGELOG.md`, `CONTRIBUTING.md` et `LICENSE`.

**Cause** : configuration `SECURE_*` jamais ajoutée à `settings.py` ; fichiers de
gouvernance projet jamais créés.

**Solution** :
- P3.8 — dans `gestion_p/settings.py` : `SECURE_CONTENT_TYPE_NOSNIFF`,
  `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS = "DENY"` toujours actifs ;
  `SECURE_SSL_REDIRECT` + `SECURE_HSTS_SECONDS`/`INCLUDE_SUBDOMAINS`/`PRELOAD`
  uniquement en production (`if not DEBUG`) pour ne pas casser `http://localhost`.
  `SecurityMiddleware` et `XFrameOptionsMiddleware` étaient déjà présents.
- P3.10 — création de `LICENSE` (MIT), `CHANGELOG.md` (format Keep a Changelog,
  synthèse de l'audit en v1.0.0) et `CONTRIBUTING.md` (conventions du projet).

**Fichiers** : `gestion_p/settings.py`, `LICENSE`, `CHANGELOG.md`,
`CONTRIBUTING.md`.

**Tests** : `python manage.py check` OK ; `check --deploy` ne signale plus aucun
warning de header de sécurité (reste uniquement `security.W009` sur `SECRET_KEY`,
géré par variable d'environnement en production).

---

## 2026-07-09 — Ajout du versionning de l'API (`/api/v1/`)

**Problème** : l'API n'était pas versionnée (`/api/...`), ce qui empêche toute
évolution future incompatible sans casser les clients existants.

**Cause** : les routes métier étaient montées directement sous `/api/` dans
`gestion_p/urls.py`, sans segment de version, et aucune classe de versionning
DRF n'était configurée.

**Solution** :
- Préfixage de toutes les routes métier sous `/api/v1/` (`accounts`, `groupes`,
  `membres`, `evenements`, `finances`, `librairie`) dans `gestion_p/urls.py`.
- `/api/health/` laissé **non versionné** : c'est un endpoint d'infrastructure
  référencé par le `HEALTHCHECK` du `Dockerfile` — le versionner casserait le
  healthcheck Docker/Render.
- Activation du versionning DRF dans `REST_FRAMEWORK` :
  `URLPathVersioning` + `DEFAULT_VERSION="v1"` + `ALLOWED_VERSIONS=["v1"]`, si
  bien que `request.version` est désormais disponible dans les vues.
- Aucune régression sur les liens email : ils sont construits via
  `reverse()` par nom de route, donc `web_verify_email` / `web_password_reset`
  résolvent automatiquement vers `/api/v1/...` (vérifié).
- Documentation mise à jour (`README.md`, `CLAUDE.md`).

**Impact client** : changement cassant pour le frontend — les appels `/api/...`
doivent devenir `/api/v1/...` (sauf `/api/health/`).

**Fichiers** : `gestion_p/urls.py`, `gestion_p/settings.py`, `README.md`,
`CLAUDE.md`.

**Tests** : `python manage.py check` OK ; résolution/reverse des URLs vérifiés
(`/api/v1/auth/login/`, `/api/health/`, liens email).

---

## 2026-07-09 — Échec du build Docker : paquet `default-libmysqlclient21` introuvable

**Problème** : `docker build` échouait à l'étape runtime (`stage-1 3/8`) avec
`E: Unable to locate package default-libmysqlclient21`.

**Cause** : l'image de base `python:3.14-slim` s'appuie désormais sur Debian
"trixie", où le paquet runtime du client MySQL a été renommé : la
bibliothèque partagée `libmysqlclient21` (nom hérité de Debian bookworm)
n'existe plus — le client MySQL par défaut sur trixie est fourni par
MariaDB, sous le paquet `libmariadb3`.

**Solution** : dans le `Dockerfile`, étape runtime, remplacement de
`default-libmysqlclient21` par `libmariadb3` (compatible avec les binaires
liés via `default-libmysqlclient-dev` utilisé au stage de build). Build
Docker vérifié en local avec succès après correctif.

**Fichiers** : `Dockerfile`.

---

## 2026-07-08 — Finalisation de la configuration de déploiement Docker/Render

**Problème** : plusieurs bugs empêchaient un déploiement Render fiable via Docker :
1. `DEBUG` restait "vrai" en production même avec `DEBUG=False` défini.
2. `DATABASE_URL` (Postgres Render) n'était jamais appliqué à `DATABASES`.
3. Le `Dockerfile` copiait tout le contexte de build (pas de `.dockerignore`) et
   exécutait `collectstatic` **au build**, alors que Render n'injecte les
   variables d'environnement du Dashboard qu'**au runtime** — le build échouait
   ou embarquait des valeurs bidon.
4. `gunicorn` écoutait en dur sur le port 8000 au lieu du `$PORT` fourni par Render.

**Cause** :
1. `DEBUG = env("DEBUG") or os.environ.get("DEBUG", "False")` — `env("DEBUG")`
   (casté en bool via le schéma `environ.Env`) valait `False`, donc l'expression
   retombait sur `os.environ.get(...)` qui renvoie la **chaîne** `"False"`,
   truthy en Python.
2. `dj_database_url` était importé mais jamais utilisé ; `DATABASES` restait
   toujours construit depuis les variables `DB_*` (MySQL).
3. Absence de `.dockerignore` + `RUN collectstatic` placé avant l'entrée en
   production dans le Dockerfile.
4. `CMD` gunicorn avec `--bind 0.0.0.0:8000` figé.

**Solution** :
- `DEBUG = env.bool("DEBUG", default=False)` (cast correct).
- `DATABASES` construit via `dj_database_url.parse(DATABASE_URL, ssl_require=not DEBUG)`
  quand `DATABASE_URL` est défini, sinon fallback MySQL `DB_*` inchangé.
- `ALLOWED_HOSTS` simplifié avec `env.list(..., default=[...])`.
- Ajout de `.dockerignore` (exclut `.env`, `.git`, `media/`, `logs/`, etc.).
- Ajout de `entrypoint.sh` : exécute `migrate` + `collectstatic` au démarrage du
  conteneur (variables d'environnement runtime disponibles), puis lance
  `gunicorn --bind 0.0.0.0:${PORT:-8000}`. Le `Dockerfile` utilise désormais cet
  entrypoint et son `HEALTHCHECK` respecte aussi `$PORT`.
- Ajout de `render.yaml` (Blueprint Docker + base Postgres gérée, health check
  `/api/health/`, variables d'environnement documentées) et de `.env.example`.
- Ajout de `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` :
  sans ce réglage, `request.is_secure()` reste toujours `False` derrière le
  proxy TLS de Render (cookies secure, CSRF, liens HTTPS mal détectés).

**Fichiers** : `gestion_p/settings.py`, `Dockerfile`, `entrypoint.sh` (nouveau),
`.dockerignore` (nouveau), `render.yaml` (nouveau), `.env.example` (nouveau).

---

## 2026-07-08 — Redis non configuré en production sur Render provoquant une erreur 500

**Problème** : déploiement Render déclenchait `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.` lors de l'accès à `/docs/`.

**Cause** : `gestion_p/settings.py` utilisait `REDIS_URL` par défaut `redis://localhost:6379/0` même en production, ce qui forçait `django_redis` à tenter une connexion à Redis local inexistant.

**Solution** : ne définir le cache Redis que si `REDIS_URL` est fourni. Si aucun Redis n'est configuré, basculer sur `LocMemCache` et, en production, stocker les sessions en base (`SESSION_ENGINE = 'django.contrib.sessions.backends.db'`).

**Fichiers** : `gestion_p/settings.py`.

---

## 2026-07-04 — `KeyError: 'request'` sur le profil (photo de profil)

**Problème** : `GET /api/user/profile/` plantait (500) dès qu'un utilisateur avait
une photo de profil : `KeyError: 'request'` dans
`UserSerializer.get_profile_picture_url`.

**Cause** : la méthode faisait `self.context["request"]`, mais plusieurs appelants
instancient `UserSerializer(user)` sans passer `request` dans le contexte
(`ProfileService.get_profile`, ainsi que login/register/MeView…).

**Solution** :
- `get_profile_picture_url` rendu défensif : `self.context.get("request")` ; si
  absent, renvoie l'URL relative (MEDIA_URL) au lieu de lever une exception.
- `ProfileService.get_profile`/`update_profile` acceptent `request` et le passent
  au serializer (URLs absolues) ; `UserProfileView` le transmet.

**Fichiers** : `accounts/serializers.py`, `accounts/profile/services.py`,
`accounts/profile/views.py`.

---

## 2026-07-04 — Suppression des vues API redondantes avec les pages HTML

**Problème** : `VerifyEmailView` et `ConfirmPasswordResetView` (endpoints API qui
consomment le token) faisaient doublon avec les pages `EmailVerifyPageView` et
`PasswordResetPageView` désormais chargées de ce flux (et généraient de la
confusion, ex. 405 sur un GET navigateur).

**Solution** : suppression des deux vues, de leurs routes
(`auth/email-verify/`, `auth/password-reset-confirm/`) et du helper de redirection.
Conservés car toujours utiles : `PasswordResetView` (demande d'envoi du lien),
`SendVerificationEmailView` (renvoi), `CheckVerificationStatusView` (statut). La
consommation du token passe exclusivement par les pages HTML.

**Fichiers** : `accounts/verification/views.py`, `accounts/urls.py`.

---

## 2026-07-03 — Pages HTML conviviales pour la vérification d'email et la réinitialisation

**Problème** : les liens des emails pointaient vers les endpoints **API**
(`/api/auth/email-verify`, `/api/auth/password-reset-confirm`) qui renvoient du
JSON brut / une page DRF — illisible pour l'utilisateur final.

**Solution** : de vraies pages web rendues par Django, au thème liturgique
(cohérent avec les emails).
- Vues serveur `EmailVerifyPageView` (GET → vérifie et affiche le résultat) et
  `PasswordResetPageView` (GET → formulaire ; POST → 2 champs mot de passe +
  confirmation, validation, résultat), réutilisant les services existants.
- Routes publiques `GET /verify-email/` et `GET|POST /reset-password/`.
- Templates `templates/auth/` (`base_auth.html`, `verify_email_result.html`,
  `password_reset_form.html`) : responsive, accessibles, afficher/masquer le mot
  de passe, contrôle de correspondance côté client.
- Nouveau réglage `PUBLIC_BASE_URL` (racine du site) ; les liens des emails
  pointent désormais vers ces pages.
- `STATICFILES_DIRS = [BASE_DIR/"static"]` ajouté pour que le logo se charge.
- Embarquement du logo email migré vers l'API moderne `email.message.MIMEPart`
  + `set_content(cid=...)` (Django 6 a supprimé `mixed_subtype`).

**Fichiers** : `accounts/verification/web_views.py` (nouveau),
`templates/auth/*` (nouveaux), `gestion_p/urls.py`, `gestion_p/settings.py`,
`accounts/verification/emails.py`.
**Tests** : `accounts/tests/test_web_pages.py` (9 tests) ; suite à 89 tests.

---

## 2026-07-02 — Refonte des templates d'email (contenu, UI, style) + correctif du nom d'app

**Problème** :
- Les emails (`verify_email.html`, `password_reset.html`) étaient en **anglais**
  alors que le projet est en français, avec un design générique daté.
- Bug : les templates utilisaient `{{ app_name }}` (minuscule) mais le contexte
  passait `App_name` (majuscule) → le nom de l'application s'affichait **vide**.

**Solution** :
- Nouvelle identité visuelle « liturgique » (nef bleu nuit + accent doré, titre
  serif Georgia, médaillon croix doré) dans `base_email.html`, compatible clients
  mail (layout en tables, styles inline, bouton bulletproof, texte d'aperçu masqué,
  aucun asset externe).
- Contenu réécrit en français (sujets, corps HTML **et** repli texte brut).
- Contexte corrigé : `App_name` → `app_name` ; `code_expiry` « 1 hour » → « 2 heures »
  (aligné sur `PASSWORD_RESET_TIMEOUT`).

**Fichiers** : `templates/emails/base_email.html`, `templates/emails/verify_email.html`,
`templates/emails/password_reset.html`, `accounts/verification/emails.py`.

---

## 2026-07-02 — Repli SMTP automatique en cas d'échec du backend email principal

**Problème** : à l'inscription, Resend renvoyait `403 (validation_error)` — « You can
only send testing emails to your own email address » — car le domaine n'est pas
vérifié sur Resend. L'email de vérification n'arrivait donc jamais aux autres
destinataires (3 tentatives échouées puis abandon).

**Cause** : un seul backend email (Resend/Anymail) était utilisé, sans repli.

**Solution** : ajout d'un repli SMTP automatique.

- `EmailService._send_with_fallback(subject, plain_message, html_message, recipient_list)` :
  1. tente l'envoi via le backend principal (Resend) ;
  2. en cas d'exception, ouvre une connexion SMTP explicite (`get_connection`) et
     ré-essaie ; l'expéditeur devient `EMAIL_HOST_USER` (contrainte Gmail).
- `send_verification_email` et `send_password_reset_email` utilisent ce helper.
- Nouveau réglage `EMAIL_FALLBACK_BACKEND` (mettre à `""` pour désactiver).

**Fichiers** : `accounts/verification/emails.py`, `gestion_p/settings.py`.
**Tests** : `accounts/tests/test_email_fallback.py` (5 tests).

---

## 2026-07-02 — Tests unitaires de l'authentification

**Ajout** : suite de tests unitaires complète pour l'authentification (package
`accounts/tests/`), couvrant modèle `User`, inscription, connexion (+ verrouillage
après 5 échecs), tokens (refresh/validate), déconnexion, changement de mot de passe,
vérification d'email et réinitialisation du mot de passe, ainsi que la couche service.

**Fichiers** : `accounts/tests/` (`base.py`, `test_models.py`, `test_registration.py`,
`test_login.py`, `test_tokens.py`, `test_session.py`, `test_email_verification.py`,
`test_password_reset.py`, `test_services.py`). Remplace l'ancien `accounts/tests.py`.

**Note infra** : la création de la base de test MySQL échoue
(`OperationalError 1824: Failed to open the referenced table 'auth_group'`) à cause
d'apps synchronisées en mode *syncdb* (fichiers de migration retirés, cf. commit
`a74e8be`). Contournement pour lancer les tests : SQLite via un settings dédié
(`DATABASES` → `sqlite3 :memory:`). Cause racine à régler : régénérer les migrations
manquantes des apps `groupes/membres/evenements/finances/librairie`.

---

## 2026-07-01 — `EMAIL_BACKEND` : import des settings cassé si la clé est absente

**Problème** : `EMAIL_BACKEND = env("EMAIL_BACKEND") or ...` levait
`ImproperlyConfigured` quand la clé n'était pas dans `.env` (le `or` de repli
n'était jamais atteint car `env()` lève avant de retourner).

**Solution** : `env("EMAIL_BACKEND", default=None)` pour laisser jouer la chaîne de
repli (`.env` → variable système → backend SMTP par défaut). Comportement de prod
inchangé.

**Fichier** : `gestion_p/settings.py`.

---

## 2026-06-30 — `UserListView` / `UserDetailView` cassées (héritage `APIView`)

**Problème** :

- `UserListView` n'avait aucun handler `get` → `405`.
- `UserDetailView` appelait `self.get_serializer(...)`, méthode inexistante sur
  `APIView` → `500` ; `perform_destroy` (hook de `generics`) n'était jamais appelé.

**Solution** :

- `UserListView.get` : liste paginée (`PageNumberPagination`) enveloppée au format Core.
- `UserDetailView` : `get`/`put` via `self.serializer_class` directement,
  `get_object` via `get_object_or_404` (404 propre), vrai handler `delete` avec
  journalisation d'activité.
- Imports ajoutés : `PageNumberPagination`, `get_object_or_404`.

**Fichier** : `accounts/auth/views.py`.

---

## 2026-06-29 — Conformité de toutes les réponses API au format Core

**Problème** : le format standardisé Core (`{success, data, error, message}`)
n'était pas respecté partout.

- Le gestionnaire d'exceptions prétendait « envelopper » les erreurs DRF mais
  renvoyait le format brut (`{"detail": ...}` / `{"champ": [...]}`).
- Quelques vues renvoyaient du JSON brut : `DashboardView`, `CheckPermissionView`,
  `UserDetailView`, `UserActivityView`.

**Solution** :

- `core/exception_handler.py` : conversion de **toutes** les réponses d'erreur DRF
  au format Core (validation, 401, 403, 404, throttling), avec garde-fou
  anti-double-emballage.
- Vues concernées : réponses enveloppées via `standardized_response` ;
  `UserActivityView.list()` surchargé pour préserver la pagination.

**Fichiers** : `core/exception_handler.py`, `accounts/auth/views.py`.

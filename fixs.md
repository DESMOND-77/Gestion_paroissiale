# Journal des correctifs (fixs.md)

Ce fichier documente les correctifs apportés au projet. Chaque entrée décrit le
problème, la cause, la solution et les fichiers touchés. Entrées les plus
récentes en haut.

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

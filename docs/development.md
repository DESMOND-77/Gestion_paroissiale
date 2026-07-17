# Guide du développeur

Conventions et pratiques pour développer sur **Gestion Paroissiale API**.
Complète le [guide de contribution](../CONTRIBUTING.md).

## Démarrage rapide

```bash
source .venv/bin/activate
docker-compose up -d db redis
python manage.py runserver 0.0.0.0:8000
```

## Conventions de code

### Langue

Le code métier, les commentaires, les messages d'API et la documentation sont
en **français**. Champs de modèles/serializers en français : `prenom`, `nom`,
`montant`, `quartier`… (`phone_number` et `role` font exception, hérités).

### Clés primaires UUID (offline-first)

Tout nouveau modèle hérite de `core.models.SyncableModel` (UUID `id` +
`created_at`/`updated_at`/`is_deleted`) ou `UUIDPrimaryKeyModel` (UUID seul).
Conséquences pratiques :

- routes en `<uuid:pk>`, **jamais** `<int:pk>` ;
- `str()` sur tout id inséré dans un JWT ou un JSON (un UUID n'est pas
  sérialisable) ;
- détection de création : `self._state.adding`, **pas** `not self.pk` (le
  défaut UUID remplit `pk` avant la première sauvegarde) ;
- comparer les ids comme des chaînes, jamais `int(...)`.

### Réponses et erreurs

- Toujours `standardized_response()` (`core/response.py`) — les clés à `None`
  sont omises.
- Ne pas attraper les exceptions DRF pour les reformater :
  `core/exception_handler.py` le fait globalement.
- Vues : hériter de `core/base_view.py::BaseAPIView`.
- Codes HTTP : 201 (création), 400 (validation), 401 (non authentifié),
  403 (interdit), 404 (introuvable).

### Permissions

- Le catalogue RBAC vit **uniquement** dans `core/rbac.py`
  (`PERMISSIONS_CATALOGUE`, `ROLE_PERMISSIONS`) — ne jamais le redéfinir ailleurs.
- Nouveau code : préférer les fabriques granulaires
  (`HasPermission("manage_membres")`, `HasAnyPermission(...)`,
  `HasAllPermissions(...)`) aux classes de hiérarchie de rôles. Attention : les
  deux mécanismes peuvent diverger (ex. `IsSecretaryOrAbove` autorise un
  trésorier à lister les membres alors que le catalogue ne lui donne pas
  `view_membres`) — choisir délibérément.

### E-mails

Toujours passer par `EmailService` (`accounts/verification/emails.py`) :
il gère le backend principal (Resend) + le repli SMTP, le logo inline (CID) et
les templates français (`templates/emails/`). Jamais `send_mail` directement.

### Journalisation

Chaque module a son logger (`logging.getLogger(__name__)`) ; jamais de
`print()`. Fichiers : `logs/gestionparoisse.log`, `logs/auth.log`,
`logs/finance.log` (rotation à 5 Mo). Détails : [`LOGGING.md`](../LOGGING.md).

## Migrations

- Chaque changement de modèle → `python manage.py makemigrations <app>` ;
- committer la migration **séparément** du code ;
- la CI échoue si des migrations manquent (`makemigrations --check --dry-run`).

## Tests

```bash
python manage.py test                              # tout
python manage.py test accounts                     # une app
python manage.py test accounts.tests.test_login    # un module
python manage.py test accounts.tests.test_login.LoginViewTests.test_login_success
```

- La suite auth vit dans `accounts/tests/`. `BaseAuthTest`
  (`accounts/tests/base.py`) rend les tests **hermétiques** : `LocMemCache`,
  backend e-mail en mémoire, client Redis neutralisé, fabriques
  (`create_user`, `auth`, `make_uid_token`).
- Exécution possible sur SQLite : `DATABASE_URL=sqlite:///ci.sqlite3
python manage.py test` (c'est ce que fait la CI).
- Couvrir les flux d'auth de bout en bout (login, logout, refresh, liste noire).

## Synchronisation hors ligne

Pour rendre une nouvelle collection synchronisable :

1. Modèle héritant de `SyncableModel` ;
2. serializer héritant de `core.serializers.WritableIDModelSerializer` ;
3. enregistrement dans le registre de `core/sync.py`.

## Journal des correctifs

Chaque correction de bug est documentée dans [`fixs.md`](../fixs.md) (racine),
nouvelle entrée **en haut**, en français : **Problème / Cause / Solution /
Fichiers** (+ **Tests** si pertinent).

## Outils de qualité

- **ruff** — linter + formateur, configuré dans
  [`pyproject.toml`](../pyproject.toml) et exécuté en CI :

  ```bash
  pip install --group dev   # installe les outils de dev (ruff)
  ruff check .              # lint : pycodestyle, pyflakes, isort, Django, bugbear, pyupgrade
  ruff format .             # formatage (style black) ; --check en CI
  ```

  Exclusions : migrations, `static/`, `media/`, `logs/`. Règles ignorées
  documentées dans `pyproject.toml` (`E501` géré par le formateur, `DJ001`
  hérité — ne pas introduire de nouveaux `null=True` sur des champs texte).

- `python manage.py check` — vérifications Django (exécuté en CI) ;
- CodeQL — analyse de sécurité automatique sur GitHub ;
- Dependabot — mises à jour hebdomadaires des dépendances.

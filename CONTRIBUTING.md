# Guide de contribution - Gestion Paroissiale API

Merci de contribuer ! Ce document décrit les règles et conventions du projet.
La langue du projet (code métier, commentaires, messages d'API, documentation)
est le **français**.

## Sommaire

- [Guide de contribution - Gestion Paroissiale API](#guide-de-contribution--gestion-paroissiale-api)
  - [Sommaire](#sommaire)
  - [Prérequis \& installation](#prérequis--installation)
  - [Workflow Git (GitHub Flow)](#workflow-git-github-flow)
  - [Convention de commits](#convention-de-commits)
  - [Style de code](#style-de-code)
  - [Tests](#tests)
  - [Documentation](#documentation)
  - [Journal des correctifs (obligatoire)](#journal-des-correctifs-obligatoire)
  - [Ouvrir une issue](#ouvrir-une-issue)
  - [Pull Requests](#pull-requests)
  - [Revue de code](#revue-de-code)

## Prérequis & installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # puis renseigner SECRET_KEY, base de données, Redis, e-mail…
docker-compose up -d db redis   # MariaDB (port 3307) + Redis (port 6380)
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Guide détaillé : [`docs/installation.md`](docs/installation.md) et
[`docs/development.md`](docs/development.md).

## Workflow Git (GitHub Flow)

Le projet suit le **GitHub Flow** :

1. Créer une branche depuis `main` ;
2. Committer des changements atomiques ;
3. Ouvrir une Pull Request ;
4. Revue de code + CI verte ;
5. Merge dans `main`.

Règles :

- **`main` = code prêt pour la production uniquement.** Ne jamais committer
  directement dessus.
- **Branches** : descriptives, en minuscules, préfixées par le type -
  `feature/verification-email`, `fix/token-blacklist`, `docs/guide-deploiement`.
- **Migrations** : committer les fichiers de migration **séparément** du code.
- Garder les branches courtes ; rebaser sur `main` avant d'ouvrir la PR si besoin.

## Convention de commits

Commits **atomiques** au format [Conventional Commits](https://www.conventionalcommits.org/fr/) :

| Préfixe     | Usage                                           |
| ----------- | ----------------------------------------------- |
| `feat:`     | Nouvelle fonctionnalité                         |
| `fix:`      | Correction de bug                               |
| `docs:`     | Documentation uniquement                        |
| `refactor:` | Refactorisation sans changement de comportement |
| `test:`     | Ajout / modification de tests                   |
| `perf:`     | Amélioration de performance                     |
| `chore:`    | Maintenance (dépendances, CI, config)           |

Exemples : `feat: Ajouter la vérification d'e-mail`, `fix: Corriger l'expiration du JWT`.

## Style de code

- **PEP 8** et idiomes Django/DRF ; s'aligner sur le style du code environnant.
- **Nommage des modèles / serializers** : champs en français
  (`prenom`, `nom`, `phone_number`, `role`).
- **Clés primaires UUID** : les nouveaux modèles héritent de
  `core.models.SyncableModel` (offline-first). Routes en `<uuid:pk>`, jamais
  `<int:pk>` ; `str()` sur tout id inséré dans un JWT/JSON ; détecter la création
  avec `self._state.adding` (pas `not self.pk`).
- **Endpoints** : versionnés sous `/api/v1/<module>/`. Exception : `/api/health/`
  reste non versionné (healthcheck Docker/Render).
- **Réponses** : utiliser `standardized_response()` de `core/response.py`
  (les clés à `None` sont omises). Les erreurs DRF sont re-formatées par
  `core/exception_handler.py`.
- **Permissions** : classes DRF de `core/permissions.py`. Préférer les fabriques
  granulaires (`HasPermission("manage_membres")`, …) adossées à `core/rbac.py`
  dans le nouveau code ; ne jamais redéfinir le catalogue de permissions ailleurs.
- **E-mails** : toujours passer par `EmailService`
  (`accounts/verification/emails.py`), jamais `send_mail` directement.
- **Logging** : chaque module a son logger ; ne pas utiliser `print()`.
- **Codes HTTP** : 201 (création), 400 (validation), 401 (non authentifié),
  403 (interdit), 404 (introuvable).

### Linting et formatage (ruff)

Le projet utilise **ruff** (linter + formateur, configuré dans
[`pyproject.toml`](pyproject.toml)) ; la CI échoue si le code n'est pas
conforme. Avant de committer :

```bash
pip install --group dev   # installe ruff
ruff check .              # lint (E, W, F, I, DJ, B, UP)
ruff format .             # formatage (style black)
```

Les migrations sont exclues du lint/formatage. Ne pas ajouter de `# noqa` sans
justification en commentaire.

## Tests

```bash
python manage.py test                 # tous les tests
python manage.py test accounts        # une app
python manage.py test accounts.tests.test_login  # un module
```

- La suite auth vit dans `accounts/tests/` ; `BaseAuthTest`
  (`accounts/tests/base.py`) rend les tests hermétiques (LocMemCache, e-mail en
  mémoire, Redis neutralisé) et fournit des fabriques (`create_user`, `auth`, …).
- La CI exécute la suite sur **SQLite** via `DATABASE_URL=sqlite:///ci.sqlite3` -
  aucun service MySQL/Redis n'est requis pour tester.
- Couvrir par des tests toute nouvelle logique (auth, permissions, calculs métier)
  et les flux complets (login, logout, refresh, liste noire).

## Documentation

- Mettre à jour le **README** et les fichiers de `docs/` impactés par le changement.
- La documentation interactive (Swagger/ReDoc) est générée automatiquement :
  soigner les serializers et docstrings des vues.
- Changement notable → entrée dans [`CHANGELOG.md`](CHANGELOG.md)
  (section « Non publié », format Keep a Changelog).

## Journal des correctifs (obligatoire)

Toute correction de bug doit être documentée dans **`fixs.md`** (racine du repo) :
nouvelle entrée datée **en haut** (plus récent en premier), en français, avec les
rubriques **Problème / Cause / Solution / Fichiers** (et **Tests** si pertinent).
Suivre le format des entrées existantes.

## Ouvrir une issue

Utiliser les [modèles d'issues](https://github.com/DESMOND-77/Gestion_paroissiale/issues/new/choose) :

- 🐛 **Bug** : description, étapes de reproduction, comportement attendu,
  environnement, logs.
- ✨ **Fonctionnalité** : problème à résoudre, solution proposée, alternatives.
- ❓ **Question** : pour toute interrogation générale.

Avant d'ouvrir une issue, vérifier qu'elle n'existe pas déjà.
**Vulnérabilité de sécurité → jamais d'issue publique**, voir [`SECURITY.md`](SECURITY.md).

## Pull Requests

- Une PR = un sujet. Remplir le [modèle de PR](.github/PULL_REQUEST_TEMPLATE.md).
- Lier l'issue correspondante (`Closes #12`).
- La CI (lint ruff + tests + `manage.py check`) doit être verte.

Checklist avant d'ouvrir la PR :

- [ ] `ruff check .` et `ruff format --check .` sans erreur.
- [ ] `python manage.py check` sans erreur.
- [ ] Tests pertinents ajoutés / verts (`python manage.py test`).
- [ ] Entrée `fixs.md` ajoutée si correction de bug.
- [ ] `CHANGELOG.md` mis à jour pour un changement notable.
- [ ] Migrations générées et committées séparément si les modèles changent.
- [ ] Documentation (README / `docs/`) mise à jour si nécessaire.

## Revue de code

- Toute PR est relue avant merge (voir [`CODEOWNERS`](.github/CODEOWNERS)).
- Le relecteur vérifie : correction, sécurité (permissions, validation des
  entrées), cohérence avec les conventions ci-dessus, couverture de tests.
- Les remarques se veulent constructives et bienveillantes - voir le
  [code de conduite](CODE_OF_CONDUCT.md).
- Merge en **squash** ou **rebase** de préférence, avec un message conforme aux
  Conventional Commits.

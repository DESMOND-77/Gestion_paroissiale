# Guide de contribution — Gestion Paroissiale API

Merci de contribuer ! Ce document résume les conventions du projet. La langue du
projet (code métier, commentaires, messages d'API) est le **français**.

## Prérequis & installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # puis renseigner SECRET_KEY, DATABASE_URL, REDIS_URL, email…
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Redis (tokens, cache, sessions) peut être lancé via `docker-compose up -d`.

## Workflow Git

- **Branches** : descriptives, en minuscules, préfixées par le type —
  `feature/verification-email`, `fix/token-blacklist`.
- **Ne jamais** committer directement sur `main` (code prêt pour la production
  uniquement). Ouvrir une Pull Request depuis une branche dédiée.
- **Commits atomiques** avec message clair au format
  [Conventional Commits](https://www.conventionalcommits.org/) :
  `feat: …`, `fix: …`, `docs: …`, `refactor: …`, `test: …`.
- **Migrations** : committer les fichiers de migration séparément du code.

## Journal des correctifs (obligatoire)

Toute correction de bug doit être documentée dans **`fixs.md`** (racine du repo) :
nouvelle entrée datée **en haut** (plus récent en premier), en français, avec les
rubriques **Problème / Cause / Solution / Fichiers** (et **Tests** si pertinent).
Suivre le format des entrées existantes.

Les changements notables orientés version sont synthétisés dans
[`CHANGELOG.md`](./CHANGELOG.md) (section « Non publié »).

## Conventions de code

- **Nommage des modèles / serializers** : champs en français
  (`prenom`, `nom`, `phone_number`, `role`).
- **Endpoints** : versionnés sous `/api/v1/<module>/`. Exception : le health
  check reste `/api/health/` (non versionné, utilisé par le healthcheck Docker).
- **Réponses** : utiliser `standardized_response()` de `core/response.py`
  (les clés à `None` sont omises). Les erreurs DRF sont re-formatées par
  `core/exception_handler.py`.
- **Permissions** : classes DRF (`IsAdmin`, `IsSecretaryOrAbove`, …) de
  `core/permissions.py`.
- **Logging** : chaque module a son logger ; ne pas utiliser `print()`.
- **Codes HTTP** : 201 (création), 400 (validation), 403 (interdit),
  404 (introuvable).

## Tests

```bash
python manage.py test                 # tous les tests
python manage.py test accounts        # une app
```

> **Caveat MySQL** : les apps locales étant créées via syncdb, la base de test
> MySQL peut échouer sur les FK inter-apps. Exécuter alors les tests sur SQLite
> en mémoire via un settings jetable :
> `python manage.py test accounts --settings=<sqlite_settings>`.

Merci de couvrir par des tests toute nouvelle logique (auth, permissions,
calculs métier).

## Checklist avant Pull Request

- [ ] `python manage.py check` sans erreur.
- [ ] Tests pertinents ajoutés / verts.
- [ ] Entrée `fixs.md` ajoutée si correction de bug.
- [ ] `CHANGELOG.md` mis à jour pour un changement notable.
- [ ] Migrations générées et committées si les modèles changent.

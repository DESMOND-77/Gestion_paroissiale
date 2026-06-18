# Gestion Paroissiale — API REST

API REST de **gestion paroissiale** développée avec Django et Django REST Framework.
Elle prend en charge l'authentification des utilisateurs, la gestion des rôles, la
vérification d'e-mail, la journalisation des activités, ainsi que la gestion des
membres, groupes, événements, finances et de la librairie de la paroisse.

> La langue de l'application, des commentaires et des messages d'API est le **français**.

---

## Sommaire

- [Gestion Paroissiale — API REST](#gestion-paroissiale--api-rest)
  - [Sommaire](#sommaire)
  - [Fonctionnalités](#fonctionnalités)
  - [Pile technique](#pile-technique)
  - [Architecture](#architecture)
    - [Flux d'une requête](#flux-dune-requête)
    - [Responsabilités des couches](#responsabilités-des-couches)
    - [Modules applicatifs](#modules-applicatifs)
  - [Prérequis](#prérequis)
  - [Installation](#installation)
  - [Configuration (.env)](#configuration-env)
  - [Lancer le projet](#lancer-le-projet)
  - [Rôles et permissions](#rôles-et-permissions)
  - [Authentification JWT](#authentification-jwt)
  - [Endpoints de l'API](#endpoints-de-lapi)
    - [Authentification \& comptes (`/api/`)](#authentification--comptes-api)
    - [Modules métier](#modules-métier)
  - [Format des réponses](#format-des-réponses)
  - [Documentation interactive](#documentation-interactive)
  - [Tests](#tests)
  - [Journalisation (logs)](#journalisation-logs)
  - [Structure du projet](#structure-du-projet)
  - [Documents complémentaires](#documents-complémentaires)

---

## Fonctionnalités

- 🔐 **Authentification JWT** complète (inscription, connexion, déconnexion, rafraîchissement, validation de jeton).
- 📧 **Vérification d'e-mail** obligatoire et **réinitialisation de mot de passe** par e-mail.
- 👥 **Gestion des utilisateurs** et **rôles hiérarchiques** (fidèle, responsable, secrétaire, trésorier, prêtre, admin).
- 🛡️ **Sécurité** : verrouillage de compte après 5 tentatives échouées (15 min), limitation de débit (throttling), liste noire de jetons via Redis.
- 🧾 **Journalisation des activités** utilisateur.
- ⛪ Modules métier : **membres**, **groupes**, **événements**, **finances** (transactions, dons, rapports), **librairie** (articles, ventes, alertes de stock).
- 📚 **Documentation API** auto-générée (Swagger / ReDoc).

---

## Pile technique

| Composant | Technologie |
| --- | --- |
| Langage | Python 3.14 |
| Framework | Django 6.0 |
| API | Django REST Framework 3.17 |
| Authentification | djangorestframework-simplejwt + TokenManager (Redis) |
| Base de données | MySQL (`mysqlclient`) — support PostgreSQL via `dj-database-url` / `psycopg2` |
| Cache / jetons / sessions | Redis 7 (`django-redis`) |
| E-mail | Resend via `django-anymail` (Render bloque le SMTP sortant en production) |
| Documentation | drf-yasg (Swagger / ReDoc) |
| Fichiers statiques | WhiteNoise |
| Serveur WSGI | Gunicorn |

---

## Architecture

### Flux d'une requête

```
Requête → gestion_p/urls.py → ViewSet/View (app/views.py) → Modèle → MySQL
                                                           ↘ Redis (liste noire JWT, sessions, rate limiting)
```

### Responsabilités des couches

- **Views** (`app/views.py`) — gestion HTTP via les ViewSets DRF, validation, logique métier, réponses standardisées.
- **Services** (app `accounts` uniquement : `auth/`, `profile/`, `verification/`) — logique métier complexe. Les autres apps gèrent la logique dans les vues.
- **Serializers** (`app/serializers.py`) — validation et transformation des données.
- **Models** (`app/models.py`) — modèles de base de données et managers personnalisés.
- **`accounts/core/`** — utilitaires partagés : `jwt_utils.py` (TokenManager sur Redis), `base_view.py`, `response.py`, `exception_handler.py`, `exceptions.py`.
- **`core/`** — permissions partagées : `IsAdmin`, `IsSecretaryOrAbove`, `IsTreasurerOrAbove`.

### Modules applicatifs

| App | Rôle |
| --- | --- |
| `accounts` | Authentification, profil, vérification e-mail, cycle de vie des jetons JWT |
| `groupes` | Gestion des groupes / associations |
| `membres` | Profils des membres / paroissiens et sacrements |
| `evenements` | Planification et gestion des événements + participations |
| `finances` | Suivi des transactions, dons, rapports financiers |
| `librairie` | Gestion des articles et des ventes |
| `core` | Permissions et mixins transverses |

---

## Prérequis

- Python 3.14+
- MySQL (ou PostgreSQL)
- Redis 7 (local ou via Docker)
- Un compte Resend (envoi d'e-mails) ou des identifiants SMTP en développement

---

## Installation

```bash
# 1. Créer et activer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Créer le fichier .env (voir section ci-dessous)

# 4. Démarrer Redis (via Docker)
docker-compose up -d

# 5. Appliquer les migrations
python manage.py migrate

# 6. Créer un super-utilisateur
python manage.py createsuperuser
```

---

## Configuration (.env)

Créer un fichier `.env` à la racine du projet :

```ini
SECRET_KEY='votre-cle-secrete'
DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,*

# Base de données
DB_NAME=gestion_paroissiale_db
DB_USER=root
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=3306

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# E-mail (Resend / Anymail)
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

> **Important** : en production (Render), l'envoi d'e-mails passe par **Resend** (via `django-anymail`) — le SMTP sortant y est bloqué. Ne pas revenir au backend SMTP en production.

---

## Lancer le projet

```bash
# Serveur de développement
python manage.py runserver 0.0.0.0:8000

# Vérifier la connectivité Redis
python test_redis.py
```

L'API est alors accessible sur `http://127.0.0.1:8000/`.

Avec Docker (Redis + Django) :

```bash
docker-compose up
```

---

## Rôles et permissions

Le modèle utilisateur personnalisé (`accounts.models.User`) étend `AbstractBaseUser`.
Le champ `USERNAME_FIELD` est l'**e-mail**.

| Rôle | Permissions métier |
| --- | --- |
| **admin** (Administrateur) | Accès complet : utilisateurs, finances, événements, groupes, membres, activités, librairie |
| **pretre** (Prêtre) | Finances, événements, groupes, membres, librairie |
| **tresorier** (Trésorier) | Finances, membres, consultation des activités |
| **secretaire** (Secrétaire) | Événements, groupes, membres, librairie |
| **responsable** (Responsable) | Membres, groupes |
| **fidele** (Fidèle / Étudiant) | Lecture de son propre profil |

Les permissions sont appliquées via les classes de `core/permissions.py`
(`IsAdmin`, `IsSecretaryOrAbove`, `IsTreasurerOrAbove`).

---

## Authentification JWT

`TokenManager` (`accounts/core/jwt_utils.py`) gère le cycle de vie complet des jetons :

- **Jeton d'accès** : 3 jours — **Jeton de rafraîchissement** : 14 jours.
- Les jetons sont suivis dans Redis par leur `jti`.
- La déconnexion et le changement de mot de passe mettent les jetons en **liste noire** côté serveur.
- À chaque changement de mot de passe, `blacklist_all_user_tokens()` invalide tous les jetons actifs de l'utilisateur.

Sécurité supplémentaire :

- **5 tentatives** de connexion échouées → verrouillage de **15 minutes** (suivi via Redis).
- La **vérification d'e-mail est obligatoire** : un utilisateur non vérifié ne peut pas s'authentifier.
- **Limitation de débit** via les classes de throttle DRF.

---

## Endpoints de l'API

Préfixe global : `/api/`

### Authentification & comptes (`/api/`)

| Méthode | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register/` | Inscription |
| POST | `/api/auth/login/` | Connexion |
| POST | `/api/auth/logout/` | Déconnexion |
| POST | `/api/auth/token/refresh` | Rafraîchir le jeton |
| POST | `/api/auth/token/validate/` | Valider un jeton |
| GET  | `/api/auth/me/` | Utilisateur courant |
| POST | `/api/auth/password-reset/` | Demande de réinitialisation du mot de passe |
| POST | `/api/auth/password-reset-confirm/` | Confirmation de réinitialisation |
| POST | `/api/auth/email-verify/` | Vérifier l'e-mail |
| POST | `/api/auth/send-verification/` | Renvoyer l'e-mail de vérification |
| GET  | `/api/auth/verification-status/` | Statut de vérification |
| GET/PUT | `/api/user/profile/` | Profil utilisateur |
| POST | `/api/user/change-password/` | Changer le mot de passe |
| GET  | `/api/users/` | Liste des utilisateurs (admin) |
| GET  | `/api/users/<id>/` | Détail d'un utilisateur (admin) |
| GET  | `/api/activities/` | Journal d'activités (admin) |
| GET  | `/api/check-permission/` | Vérifier une permission |

### Modules métier

| Module | Endpoint de base | Endpoints spécifiques |
| --- | --- | --- |
| Groupes | `/api/groupes/` | CRUD via ViewSet |
| Membres | `/api/membres/` | CRUD via ViewSet |
| Événements | `/api/evenements/` | CRUD via ViewSet |
| Finances | `/api/finances/transactions/` | `/api/finances/rapport/` (rapport financier), `/api/finances/membre/<id>/dons/` (dons d'un membre) |
| Librairie | `/api/librairie/articles/`, `/api/librairie/ventes/` | `/api/librairie/alertes/` (alertes de stock) |

---

## Format des réponses

Tous les endpoints renvoient une réponse standardisée
(via `standardized_response()` de `accounts/core/response.py`) :

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": "..."
}
```

Un gestionnaire d'exceptions personnalisé (`accounts/core/exception_handler.py`)
convertit les exceptions DRF dans ce même format.

---

## Documentation interactive

- **Swagger UI** : [`/docs/`](http://127.0.0.1:8000/docs/)
- **ReDoc** : [`/redoc/`](http://127.0.0.1:8000/redoc/)
- **Administration Django** : [`/admin/`](http://127.0.0.1:8000/admin/)

---

## Tests

```bash
# Tous les tests
python manage.py test

# Tests d'une app
python manage.py test accounts

# Un module de test précis
python manage.py test accounts.auth.views

# Test de la journalisation
python test_logging.py

# Test de connectivité Redis
python test_redis.py
```

---

## Journalisation (logs)

Toutes les modules disposent d'une journalisation détaillée :

- **Sortie console + fichiers** : les logs apparaissent dans le terminal et dans des fichiers rotatifs.
- **Fichiers de log** :
  - `logs/gestionparoisse.log` — principal
  - `logs/auth.log` — sécurité / authentification
  - `logs/finance.log` — opérations financières
- **Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL.
- **Rotation automatique** : à 5 Mo, 5 sauvegardes conservées.

Guide complet : [`LOGGING.md`](LOGGING.md). Configuration dans la section `LOGGING` de `gestion_p/settings.py`.

---

## Structure du projet

```
backend/
├── gestion_p/          # Configuration du projet (settings, urls, wsgi)
├── accounts/           # Authentification, profil, vérification, JWT
│   ├── auth/           # Inscription, connexion, gestion des utilisateurs
│   ├── profile/        # Gestion du profil
│   ├── verification/   # Vérification e-mail & réinitialisation du mot de passe
│   └── core/           # jwt_utils, base_view, response, exception_handler
├── core/               # Permissions et mixins partagés
├── groupes/            # Gestion des groupes
├── membres/            # Gestion des membres et sacrements
├── evenements/         # Gestion des événements et participations
├── finances/           # Transactions, dons, rapports
├── librairie/          # Articles et ventes
├── templates/emails/   # Modèles d'e-mails
├── logs/               # Fichiers de journalisation
├── media/              # Fichiers téléversés
├── static/             # Fichiers statiques
├── docker-compose.yaml # Redis + service web
├── requirements.txt
└── manage.py
```

---

## Documents complémentaires

- [`LOGGING.md`](LOGGING.md) — guide de configuration de la journalisation.
- [`ANALYSE_COHERENCE_API.md`](ANALYSE_COHERENCE_API.md) / [`POST_ANALYSE_COHERENCE_API.md`](POST_ANALYSE_COHERENCE_API.md) — analyses de cohérence de l'API.

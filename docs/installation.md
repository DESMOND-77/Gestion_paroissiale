# Installation

Guide d'installation pas à pas pour un environnement de développement.

## Prérequis

| Outil                              | Version              | Obligatoire                             |
| ---------------------------------- | -------------------- | --------------------------------------- |
| Python                             | 3.14+                | ✅                                      |
| MySQL / MariaDB (ou PostgreSQL)    | MariaDB 11 / MySQL 8 | ✅ (SQLite possible via `DATABASE_URL`) |
| Redis                              | 7                    | Recommandé (repli `LocMemCache` sinon)  |
| Docker + Docker Compose            | récent               | Optionnel (fournit MariaDB + Redis)     |
| Compte Resend ou identifiants SMTP | -                    | Pour l'envoi d'e-mails                  |

Sous Debian/Ubuntu, `mysqlclient` nécessite des paquets système :

```bash
sudo apt-get install default-libmysqlclient-dev pkg-config gcc python3-dev
```

## 1. Cloner et créer l'environnement

```bash
git clone https://github.com/DESMOND-77/Gestion_paroissiale.git
cd Gestion_paroissiale

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Renseigner au minimum : `SECRET_KEY`, la base de données (`DB_*` ou
`DATABASE_URL`), `REDIS_URL`, et la configuration e-mail. Chaque variable est
commentée dans [`.env.example`](../.env.example).

## 3. Base de données et Redis

### Option A - Docker (recommandé)

```bash
docker-compose up -d db redis
```

- MariaDB 11 exposée sur `127.0.0.1:3307` (base `gestion_paroissiale_db`,
  utilisateur `root` / mot de passe `root`).
- Redis 7 exposé sur `127.0.0.1:6380`.

Les valeurs par défaut de `.env.example` pointent déjà vers ces ports.

### Option B - services locaux

Installer MySQL/MariaDB et Redis nativement, créer la base :

```sql
CREATE DATABASE gestion_paroissiale_db CHARACTER SET utf8mb4;
```

puis adapter `DB_HOST`/`DB_PORT` (3306) et `REDIS_URL` (6379) dans `.env`.

### Option C - SQLite (tests rapides uniquement)

```bash
DATABASE_URL=sqlite:///db.sqlite3 python manage.py migrate
```

## 4. Migrations et super-utilisateur

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 5. Lancer le serveur

```bash
python manage.py runserver 0.0.0.0:8000
```

Vérifications :

- API : <http://127.0.0.1:8000/api/health/> (état BDD + Redis)
- Swagger : <http://127.0.0.1:8000/docs/>
- Admin : <http://127.0.0.1:8000/admin/>
- Connectivité Redis : `python test_redis.py`

## 6. Lancer les tests

```bash
python manage.py test
```

La suite (90+ tests) est hermétique : elle n'exige ni Redis ni serveur mail.

## Environnement complet en Docker

Pour lancer aussi l'API dans un conteneur (build du `Dockerfile` de production) :

```bash
docker-compose up
# API : http://127.0.0.1:8100/
```

## Dépannage

| Problème                           | Solution                                                                            |
| ---------------------------------- | ----------------------------------------------------------------------------------- |
| `mysqlclient` ne compile pas       | Installer `default-libmysqlclient-dev pkg-config` (voir prérequis)                  |
| `ImproperlyConfigured: SECRET_KEY` | Le fichier `.env` est manquant ou incomplet                                         |
| Les e-mails ne partent pas         | Vérifier `RESEND_API_KEY` / identifiants SMTP ; voir la FAQ du README               |
| Redis indisponible                 | L'app démarre en mode dégradé ; vérifier `REDIS_URL` et `docker-compose ps`         |
| Erreur MySQL 1824 (FK)             | Exécuter `python manage.py migrate` - toutes les apps ont des migrations committées |

# Déploiement

Deux cibles de déploiement sont supportées : **Docker** (auto-hébergé) et
**Render** (déploiement de référence, via Blueprint).

## Image Docker

Le [`Dockerfile`](../Dockerfile) est multi-stage (builder + runtime slim),
tourne sous un **utilisateur non-root** et embarque un `HEALTHCHECK` sur
`/api/health/`.

```bash
docker build -t gestion-paroissiale .
docker run --env-file .env -e PORT=8000 -p 8000:8000 gestion-paroissiale
```

Au démarrage, [`entrypoint.sh`](../entrypoint.sh) exécute :

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput --clear`
3. `gunicorn gestion_p.wsgi:application --bind 0.0.0.0:${PORT:-8000}
--workers ${WEB_CONCURRENCY:-4}`

> Migrations et `collectstatic` s'exécutent au **démarrage du conteneur**, pas
> au build : sur Render, les variables d'environnement ne sont injectées qu'au
> runtime.

## docker-compose (environnement complet)

```bash
docker-compose up -d
```

| Service | Image                              | Port hôte |
| ------- | ---------------------------------- | --------- |
| `db`    | mariadb:11                         | 3307      |
| `redis` | redis:7-alpine (conf `redis.conf`) | 6380      |
| `web`   | build du Dockerfile                | 8100      |

Le service `web` lit `.env` puis surcharge `DB_*` et `REDIS_URL` pour pointer
vers les conteneurs.

## Render (production de référence)

Le Blueprint [`render.yaml`](../render.yaml) décrit le déploiement :

- **Service web** `gestion-paroissiale-api` (runtime Docker, plan free, région
  Oregon), health check sur `/api/health/`, auto-deploy sur `main`.
- **Base PostgreSQL** `gestion-paroissiale-db` - l'app bascule sur PostgreSQL
  dès que `DATABASE_URL` est définie (prioritaire sur les `DB_*`).
- **Secrets** (`sync: false`) à renseigner dans le Dashboard :
  `FRONTEND_URL`, `REDIS_URL`, `RESEND_API_KEY`, `FROM_EMAIL`,
  `TEST_RECIPIENT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.
  `SECRET_KEY` est généré automatiquement par Render.

### Contraintes spécifiques à Render

- **SMTP sortant bloqué** : seul le backend **Resend**
  (`anymail.backends.resend.EmailBackend`) fonctionne en production. Laisser
  `EMAIL_FALLBACK_BACKEND=""` (le repli SMTP échouerait de toute façon) et ne
  jamais faire du SMTP le backend principal en prod.
- **Pas de Redis gratuit** : pointer `REDIS_URL` vers une instance externe
  (ex. Upstash) ou laisser vide - l'app fonctionne alors en mode dégradé
  (`LocMemCache` + sessions en base).
- `PUBLIC_BASE_URL` doit pointer vers l'URL publique de l'API **suffixée
  `/api`** (ex. `https://gestiparr.onrender.com/api`) : c'est la base des liens
  de vérification/réinitialisation envoyés par e-mail.

## Checklist de mise en production

- [ ] `DEBUG=False` et `SECRET_KEY` fort (généré, jamais committé)
- [ ] `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
      restreints aux domaines réels
- [ ] `DATABASE_URL` (PostgreSQL) et `REDIS_URL` configurés
- [ ] E-mail : `EMAIL_BACKEND=anymail.backends.resend.EmailBackend`,
      `RESEND_API_KEY` valide, domaine expéditeur vérifié chez Resend
- [ ] `/api/health/` renvoie `success: true` (BDD + Redis)
- [ ] HSTS / redirection SSL actives (automatiques quand `DEBUG=False`)
- [ ] Superutilisateur créé, rôle par défaut des inscriptions = `fidele`

## Rollback

Render conserve les déploiements précédents : _Dashboard → service → Deploys →
Rollback_. Les migrations étant appliquées au démarrage, un rollback de code
n'annule pas une migration destructive - écrire des migrations
rétro-compatibles.

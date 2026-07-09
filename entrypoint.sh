#!/bin/sh
set -e

# Migrate & collectstatic run at container start, not at build time: on Render
# the Dashboard env vars (SECRET_KEY, DATABASE_URL, ...) are only injected at
# runtime, not into the Docker build step, so settings.py can't be imported
# during `docker build` (see fixs.md, entrée déploiement Render).
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

exec gunicorn gestion_p.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-4}" \
    --worker-class sync \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -

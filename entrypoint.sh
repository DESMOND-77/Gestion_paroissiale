#!/bin/sh
set -e

# Migrate & collectstatic run at container start, not at build time: on Render
# the Dashboard env vars (SECRET_KEY, DATABASE_URL, ...) are only injected at
# runtime, not into the Docker build step, so settings.py can't be imported
# during `docker build` (see fixs.md, entrée déploiement Render).
# 2. Commandes d'initialisation Django habituelles
echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

# 3. Lancement de Gunicorn au premier plan
echo "==> Starting Gunicorn web server..."
exec gunicorn gestion_p.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-4}" \
    --worker-class sync \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
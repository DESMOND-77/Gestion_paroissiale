# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gestion Paroissiale** — A parish management REST API built with Django. Language of application and code comments is French. The system handles user authentication, roles (fidèle/étudiant, prêtre, admin, secrétaire, trésorier, responsable), email verification, and activity logging.

## Commands

```bash
# Activate virtualenv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver 0.0.0.0:8000

# Create a superuser
python manage.py createsuperuser

# Run all tests
python manage.py test

# Run a single app's tests
python manage.py test accounts

# Run a specific test module
python manage.py test accounts.auth.views

# Start Redis (via Docker)
docker-compose up -d

# Check Redis connectivity
python test_redis.py
```

## Environment Configuration

Requires a `.env` file at the project root. Key variables:

```json
SECRET_KEY='...'
DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,*
DB_NAME=gestion_paroissiale_db
DB_USER=root
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=3306
REDIS_URL=redis://127.0.0.1:6379/0
```

Email is sent via Gmail SMTP — `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` (app password) must also be set.

## Architecture

### Request flow

```flow
Request → gestion_p/urls.py → ViewSet/View (app/views.py) → Model → MySQL
                                                           ↘ Redis (JWT blacklist, sessions, rate limiting)
```

### Layer responsibilities

- **Views** (`app/views.py`) — HTTP handling via DRF ViewSets, request validation, business logic (see note below), call serializers, return standardized responses via `accounts/core/response.py:standardized_response()`.
- **Services** (accounts only: `accounts/auth/services.py`, `accounts/profile/services.py`, `accounts/verification/services.py`) — complex business logic. *Note: Accounts app uses service layer; other apps handle logic in views.*
- **Serializers** (`app/serializers.py`) — data validation, field transformation.
- **Models** (`app/models.py`) — database models, custom managers.
- **`accounts/core/`** — shared utilities: `jwt_utils.py` (TokenManager over Redis), `base_view.py` (BaseAPIView), `response.py`, `exception_handler.py`, `exceptions.py`.
- **`core/`** — shared permissions: `permissions.py` (IsAdmin, IsSecretaryOrAbove, IsTreasurerOrAbove).

### App modules

| App | Purpose |
| --- | --- |
| `accounts` | User authentication, profile, email verification, JWT token lifecycle |
| `groupes` | Group/association management |
| `membres` | Member/parishioner profiles and metadata |
| `evenements` | Event scheduling and management |
| `finances` | Transaction tracking, donation records, financial reports |
| `librairie` | Library/document management |

### Custom User model

`accounts.models.User` extends `AbstractBaseUser`. Key fields: `role` (fidele/etudiant | pretre | admin), `is_verified`, `sacrement`, `created_by` (self-FK). Always use `AUTH_USER_MODEL = 'accounts.User'` when referencing the user in new apps.

### JWT & Redis

`TokenManager` (`accounts/core/jwt_utils.py`) manages the full token lifecycle:

- Access token: 3 days; Refresh token: 14 days.
- Tokens are tracked in Redis by `jti`; logout and password-change blacklist tokens server-side.
- On password change, `blacklist_all_user_tokens()` invalidates every active token for the user.

### Role hierarchy & permissions

User roles are enforced via custom permission classes in `core/permissions.py`:

- **Admin** — full system access
- **Prêtre** — priest, can access treasurer and secretary-level operations
- **Trésorier** (Treasurer) — financial operations (`IsTreasurerOrAbove`)
- **Secrétaire** (Secretary) — member and event management (`IsSecretaryOrAbove`)
- **Responsable** (Coordinator) — can access secretary-level operations
- **Fidèle/Étudiant** (Parishioner/Student) — basic read access to own profile

### Authentication security

- 5 failed login attempts trigger a 15-minute account lockout (tracked in Redis).
- Email verification is required; unverified users cannot authenticate.
- Rate limiting is applied via DRF throttle classes.
- Custom exception handler (`accounts/core/exception_handler.py`) converts DRF exceptions to standardized response format.

### API response format

All endpoints return:

```json
{ "success": bool, "data": {}, "error": "...", "message": "..." }
```

Use `standardized_response()` from `accounts/core/response.py` for every new endpoint.

### API documentation

Swagger UI is at `/docs/` and ReDoc at `/redoc/` (powered by drf-spectacular/drf-yasg).

## Key files

| Purpose | Path |
| --- | --- |
| Settings | `gestion_p/settings.py` |
| Root URL router | `gestion_p/urls.py` |
| User model | `accounts/models.py` |
| Auth service | `accounts/auth/services.py` |
| Profile service | `accounts/profile/services.py` |
| Email verification | `accounts/verification/services.py` |
| JWT / Redis utils | `accounts/core/jwt_utils.py` |
| Exception handler | `accounts/core/exception_handler.py` |
| Role permissions | `core/permissions.py` |
| Response formatter | `accounts/core/response.py` |
| Email templates | `templates/emails/` |
| Docker setup | `docker-compose.yaml` |
| Logging config | `gestion_p/settings.py` (LOGGING section) |
| Logging guide | `LOGGING.md` |
| User activity logs | `logs/` |
| Uploaded media | `media/` |

## Logging

All modules have comprehensive logging for debugging:

- **Console & file output**: Logs appear in terminal and are written to rotating files
- **Log files**: `logs/gestion_paroisse.log` (main), `logs/auth.log` (security), `logs/finance.log` (financial)
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Auto-rotation**: Files rotate at 5MB with 5 backups retained

View logging guide: `LOGGING.md` for detailed configuration and usage.

Test logging: `python test_logging.py`

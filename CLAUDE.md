# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gestion Paroissiale** is a Django REST API for managing parish (church) operations. The application language, comments, and API messages are **French**.

Key tech stack:

- **Framework**: Django 6.0 + Django REST Framework 3.17
- **Auth**: JWT (djangorestframework-simplejwt) with Redis token tracking
- **Database**: MySQL (default) or PostgreSQL via `DATABASE_URL`
- **Cache/Sessions/Tokens**: Redis 7
- **Email**: Resend via django-anymail (SMTP is blocked in production on Render)
- **Documentation**: drf-yasg (Swagger/ReDoc at `/docs/` and `/redoc/`)

---

## Common Development Commands

```bash
# Environment setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Database & migrations
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser

# Development server
python manage.py runserver 0.0.0.0:8000

# Testing
python manage.py test                    # All tests
python manage.py test accounts           # Single app
python manage.py test accounts.tests.test_login  # Single test module
python manage.py test accounts.tests.test_login.LoginViewTests.test_login_success  # Single test
python test_logging.py                   # Logging test
python test_redis.py                     # Redis connectivity

# Redis (via Docker)
docker-compose up -d
```

---

## Architecture

### Request Flow

```flow
HTTP Request → gestion_p/urls.py → ViewSet/View (app/views.py) → Service/Model → MySQL
                                                               ↘ Redis (tokens, sessions, rate limiting)
```

### Core Layers

**Views** (`app/views.py`): HTTP handling via DRF ViewSets, validation, business logic, standardized responses.

**Services** (in `accounts` subdirectories: `auth/`, `profile/`, `verification/`): Complex business logic. Other apps embed service logic in views or use a `service.py` file (e.g., `membres/service.py`).

**Serializers** (`app/serializers.py`): Data validation and transformation.

**Models** (`app/models.py`): Database models and custom managers.

**Shared Utilities** — all live in the root-level `core/` app (NOT `accounts/core/`):

- `core/jwt_utils.py`: `TokenManager` handles JWT lifecycle (tracking in Redis by `jti`, blacklisting on logout/password change). Falls back to `LocMemCache` semantics when Redis is unavailable.
- `core/response.py`: `standardized_response()`. Note it **omits** keys whose value is `None` — a success response is often just `{"success": true, "data": {...}}` with no `error`/`message`.
- `core/exception_handler.py`: `custom_exception_handler` (wired via `REST_FRAMEWORK["EXCEPTION_HANDLER"]`) converts **every** DRF error (validation, 401, 403, 404, throttling) into the standardized format.
- `core/base_view.py`: `BaseAPIView` — base class most auth/module views extend. Centralizes exception handling (`AuthenticationFailed` → standardized 401) and adds `check_extra_permission()`.
- `core/permissions.py`: Shared permission classes (`IsAdmin`, `IsSecretaryOrAbove`, `IsTreasurerOrAbove`).
- `core/health.py` + `core/views.py`: `HealthCheckView` (Redis + DB status, unauthenticated).

---

## Key Modules

| Module | Purpose |
| -------- | --------- |
| `accounts` | User auth (register, login, logout), JWT token management, email verification, password reset, user profile |
| `membres` | Member/parishioner profiles, sacraments, signals for profile creation on user signup |
| `groupes` | Group/association management |
| `evenements` | Event planning and participation |
| `finances` | Transactions, donations, financial reports |
| `librairie` | Library articles, sales, stock alerts |
| `core` | Shared permissions and mixins |

---

## Authentication & Authorization

- **Custom User Model**: `accounts.models.User` extends `AbstractBaseUser` with `USERNAME_FIELD = 'email'`.
- **Roles** (hierarchical): fidèle < responsable < secrétaire < trésorier < prêtre < admin
- **Required**: Email verification before first login. Failed login attempts (5) trigger 15-minute lockout via Redis.
- **JWT** (`SIMPLE_JWT` in settings): access token 15 min, refresh token 7 days, with `ROTATE_REFRESH_TOKENS`. Tokens tracked in Redis by `jti` (JWT ID). Logout and password changes blacklist all of a user's tokens. `TokenManager.generate_token()` issues the pair; the standard `rest_framework_simplejwt.TokenRefreshView` name is overridden by the local `accounts/auth/views.TokenRefreshView`.

---

## Standardized Response Format

All endpoints return:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": "..."
}
```

Use `standardized_response()` from `accounts/core/response.py` for consistency.

---

## Email Configuration

**CRITICAL in Production**: Email is sent via **Resend** (configured in `django-anymail`). SMTP outbound is **blocked on Render**. Never revert to SMTP backend in production settings. See `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`.

---

## Development Workflow

### Naming Conventions

- **Models**: French plurals in field names where appropriate (e.g., `prenom`, `nom` instead of `first_name`, `last_name` in new code).
- **Serializers**: Mirror model field names for consistency.
- **API Endpoints**: `/api/<module>/` (e.g., `/api/membres/`, `/api/finances/transactions/`).

### Code Patterns

1. **Permission Checks**: Use DRF permission classes in `permission_classes` or call `self.check_object_permissions(request, obj)`.
2. **Status Codes**: Return appropriate HTTP status (201 for creation, 400 for validation, 404 for not found, 403 for forbidden).
3. **Logging**: Each module has its own logger; enable via Django's `LOGGING` config in settings.
4. **Migrations**: Always create migrations for model changes; commit them separately from code changes.

### Serializer & Field Names

When working with User-related serializers, use **French field names**:

- `prenom` (first name)
- `nom` (last name)
- `email` (email)
- `phone_number` (telephone)
- `role` (user role)

Example from `accounts/serializers.py`:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "prenom", "nom", "phone_number", "role", ...]
```

### Testing Patterns

- The `accounts` auth suite lives in the `accounts/tests/` package. `accounts/tests/base.py` provides `BaseAuthTest`, which makes tests hermetic: `LocMemCache`, in-memory email backend, Redis client neutralized (`TokenManager.get_redis_client` mocked to `None`), and helper factories (`create_user`, `auth`, `make_uid_token`).
- **Known caveat**: creating the MySQL test DB currently fails with `OperationalError 1824: Failed to open the referenced table 'auth_group'` because several apps (`groupes/membres/evenements/finances/librairie`) ship without migration files and are created via syncdb, which MySQL rejects for cross-app FKs. Workaround: run tests on SQLite with a throwaway settings module that overrides `DATABASES` to `sqlite3 :memory:` (`python manage.py test accounts --settings=<sqlite_settings>`). Root fix: regenerate the missing migrations with `makemigrations`.
- Test auth flows thoroughly (login, logout, token refresh, blacklisting).

---

## Git Workflow

- **Branch naming**: Descriptive, lowercase (e.g., `feature/email-verification`, `fix/token-blacklist`).
- **Commits**: Atomic, with clear messages (e.g., "feat: Add email verification", "fix: Correct JWT token expiration").
- **Main branch**: Production-ready code only.
- **Fix log**: Every bug fix / correctif must also be documented in `fixs.md` at the repo root — add a new dated entry at the TOP (newest first), in French, with **Problème / Cause / Solution / Fichiers** (and Tests when relevant). Follow the existing entry format.

---

## Debugging & Logging

- **Log files** (defined in settings):
  - `logs/gestionparoisse.log` — main application
  - `logs/auth.log` — security/authentication
  - `logs/finance.log` — financial operations
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL. Rotation at 5 MB.
- **Console**: Logs output to terminal and files simultaneously.

See `LOGGING.md` for detailed configuration.

---

## Documentation

- **Interactive API docs**: `/docs/` (Swagger), `/redoc/` (ReDoc)
- **Admin panel**: `/admin/`
- **Supplementary docs**:
  - `README.md` — full project overview
  - `LOGGING.md` — logging configuration
  - `ANALYSE_COHERENCE_API.md` — API coherence analysis

---

## Important Configuration Files

- `.env`: Environment variables (SECRET_KEY, DEBUG, DATABASE_URL, REDIS_URL, email credentials)
- `gestion_p/settings.py`: Django configuration (installed apps, middleware, databases, email backend)
- `gestion_p/urls.py`: URL routing
- `docker-compose.yaml`: Redis container config
- `requirements.txt`: Python dependencies

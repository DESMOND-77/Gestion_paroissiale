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
python manage.py test accounts.auth.views # Specific module
python test_logging.py                   # Logging test
python test_redis.py                     # Redis connectivity

# Redis (via Docker)
docker-compose up -d
```

---

## Architecture

### Request Flow

```
HTTP Request → gestion_p/urls.py → ViewSet/View (app/views.py) → Service/Model → MySQL
                                                               ↘ Redis (tokens, sessions, rate limiting)
```

### Core Layers

**Views** (`app/views.py`): HTTP handling via DRF ViewSets, validation, business logic, standardized responses.

**Services** (in `accounts` subdirectories: `auth/`, `profile/`, `verification/`): Complex business logic. Other apps embed service logic in views or use a `service.py` file (e.g., `membres/service.py`).

**Serializers** (`app/serializers.py`): Data validation and transformation.

**Models** (`app/models.py`): Database models and custom managers.

**Shared Utilities**:
- `accounts/core/jwt_utils.py`: `TokenManager` handles JWT lifecycle (tracking in Redis, blacklisting on logout/password change).
- `accounts/core/response.py`: `standardized_response()` wraps all responses in `{success, data, error, message}` format.
- `accounts/core/exception_handler.py`: Converts DRF exceptions to standardized format.
- `accounts/core/exceptions.py`: Custom exception classes.
- `core/permissions.py`: Shared permission classes (`IsAdmin`, `IsSecretaryOrAbove`, `IsTreasurerOrAbove`).

---

## Key Modules

| Module | Purpose |
|--------|---------|
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
- **JWT**: Access token 3 days, refresh token 14 days. Tokens tracked in Redis by `jti` (JWT ID). Logout and password changes blacklist all user tokens.

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

- Use Django's test framework (`python manage.py test`).
- Test auth flows thoroughly (login, logout, token refresh, blacklisting).
- For Redis-dependent tests, ensure Redis is running locally.

---

## Git Workflow

- **Branch naming**: Descriptive, lowercase (e.g., `feature/email-verification`, `fix/token-blacklist`).
- **Commits**: Atomic, with clear messages (e.g., "feat: Add email verification", "fix: Correct JWT token expiration").
- **Main branch**: Production-ready code only.

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

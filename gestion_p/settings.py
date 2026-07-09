import os
import logging
import logging.handlers
from datetime import timedelta
from pathlib import Path
import environ
import dj_database_url
import redis

environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent, ".env"))
env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

SECRET_KEY = env("SECRET_KEY") or os.environ.get("SECRET_KEY")
# env.bool() cast est indispensable ici : `env("DEBUG") or os.environ.get(...)` renvoyait
# la chaîne "False" (tronquée en bool -> True) dès que DEBUG=False était défini, ce qui
# activait silencieusement le mode debug de Django en production.
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# Environnement Redis
REDIS_URL = env("REDIS_URL", default=None) or os.environ.get("REDIS_URL")
if REDIS_URL is None and DEBUG:
    REDIS_URL = "redis://localhost:6379/0"


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",
    "drf_yasg",
    "anymail",
    # local apps
    "accounts",
    "core",
    "groupes",
    "membres",
    "evenements",
    "finances",
    "librairie",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # doit être en haut pour gérer les CORS avant les autres middlewares
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # sert les fichiers statiques (admin, swagger) en prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gestion_p.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gestion_p.wsgi.application"

# DB config : DATABASE_URL (Postgres Render, déploiement) prioritaire sur le MySQL local
DATABASE_URL = env("DATABASE_URL", default=None) or os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME") or os.environ.get("DB_NAME"),
            "USER": env("DB_USER") or os.environ.get("DB_USER"),
            "PASSWORD": env("DB_PASSWORD") or os.environ.get("DB_PASSWORD"),
            "HOST": env("DB_HOST") or os.environ.get("DB_HOST"),
            "PORT": env("DB_PORT") or os.environ.get("DB_PORT"),
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


AUTH_USER_MODEL = "accounts.User"

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Logging pour le suivi
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} - {name} - {funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "gestionparoisse.log"),
            "maxBytes": 5242880,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "auth_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "auth.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "core_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "core.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "finance_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "finance.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "groupe_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "groupe.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "membre_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "membre.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "evenement_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "evenement.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "librairie_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "librairie.log"),
            "maxBytes": 5242880,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "accounts": {
            "handlers": ["auth_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "accounts.auth": {
            "handlers": ["auth_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core": {
            "handlers": ["core_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "finances": {
            "handlers": ["file", "finance_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "groupes": {
            "handlers": ["groupe_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "membres": {
            "handlers": ["membre_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "evenements": {
            "handlers": ["evenement_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "librairie": {
            "handlers": ["librairie_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Créez le dossier logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

SESSION_COOKIE_SECURE = True

# Render (comme la plupart des PaaS) termine le TLS au niveau du proxy et
# transmet en HTTP en interne : sans ce header, request.is_secure() renvoie
# toujours False derrière le proxy, ce qui casse les cookies secure, le CSRF
# et la génération de liens HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF — config complète selon l'environnement
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
    # CORS - Définir les origines autorisées en production
    CORS_ALLOWED_ORIGINS = env.list(
        "CORS_ALLOWED_ORIGINS",
        default=["https://example.com"],  # À configurer via variable d'environnement
    )

    # SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default=None)
else:
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    # CORS - Autoriser localhost en développement
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


# REST Framework + SimpleJWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_RATES": {
        "user": "100/minute",  # Limite de 100 requêtes par utilisateur par minute
        "anon": "100/minute",  # Limite de 100 requêtes par IP anonyme par minute
    },
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
}

# Pour xhtml2pdf
XHTML2PDF = {
    "default": {
        "encoding": "utf-8",
    }
}

# Cache pour les sessions (optionnel mais recommandé)
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"

# Note: ASGI/Channels not used - API is synchronous REST only
# If WebSockets needed in future: install channels + channels-redis
# and configure ASGI_APPLICATION + CHANNEL_LAYERS
# Cache settings - UNE seule définition !
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "RETRY_ON_TIMEOUT": True,
                "IGNORE_EXCEPTIONS": True,
                "MAX_CONNECTIONS": 1000,
                "PICKLE_VERSION": 4,
            },
            "KEY_PREFIX": "gestion_paroisse",
            "TIMEOUT": 86400 * 14,  # 14 jours pour les refresh tokens
        }
    }
    # Si Redis est disponible, on peut utiliser le cache pour les sessions
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
    if not DEBUG:
        # En production sans Redis configuré, utiliser la session DB pour éviter
        # des erreurs critiques de cache partagés sur Render.
        SESSION_ENGINE = "django.contrib.sessions.backends.db"


# Configuration Simple JWT optimisée pour Redis
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=15
    ),  # en production, vous pouvez réduire à 15 minutes
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=7
    ),  # en production, vous pouvez réduire à 7 jours
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(days=3),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=14),
}

# JWT cookies settings
JWT_AUTH_COOKIE_SECURE = False  # Set to True in production with HTTPS
JWT_COOKIE_NAME = "refresh_token"

#########################################################
# SESSION_COOKIE_DOMAIN = "xxxxx.com"  # Set your domain here for production


EMAIL_VERIFICATION_TIMEOUT = 3600 * 24 * 3  # 3 DAYS
PASSWORD_RESET_TIMEOUT = (
    7200  # 2 heures (Django utilise cette valeur pour les tokens de reset)
)
MOBILE_VERIFICATION_REDIRECT = True  # Enable redirect after mobile verification

REQUIRE_EMAIL_VERIFICATION = True  # Require email verification on registration

APP_NAME = "Gestion Paroissiale"
# Chemin (système de fichiers) du logo embarqué dans les emails via CID
# (`src="cid:logo"`). Une image inline s'affiche toujours, contrairement à une
# URL distante que beaucoup de clients mail bloquent par défaut.
EMAIL_LOGO_PATH = os.path.join(BASE_DIR, "static", "logo.png")
# print(f"EMAIL_LOGO_PATH: {EMAIL_LOGO_PATH} (exists: {os.path.exists(EMAIL_LOGO_PATH)})")
# Email settings
# Resend API key and email backend are configured in the .env file
FROM_EMAIL = env("FROM_EMAIL") or os.environ.get("FROM_EMAIL")
TEST_RECIPIENT = env("TEST_RECIPIENT") or os.environ.get("TEST_RECIPIENT")
EMAIL_BACKEND = env("EMAIL_BACKEND", default=None) or os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
# Backend de repli utilisé automatiquement si l'envoi via le backend principal
# (Resend/Anymail) échoue. Mettre à None/"" pour désactiver le fallback.
EMAIL_FALLBACK_BACKEND = env("EMAIL_FALLBACK_BACKEND", default=None) or os.environ.get(
    "EMAIL_FALLBACK_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
ANYMAIL = {
    "RESEND_API_KEY": env("RESEND_API_KEY") or os.environ.get("RESEND_API_KEY"),
}

# Gmail SMTP configuration
EMAIL_HOST = env("EMAIL_HOST") or os.environ.get("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT") or int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_SSL = env("EMAIL_USE_SSL") or os.environ.get("EMAIL_USE_SSL", "False")
EMAIL_HOST_USER = env("EMAIL_HOST_USER") or os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD") or os.environ.get(
    "EMAIL_HOST_PASSWORD"
)
EMAIL_TIMEOUT = 10  # 10 second timeout for SMTP connections
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
CONTACT_EMAIL = default = EMAIL_HOST_USER


FRONTEND_URL = env(
    "FRONTEND_URL", default="http://localhost:8000/api"
) or os.environ.get("FRONTEND_URL", "http://localhost:8000/api")

# URL publique de base du backend (racine du site), utilisée pour construire les
# liens des emails vers les pages HTML de vérification / réinitialisation servies
# par Django. Sans slash final.
PUBLIC_BASE_URL = (
    env("PUBLIC_BASE_URL", default=None)
    or os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")
).rstrip("/")


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Libreville"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Dossier source des fichiers statiques du projet (logo, etc.) — nécessaire pour
# que {% static %} les trouve en dev et que collectstatic les récupère en prod.
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise sert les fichiers statiques en production (Render n'a pas de serveur
# web dédié). En DEBUG, runserver les sert via les finders — pas de manifeste requis.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


"""Django settings for mini_trello_be.

Every value that differs between a laptop, CI and a deployment is read from the
environment. See the Configuration table in the repository README, and
``.env.example`` for a working local set.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# ---------------------------------------------------------------- security

# Previously a hardcoded 'django-insecure-...' literal committed to the repo.
# The insecure fallback only applies in DEBUG; production must supply a key.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = env_bool("DJANGO_DEBUG", True)

if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(50))'"
        )
    SECRET_KEY = "django-insecure-development-only-do-not-use-in-production"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

# -------------------------------------------------------------- application

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "graphene_django",
    "corsheaders",
    "boards",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware must sit above CommonMiddleware, otherwise CommonMiddleware
    # can issue a redirect before the CORS headers are attached and the browser
    # reports a CORS failure. It was last in the list.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000")

ROOT_URLCONF = "mini_trello_be.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mini_trello_be.wsgi.application"

# ------------------------------------------------------------------ storage

# Cards live in DynamoDB (see boards/dynamodb.py). This relational database
# backs only Django's own tables: sessions, auth and the admin.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_DB_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------- validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------- i18n/static

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ------------------------------------------------------------------ graphene

GRAPHENE = {
    "SCHEMA": "mini_trello_be.schema.schema",
}

#: GraphiQL is a development tool; it must not be exposed in production.
GRAPHIQL_ENABLED = env_bool("GRAPHIQL_ENABLED", DEBUG)

# ------------------------------------------------------------------- logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
    "loggers": {
        "boards": {"level": os.environ.get("LOG_LEVEL", "INFO"), "propagate": True},
    },
}

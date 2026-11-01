# Owner: Person A
"""
Django settings for tatkal_core project.
Configured with MySQL InnoDB backend (app_rw and app_ro roles),
JWT Authentication via SimpleJWT, CORS for Next.js 14 frontend,
and strict rate limiting for high-concurrency Tatkal booking.
"""

import os
from pathlib import Path
from datetime import timedelta
import dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load environment from root .env
dotenv.load_dotenv(REPO_ROOT / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-tatkal-production-grade-key-pes2026-chiranth-jashruth")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "booking_engine",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "tatkal_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "tatkal_core.wsgi.application"
ASGI_APPLICATION = "tatkal_core.asgi.application"

# Database Configuration: Separate Read-Write and Read-Only roles
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tatkal_db")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "Chiranth@SQL")

# Use app_rw by default, matching .env DB_APP_RW_USER
RW_USER = os.getenv("DB_APP_RW_USER") or os.getenv("MYSQL_RW_USER") or "app_rw"
RW_PASSWORD = os.getenv("DB_APP_RW_PASSWORD") or os.getenv("MYSQL_RW_PASSWORD") or "TatkalRw_SecurePass#2026"

RO_USER = os.getenv("DB_APP_RO_USER") or os.getenv("MYSQL_RO_USER") or "app_ro"
RO_PASSWORD = os.getenv("DB_APP_RO_PASSWORD") or os.getenv("MYSQL_RO_PASSWORD") or "TatkalRo_SecurePass#2026"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": MYSQL_DATABASE,
        "USER": RW_USER,
        "PASSWORD": RW_PASSWORD,
        "HOST": MYSQL_HOST,
        "PORT": MYSQL_PORT,
        "CONN_MAX_AGE": 300,
        "OPTIONS": {
            "charset": "utf8mb4",
            "autocommit": False,
            "connect_timeout": 5,
        },
    },
    "readonly": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": MYSQL_DATABASE,
        "USER": RO_USER,
        "PASSWORD": RO_PASSWORD,
        "HOST": MYSQL_HOST,
        "PORT": MYSQL_PORT,
        "CONN_MAX_AGE": 300,
        "OPTIONS": {
            "charset": "utf8mb4",
            "autocommit": True,
            "connect_timeout": 5,
        },
    },
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = False

STATIC_URL = "/static/"

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "booking_engine.auth_backend.CustomJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/minute",
        "user": "300/minute",
        "tatkal_burst": "10/minute",
        "tatkal_sustained": "60/hour",
    },
    "EXCEPTION_HANDLER": "booking_engine.exceptions.custom_exception_handler",
}

# SimpleJWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "SIGNING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256",
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "idempotency-key",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

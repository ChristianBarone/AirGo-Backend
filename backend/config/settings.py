import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "False") == "True"

# ── Apps ──────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "core",
    "corsheaders",
    "channels",
]

# ── Hosts ─────────────────────────────────────────────────────────────────────

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# ── Middleware ────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ── CORS ──────────────────────────────────────────────────────────────────────

## CAMBIAR PUERTO SERVIDOR FRONTEND (3000) SI ES DIFERENTE
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── URLs / WSGI ───────────────────────────────────────────────────────────────

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ── Templates ─────────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

# ── Base de datos ─────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "airgo"),
        "USER": os.getenv("POSTGRES_USER", "airgo_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "airgo_pass"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = []

# ── DRF ───────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ── SimpleJWT ─────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── drf-spectacular (Swagger / ReDoc) ─────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    "TITLE": "API AirGo",
    "DESCRIPTION": "Documentación de la API REST del proyecto AirGo",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Botón "Authorize" con JWT Bearer en Swagger UI
    "SECURITY": [{"BearerAuth": []}],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,  # mantiene el token al recargar la página
        "displayRequestDuration": True,  # muestra cuánto tarda cada request
        "filter": True,  # barra de búsqueda por tag/endpoint
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Introduce el access token obtenido en POST /auth/google/. "
                    "Formato esperado por Swagger: escribe solo el token, "
                    "el prefijo 'Bearer' se añade automáticamente."
                ),
            }
        }
    },
}

# ── Internacionalización ──────────────────────────────────────────────────────

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# ── Archivos estáticos y media ────────────────────────────────────────────────

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ── CSRF ──────────────────────────────────────────────────────────────────────

csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o for o in csrf_origins.split(",") if o]

# --Refresh---------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,  # ← cada refresh emite nuevo refresh token
    "BLACKLIST_AFTER_ROTATION": True,  # ← invalida el anterior
}

# ── Channels / WebSocket ──────────────────────────────────────────────────────
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (os.getenv("REDIS_HOST", "redis"), int(os.getenv("REDIS_PORT", "6379")))
            ],
        },
    }
}

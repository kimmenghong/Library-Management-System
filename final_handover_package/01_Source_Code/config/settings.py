import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_value(name, default=None, aliases=()):
    """Read an environment variable with optional backward-compatible aliases."""
    for key in (name, *aliases):
        value = os.getenv(key)
        if value is not None:
            return value
    return default


def env_bool(name, default=False, aliases=()):
    value = env_value(name, None, aliases=aliases)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default="", aliases=()):
    return [
        item.strip()
        for item in str(env_value(name, default, aliases=aliases)).split(",")
        if item.strip()
    ]


def env_int(name, default, aliases=()):
    try:
        return int(env_value(name, str(default), aliases=aliases))
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"{name} must be an integer.") from exc


DEVELOPMENT_SECRET_KEY = "django-insecure-library-management-system-dev-key"

DEBUG = env_bool("DEBUG", True, aliases=("DJANGO_DEBUG",))

SECRET_KEY = env_value(
    "SECRET_KEY",
    DEVELOPMENT_SECRET_KEY,
    aliases=("DJANGO_SECRET_KEY",),
)
if not DEBUG and SECRET_KEY == DEVELOPMENT_SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY must be set to a strong, unique value when DEBUG=False."
    )

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,testserver",
    aliases=("DJANGO_ALLOWED_HOSTS",),
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS cannot be empty in production.")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.library.apps.LibraryConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


DATABASE_ENGINE = env_value("DATABASE_ENGINE", "sqlite").lower()

if DATABASE_ENGINE in {"postgres", "postgresql"}:
    database_password = env_value("DATABASE_PASSWORD", "")
    if not database_password or database_password.startswith("copy-your-"):
        raise ImproperlyConfigured(
            "DATABASE_PASSWORD must be set to the real Supabase database password "
            "when DATABASE_ENGINE=postgresql."
        )
    postgres_options = {
        "sslmode": os.getenv("DATABASE_SSLMODE", "require"),
    }
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_value("DATABASE_NAME", "library_management"),
            "USER": env_value("DATABASE_USER", "postgres"),
            "PASSWORD": database_password,
            "HOST": env_value("DATABASE_HOST", "localhost"),
            "PORT": env_value("DATABASE_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", 60),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": postgres_options,
            "DISABLE_SERVER_SIDE_CURSORS": env_bool(
                "DATABASE_DISABLE_SERVER_SIDE_CURSORS",
                False,
            ),
        }
    }
elif DATABASE_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env_value("DATABASE_NAME", "library_management"),
            "USER": env_value("DATABASE_USER", "root"),
            "PASSWORD": env_value("DATABASE_PASSWORD", ""),
            "HOST": env_value("DATABASE_HOST", "localhost"),
            "PORT": env_value("DATABASE_PORT", "3306"),
            "CONN_MAX_AGE": env_int("DATABASE_CONN_MAX_AGE", 60),
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    sqlite_name = Path(env_value("SQLITE_NAME", "db.sqlite3"))
    if not sqlite_name.is_absolute():
        sqlite_name = BASE_DIR / sqlite_name
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_name,
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
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


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Phnom_Penh"
USE_I18N = True
USE_TZ = True


STATIC_URL = env_value("STATIC_URL", "/static/")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(env_value("STATIC_ROOT", BASE_DIR / "staticfiles"))
if not STATIC_ROOT.is_absolute():
    STATIC_ROOT = BASE_DIR / STATIC_ROOT

MEDIA_URL = env_value("MEDIA_URL", "/media/")
MEDIA_ROOT = Path(env_value("MEDIA_ROOT", BASE_DIR / "media"))
if not MEDIA_ROOT.is_absolute():
    MEDIA_ROOT = BASE_DIR / MEDIA_ROOT

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "library.User"

LOGIN_URL = "library:login"
LOGIN_REDIRECT_URL = "library:dashboard"
LOGOUT_REDIRECT_URL = "library:login"
PASSWORD_RESET_TIMEOUT = env_int("PASSWORD_RESET_TIMEOUT", 60 * 60 * 24)
TEST_RUNNER = "apps.library.test_runner.LibraryDiscoverRunner"

USE_SUPABASE_AUTH = env_bool("USE_SUPABASE_AUTH", False)
SUPABASE_PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_AUTH_REDIRECT_URL = os.getenv("SUPABASE_AUTH_REDIRECT_URL", "")
SUPABASE_AUTH_TIMEOUT = env_int("SUPABASE_AUTH_TIMEOUT", 10)
SUPABASE_AUTH_DEFAULT_ROLE = os.getenv("SUPABASE_AUTH_DEFAULT_ROLE", "Student")
SUPABASE_AUTH_REQUIRE_LOCAL_USER = env_bool(
    "SUPABASE_AUTH_REQUIRE_LOCAL_USER",
    True,
)
SUPABASE_AUTH_SESSION_KEY = os.getenv(
    "SUPABASE_AUTH_SESSION_KEY",
    "supabase_auth",
)

if USE_SUPABASE_AUTH and (not SUPABASE_URL or not SUPABASE_ANON_KEY):
    raise ImproperlyConfigured(
        "SUPABASE_URL and SUPABASE_ANON_KEY are required when "
        "USE_SUPABASE_AUTH=True."
    )
if USE_SUPABASE_AUTH and (
    "your-project-ref" in SUPABASE_URL
    or "copy-your-" in SUPABASE_ANON_KEY
    or SUPABASE_ANON_KEY == "your-supabase-anon-key"
):
    raise ImproperlyConfigured(
        "Replace the Supabase Auth placeholder values before enabling "
        "USE_SUPABASE_AUTH."
    )

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 25)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
EMAIL_PENDING_TIMEOUT_MINUTES = env_int("EMAIL_PENDING_TIMEOUT_MINUTES", 15)
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Library Management System <noreply@example.com>",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": env_int("API_PAGE_SIZE", 20),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 1)),
    "ROTATE_REFRESH_TOKENS": env_bool("JWT_ROTATE_REFRESH_TOKENS", False),
    "BLACKLIST_AFTER_ROTATION": env_bool("JWT_BLACKLIST_AFTER_ROTATION", False),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

MAX_UPLOAD_SIZE = env_int("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
PROFILE_IMAGE_MAX_SIZE = env_int("PROFILE_IMAGE_MAX_SIZE", 5 * 1024 * 1024)
REPORT_UPLOAD_MAX_SIZE = env_int("REPORT_UPLOAD_MAX_SIZE", 2 * 1024 * 1024)
REPORT_UPLOAD_ALLOWED_EXTENSIONS = env_list(
    "REPORT_UPLOAD_ALLOWED_EXTENSIONS",
    ".csv",
)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE
FILE_UPLOAD_PERMISSIONS = 0o644

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
CSRF_COOKIE_SAMESITE = env_value("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SAMESITE = env_value("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", False)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False if DEBUG else True)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = env_value(
    "SECURE_CROSS_ORIGIN_OPENER_POLICY",
    "same-origin",
)
SECURE_REFERRER_POLICY = env_value("SECURE_REFERRER_POLICY", "same-origin")
X_FRAME_OPTIONS = env_value("X_FRAME_OPTIONS", "DENY")

if env_bool("USE_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

LOG_DIR = Path(env_value("LOG_DIR", BASE_DIR / "logs"))
if not LOG_DIR.is_absolute():
    LOG_DIR = BASE_DIR / LOG_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "verbose": {
            "format": (
                "{levelname} {asctime} {name} " "{module}.{funcName}:{lineno} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "library.log",
            "maxBytes": env_int("LOG_FILE_MAX_BYTES", 1024 * 1024),
            "backupCount": env_int("LOG_FILE_BACKUP_COUNT", 5),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "library.audit": {
            "handlers": ["console", "file"],
            "level": os.getenv("LIBRARY_AUDIT_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "library.errors": {
            "handlers": ["console", "file"],
            "level": os.getenv("LIBRARY_ERROR_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}

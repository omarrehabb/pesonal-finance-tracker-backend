"""
Django settings for backend project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-fallback-key"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

# Allowed hosts
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Your apps
    "core",
    "transactions",
    "budgets",

    # Third-party
    "rest_framework",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "two_factor",
    "corsheaders",
    # Social auth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Authentication classes with optional 2FA enforcement
_base_auth_classes = [
    "rest_framework.authentication.SessionAuthentication",
    "rest_framework.authentication.BasicAuthentication",
]
if os.environ.get("DJANGO_ENFORCE_2FA", "false").lower() == "true":
    # Enforce OTP: only use our 2FA authenticator for API views by default
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "transactions.authentication.TwoFactorAuthentication",
    ]
else:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = _base_auth_classes

# Two-factor authentication
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"
OTP_TOTP_ISSUER = "Finance Tracker"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Whitenoise only in production
if not DEBUG:
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "backend.wsgi.application"

# CORS / CSRF
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    f"https://{os.environ.get('FLY_APP_NAME', '')}.fly.dev",
]
CORS_ALLOW_CREDENTIALS = True

SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False

# Database
# Database
# Only require SSL for Postgres URLs. SQLite doesn't support sslmode.
_env_db_url = os.environ.get("DATABASE_URL", "").strip()
if _env_db_url:
    _ssl_required = _env_db_url.startswith("postgres://") or _env_db_url.startswith("postgresql://")
    _db_config = dj_database_url.parse(
        _env_db_url,
        conn_max_age=600,
        ssl_require=_ssl_required,
    )
else:
    _db_config = dj_database_url.parse(
        f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )

DATABASES = {"default": _db_config}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

_project_static = BASE_DIR / "static"
STATICFILES_DIRS = [_project_static] if _project_static.exists() else []

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Django allauth / sites
SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Minimal account settings (email optional; no email verification for demo)
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_ADAPTER = "core.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "core.adapters.SocialAdapter"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.environ.get(
    "ACCOUNT_DEFAULT_HTTP_PROTOCOL",
    "https" if not DEBUG else "http",
)

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"prompt": "select_account"},
    }
}

# Skip the allauth intermediate confirmation page and jump straight to the
# provider authorization screen when hitting /accounts/<provider>/login/
SOCIALACCOUNT_LOGIN_ON_GET = True

# Allow 'next=' redirects to these domains (for dev convenience)
ACCOUNT_ALLOWED_REDIRECT_DOMAINS = [
    "localhost:3000",
    "127.0.0.1:3000",
]

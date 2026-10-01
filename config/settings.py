"""Django settings for the Right Point Solutions site.

Values that change between environments are read from the process environment
so the same image can run in development and production.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_flag(name, default="False"):
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-7(ei88x7oj%1_8madk7cy3*b%ojyu-+@qk3v9ki#zz_9eutj03"
)
# Vercel runs the app in production unless explicitly overridden. Keeping the
# development default here can expose debug pages and make deployment checks fail.
DEBUG = env_flag("DJANGO_DEBUG", "False")
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]
# Vercel can route requests through a unique deployment hostname that is not
# known when the environment variables are configured. Always allow the
# platform's deployment domains in addition to any explicit project hosts.
vercel_hosts = [
    host.strip()
    for host in (
        os.environ.get("VERCEL_URL", ""),
        os.environ.get("VERCEL_BRANCH_URL", ""),
        os.environ.get("VERCEL_PROJECT_PRODUCTION_URL", ""),
    )
    if host.strip()
]
# An explicit list is required in production; locally and under the test client
# we accept any host so the dev server and `manage.py test` work out of the box.
# Vercel uses ephemeral deployment hostnames, so allow its routed host when
# the function is running on the platform. Explicit hosts remain available for
# non-Vercel production deployments.
if DEBUG or os.environ.get("VERCEL") == "1":
    ALLOWED_HOSTS = ["*"]
elif not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
        ".vercel.app",
        "rightpoint.co.ke",
        "www.rightpoint.co.ke",
    ]
else:
    ALLOWED_HOSTS.extend([".vercel.app", "rightpoint.co.ke", "www.rightpoint.co.ke"])
ALLOWED_HOSTS.extend(host for host in vercel_hosts if host not in ALLOWED_HOSTS)

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS.extend(
    origin if origin.startswith("http") else f"https://{origin}"
    for origin in vercel_hosts
    if origin and (origin.startswith("http") or origin not in CSRF_TRUSTED_ORIGINS)
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "core",
    "solutions",
    "products",
    "casestudies",
    "contact",
    "quotes",
    "invoices",
    "accounts",
    "django.contrib.sites",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
                "products.context_processors.basket_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DJANGO_DB_USER", ""),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
        "HOST": os.environ.get("DJANGO_DB_HOST", ""),
        "PORT": os.environ.get("DJANGO_DB_PORT", ""),
    }
}

# Vercel provides Postgres as a URL. Support it when the explicit Django
# connection variables are not present, while retaining the local SQLite
# fallback for development and the existing explicit configuration.
if os.environ.get("POSTGRES_URL") and not os.environ.get("DJANGO_DB_ENGINE"):
    from urllib.parse import unquote, urlparse

    database_url = urlparse(os.environ["POSTGRES_URL"])
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(database_url.path.lstrip("/")),
        "USER": unquote(database_url.username or ""),
        "PASSWORD": unquote(database_url.password or ""),
        "HOST": database_url.hostname or "",
        "PORT": str(database_url.port or "5432"),
        "OPTIONS": {"sslmode": "require"},
    }

if os.environ.get("DJANGO_REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["DJANGO_REDIS_URL"],
        }
    }
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticroot"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Manifest hashing breaks `{% static %}` until collectstatic has run, so it is
# only switched on outside DEBUG. WhiteNoise then serves the hashed files.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_NAME = os.environ.get("SITE_NAME", "Right Point Solutions")
SITE_URL = os.environ.get("SITE_URL", "https://rightpoint.co.ke").rstrip("/")
SITE_ID = 1

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
SITE_DESCRIPTION = (
    "Nairobi-based security technology company delivering CCTV and video intelligence, "
    "access control, electric fencing, data centre construction, risk consultancy and "
    "security assessments across Kenya."
)

EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_flag("DJANGO_EMAIL_USE_TLS", "True")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Right Point Solutions <noreply@rightpoint.co.ke>")
ENQUIRY_NOTIFY_EMAILS = [
    e.strip() for e in os.environ.get("ENQUIRY_NOTIFY_EMAILS", "rightpointsolutionske@gmail.com").split(",") if e.strip()
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"
REFERRER_POLICY = "strict-origin-when-cross-origin"

# Only switch on transport security when the site is actually served over TLS;
# enabling it locally redirects the dev server into an infinite loop.
if env_flag("DJANGO_SECURE_SSL_REDIRECT"):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "[{asctime}] {levelname} {name} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}


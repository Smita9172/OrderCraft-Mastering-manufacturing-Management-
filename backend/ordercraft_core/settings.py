"""
Django settings for OrderCraft: Manufacturing Management ERP.

Frontend: HTML, CSS, Vanilla JavaScript
Backend: Python 3, Django 6
API: Django REST Framework
Database: Supabase PostgreSQL with SQLite fallback
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# BASE DIRECTORY & ENVIRONMENT VARIABLES
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Load project-root .env first, then backend/.env.
# override=True makes the .env files win over stale system environment
# variables, so backend/.env (loaded last) has the final say.
load_dotenv(BASE_DIR.parent / '.env', override=True)
load_dotenv(BASE_DIR / '.env', override=True)

# -------------------------------------------------
# SECURITY SETTINGS
# -------------------------------------------------

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'ordercraft-manufacturing-super-secret-key-2026'
)

DEBUG = os.getenv('DEBUG', 'True').strip().lower() in (
    'true', '1', 'yes'
)

ALLOWED_HOSTS = ['*']

# -------------------------------------------------
# APPLICATION DEFINITION
# -------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Libraries
    'corsheaders',
    'rest_framework',

    # OrderCraft Core Modules
    'apps.accounts',
    'apps.bom',
    'apps.orders',
    'apps.procurement',
    'apps.invoices',
    'apps.payments',
    'apps.analytics',
]

# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ordercraft_core.urls'

# -------------------------------------------------
# FRONTEND CONFIGURATION
# -------------------------------------------------

FRONTEND_DIR = BASE_DIR.parent / 'frontend'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ordercraft_core.wsgi.application'

# -------------------------------------------------
# DATABASE CONFIGURATION
# SUPABASE POSTGRESQL + SQLITE FALLBACK
# -------------------------------------------------

def _env(name, default=''):
    """Read an env var and strip stray spaces/quotes (e.g. 'PORT=5432 ')."""
    return os.getenv(name, default).strip().strip('"').strip("'")


import socket

supabase_host = _env('SUPABASE_DB_HOST')
db_url = _env('DATABASE_URL')
force_sqlite = _env('USE_LOCAL_SQLITE', 'false').lower() in ('true', '1')

def _is_host_resolvable(host, port=5432):
    if not host:
        return False
    try:
        socket.getaddrinfo(host, int(port), socket.AF_UNSPEC, socket.SOCK_STREAM)
        return True
    except (socket.gaierror, socket.herror, OSError):
        return False

use_postgres = bool(supabase_host or db_url) and not force_sqlite

# If host resolution fails (e.g. running offline or in restricted sandbox), fall back cleanly to SQLite
if use_postgres and supabase_host:
    port = _env('SUPABASE_DB_PORT', '5432')
    if not _is_host_resolvable(supabase_host, port):
        print(f">> [OrderCraft] Notice: Supabase host '{supabase_host}' is not resolvable from current network (offline/sandbox mode).")
        print(">> [OrderCraft] Gracefully falling back to local SQLite database (db.sqlite3) so system remains 100% operational.")
        use_postgres = False

if use_postgres:

    # PostgreSQL configuration requires psycopg 3
    try:
        import psycopg  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL driver missing. Run: pip install 'psycopg[binary]'"
        ) from exc

    if supabase_host:
        # Individual credentials take priority over DATABASE_URL.
        # Special characters in the password are safe here (no URL parsing).
        db_user = _env('SUPABASE_DB_USER', 'postgres')

        # Supabase poolers need the full "postgres.<project-ref>" username.
        if 'pooler.supabase.com' in supabase_host and '.' not in db_user:
            raise RuntimeError(
                f"SUPABASE_DB_USER is '{db_user}', but the Supabase pooler "
                "requires 'postgres.<project-ref>'. Check backend/.env and "
                "any system environment variable named SUPABASE_DB_USER."
            )

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': _env('SUPABASE_DB_NAME', 'postgres'),
                'USER': db_user,
                'PASSWORD': os.getenv('SUPABASE_DB_PASSWORD', ''),
                'HOST': supabase_host,
                'PORT': _env('SUPABASE_DB_PORT', '5432'),
                'OPTIONS': {
                    'sslmode': 'require',
                },
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': True,
            }
        }

    else:
        # Fallback: DATABASE_URL (password must be URL-encoded: @ -> %40, % -> %25)
        try:
            import dj_database_url
        except ImportError as exc:
            raise RuntimeError(
                "Run: pip install dj-database-url"
            ) from exc

        DATABASES = {
            'default': dj_database_url.parse(
                db_url,
                conn_max_age=0,
                conn_health_checks=True,
                ssl_require=True,
            )
        }

    _db = DATABASES['default']
    print(
        f">> [OrderCraft] Supabase PostgreSQL enabled | "
        f"user={_db.get('USER')} host={_db.get('HOST')} port={_db.get('PORT')}"
    )

else:

    # Automatic local SQLite fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

    print(">> [OrderCraft] Using local SQLite database!")

# -------------------------------------------------
# AUTHENTICATION & CUSTOM USER MODEL
# -------------------------------------------------

AUTH_USER_MODEL = 'accounts.CustomUser'

# Keep Django's auth decorators aligned with the existing OrderCraft pages.
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/app/'
LOGOUT_REDIRECT_URL = '/login/'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

# -------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------

STATIC_URL = '/static/'

# The frontend is kept as the single source of truth for static assets. Django's
# staticfiles finder will expose frontend/css, frontend/js, and any future
# frontend asset directories below /static/ without copying or duplicating them.
STATICFILES_DIRS = [
    FRONTEND_DIR,
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------------------------
# CORS CONFIGURATION
# Development configuration
# -------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# -------------------------------------------------
# DJANGO REST FRAMEWORK
# -------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],

    'DEFAULT_PAGINATION_CLASS': None,
}

# -------------------------------------------------
# DEFAULT PRIMARY KEY
# -------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

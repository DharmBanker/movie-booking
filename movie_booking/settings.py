"""
Django Settings — Movie Booking Backend
Production-ready configuration with environment variable support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# Core Security
# ============================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Always allow Django test client and Vercel deployment domains
for _host in ['testserver', '.vercel.app', '.onrender.com', '.railway.app']:
    if _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)

# CSRF trusted origins for Vercel domains (required for POST requests)
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.onrender.com',
    'https://*.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Detect platform
_IS_VERCEL  = os.getenv('VERCEL', '')   == '1'
_IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT', '') != ''

# ============================================================
# Production security headers — only active when DEBUG=False
# ============================================================
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Both Vercel and Railway terminate SSL at the edge proxy —
    # enabling SECURE_SSL_REDIRECT here causes infinite redirect loops
    SECURE_SSL_REDIRECT = not (_IS_VERCEL or _IS_RAILWAY)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ============================================================
# Installed Applications
# ============================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'django_filters',
    'django_celery_results',
    'drf_spectacular',
]

LOCAL_APPS = [
    'movies',
    'bookings',
    'frontend',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================
# Middleware
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'movie_booking.urls'

# ============================================================
# Templates
# ============================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'movie_booking.wsgi.application'

# ============================================================
# Database
# Priority order:
#   1. DATABASE_URL env var  → Neon / Supabase / Vercel Postgres
#   2. USE_SQLITE=True       → SQLite (local dev, no PostgreSQL needed)
#   3. Individual DB_* vars  → Local PostgreSQL
# ============================================================

import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_SQLITE = os.getenv('USE_SQLITE', 'False').lower() == 'true'

if DATABASE_URL:
    # Production: Railway / Neon / Supabase PostgreSQL via DATABASE_URL
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
            engine='django.db.backends.postgresql',
        )
    }
elif USE_SQLITE:
    # Local dev: SQLite (no PostgreSQL needed)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Local dev: PostgreSQL via individual env vars
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'movie_booking_db'),
            'USER': os.getenv('DB_USER', 'movie_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {'connect_timeout': 10},
            'CONN_MAX_AGE': 60,
        }
    }

# ============================================================
# Password Validation
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# Internationalization
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ============================================================
# Static & Media Files
# STORAGES replaces deprecated STATICFILES_STORAGE in Django 4.2+
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# Django REST Framework
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'movies.pagination.StandardResultsPagination',
    'PAGE_SIZE': int(os.getenv('PAGINATION_PAGE_SIZE', 20)),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # No authentication required — all endpoints are public
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/hour',
    },
}

# ============================================================
# Redis
# ============================================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# ============================================================
# Celery
# ============================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db')
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ── Eager mode: run tasks inline when Redis is not available ──
# In tests:   always eager (no Redis needed)
# On Vercel:  always eager (serverless, no workers)
# On Railway: eager unless REDIS_URL is explicitly set
# In dev:     USE_CELERY_EAGER=True in .env
import sys
_is_test    = 'test' in sys.argv
_eager      = os.getenv('USE_CELERY_EAGER', 'False').lower() == 'true'
_no_redis   = _IS_RAILWAY and os.getenv('REDIS_URL', '').startswith('redis://localhost')

if _is_test or _eager or _IS_VERCEL or _no_redis:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================
# Email
# ============================================================
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL', 'Movie Booking <noreply@moviebooking.com>'
)

# ============================================================
# API Documentation (drf-spectacular)
# ENUM_NAME_OVERRIDES fixes the "status" collision warning across models
# ============================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Movie Booking API',
    'DESCRIPTION': (
        'Scalable movie booking backend with genre/language filtering '
        'and automated email confirmations.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    # Fix enum collision: Movie.status, Show.status, Booking.status all named "status"
    'ENUM_NAME_OVERRIDES': {
        'MovieStatusEnum': 'movies.models.Movie.STATUS_CHOICES',
        'BookingStatusEnum': 'bookings.models.Booking.STATUS_CHOICES',
        'EmailLogStatusEnum': 'bookings.models.BookingEmailLog.STATUS_CHOICES',
    },
    'ENUM_GENERATE_CHOICE_DESCRIPTION': True,
}

# ============================================================
# Logging
# ============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'movies': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'bookings': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Add file handler only in local dev (Vercel/Railway filesystems are read-only)
_log_file = BASE_DIR / 'logs' / 'django.log'
if not _IS_VERCEL and not _IS_RAILWAY and _log_file.parent.exists():
    LOGGING['handlers']['file'] = {
        'class': 'logging.FileHandler',
        'filename': _log_file,
        'formatter': 'verbose',
    }
    # Wire the file handler into root, django, movies, and bookings loggers
    for _logger_name in ['root', 'django', 'movies', 'bookings']:
        LOGGING['loggers'].setdefault(_logger_name, {})
        _logger_cfg = LOGGING['loggers'][_logger_name] if _logger_name != 'root' else LOGGING['root']
        if 'file' not in _logger_cfg.get('handlers', []):
            _logger_cfg.setdefault('handlers', []).append('file')

# ============================================================
# App Settings
# ============================================================
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
MAX_SEATS_PER_BOOKING = int(os.getenv('MAX_SEATS_PER_BOOKING', 10))

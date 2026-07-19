"""
Django settings for CryptoInvest enterprise platform.
"""
import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    USE_SQLITE=(bool, True),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    MIN_WITHDRAWAL=(float, 10.0),
    MAX_WITHDRAWAL=(float, 100000.0),
    REFERRAL_BONUS_PERCENT=(float, 5.0),
    AXES_FAILURE_LIMIT=(int, 5),
    AXES_COOLOFF_TIME=(int, 1),
)

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='insecure-dev-key-change-me')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

SITE_NAME = env('SITE_NAME', default='CryptoInvest')
SITE_URL = env('SITE_URL', default='http://127.0.0.1:8000')
DEFAULT_CURRENCY = env('DEFAULT_CURRENCY', default='USD')
MIN_WITHDRAWAL = env('MIN_WITHDRAWAL')
MAX_WITHDRAWAL = env('MAX_WITHDRAWAL')
REFERRAL_BONUS_PERCENT = env('REFERRAL_BONUS_PERCENT')

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'django_celery_beat',
    'django_celery_results',
    'axes',
    'channels',
    # Local apps
    'core',
    'accounts.apps.AccountsConfig',
    'wallets',
    'investments',
    'transactions',
    'notifications',
    'referrals',
    'support',
    'cms',
    'markets',
    'staffpanel',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
    'core.middleware.AuditLogMiddleware',
    'core.middleware.ThemeMiddleware',
    'core.middleware.MaintenanceModeMiddleware',
    'core.middleware.SessionTimeoutMiddleware',
    'core.middleware.LanguageMiddleware',
    'core.middleware.TimezoneMiddleware',
    'core.middleware.GeoBlockMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'core.context_processors.site_settings',
                'notifications.context_processors.unread_notifications',
            ],
            # Available in every template: {{ amount|money }} {{ amount|money:4 }}
            'builtins': [
                'core.templatetags.money_filters',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
if env.bool('USE_SQLITE', default=True):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL', default='postgres://crypto_user:crypto_pass@localhost:5432/crypto_invest')
    }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

# ---------------------------------------------------------------------------
# Social OAuth (Google + X/Twitter) — leave blank to hide buttons
# ---------------------------------------------------------------------------
GOOGLE_OAUTH_CLIENT_ID = env('GOOGLE_OAUTH_CLIENT_ID', default='')
GOOGLE_OAUTH_CLIENT_SECRET = env('GOOGLE_OAUTH_CLIENT_SECRET', default='')
X_OAUTH_CLIENT_ID = env('X_OAUTH_CLIENT_ID', default='')
X_OAUTH_CLIENT_SECRET = env('X_OAUTH_CLIENT_SECRET', default='')


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Axes (brute-force protection)
AXES_FAILURE_LIMIT = env('AXES_FAILURE_LIMIT')
AXES_COOLOFF_TIME = env('AXES_COOLOFF_TIME')
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]
AXES_RESET_ON_SUCCESS = True

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('de', 'Deutsch'),
    ('ar', 'العربية'),
    ('zh-hans', '中文'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Manifest storage breaks collectstatic if any static path is missing.
# CompressedStaticFilesStorage is safer for PythonAnywhere.
_static_backend = 'django.contrib.staticfiles.storage.StaticFilesStorage'
if not DEBUG:
    _static_backend = env(
        'STATICFILES_STORAGE',
        default='whitenoise.storage.CompressedStaticFilesStorage',
    )
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': _static_backend,
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='CryptoInvest <noreply@cryptoinvest.local>')

# ---------------------------------------------------------------------------
# Cache & Redis
# ---------------------------------------------------------------------------
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cryptoinvest-cache',
    }
}

# Channels / WebSockets (InMemory for local dev; Redis in production)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Prefer Redis only when explicitly enabled (Docker / paid Redis).
# PythonAnywhere free/start plans usually have no Redis — keep LocMem/InMemory.
if env.bool('USE_REDIS_CACHE', default=False):
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_RESULT_EXTENDED = True
# Without Redis (e.g. PythonAnywhere free): run Celery tasks in-process
if env.bool('CELERY_TASK_ALWAYS_EAGER', default=not env.bool('USE_REDIS_CACHE', default=False)):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# ---------------------------------------------------------------------------
# REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '1000/hour',
        'login': '10/minute',
        'deposit': '20/hour',
        'withdraw': '10/hour',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'CryptoInvest API',
    'DESCRIPTION': 'Enterprise cryptocurrency investment platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ---------------------------------------------------------------------------
# Crispy Forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = False  # needed for HTMX
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE')
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE')

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://127.0.0.1:5173',
    'http://localhost:5173',
])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'cryptoinvest.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'audit': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'audit.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django.security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'axes': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'investments': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'transactions': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'wallets': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'core': {'handlers': ['console', 'file'], 'level': 'INFO'},
    },
}

# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

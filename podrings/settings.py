from pathlib import Path
import dj_database_url
import os


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') in ('1', 'true', 'yes')
ALLOWED_HOSTS = ['*']
DOMAIN = os.getenv('DOMAIN', 'podrings.org')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'easy_thumbnails',
    'django_bootstrap5',
    'django_rq',
    'corsheaders',
    'podrings.moderation',
    'podrings.creative',
    'podrings.community',
    'podrings.seo',
    'podrings.theme',
    'podrings.front',
    'podrings.mail',
    'podrings.contrib.apple',
    'django.contrib.admin',
    'tempus_dominus'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False
        },
        'podrings.creative': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False
        }
    }
}

if SENTRY_DSN := os.getenv('SENTRY_DSN'):
    import logging
    import sentry_sdk

    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.rq import RqIntegration

    sentry_sdk.init(
        SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.WARNING
            ),
            RqIntegration(),
            RedisIntegration()
        ]
    )

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s '
                          '%(process)d %(thread)d %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'WARNING',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'django.db.backends': {
                'level': 'ERROR',
                'handlers': ['console'],
                'propagate': False
            },
            'raven': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'podrings.middleware.is_ajax_middleware'
)

ROOT_URLCONF = 'podrings.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            )
        }
    }
]

WSGI_APPLICATION = 'podrings.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///%s' % os.path.join(BASE_DIR, 'db.sqlite')
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'  # NOQA
    }
]

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    'accept-encoding',
    'accept',
    'authorization',
    'cache-control',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken'
)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTHENTICATION_BACKENDS = ('podrings.auth.EmailBackend',)
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

THUMBNAIL_DEFAULT_STORAGE = 'podrings.storage.ThumbnailStorage'
STATIC_ROOT = os.getenv('STATIC_ROOT') or os.path.join(BASE_DIR, 'static')
MEDIA_URL = os.getenv('MEDIA_URL') or '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT') or os.path.join(BASE_DIR, 'media')

STORAGES = {
    'default': {
        'BACKEND': 'podrings.storage.Boto3Storage'
    }
}

if not DEBUG:
    STORAGES['staticfiles'] = {
        'BACKEND': 'podrings.storage.StaticStorage'
    }

    STATIC_URL = os.getenv('STATIC_URL') or '/static/'
else:
    STORAGES['staticfiles'] = {
        'BACKEND': 'podrings.storage.LocalNetworkStorage'
    }

    STATIC_URL = '/static/'

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_S3_BUCKET')
AWS_STORAGE_STATIC_BUCKET_NAME = os.getenv('AWS_S3_STATIC_BUCKET')
AWS_S3_HOST = os.getenv('AWS_S3_HOST')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_CUSTOM_STATIC_DOMAIN = os.getenv('AWS_S3_CUSTOM_STATIC_DOMAIN')

AWS_DEFAULT_ACL = 'public-read'
AWS_PRELOAD_METADATA = True
AWS_QUERYSTRING_AUTH = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL
    }
}

RQ_QUEUES = {
    'default': {
        'URL': REDIS_URL
    }
}

OP3_API_KEY = os.getenv('OP3_API_KEY')

EMAIL_BACKEND = 'anymail.backends.mailersend.EmailBackend'
DEFAULT_FROM_NAME = 'Mark from Podrings'
DEFAULT_FROM_EMAIL = 'hello@podrings.org'

ANYMAIL = {
    'MAILERSEND_API_TOKEN': os.getenv('MAILERSEND_API_KEY'),
    'MAILERSEND_SENDER_DOMAIN': 'podrings.org'
}

TEMPUS_DOMINUS_INCLUDE_ASSETS = False

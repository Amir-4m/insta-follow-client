"""
Django settings for conf project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from decouple import config, Csv

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)
DEVEL = config("DEVEL", default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# Application definition
INSTALLED_APPS = [
    # Local
    'apps.insta_users',
    'apps.proxies',
    'apps.simulators',
    'django_celery_beat',

    # Third Parties

    # Default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

WSGI_APPLICATION = 'conf.wsgi.application'
ROOT_URLCONF = 'conf.urls'
APPEND_SLASH = False
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASS'),
        'HOST': config('DB_HOST', default=""),
        'PORT': config('DB_PORT', default=""),
    },
}

CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': config('CACHE_HOST', default=''),
        'KEY_PREFIX': 'INSTA_FOLLOW_CLIENT',
    },
}

CELERY_BROKER_URL = 'amqp://%(USER)s:%(PASS)s@%(HOST)s' % {
    'USER': config('CELERY_USER'),
    'PASS': config('CELERY_PASS'),
    'HOST': config('CELERY_HOST'),
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = False
USE_L10N = False
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_ROOT = BASE_DIR.parent / 'static'
STATIC_URL = config('STATIC_URL', default='/static/')

MEDIA_ROOT = BASE_DIR.parent / 'media'
MEDIA_URL = config('MEDIA_URL', default='/media/')

LOG_DIR = BASE_DIR.parent / 'logs'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_devel_true': {
            '()': 'utils.log.RequireDevelTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_devel_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'django.log',
            'formatter': 'verbose' if DEBUG else 'simple',
        },
        'db_queries': {
            'level': 'DEBUG',
            'filters': ['require_devel_true'],
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'db_queries.log',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['db_queries'],
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'apps.insta_users.tasks': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Custom Values
INSTA_FOLLOW_BASE_URL = config('INSTA_FOLLOW_BASE_URL')
INSTA_FOLLOW_ORDER_LIMIT = config('INSTA_FOLLOW_ORDER_LIMIT', cast=int, default=5)
INSTA_FOLLOW_TEST_USER_UPDATE_TOKEN = config('INSTA_FOLLOW_TEST_USER_UPDATE_TOKEN', default='')

INSTA_FOLLOW_SETTINGS = {
    "delay_follow": 3,
    "delay_like": 3,
    "delay_comment": 7,

    "pre_lock_follow": 15,
    "pre_lock_like": 10,
    "pre_lock_comment": 10,

    "lock_follow": 60,
    "lock_like": 30,
    "lock_comment": 30,

    "max_lock": 5,
}

SIGN_UP_PROXY_IP = config('SIGN_UP_PROXY_IP')
SIGN_UP_PROXY_PORT = config('SIGN_UP_PROXY_PORT', cast=int)
SIGN_UP_PROXY_USER = config('SIGN_UP_PROXY_USER')
SIGN_UP_PROXY_PASS = config('SIGN_UP_PROXY_PASS')

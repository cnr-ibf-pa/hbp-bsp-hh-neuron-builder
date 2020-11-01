"""
Django settings for hh_neuron_builder project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '4s1h2vtrbr)-c@8q9&^j(pkf+k$wks+(u43-lsn&mzm1zolvb#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'hhnb.MyUser'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'mozilla_django_oidc',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sslserver',
    'hhnb',
    'efelg',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'mozilla_django_oidc.middleware.SessionRefresh',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 200000000
FILE_UPLOAD_MAX_MEMORY_SIZE = 200000000


AUTHENTICATION_BACKENDS = [
    'auth.backend.MyOIDCBackend',
    'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'hh_neuron_builder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'efelg/templates'),
            os.path.join(BASE_DIR, 'hhnb/templates')
        ],
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

WSGI_APPLICATION = 'hh_neuron_builder.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'ebrains_oidc_authentication/static'),
    os.path.join(BASE_DIR, 'efelg/static'),
    os.path.join(BASE_DIR, 'hhnb/static'),
    os.path.join(BASE_DIR, 'static')
]

MEDIA_ROOT = os.path.join("../app", 'media')


# OIDC PARAMETERS
OIDC_RP_CLIENT_ID = os.environ['OIDC_RP_CLIENT_ID']
OIDC_RP_CLIENT_SECRET = os.environ['OIDC_RP_CLIENT_SECRET']

OIDC_RP_SCOPES = 'openid profile email'

OIDC_CREATE_USER = False
OIDC_STORE_ACCESS_TOKEN = True


OIDC_RP_SIGN_ALGO = 'RS256'

OIDC_OP_JWKS_ENDPOINT = "https://iam.ebrains.eu/auth/realms/hbp/protocol/openid-connect/certs"

OIDC_OP_AUTHORIZATION_ENDPOINT = "https://iam.ebrains.eu/auth/realms/hbp/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://iam.ebrains.eu/auth/realms/hbp/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = "https://iam.ebrains.eu/auth/realms/hbp/protocol/openid-connect/userinfo"

LOGIN_REDIRECT_URL = "/hh-neuron-builder"
LOGOUT_REDIRECT_URL = "/hh-neuron-builder"

LOGIN_URL = 'oidc_authentication_init'

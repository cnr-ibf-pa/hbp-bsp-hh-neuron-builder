from django.core.management import utils


DEBUG = True

SECRET_KEY = utils.get_random_secret_key()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

MEDIA_ROOT = os.path.join('/apps', 'media')


"""
Local presentation settings.

This profile keeps the five-county demonstration independent of external MySQL,
email and object-storage credentials. The SQLite database is persistent between
the migrate, seed and runserver commands and is ignored by Git.
"""

import os

# These values only satisfy base-setting imports. The presentation profile never
# connects to MySQL and must never be used as a deployed environment.
os.environ.setdefault(
    'DJANGO_SECRET_KEY',
    'local-presentation-key-not-for-production',
)
os.environ.setdefault('DB_NAME', '')
os.environ.setdefault('DB_USER', '')
os.environ.setdefault('DB_PASSWORD', '')
os.environ.setdefault('DB_HOST', 'localhost')

from .development import *  # noqa: F401,F403


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get(
            'PILOT_DEMO_DB_PATH',
            BASE_DIR / 'pilot_demo.sqlite3',  # noqa: F405
        ),
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media'  # noqa: F405
MEDIA_URL = '/media/'

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

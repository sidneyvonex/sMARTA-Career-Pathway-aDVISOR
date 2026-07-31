import os

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media'  # noqa: F405
MEDIA_URL = '/media/'

SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    'AUTH_COOKIE_SECURE': False,
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

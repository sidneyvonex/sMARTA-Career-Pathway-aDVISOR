from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]

# Use in-memory email in dev — no real emails sent
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use local filesystem for media in dev — no Azure needed
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

#!/bin/bash
set -e

cd /home/site/wwwroot/backend

# Apply pending migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start WSGI server
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --log-level info \
  --timeout 120

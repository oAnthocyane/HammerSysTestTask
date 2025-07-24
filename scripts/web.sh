#!/bin/bash

/usr/local/bin/wait-for-it.sh referring_db:5432 --timeout=30 --strict -- echo "Database is up and ready"

echo "Run Django migrations..."
uv run manage.py migrate || echo "No migrations to apply"

echo "Collecting static files..."
uv run manage.py collectstatic --noinput --clear || echo "No static files to collect"

echo "Starting Django application..."
uv run gunicorn referral_system.wsgi --bind 0.0.0.0:8000 --workers 4 --timeout 30 || echo "Failed to start Gunicorn"
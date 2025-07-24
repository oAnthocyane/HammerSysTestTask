#!/bin/bash

/usr/local/bin/wait-for-it.sh referring_db:5432 --timeout=30 --strict -- echo "Database is up and ready"

echo "Start APScheduler..."
uv run manage.py cleanup_expired_codes || echo "Failed to start APScheduler"

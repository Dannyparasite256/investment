#!/bin/sh
set -e

echo "Waiting for database..."
python << 'PY'
import os, time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.db import connection
for i in range(30):
    try:
        connection.ensure_connection()
        print("Database ready.")
        break
    except Exception as e:
        print(f"DB not ready ({e}), retry {i+1}/30...")
        time.sleep(2)
else:
    raise SystemExit("Database never became ready")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput 2>/dev/null || true

# Seed demo data if empty (idempotent)
python manage.py seed_platform --quiet 2>/dev/null || true

exec "$@"

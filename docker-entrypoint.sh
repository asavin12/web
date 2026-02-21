#!/bin/bash
set -e

echo "=== UnstressVN Docker Entrypoint ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY=0
until python -c "
import psycopg2, os, urllib.parse

# Support DATABASE_URL (Coolify provides this)
database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    parsed = urllib.parse.urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    dbname = parsed.path.lstrip('/')
    user = parsed.username
    password = parsed.password
else:
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    dbname = os.environ.get('DB_NAME', 'unstressvn')
    user = os.environ.get('DB_USER', 'unstressvn')
    password = os.environ.get('DB_PASSWORD', 'unstressvn')

try:
    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, connect_timeout=3)
    conn.close()
    print(f'PostgreSQL is ready! ({host}:{port}/{dbname})')
except Exception as e:
    print(f'Waiting for DB... ({e})')
    exit(1)
" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL not available after $MAX_RETRIES retries"
        exit 1
    fi
    sleep 2
done

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn on port 8000..."
exec gunicorn unstressvn_settings.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120 \
    --keepalive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level warning

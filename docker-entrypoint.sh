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

# Fix PostgreSQL sequences (prevent "duplicate key" errors after data restore/import)
echo "Fixing PostgreSQL sequences..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        DO \$\$
        DECLARE
            r RECORD;
            max_id BIGINT;
        BEGIN
            FOR r IN
                SELECT s.relname AS seq_name, t.relname AS table_name, a.attname AS column_name
                FROM pg_class s
                JOIN pg_depend d ON d.objid = s.oid
                JOIN pg_class t ON d.refobjid = t.oid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
                WHERE s.relkind = 'S'
            LOOP
                EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', r.column_name, r.table_name) INTO max_id;
                EXECUTE format('SELECT setval(%L, GREATEST(%s + 1, 1), false)', r.seq_name, max_id);
            END LOOP;
        END \$\$;
    \"\"\")
print('All sequences synced.')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Seed navigation data if empty
echo "Seeding navigation data..."
python manage.py seed_navigation 2>&1 || echo "Navigation seed skipped (may already exist)"

# Upgrade navigation data (fix icons, add dropdown children)
echo "Upgrading navigation data..."
python manage.py upgrade_navigation 2>&1 || echo "Navigation upgrade skipped"

# Cleanup duplicate resources (from sample data scripts run multiple times)
echo "Cleaning up duplicate records..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
django.setup()
from collections import defaultdict

for model_path in ['resources.models.Resource', 'news.models.NewsArticle', 'knowledge.models.KnowledgeArticle']:
    try:
        app, _, cls = model_path.rsplit('.', 2)
        module = __import__(app + '.models', fromlist=[cls])
        Model = getattr(module, cls)
        title_field = 'title' if hasattr(Model, 'title') else None
        if not title_field:
            continue
        title_ids = defaultdict(list)
        for obj in Model.objects.all().order_by('id'):
            title_ids[getattr(obj, title_field)].append(obj.id)
        to_delete = []
        for title, ids in title_ids.items():
            if len(ids) > 1:
                keep = max(ids)
                to_delete.extend(i for i in ids if i != keep)
        if to_delete:
            deleted, _ = Model.objects.filter(id__in=to_delete).delete()
            print(f'  {cls}: removed {deleted} duplicates')
        else:
            print(f'  {cls}: no duplicates')
    except Exception as e:
        print(f'  {model_path}: skipped ({e})')
" 2>&1 || echo "Duplicate cleanup skipped"

# Start Gunicorn
echo "Starting Gunicorn on port 8000..."
exec gunicorn unstressvn_settings.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

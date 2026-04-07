#!/bin/bash
set -e

echo "=== UnstressVN Docker Entrypoint ==="

# =============================================
# Parse database connection info (reused below)
# =============================================
parse_db_conn() {
  local database_url="${DATABASE_URL:-}"
  if [ -n "$database_url" ]; then
    # Parse DATABASE_URL: postgres://user:pass@host:port/dbname
    DB_USER_PARSED=$(echo "$database_url" | sed -n 's|.*://\([^:]*\):.*|\1|p')
    DB_PASS_PARSED=$(echo "$database_url" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
    DB_HOST_PARSED=$(echo "$database_url" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    DB_PORT_PARSED=$(echo "$database_url" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME_PARSED=$(echo "$database_url" | sed -n 's|.*/\([^?]*\).*|\1|p')
  else
    DB_USER_PARSED="${DB_USER:-unstressvn}"
    DB_PASS_PARSED="${DB_PASSWORD:-unstressvn}"
    DB_HOST_PARSED="${DB_HOST:-localhost}"
    DB_PORT_PARSED="${DB_PORT:-5432}"
    DB_NAME_PARSED="${DB_NAME:-unstressvn}"
  fi
}
parse_db_conn

# =============================================
# Persist SECRET_KEY in PostgreSQL
# Prevents encryption data loss across Docker rebuilds
# =============================================
if [ -z "${SECRET_KEY:-}" ]; then
  echo "SECRET_KEY not set — reading/creating from database..."
  
  # Use .pgpass file instead of PGPASSWORD in command line (security: not visible in ps aux)
  export PGPASSFILE="/tmp/.pgpass_$$"
  echo "$DB_HOST_PARSED:${DB_PORT_PARSED:-5432}:$DB_NAME_PARSED:$DB_USER_PARSED:$DB_PASS_PARSED" > "$PGPASSFILE"
  chmod 600 "$PGPASSFILE"
  
  psql -h "$DB_HOST_PARSED" -p "${DB_PORT_PARSED:-5432}" \
    -U "$DB_USER_PARSED" -d "$DB_NAME_PARSED" -qtAX \
    -c "CREATE TABLE IF NOT EXISTS _app_config (key VARCHAR(64) PRIMARY KEY, value TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW());" \
    2>/dev/null || true

  STORED_KEY=$(psql -h "$DB_HOST_PARSED" -p "${DB_PORT_PARSED:-5432}" \
    -U "$DB_USER_PARSED" -d "$DB_NAME_PARSED" -qtAX \
    -c "SELECT value FROM _app_config WHERE key='secret_key';" 2>/dev/null || echo "")

  if [ -n "$STORED_KEY" ]; then
    export SECRET_KEY="$STORED_KEY"
    echo "SECRET_KEY loaded from database."
  else
    # Generate and store a new key
    NEW_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    # Use dollar-quoting to safely handle special characters in key
    psql -h "$DB_HOST_PARSED" -p "${DB_PORT_PARSED:-5432}" \
      -U "$DB_USER_PARSED" -d "$DB_NAME_PARSED" -qtAX \
      -c "INSERT INTO _app_config (key, value) VALUES ('secret_key', \$\$${NEW_KEY}\$\$) ON CONFLICT (key) DO NOTHING;" \
      2>/dev/null || true
    export SECRET_KEY="$NEW_KEY"
    echo "SECRET_KEY generated and stored in database."
  fi
  
  # Clean up .pgpass file
  rm -f "$PGPASSFILE"
  unset PGPASSFILE
fi

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

# Ensure media stream categories exist
echo "Ensuring media categories..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
django.setup()
from mediastream.models import MediaCategory
for name, slug, desc, icon, order in [
    ('Luyện nghe', 'luyen-nghe', 'Luyện nghe tiếng Đức, tiếng Anh qua video & audio', 'headphones', 1),
    ('Phim & Series', 'phim', 'Xem phim, series để cải thiện khả năng nghe hiểu', 'film', 2),
    ('Âm nhạc', 'am-nhac', 'Học ngoại ngữ qua bài hát và MV', 'music', 3),
    ('Podcast', 'podcast', 'Podcast học ngoại ngữ đa dạng chủ đề', 'mic', 4),
    ('Bài giảng', 'bai-giang', 'Bài giảng, hướng dẫn ngữ pháp và từ vựng', 'book-open', 5),
    ('Thư giãn', 'thu-gian', 'Nội dung thư giãn, giải trí', 'coffee', 6),
    ('YouTube', 'youtube', 'Video YouTube nhúng', 'youtube', 10),
]:
    obj, c = MediaCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc, 'icon': icon, 'order': order})
    if c: print(f'  Created: {name}')
print('Media categories OK')
" 2>&1 || echo "Media categories setup skipped"

# Migrate YouTube videos from core.Video to StreamMedia
echo "Migrating YouTube videos to Stream..."
python manage.py migrate_videos_to_stream 2>&1 || echo "Video migration skipped"

# Fetch YouTube metadata for videos missing duration/info
echo "Fetching YouTube metadata..."
python manage.py fetch_youtube_metadata 2>&1 || echo "YouTube metadata fetch skipped"

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
    --timeout 300 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

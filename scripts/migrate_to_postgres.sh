#!/bin/bash
# Script migrate dữ liệu từ SQLite sang PostgreSQL
# Sử dụng: ./scripts/migrate_to_postgres.sh

set -e

echo "🔄 UnstressVN - Migrate SQLite to PostgreSQL"
echo "=============================================="

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "✅ Running inside Docker container"
    PYTHON_CMD="python"
else
    echo "📍 Running on host machine"
    PYTHON_CMD="python"
    
    # Activate virtual environment if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Step 1: Export data from SQLite
echo ""
echo "📤 Step 1: Exporting data from SQLite..."
echo "----------------------------------------"

# Backup current DATABASE_URL
ORIGINAL_DATABASE_URL=$DATABASE_URL
unset DATABASE_URL

# Export all data to JSON
$PYTHON_CMD manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude auth.permission \
    --exclude contenttypes \
    --exclude admin.logentry \
    --exclude sessions.session \
    --indent 2 \
    > data_backup.json

echo "✅ Data exported to data_backup.json"

# Step 2: Check PostgreSQL connection
echo ""
echo "🔍 Step 2: Checking PostgreSQL connection..."
echo "--------------------------------------------"

# Restore DATABASE_URL
export DATABASE_URL=$ORIGINAL_DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set!"
    echo "Please set DATABASE_URL environment variable:"
    echo "export DATABASE_URL=postgres://user:password@localhost:5432/unstressvn"
    exit 1
fi

echo "DATABASE_URL: $DATABASE_URL"

# Step 3: Run migrations on PostgreSQL
echo ""
echo "🔧 Step 3: Running migrations on PostgreSQL..."
echo "----------------------------------------------"

$PYTHON_CMD manage.py migrate --run-syncdb

echo "✅ Migrations completed"

# Step 4: Load data into PostgreSQL
echo ""
echo "📥 Step 4: Loading data into PostgreSQL..."
echo "------------------------------------------"

$PYTHON_CMD manage.py loaddata data_backup.json

echo "✅ Data loaded successfully"

# Step 5: Verify
echo ""
echo "✅ Step 5: Verification..."
echo "--------------------------"

$PYTHON_CMD manage.py shell -c "
from django.contrib.auth.models import User
from resources.models import Resource
from accounts.models import UserProfile

print(f'Users: {User.objects.count()}')
print(f'Resources: {Resource.objects.count()}')
print(f'Profiles: {UserProfile.objects.count()}')
"

echo ""
echo "🎉 Migration completed successfully!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Verify data in PostgreSQL"
echo "2. Update .env to use DATABASE_URL permanently"
echo "3. Remove data_backup.json if no longer needed"

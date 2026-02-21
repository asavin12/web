#!/usr/bin/env python
"""
Reset the UnstressVN Django database and recreate sample data.
This will:
1. Stop any running server
2. Delete the database
3. Run migrations
4. Create sample data
5. Optionally restart the server

Usage: python reset.py [--no-sample-data] [--start]
"""

import os
import sys
import subprocess
import argparse
import shutil

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

# SAFETY GUARD: Refuse to run in production
# Kiểm tra SiteConfiguration trong database (nếu có)
try:
    import django
    django.setup()
    from core.models import SiteConfiguration
    from django.db import connection
    tables = connection.introspection.table_names()
    if 'core_siteconfiguration' in tables:
        config = SiteConfiguration.get_instance()
        if not config.debug_mode:
            print("❌ ABORTED: Cannot reset database when Debug Mode = OFF (production).")
            print("   This script is only for development environments.")
            print("   Change Debug Mode in Admin → Cấu hình hệ thống if needed.")
            sys.exit(1)
except Exception:
    pass  # DB chưa sẵn sàng — cho phép chạy (lần đầu setup)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the virtual environment Python
VENV_PYTHON = os.path.join(os.path.dirname(BASE_DIR), '.venv', 'bin', 'python')

# Database file
DB_FILE = os.path.join(BASE_DIR, 'db.sqlite3')


def confirm_reset():
    """Ask user to confirm database reset."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              ⚠️  WARNING: DATABASE RESET                      ║
╠══════════════════════════════════════════════════════════════╣
║  This will DELETE all data in the database!                  ║
║  - All users                                                 ║
║  - All resources                                             ║
║  - All forum posts                                           ║
║  - All chat messages                                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    return response == 'yes'


def stop_server():
    """Stop any running Django server."""
    print("\n🛑 Stopping any running server...")
    subprocess.run([VENV_PYTHON, 'stop.py'], cwd=BASE_DIR, capture_output=True)


def delete_database():
    """Delete the SQLite database file."""
    print("\n🗑️  Deleting database...")
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"   Deleted: {DB_FILE}")
    else:
        print("   Database file not found (already clean).")


def delete_migrations():
    """Delete migration files (optional, not enabled by default)."""
    apps = ['accounts', 'core', 'resources', 'partners', 'forum', 'chat', 'search']
    
    for app in apps:
        migrations_dir = os.path.join(BASE_DIR, app, 'migrations')
        if os.path.exists(migrations_dir):
            for f in os.listdir(migrations_dir):
                if f.endswith('.py') and f != '__init__.py':
                    filepath = os.path.join(migrations_dir, f)
                    os.remove(filepath)
                    print(f"   Deleted: {filepath}")


def run_migrations():
    """Run Django migrations."""
    print("\n📦 Running migrations...")
    
    # Make migrations
    result = subprocess.run(
        [VENV_PYTHON, 'manage.py', 'makemigrations'],
        cwd=BASE_DIR
    )
    
    # Apply migrations
    result = subprocess.run(
        [VENV_PYTHON, 'manage.py', 'migrate'],
        cwd=BASE_DIR
    )
    
    if result.returncode == 0:
        print("✅ Migrations completed successfully.")
    else:
        print("❌ Migration failed!")
        sys.exit(1)


def create_superuser():
    """Create a default superuser."""
    print("\n👤 Creating superuser...")
    
    # Use Django's shell to create superuser
    create_user_script = '''
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@unstressvn_settings.com', 'admin123')
    print("   Created superuser: admin / admin123")
else:
    print("   Superuser 'admin' already exists.")
'''
    
    subprocess.run(
        [VENV_PYTHON, '-c', create_user_script],
        cwd=BASE_DIR,
        env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'unstressvn_settings.settings'}
    )


def create_sample_data():
    """Run the sample data creation script."""
    print("\n📝 Creating sample data...")
    
    sample_data_script = os.path.join(BASE_DIR, 'create_full_sample_data.py')
    
    if os.path.exists(sample_data_script):
        result = subprocess.run(
            [VENV_PYTHON, sample_data_script],
            cwd=BASE_DIR
        )
        if result.returncode == 0:
            print("✅ Sample data created successfully.")
        else:
            print("⚠️  Sample data creation had some issues.")
    else:
        print("⚠️  Sample data script not found. Skipping.")


def collect_static():
    """Collect static files."""
    print("\n📁 Collecting static files...")
    subprocess.run(
        [VENV_PYTHON, 'manage.py', 'collectstatic', '--noinput'],
        cwd=BASE_DIR,
        capture_output=True
    )


def start_server():
    """Start the Django development server."""
    print("\n🚀 Starting server...")
    subprocess.run([VENV_PYTHON, 'start.py'], cwd=BASE_DIR)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Reset UnstressVN database')
    parser.add_argument('--no-sample-data', action='store_true', 
                        help='Skip creating sample data')
    parser.add_argument('--start', action='store_true',
                        help='Start server after reset')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--clean-migrations', action='store_true',
                        help='Also delete migration files')
    
    args = parser.parse_args()
    
    # Check if Python exists in venv
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ Virtual environment not found at: {VENV_PYTHON}")
        sys.exit(1)
    
    # Confirm with user
    if not args.force:
        if not confirm_reset():
            print("\n❌ Reset cancelled.")
            sys.exit(0)
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║               🔄 Resetting UnstressVN Database              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Stop server
    stop_server()
    
    # Delete database
    delete_database()
    
    # Optionally delete migrations
    if args.clean_migrations:
        print("\n🗑️  Deleting migration files...")
        delete_migrations()
    
    # Run migrations
    run_migrations()
    
    # Create superuser
    create_superuser()
    
    # Create sample data
    if not args.no_sample_data:
        create_sample_data()
    
    # Collect static
    collect_static()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   ✅ Reset Complete!                         ║
╠══════════════════════════════════════════════════════════════╣
║  Superuser: admin                                            ║
║  Password:  admin123                                         ║
║                                                              ║
║  Run 'python start.py' to start the server.                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Optionally start server
    if args.start:
        start_server()


if __name__ == '__main__':
    main()

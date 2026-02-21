#!/usr/bin/env python
"""
Start the UnstressVN Django development server.
Usage: python start.py [port]
Default port: 8000
"""

import os
import sys
import subprocess

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the virtual environment Python
VENV_PYTHON = os.path.join(BASE_DIR, '.venv', 'bin', 'python')

# Default port
DEFAULT_PORT = 8000


def get_port():
    """Get port from command line argument or use default."""
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            print(f"Using default port: {DEFAULT_PORT}")
    return DEFAULT_PORT


def check_migrations():
    """Check if there are pending migrations."""
    print("🔍 Checking for pending migrations...")
    result = subprocess.run(
        [VENV_PYTHON, 'manage.py', 'showmigrations', '--plan'],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    if '[ ]' in result.stdout:
        print("⚠️  There are pending migrations. Running migrate...")
        subprocess.run([VENV_PYTHON, 'manage.py', 'migrate'], cwd=BASE_DIR)
    else:
        print("✅ All migrations are applied.")


def start_server(port):
    """Start the Django development server."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🌐 UnstressVN Server                     ║
╠══════════════════════════════════════════════════════════════╣
║  Starting development server...                              ║
║  URL: http://127.0.0.1:{port:<5}                                ║
║  Press Ctrl+C to stop the server                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        subprocess.run(
            [VENV_PYTHON, 'manage.py', 'runserver', f'0.0.0.0:{port}'],
            cwd=BASE_DIR
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped.")


def main():
    """Main entry point."""
    # Check if Python exists in venv
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ Virtual environment not found at: {VENV_PYTHON}")
        print("Please create a virtual environment first:")
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    port = get_port()
    
    # Check migrations
    check_migrations()
    
    # Start the server
    start_server(port)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
Stop the UnstressVN Django development server.
Finds and kills all Django runserver processes.
Usage: python stop.py
"""

import os
import subprocess
import signal
import sys


def find_django_processes():
    """Find all Django runserver processes."""
    processes = []
    try:
        # Find processes running manage.py runserver
        result = subprocess.run(
            ['pgrep', '-f', 'manage.py runserver'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            processes.extend(pids)
    except Exception as e:
        print(f"Error finding processes: {e}")
    
    return processes


def find_port_processes(port=8000):
    """Find processes listening on the specified port."""
    processes = []
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            processes.extend(pids)
    except Exception:
        pass  # lsof might not be available
    
    return processes


def kill_process(pid):
    """Kill a process by PID."""
    try:
        os.kill(int(pid), signal.SIGTERM)
        return True
    except ProcessLookupError:
        return False  # Process already dead
    except PermissionError:
        print(f"⚠️  Permission denied to kill process {pid}")
        return False
    except Exception as e:
        print(f"⚠️  Error killing process {pid}: {e}")
        return False


def main():
    """Main entry point."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 🛑 Stopping UnstressVN Server               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Find Django processes
    django_pids = find_django_processes()
    
    # Also check common ports
    port_pids = []
    for port in [8000, 8080, 8888]:
        port_pids.extend(find_port_processes(port))
    
    # Combine and deduplicate
    all_pids = list(set(django_pids + port_pids))
    
    if not all_pids:
        print("ℹ️  No Django server processes found running.")
        return
    
    print(f"🔍 Found {len(all_pids)} process(es) to stop...")
    
    killed = 0
    for pid in all_pids:
        if pid:  # Skip empty strings
            print(f"   Stopping process {pid}...", end=" ")
            if kill_process(pid):
                print("✅")
                killed += 1
            else:
                print("❌")
    
    if killed > 0:
        print(f"\n✅ Successfully stopped {killed} process(es).")
    else:
        print("\n⚠️  No processes were stopped.")


if __name__ == '__main__':
    main()

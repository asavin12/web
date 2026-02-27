#!/usr/bin/env python
"""
Script tạo và quản lý password bảo mật cao cho UnstressVN
Usage:
    python scripts/manage_passwords.py generate           # Tạo password mới
    python scripts/manage_passwords.py init               # Khởi tạo SiteConfiguration + API Keys
    python scripts/manage_passwords.py show               # Hiển thị config (ẩn secret)
    python scripts/manage_passwords.py export             # Export settings ra file .env.example
    python scripts/manage_passwords.py update-postgres    # Cập nhật password PostgreSQL
"""

import os
import sys
import string
import secrets
import argparse

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

import django
django.setup()

from core.models import SiteConfiguration, APIKey


def generate_secure_password(length=32, include_special=True):
    """Tạo password bảo mật cao bằng secrets module (cryptographically secure)"""
    if length < 16:
        length = 16
    
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = '!@#$%^&*()_+-=[]{}|;:,.<>?' if include_special else ''
    
    # Ensure at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
    ]
    
    if include_special:
        password.append(secrets.choice(special))
    
    # Fill the rest
    all_chars = lowercase + uppercase + digits + special
    remaining = length - len(password)
    password.extend(secrets.choice(all_chars) for _ in range(remaining))
    
    # Secure shuffle using secrets
    for i in range(len(password) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password[i], password[j] = password[j], password[i]
    
    return ''.join(password)


def cmd_generate(args):
    """Tạo password mới"""
    print("\n🔐 Password Generator - UnstressVN")
    print("=" * 50)
    
    count = args.count or 5
    length = args.length or 32
    
    print(f"\nTạo {count} password với độ dài {length} ký tự:\n")
    
    for i in range(count):
        password = generate_secure_password(length, not args.no_special)
        print(f"  {i+1}. {password}")
    
    print("\n💡 Copy password và lưu an toàn!")
    print()


def cmd_init(args):
    """Khởi tạo SiteConfiguration + API Keys"""
    print("\n⚙️ Khởi tạo SiteConfiguration")
    print("=" * 50)
    
    # Init SiteConfiguration singleton
    config = SiteConfiguration.get_instance()
    print(f"✅ SiteConfiguration: {config.site_name}")
    
    # Init API keys
    created = APIKey.create_default_keys()
    if created:
        print(f"✅ Đã tạo API Keys: {', '.join(created)}")
    else:
        print("ℹ️ API Keys đã tồn tại")
    
    print(f"\n📋 Cấu hình hiện tại:")
    print(f"  • Site: {config.site_name}")
    print(f"  • Debug: {'ON' if config.debug_mode else 'OFF'}")
    print(f"  • Email: {config.email_host or '(chưa cấu hình)'}")
    minio = config.get_minio_config()
    if minio:
        print(f"  • MinIO: {minio['endpoint_url']}")
    else:
        print(f"  • MinIO: (chưa cấu hình — local storage)")
    
    print()


def cmd_show(args):
    """Hiển thị cấu hình hiện tại"""
    print("\n📋 SiteConfiguration - UnstressVN")
    print("=" * 50)
    
    config = SiteConfiguration.get_instance()
    
    print(f"\n🔹 Website:")
    print(f"   site_name: {config.site_name}")
    print(f"   site_description: {config.site_description or '(trống)'}")
    print(f"   contact_email: {config.contact_email or '(trống)'}")
    
    print(f"\n🔹 Chế độ:")
    print(f"   debug_mode: {'ON' if config.debug_mode else 'OFF'}")
    print(f"   maintenance_mode: {'ON' if config.maintenance_mode else 'OFF'}")
    
    print(f"\n🔹 Email SMTP:")
    print(f"   email_host: {config.email_host or '(trống)'}")
    print(f"   email_port: {config.email_port}")
    if args.show_secrets:
        print(f"   email_host_password: {config.email_host_password or '(trống)'}")
    else:
        print(f"   email_host_password: {'●●●●●●●●' if config.email_host_password else '(trống)'}")
    
    print(f"\n🔹 MinIO Storage:")
    minio = config.get_minio_config()
    if minio:
        print(f"   endpoint: {minio['endpoint_url']}")
        print(f"   bucket: {minio['bucket']}")
        if args.show_secrets:
            print(f"   access_key: {minio['access_key']}")
            print(f"   secret_key: {minio['secret_key']}")
        else:
            print(f"   access_key: {'●●●●●●●●' if minio['access_key'] else '(trống)'}")
            print(f"   secret_key: {'●●●●●●●●' if minio['secret_key'] else '(trống)'}")
    else:
        print(f"   (chưa cấu hình — local storage)")
    
    print(f"\n🔹 API Keys:")
    for key in APIKey.objects.filter(is_active=True):
        if args.show_secrets:
            print(f"   {key.name}: {key.key}")
        else:
            print(f"   {key.name}: {key.key[:10]}...{key.key[-4:]}")
    
    if not args.show_secrets:
        print("\n💡 Thêm --show-secrets để hiển thị password đầy đủ")
    print()


def cmd_export(args):
    """Export settings ra file .env"""
    print("\n📤 Export Settings to .env")
    print("=" * 50)
    
    output_file = args.output or '.env.generated'
    config = SiteConfiguration.get_instance()
    
    lines = [
        "# UnstressVN Environment Variables",
        "# Generated by manage_passwords.py",
        f"# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# ============ Site ============",
        f"SITE_NAME={config.site_name}",
        f"DEBUG={'True' if config.debug_mode else 'False'}",
        "",
        "# ============ Email ============",
        f"EMAIL_HOST={config.email_host or ''}",
        f"EMAIL_PORT={config.email_port}",
        f"EMAIL_USE_TLS={'True' if config.email_use_tls else 'False'}",
        f"EMAIL_HOST_USER={config.email_host_user or ''}",
        f"EMAIL_HOST_PASSWORD={config.email_host_password or ''}",
        "",
        "# ============ MinIO ============",
        f"MINIO_ENDPOINT_URL={config.minio_endpoint_url or ''}",
        f"MINIO_ACCESS_KEY={config.minio_access_key or ''}",
        f"MINIO_SECRET_KEY={config.minio_secret_key or ''}",
        f"MINIO_MEDIA_BUCKET={config.minio_media_bucket}",
        "",
        "# ============ API Keys ============",
    ]
    
    for key in APIKey.objects.filter(is_active=True):
        env_name = key.name.upper().replace(' ', '_').replace('-', '_')
        lines.append(f"{env_name}={key.key}")

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Đã export ra: {output_file}")
    print(f"⚠️ Lưu ý: File này chứa password thật, bảo mật cẩn thận!")
    print()


def cmd_update_postgres(args):
    """Tạo password PostgreSQL mới"""
    print("\n🐘 Update PostgreSQL Password")
    print("=" * 50)
    
    new_password = generate_secure_password(32, include_special=False)  # No special for postgres
    
    print(f"\n🔐 Password mới (không có ký tự đặc biệt): ")
    print(f"   {new_password}")
    
    print("\n📋 Các bước cần thực hiện:")
    print("   1. Cập nhật password trong PostgreSQL:")
    print(f"      sudo -u postgres psql -c \"ALTER USER unstressvn WITH PASSWORD '{new_password}';\"")
    print()
    print("   2. Cập nhật file .env:")
    print(f"      DATABASE_PASSWORD={new_password}")
    print()
    print("   3. Restart server:")
    print("      ./stop.sh && ./start.sh")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='UnstressVN Password Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # generate command
    gen_parser = subparsers.add_parser('generate', help='Tạo password mới')
    gen_parser.add_argument('-n', '--count', type=int, default=5, help='Số password tạo')
    gen_parser.add_argument('-l', '--length', type=int, default=32, help='Độ dài password')
    gen_parser.add_argument('--no-special', action='store_true', help='Không dùng ký tự đặc biệt')
    
    # init command
    subparsers.add_parser('init', help='Khởi tạo default settings')
    
    # show command
    show_parser = subparsers.add_parser('show', help='Hiển thị settings')
    show_parser.add_argument('--show-secrets', action='store_true', help='Hiển thị password đầy đủ')
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export ra file .env')
    export_parser.add_argument('-o', '--output', help='Output file', default='.env.generated')
    
    # update-postgres command
    subparsers.add_parser('update-postgres', help='Tạo password PostgreSQL mới')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'init':
        cmd_init(args)
    elif args.command == 'show':
        cmd_show(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'update-postgres':
        cmd_update_postgres(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

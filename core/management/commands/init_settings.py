"""
Management command để khởi tạo default settings
Tạo SiteConfiguration singleton và API Keys mặc định
"""
from django.core.management.base import BaseCommand
from core.models import SiteConfiguration, APIKey


class Command(BaseCommand):
    help = 'Khởi tạo default settings cho website (SiteConfiguration singleton + API Keys)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ghi đè các settings đã tồn tại',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔧 Khởi tạo default settings...'))
        
        # Init SiteConfiguration (singleton — tự tạo nếu chưa có)
        self.stdout.write('  → Tạo SiteConfiguration singleton...')
        config = SiteConfiguration.get_instance()
        self.stdout.write(self.style.SUCCESS(f'    ✓ SiteConfiguration: {config.site_name}'))
        
        # Show MinIO status
        minio_config = config.get_minio_config()
        if minio_config:
            self.stdout.write(f'\n  📦 MinIO Storage:')
            self.stdout.write(f'    • Endpoint: {minio_config["endpoint_url"]}')
            self.stdout.write(f'    • Bucket: {minio_config["bucket"]}')
        else:
            self.stdout.write(f'\n  📦 MinIO Storage: (chưa cấu hình — local storage)')
        
        # Init API Keys
        self.stdout.write('\n  → Tạo API Keys...')
        created_keys = APIKey.create_default_keys()
        if created_keys:
            self.stdout.write(self.style.SUCCESS(f'    ✓ Đã tạo: {", ".join(created_keys)}'))
        else:
            self.stdout.write('    ✓ API Keys đã tồn tại')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Hoàn tất! Truy cập Admin Panel để cấu hình chi tiết.'))
        self.stdout.write(self.style.NOTICE('   /admin/core/siteconfiguration/ - Cấu hình hệ thống'))
        self.stdout.write(self.style.NOTICE('   /admin/core/apikey/ - API Keys'))

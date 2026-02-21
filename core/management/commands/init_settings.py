"""
Management command để khởi tạo default settings
Bao gồm MinIO, Database, Email settings
"""
from django.core.management.base import BaseCommand
from core.models import SiteSettings, APIKey


class Command(BaseCommand):
    help = 'Khởi tạo default settings cho website (MinIO, Database, Email, API Keys)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Ghi đè các settings đã tồn tại',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔧 Khởi tạo default settings...'))
        
        # Init Site Settings
        self.stdout.write('  → Tạo Site Settings (Database, Email, MinIO)...')
        SiteSettings.init_default_settings()
        
        # Count settings
        count = SiteSettings.objects.count()
        self.stdout.write(self.style.SUCCESS(f'    ✓ {count} settings đã được tạo'))
        
        # List MinIO settings
        minio_settings = SiteSettings.objects.filter(setting_type='storage')
        if minio_settings.exists():
            self.stdout.write('\n  📦 MinIO Storage Settings:')
            for s in minio_settings:
                value = '●●●●●●●●' if s.is_secret else (s.value if s.value else '(chưa cấu hình)')
                self.stdout.write(f'    • {s.name}: {value}')
        
        # Init API Keys
        self.stdout.write('\n  → Tạo API Keys...')
        created_keys = APIKey.create_default_keys()
        if created_keys:
            self.stdout.write(self.style.SUCCESS(f'    ✓ Đã tạo: {", ".join(created_keys)}'))
        else:
            self.stdout.write('    ✓ API Keys đã tồn tại')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Hoàn tất! Truy cập Admin Panel để cấu hình chi tiết.'))
        self.stdout.write(self.style.NOTICE('   /admin/core/sitesettings/ - Site Settings'))
        self.stdout.write(self.style.NOTICE('   /admin/core/apikey/ - API Keys'))

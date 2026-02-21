from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils import timezone
import logging
import secrets

# Import từ module youtube utility
from .youtube import extract_youtube_id, fetch_youtube_info
from .base_models import N8NTrackingMixin
from .fields import EncryptedTextField

logger = logging.getLogger(__name__)


class APIKey(models.Model):
    """
    Lưu trữ các API Keys và Secret Keys trong database
    Thay vì lưu trong .env file
    """
    KEY_TYPE_CHOICES = [
        ('n8n_api', 'N8N Automation API Key'),
        ('admin_secret', 'Admin Secret Key'),
        ('webhook', 'Webhook Secret'),
        ('external_api', 'External API Key'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên key',
                           help_text='Tên định danh (VD: n8n_api_key, admin_secret)')
    key = models.CharField(max_length=255, verbose_name='API Key',
                          help_text='Giá trị key (tự động tạo nếu để trống)')
    key_type = models.CharField(max_length=20, choices=KEY_TYPE_CHOICES, default='other',
                                verbose_name='Loại key')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    
    # Tracking
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Sử dụng lần cuối')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='Số lần sử dụng')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['key_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_key_type_display()})"
    
    def save(self, *args, **kwargs):
        # Tự động tạo key nếu để trống
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
        # Clear cache khi update
        cache.delete(f'api_key_{self.name}')
    
    @classmethod
    def get_key(cls, name, default=None):
        """
        Lấy API key theo tên, có cache
        Usage: APIKey.get_key('n8n_api_key')
        """
        cache_key = f'api_key_{name}'
        key = cache.get(cache_key)
        
        if key is None:
            try:
                api_key = cls.objects.get(name=name, is_active=True)
                key = api_key.key
                cache.set(cache_key, key, timeout=3600)  # Cache 1 hour
            except cls.DoesNotExist:
                key = default
        
        return key
    
    @classmethod
    def verify_key(cls, name, provided_key):
        """
        Xác thực API key
        Returns: True nếu key hợp lệ
        """
        from django.utils import timezone
        
        expected_key = cls.get_key(name)
        if expected_key and expected_key == provided_key:
            # Update usage stats
            try:
                api_key = cls.objects.get(name=name)
                api_key.last_used_at = timezone.now()
                api_key.usage_count += 1
                api_key.save(update_fields=['last_used_at', 'usage_count'])
            except cls.DoesNotExist:
                pass
            return True
        return False
    
    @classmethod
    def create_default_keys(cls):
        """Tạo các keys mặc định nếu chưa có (auto-generate secure keys)"""
        defaults = [
            {
                'name': 'n8n_api_key',
                'key_type': 'n8n_api',
                'description': 'API Key cho n8n automation tự động đăng bài',
                'key': secrets.token_urlsafe(32),
            },
            {
                'name': 'admin_secret_key',
                'key_type': 'admin_secret',
                'description': 'Secret key để truy cập admin panel',
                'key': secrets.token_urlsafe(32),
            },
        ]
        
        created_keys = []
        for data in defaults:
            key, created = cls.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                created_keys.append(key.name)
        
        return created_keys


class SiteSettings(models.Model):
    """
    Singleton model để lưu trữ thông tin cài đặt website
    Bao gồm thông tin database, email, API keys, storage (MinIO), etc.
    """
    SETTING_TYPE_CHOICES = [
        ('database', 'Database Config'),
        ('email', 'Email Config'),
        ('storage', 'Storage (MinIO/S3)'),
        ('api', 'API Config'),
        ('security', 'Security'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên cài đặt',
                           help_text='Tên định danh (VD: postgres_password, smtp_password)')
    value = models.TextField(verbose_name='Giá trị', 
                            help_text='Giá trị cài đặt (có thể là password)')
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPE_CHOICES, 
                                   default='general', verbose_name='Loại')
    is_secret = models.BooleanField(default=False, verbose_name='Là mật khẩu/secret',
                                    help_text='Đánh dấu nếu là password để ẩn khi hiển thị')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
        ordering = ['setting_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_setting_type_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache khi update
        cache.delete(f'site_setting_{self.name}')
    
    @classmethod
    def get(cls, name, default=None):
        """Lấy giá trị setting theo tên, có cache"""
        cache_key = f'site_setting_{name}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(name=name)
                value = setting.value
                # Cache 1 hour
                cache.set(cache_key, value, timeout=3600)
            except cls.DoesNotExist:
                value = default
        
        # Return None nếu value là empty string
        if value == '':
            return default
        return value
    
    @classmethod
    def get_minio_config(cls):
        """
        Lấy toàn bộ MinIO config từ database
        Returns dict hoặc None nếu không có config
        """
        import os
        
        endpoint = cls.get('minio_endpoint_url')
        
        if not endpoint:
            return None
            
        return {
            'endpoint_url': endpoint,
            'access_key': cls.get('minio_access_key', ''),
            'secret_key': cls.get('minio_secret_key', ''),
            'bucket': cls.get('minio_bucket', 'mediastream'),
            'region': cls.get('minio_region', 'us-east-1'),
            'custom_domain': cls.get('minio_custom_domain'),
        }
    
    @classmethod
    def set(cls, name, value, setting_type='general', is_secret=False, description=''):
        """Tạo hoặc cập nhật setting"""
        obj, created = cls.objects.update_or_create(
            name=name,
            defaults={
                'value': value,
                'setting_type': setting_type,
                'is_secret': is_secret,
                'description': description,
            }
        )
        return obj
    
    @classmethod
    def generate_secure_password(cls, length=32, include_special=True):
        """
        Tạo password bảo mật cao
        - Ít nhất 1 chữ hoa, 1 chữ thường, 1 số, 1 ký tự đặc biệt
        - Dài tối thiểu 16 ký tự
        """
        import string
        import random
        
        if length < 16:
            length = 16
        
        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()_+-=[]{}|;:,.<>?' if include_special else ''
        
        # Ensure at least one of each type
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
        ]
        
        if include_special:
            password.append(random.choice(special))
        
        # Fill the rest with random chars
        all_chars = lowercase + uppercase + digits + special
        remaining_length = length - len(password)
        password.extend(random.choice(all_chars) for _ in range(remaining_length))
        
        # Shuffle to randomize position
        random.shuffle(password)
        
        return ''.join(password)
    
    @classmethod
    def init_default_settings(cls):
        """Khởi tạo các settings mặc định với password bảo mật"""
        
        # Database settings
        cls.set(
            name='postgres_host',
            value='localhost',
            setting_type='database',
            description='PostgreSQL Host'
        )
        cls.set(
            name='postgres_port',
            value='5433',
            setting_type='database',
            description='PostgreSQL Port'
        )
        cls.set(
            name='postgres_db',
            value='unstressvn',
            setting_type='database',
            description='PostgreSQL Database Name'
        )
        cls.set(
            name='postgres_user',
            value='unstressvn',
            setting_type='database',
            description='PostgreSQL Username'
        )
        
        # Only set password if not exists (don't override)
        if not cls.objects.filter(name='postgres_password').exists():
            cls.set(
                name='postgres_password',
                value=cls.generate_secure_password(),
                setting_type='database',
                is_secret=True,
                description='PostgreSQL Password (auto-generated if not set)'
            )
        
        # Email settings
        cls.set(
            name='email_host',
            value='smtp.gmail.com',
            setting_type='email',
            description='SMTP Server'
        )
        cls.set(
            name='email_address',
            value='unstressvn@gmail.com',
            setting_type='email',
            description='Email Address'
        )
        
        # MinIO/S3 Storage settings
        cls.set(
            name='minio_endpoint_url',
            value='',
            setting_type='storage',
            description='MinIO Endpoint URL (VD: https://minio.unstressvn.com). Để trống nếu dùng local storage.'
        )
        cls.set(
            name='minio_access_key',
            value='',
            setting_type='storage',
            is_secret=False,
            description='MinIO Access Key (Username)'
        )
        if not cls.objects.filter(name='minio_secret_key').exists():
            cls.set(
                name='minio_secret_key',
                value='',
                setting_type='storage',
                is_secret=True,
                description='MinIO Secret Key (Password)'
            )
        cls.set(
            name='minio_bucket',
            value='mediastream',
            setting_type='storage',
            description='MinIO Bucket name cho media files'
        )
        cls.set(
            name='minio_region',
            value='us-east-1',
            setting_type='storage',
            description='MinIO Region (thường là us-east-1)'
        )
        cls.set(
            name='minio_custom_domain',
            value='',
            setting_type='storage',
            description='Custom domain cho MinIO/CDN (tùy chọn)'
        )
        
        return True


class Video(N8NTrackingMixin, models.Model):
    """
    Model lưu trữ video học tập
    Hỗ trợ YouTube và các nguồn video khác
    Có n8n tracking để automation
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('de', 'Deutsch'),
        ('all', _('Mọi ngôn ngữ')),
    ]
    
    LEVEL_CHOICES = [
        ('A1', _('A1 - Sơ cấp')),
        ('A2', _('A2 - Sơ trung')),
        ('B1', _('B1 - Trung cấp')),
        ('B2', _('B2 - Trung cao')),
        ('C1', _('C1 - Cao cấp')),
        ('C2', _('C2 - Thành thạo')),
        ('all', _('Mọi trình độ')),
    ]
    
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    # YouTube embed
    youtube_id = models.CharField(
        max_length=100, 
        verbose_name='YouTube Video ID hoặc URL',
        help_text='Nhập ID video (ví dụ: dQw4w9WgXcQ) hoặc URL đầy đủ từ YouTube'
    )
    
    # Thông tin video
    thumbnail = models.URLField(blank=True, verbose_name='Ảnh thumbnail',
                                help_text='Để trống sẽ tự lấy từ YouTube')
    duration = models.CharField(max_length=10, blank=True, verbose_name='Thời lượng',
                                help_text='Ví dụ: 12:30')
    
    # Phân loại
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en',
                                 verbose_name='Ngôn ngữ')
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='all',
                             verbose_name='Trình độ')
    
    # Thống kê (lưu local)
    view_count = models.PositiveIntegerField(default=0, verbose_name='Lượt xem')
    
    # Bookmarks - Người dùng đã lưu video này
    bookmarks = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='bookmarked_videos',
        verbose_name='Đã lưu'
    )
    
    # Hiển thị
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
        ordering = ['-is_featured', 'order', '-created_at']
    
    def save(self, *args, **kwargs):
        # Kiểm tra xem có cần auto-fetch không
        auto_fetch = kwargs.pop('auto_fetch_youtube', True)
        
        # Trích xuất YouTube ID từ URL nếu cần
        old_youtube_id = None
        if self.pk:
            try:
                old_instance = Video.objects.get(pk=self.pk)
                old_youtube_id = old_instance.youtube_id
            except Video.DoesNotExist:
                pass
        
        self.youtube_id = extract_youtube_id(self.youtube_id)
        
        # Tự động lấy thông tin từ YouTube nếu:
        # 1. auto_fetch=True
        # 2. youtube_id mới hoặc thay đổi
        # 3. title đang trống hoặc là placeholder
        is_new_video = old_youtube_id != self.youtube_id
        needs_title = not self.title or self.title.strip() == ''
        
        if auto_fetch and self.youtube_id and (is_new_video or needs_title):
            try:
                youtube_info = fetch_youtube_info(self.youtube_id)
                if youtube_info:
                    # Chỉ cập nhật nếu field đang trống
                    if not self.title:
                        self.title = youtube_info.get('title', '')[:255]
                    if not self.description:
                        self.description = youtube_info.get('description', '')
                    if not self.duration:
                        self.duration = youtube_info.get('duration', '')
                    if youtube_info.get('thumbnail'):
                        self.thumbnail = youtube_info.get('thumbnail')
                    logger.info(f"Đã tự động lấy thông tin YouTube cho video: {self.youtube_id}")
            except Exception as e:
                logger.error(f"Lỗi khi auto-fetch YouTube info: {e}")
        
        # Tự tạo slug từ tiêu đề
        if not self.slug and self.title:
            self.slug = slugify(self.title)
            # Đảm bảo unique
            counter = 1
            original_slug = self.slug
            while Video.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Tự động lấy thumbnail từ YouTube nếu chưa có
        if self.youtube_id and not self.thumbnail:
            self.thumbnail = f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        
        super().save(*args, **kwargs)
    
    def fetch_youtube_metadata(self):
        """
        Gọi thủ công để cập nhật thông tin từ YouTube
        Sẽ ghi đè các field hiện tại
        """
        if not self.youtube_id:
            return False
        
        youtube_info = fetch_youtube_info(self.youtube_id)
        if youtube_info:
            self.title = youtube_info.get('title', self.title)[:255]
            self.description = youtube_info.get('description', self.description)
            self.duration = youtube_info.get('duration', self.duration)
            if youtube_info.get('thumbnail'):
                self.thumbnail = youtube_info.get('thumbnail')
            self.save(auto_fetch_youtube=False)
            return True
        return False
    
    def __str__(self):
        return self.title
    
    @property
    def youtube_url(self):
        return f"https://www.youtube.com/watch?v={self.youtube_id}"
    
    @property
    def embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}"
    
    def get_language_display_vi(self):
        """Lấy tên ngôn ngữ tiếng Việt"""
        return dict(self.LANGUAGE_CHOICES).get(self.language, self.language)
    
    def is_bookmarked_by(self, user):
        """Kiểm tra user đã bookmark video này chưa"""
        if user.is_authenticated:
            return self.bookmarks.filter(pk=user.pk).exists()
        return False
    
    @property
    def bookmark_count(self):
        """Đếm số lượng bookmark"""
        return self.bookmarks.count()


class NavigationLink(models.Model):
    """
    Model lưu trữ các link điều hướng cho navbar và footer
    Quản lý hoàn toàn từ admin panel
    """
    LOCATION_CHOICES = [
        ('navbar', 'Navbar'),
        ('footer', 'Footer'),
        ('both', 'Cả hai'),
    ]
    
    FOOTER_SECTION_CHOICES = [
        ('company', 'Công ty'),
        ('resources', 'Tài nguyên'),
        ('community', 'Cộng đồng'),
        ('legal', 'Pháp lý'),
        ('social', 'Mạng xã hội'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Tên hiển thị')
    url = models.CharField(max_length=500, verbose_name='URL',
                          help_text='URL nội bộ (VD: /about) hoặc URL bên ngoài (VD: https://facebook.com)')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon',
                           help_text='Tên icon (VD: FaHome, FaFacebook, MdEmail)')
    
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='navbar',
                                verbose_name='Vị trí')
    footer_section = models.CharField(max_length=20, choices=FOOTER_SECTION_CHOICES, 
                                      blank=True, verbose_name='Phần trong Footer',
                                      help_text='Chỉ áp dụng khi location là Footer hoặc Cả hai')
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='Menu cha',
                               help_text='Để trống nếu là menu chính')
    
    open_in_new_tab = models.BooleanField(default=False, verbose_name='Mở tab mới',
                                          help_text='Thường dùng cho link bên ngoài')
    
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Link điều hướng'
        verbose_name_plural = 'Links điều hướng'
        ordering = ['location', 'footer_section', 'order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name
    
    @property
    def is_external(self):
        """Kiểm tra link có phải bên ngoài không"""
        return self.url.startswith('http://') or self.url.startswith('https://')
    
    @classmethod
    def get_navbar_links(cls):
        """Lấy tất cả link cho navbar"""
        return cls.objects.filter(
            is_active=True,
            location__in=['navbar', 'both'],
            parent__isnull=True
        ).prefetch_related('children')
    
    @classmethod
    def get_footer_links(cls):
        """Lấy tất cả link cho footer, nhóm theo section"""
        links = cls.objects.filter(
            is_active=True,
            location__in=['footer', 'both'],
            parent__isnull=True
        )
        
        # Nhóm theo footer_section
        grouped = {}
        for link in links:
            section = link.footer_section or 'other'
            if section not in grouped:
                grouped[section] = []
            grouped[section].append(link)
        
        return grouped


# =============================================
# SITE CONFIGURATION — Singleton Model
# =============================================

class SiteConfiguration(models.Model):
    """
    Cấu hình tập trung cho toàn bộ website — singleton (chỉ 1 bản ghi).
    Quản lý qua Admin → Cấu hình hệ thống.
    Dữ liệu nhạy cảm được mã hoá Fernet trước khi lưu vào database.

    Khi database bị đánh cắp, kẻ tấn công KHÔNG thể đọc các trường mã hoá
    vì encryption key nằm trong file .secret_key (ngoài database).
    """

    # === Thông tin website ===
    site_name = models.CharField(
        'Tên website', max_length=100, default='UnstressVN',
    )
    site_description = models.TextField(
        'Mô tả website', blank=True,
        default='Nền tảng học ngoại ngữ miễn phí',
    )
    contact_email = models.EmailField(
        'Email liên hệ', default='unstressvn@gmail.com',
    )

    # === Chế độ hoạt động ===
    debug_mode = models.BooleanField(
        'Chế độ Debug', default=True,
        help_text='⚠️ BẮT BUỘC tắt khi deploy production!',
    )
    maintenance_mode = models.BooleanField(
        'Chế độ bảo trì', default=False,
        help_text='Bật khi đang bảo trì website — hiển thị trang bảo trì.',
    )

    # === Bảo mật & Network ===
    allowed_hosts = models.TextField(
        'Allowed Hosts',
        default='localhost,127.0.0.1,host.docker.internal',
        help_text='Danh sách domain được phép truy cập, phân cách bằng dấu phẩy. '
                  'VD: unstressvn.com,www.unstressvn.com',
    )
    csrf_trusted_origins = models.TextField(
        'CSRF Trusted Origins',
        default='http://localhost:8000,http://127.0.0.1:8000,http://host.docker.internal:8000',
        help_text='URL gốc tin cậy cho CSRF, phân cách bằng dấu phẩy. '
                  'VD: https://unstressvn.com,https://www.unstressvn.com',
    )
    cors_allowed_origins = models.TextField(
        'CORS Allowed Origins',
        default='http://localhost:3000,http://127.0.0.1:3000,'
                'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000',
        help_text='Origin frontend được phép CORS, phân cách bằng dấu phẩy.',
    )

    # === Email SMTP ===
    email_host = models.CharField(
        'SMTP Host', max_length=255, default='smtp.gmail.com',
    )
    email_port = models.IntegerField('SMTP Port', default=587)
    email_use_tls = models.BooleanField('Sử dụng TLS', default=True)
    email_host_user = models.CharField(
        'Email tài khoản SMTP', max_length=255, blank=True, default='',
    )
    email_host_password = EncryptedTextField(
        'Mật khẩu SMTP', blank=True, default='',
        help_text='🔒 App Password (Gmail) hoặc SMTP password. Mã hoá tự động khi lưu.',
    )
    default_from_email = models.CharField(
        'Email người gửi', max_length=255,
        default='UnstressVN <unstressvn@gmail.com>',
    )

    # === API Keys ===
    youtube_api_key = EncryptedTextField(
        'YouTube API Key', blank=True, default='',
        help_text='🔒 Google YouTube Data API v3 key. Mã hoá tự động khi lưu.',
    )

    # === MinIO/S3 Storage ===
    minio_endpoint_url = models.CharField(
        'MinIO Endpoint URL', max_length=500, blank=True, default='',
        help_text='VD: https://minio.unstressvn.com — Để trống = local storage.',
    )
    minio_access_key = EncryptedTextField(
        'MinIO Access Key', blank=True, default='',
        help_text='🔒 Mã hoá tự động khi lưu.',
    )
    minio_secret_key = EncryptedTextField(
        'MinIO Secret Key', blank=True, default='',
        help_text='🔒 Mã hoá tự động khi lưu.',
    )
    minio_media_bucket = models.CharField(
        'MinIO Bucket', max_length=100, default='mediastream',
    )
    minio_region = models.CharField(
        'MinIO Region', max_length=50, default='us-east-1',
    )
    minio_custom_domain = models.CharField(
        'MinIO Custom Domain (CDN)', max_length=500, blank=True, default='',
    )

    # === Elasticsearch ===
    elasticsearch_url = models.CharField(
        'Elasticsearch URL', max_length=500, default='http://localhost:9200',
    )
    elasticsearch_autosync = models.BooleanField(
        'Elasticsearch Auto-sync', default=False,
    )

    # === Redis ===
    redis_url = models.CharField(
        'Redis URL', max_length=500, blank=True, default='',
        help_text='VD: redis://localhost:6379 — Để trống = InMemory channel layer.',
    )

    # === Mạng xã hội ===
    facebook_url = models.URLField('Facebook', blank=True, default='')
    youtube_channel_url = models.URLField('YouTube Channel', blank=True, default='')
    tiktok_url = models.URLField('TikTok', blank=True, default='')
    github_url = models.URLField('GitHub', blank=True, default='')

    # === Metadata ===
    updated_at = models.DateTimeField('Cập nhật lần cuối', auto_now=True)

    class Meta:
        verbose_name = 'Cấu hình hệ thống'
        verbose_name_plural = 'Cấu hình hệ thống'

    def __str__(self):
        return f'Cấu hình — {self.site_name}'

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton — luôn chỉ có 1 bản ghi
        super().save(*args, **kwargs)
        # Reload settings ngay lập tức
        try:
            from core.config import invalidate_cache
            invalidate_cache()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        pass  # Không cho xoá

    @classmethod
    def get_instance(cls):
        """Lấy instance duy nhất, tự tạo nếu chưa có."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def get_minio_config(self):
        """Trả về dict MinIO config hoặc None nếu chưa cấu hình."""
        if not self.minio_endpoint_url:
            return None
        return {
            'endpoint_url': self.minio_endpoint_url,
            'access_key': self.minio_access_key or '',
            'secret_key': self.minio_secret_key or '',
            'bucket': self.minio_media_bucket,
            'region': self.minio_region,
            'custom_domain': self.minio_custom_domain or None,
        }


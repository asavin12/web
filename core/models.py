from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils import timezone
import logging
import secrets
import hashlib
import hmac

# Import từ module youtube utility
from .youtube import extract_youtube_id, fetch_youtube_info
from .base_models import N8NTrackingMixin
from .fields import EncryptedTextField

logger = logging.getLogger(__name__)


def _hash_api_key(raw_key: str) -> str:
    """
    Hash API key bằng HMAC-SHA256 với SECRET_KEY.
    Trả về hex digest. Dùng để lưu key_hash thay vì plain text.
    """
    secret = getattr(settings, 'SECRET_KEY', 'fallback-key')
    return hmac.new(
        secret.encode('utf-8'),
        raw_key.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


class APIKey(models.Model):
    """
    Lưu trữ các API Keys và Secret Keys trong database.
    Key plain text chỉ hiển thị trong admin. key_hash dùng để verify.
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
    key_hash = models.CharField(max_length=128, blank=True, default='', verbose_name='Key Hash',
                                help_text='HMAC-SHA256 hash — auto-generated on save')
    key_prefix = models.CharField(max_length=12, blank=True, default='', verbose_name='Key Prefix',
                                  help_text='First 8 chars for identification')
    key_type = models.CharField(max_length=20, choices=KEY_TYPE_CHOICES, default='other',
                                verbose_name='Loại key')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    
    # Security fields
    allowed_ips = models.TextField(blank=True, default='', verbose_name='Allowed IPs',
                                   help_text='Comma-separated IPs (empty = allow all)')
    rate_limit = models.PositiveIntegerField(default=0, verbose_name='Rate limit/min',
                                              help_text='0 = unlimited')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Hết hạn',
                                       help_text='Key hết hạn tự động (blank = không hết hạn)')
    
    # Tracking
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Sử dụng lần cuối')
    last_used_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP lần cuối')
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
        # Always recompute hash + prefix on save
        self.key_hash = _hash_api_key(self.key)
        self.key_prefix = self.key[:8] if self.key else ''
        super().save(*args, **kwargs)
        # Clear cache khi update
        cache.delete(f'api_key_{self.name}')
    
    @property
    def is_expired(self):
        """Check if key has expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    def check_ip(self, ip):
        """Check if IP is allowed"""
        if not self.allowed_ips:
            return True
        allowed = [x.strip() for x in self.allowed_ips.split(',') if x.strip()]
        return ip in allowed

    def check_rate_limit(self):
        """Check rate limit using cache counter"""
        if self.rate_limit <= 0:
            return True
        cache_key = f'api_rate_{self.name}'
        count = cache.get(cache_key, 0)
        if count >= self.rate_limit:
            return False
        cache.set(cache_key, count + 1, timeout=60)
        return True
    
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
                if api_key.is_expired:
                    return default
                key = api_key.key
                cache.set(cache_key, key, timeout=3600)  # Cache 1 hour
            except cls.DoesNotExist:
                key = default
        
        return key
    
    @classmethod
    def verify_key(cls, name, provided_key, request=None):
        """
        Xác thực API key bằng HMAC constant-time comparison.
        Supports IP check, rate limit, expiry.
        Returns: True nếu key hợp lệ
        """
        try:
            api_key_obj = cls.objects.get(name=name, is_active=True)
        except cls.DoesNotExist:
            return False

        # Expiry check
        if api_key_obj.is_expired:
            return False

        # HMAC verification (constant-time)
        provided_hash = _hash_api_key(provided_key)
        if not hmac.compare_digest(provided_hash, api_key_obj.key_hash):
            # Fallback: direct compare for keys saved before hash migration
            if api_key_obj.key != provided_key:
                return False

        # IP check
        if request:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
            if not api_key_obj.check_ip(client_ip):
                logger.warning(f'API key {name} blocked from IP {client_ip}')
                return False

        # Rate limit
        if not api_key_obj.check_rate_limit():
            logger.warning(f'API key {name} rate limited')
            return False

        # Update usage stats
        update_fields = ['last_used_at', 'usage_count']
        api_key_obj.last_used_at = timezone.now()
        api_key_obj.usage_count += 1
        if request:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
            api_key_obj.last_used_ip = client_ip
            update_fields.append('last_used_ip')
        api_key_obj.save(update_fields=update_fields)
        return True
    
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
    Model lưu trữ các link điều hướng cho navbar và footer.
    Quản lý hoàn toàn từ admin panel — hỗ trợ menu phân cấp (parent → children).
    
    Navbar structure:
      - Menu chính (parent=None, location=navbar): Trang chủ, Thư viện, ...
      - Dropdown menu (parent=None, location=navbar, có children): Tin tức, Kiến thức, ...
      - Sub-menu (parent=<dropdown>, location=navbar): Học tiếng Đức, Ngữ pháp, ...
    
    Footer structure:
      - Link footer (location=footer/both): nhóm theo footer_section
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
    name_vi = models.CharField(max_length=100, blank=True, verbose_name='Tên tiếng Việt',
                               help_text='Tên hiển thị bằng tiếng Việt (fallback = name)')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='Tên tiếng Anh',
                               help_text='Tên hiển thị bằng tiếng Anh (fallback = name)')
    name_de = models.CharField(max_length=100, blank=True, verbose_name='Tên tiếng Đức',
                               help_text='Tên hiển thị bằng tiếng Đức (fallback = name)')
    
    url = models.CharField(max_length=500, verbose_name='URL',
                          help_text='URL nội bộ (VD: /tin-tuc) hoặc URL bên ngoài (VD: https://discord.gg/...)')
    description = models.CharField(max_length=200, blank=True, verbose_name='Mô tả ngắn',
                                   help_text='Mô tả hiển thị dưới tên menu (tuỳ chọn, dùng cho mega-menu)')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon',
                           help_text='Tên lucide icon (VD: Newspaper, BookOpen, Wrench, Users, GraduationCap)')
    
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='navbar',
                                verbose_name='Vị trí')
    footer_section = models.CharField(max_length=20, choices=FOOTER_SECTION_CHOICES, 
                                      blank=True, verbose_name='Phần trong Footer',
                                      help_text='Chỉ áp dụng khi location là Footer hoặc Cả hai')
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='Menu cha',
                               help_text='Để trống nếu là menu chính / dropdown')
    
    open_in_new_tab = models.BooleanField(default=False, verbose_name='Mở tab mới',
                                          help_text='Thường dùng cho link bên ngoài')
    is_coming_soon = models.BooleanField(default=False, verbose_name='Sắp ra mắt',
                                         help_text='Hiển thị badge "Soon" và vô hiệu hoá link')
    badge_text = models.CharField(max_length=20, blank=True, verbose_name='Badge',
                                  help_text='Text hiển thị trên badge (VD: New, Hot, Soon). Để trống = không badge')
    
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Link điều hướng'
        verbose_name_plural = 'Links điều hướng'
        ordering = ['location', 'footer_section', 'order', 'name']
    
    def __str__(self):
        prefix = ''
        if self.parent:
            prefix = f"  └─ "
        location_tag = f"[{self.get_location_display()}]"
        return f"{prefix}{self.name} {location_tag}"
    
    @property
    def is_external(self):
        """Kiểm tra link có phải bên ngoài không"""
        return self.url.startswith('http://') or self.url.startswith('https://')
    
    @property
    def has_children(self):
        """Kiểm tra có submenu không"""
        return self.children.filter(is_active=True).exists()
    
    def get_localized_name(self, lang='vi'):
        """Lấy tên theo ngôn ngữ"""
        field = f'name_{lang}'
        return getattr(self, field, '') or self.name
    
    @classmethod
    def get_navbar_links(cls):
        """Lấy tất cả link cho navbar (parent-level), kèm children active"""
        return cls.objects.filter(
            is_active=True,
            location__in=['navbar', 'both'],
            parent__isnull=True
        ).prefetch_related(
            models.Prefetch(
                'children',
                queryset=cls.objects.filter(is_active=True).order_by('order')
            )
        ).order_by('order')
    
    @classmethod
    def get_footer_links(cls):
        """Lấy tất cả link cho footer, nhóm theo section"""
        links = cls.objects.filter(
            is_active=True,
            location__in=['footer', 'both'],
            parent__isnull=True
        ).order_by('footer_section', 'order')
        
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
    gemini_api_key = EncryptedTextField(
        'Google Gemini API Key', blank=True, default='',
        help_text='🔒 Google Gemini API key cho dịch phụ đề realtime. Mã hoá tự động khi lưu.',
    )

    # === Google Drive Service Account ===
    gdrive_service_account_json = EncryptedTextField(
        'Google Drive Service Account JSON', blank=True, default='',
        help_text='🔒 Nội dung file JSON Service Account (Google Cloud). Mã hoá tự động khi lưu.',
    )
    gdrive_folder_id = models.CharField(
        'Google Drive Folder ID', max_length=255, blank=True, default='',
        help_text='ID thư mục gốc trên Google Drive. '
                  'Lấy từ URL: drive.google.com/drive/folders/FOLDER_ID',
    )
    gdrive_folder_mapping = models.JSONField(
        'Thư mục GDrive theo loại media', default=dict, blank=True,
        help_text='Tự động quản lý: {"video": "FOLDER_ID", "audio": "FOLDER_ID", "podcast": "FOLDER_ID"}',
    )

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



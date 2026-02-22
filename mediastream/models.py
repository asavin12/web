"""
Media Stream Models
Quản lý video và audio files cho học ngoại ngữ
Hỗ trợ streaming với bảo vệ referrer (chỉ cho phép truy cập từ domain chính)
Hỗ trợ MinIO/S3 storage - Config từ Admin Panel
"""

import os
import uuid
import mimetypes
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator


def get_media_storage():
    """Get storage backend - MinIO nếu configured (từ Admin), ngược lại default"""
    from .storage import is_minio_configured, PrivateMediaStreamStorage
    if is_minio_configured():
        return PrivateMediaStreamStorage()
    from django.core.files.storage import default_storage
    return default_storage


def get_thumbnail_storage():
    """Get storage cho thumbnails - MinIO nếu configured (từ Admin)"""
    from .storage import is_minio_configured, PublicMediaStreamStorage
    if is_minio_configured():
        return PublicMediaStreamStorage()
    from django.core.files.storage import default_storage
    return default_storage


def get_media_upload_path(instance, filename):
    """Generate unique upload path for media files"""
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"stream/{instance.media_type}/{unique_name}"


class MediaCategory(models.Model):
    """Danh mục media cho tổ chức tốt hơn"""
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='children',
        verbose_name='Danh mục cha'
    )
    
    # SEO
    icon = models.CharField(max_length=50, blank=True, default='folder', verbose_name='Icon')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục Media'
        verbose_name_plural = 'Danh mục Media'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class StreamMedia(models.Model):
    """Model chính cho video/audio streaming"""
    
    MEDIA_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    
    STORAGE_TYPE_CHOICES = [
        ('local', 'Local Storage'),
        ('gdrive', 'Google Drive'),
    ]
    
    LANGUAGE_CHOICES = [
        ('vi', 'Tiếng Việt'),
        ('en', 'Tiếng Anh'),
        ('de', 'Tiếng Đức'),
        ('all', 'Đa ngôn ngữ'),
    ]
    
    LEVEL_CHOICES = [
        ('A1', 'A1 - Sơ cấp'),
        ('A2', 'A2 - Cơ bản'),
        ('B1', 'B1 - Trung cấp'),
        ('B2', 'B2 - Trung cao'),
        ('C1', 'C1 - Cao cấp'),
        ('C2', 'C2 - Thành thạo'),
        ('all', 'Tất cả trình độ'),
    ]
    
    # Identification
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Storage type
    storage_type = models.CharField(
        max_length=10, choices=STORAGE_TYPE_CHOICES, default='local',
        verbose_name='Loại lưu trữ',
        help_text='local = file trên VPS, gdrive = stream từ Google Drive'
    )
    
    # File (local storage)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, verbose_name='Loại media')
    file = models.FileField(
        upload_to=get_media_upload_path,
        storage=get_media_storage,
        verbose_name='File media',
        blank=True,  # Không bắt buộc nếu dùng Google Drive
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'webm', 'ogg', 'mov', 'flv', 'avi', 'm4v',
                                    'mp3', 'wav', 'm4a', 'aac', 'flac', 'wma']
            )
        ]
    )
    
    # Google Drive storage
    gdrive_file_id = models.CharField(
        max_length=255, blank=True, default='',
        verbose_name='Google Drive File ID',
        help_text='ID file trên Google Drive (lấy từ URL chia sẻ). Để trống nếu dùng local.'
    )
    gdrive_url = models.URLField(
        max_length=500, blank=True, default='',
        verbose_name='Google Drive URL',
        help_text='URL chia sẻ Google Drive (tự động trích xuất File ID)'
    )
    
    # File metadata
    file_size = models.BigIntegerField(default=0, verbose_name='Kích thước (bytes)')
    duration = models.PositiveIntegerField(null=True, blank=True, verbose_name='Thời lượng (giây)')
    mime_type = models.CharField(max_length=100, blank=True, verbose_name='MIME type')
    
    # For video
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name='Chiều rộng')
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name='Chiều cao')
    thumbnail = models.ImageField(
        upload_to='stream/thumbnails/', 
        storage=get_thumbnail_storage,
        null=True, blank=True, 
        verbose_name='Ảnh thumbnail'
    )
    
    # Content
    description = models.TextField(blank=True, verbose_name='Mô tả')
    transcript = models.TextField(blank=True, verbose_name='Lời thoại/Transcript')
    
    # Organization
    category = models.ForeignKey(
        MediaCategory, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='media_files',
        verbose_name='Danh mục'
    )
    
    # Language learning
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='all',
                                 verbose_name='Ngôn ngữ')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='all',
                              verbose_name='Trình độ')
    
    # Tags
    tags = models.CharField(max_length=500, blank=True, 
                            help_text='Các tag cách nhau bởi dấu phẩy',
                            verbose_name='Tags')
    
    # Access control
    is_public = models.BooleanField(default=True, verbose_name='Công khai')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    requires_login = models.BooleanField(default=False, verbose_name='Yêu cầu đăng nhập')
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0, verbose_name='Lượt xem')
    download_count = models.PositiveIntegerField(default=0, verbose_name='Lượt tải')
    
    # Meta
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='uploaded_media',
        verbose_name='Người upload'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Media Stream'
        verbose_name_plural = 'Media Streams'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uid']),
            models.Index(fields=['slug']),
            models.Index(fields=['media_type', 'language', 'level']),
            models.Index(fields=['is_active', 'is_public']),
        ]
    
    def __str__(self):
        return f"[{self.get_media_type_display()}] {self.title}"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = str(self.uid)[:8]
            
            # Ensure unique slug
            slug = base_slug
            counter = 1
            while StreamMedia.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-extract Google Drive file ID from URL
        if self.gdrive_url and not self.gdrive_file_id:
            self.gdrive_file_id = self._extract_gdrive_id(self.gdrive_url)
        
        # Auto-set storage_type
        if self.gdrive_file_id and not self.file:
            self.storage_type = 'gdrive'
        elif self.file and not self.gdrive_file_id:
            self.storage_type = 'local'
        
        # Auto-detect mime type
        if self.file and not self.mime_type:
            mime_type, _ = mimetypes.guess_type(self.file.name)
            self.mime_type = mime_type or 'application/octet-stream'
        
        # Default mime type for Google Drive video
        if self.storage_type == 'gdrive' and not self.mime_type:
            self.mime_type = 'video/mp4' if self.media_type == 'video' else 'audio/mpeg'
        
        # Auto-set file size
        if self.file:
            try:
                self.file_size = self.file.size
            except (ValueError, AttributeError):
                pass
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def _extract_gdrive_id(url):
        """Extract Google Drive file ID from various URL formats"""
        import re
        patterns = [
            # https://drive.google.com/file/d/FILE_ID/view
            r'/file/d/([a-zA-Z0-9_-]+)',
            # https://drive.google.com/open?id=FILE_ID
            r'[?&]id=([a-zA-Z0-9_-]+)',
            # https://docs.google.com/uc?id=FILE_ID
            r'uc\?.*id=([a-zA-Z0-9_-]+)',
            # Direct ID (no URL, just the ID string)
            r'^([a-zA-Z0-9_-]{20,})$',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ''
    
    def get_stream_url(self):
        """Get secure stream URL"""
        return f"/media-stream/play/{self.uid}/"
    
    def get_download_url(self):
        """Get secure download URL"""
        return f"/media-stream/download/{self.uid}/"
    
    def get_embed_code(self):
        """Get HTML embed code"""
        if self.media_type == 'video':
            return f'''<video controls src="{self.get_stream_url()}" style="max-width:100%;">
  Your browser does not support the video tag.
</video>'''
        else:
            return f'''<audio controls src="{self.get_stream_url()}">
  Your browser does not support the audio tag.
</audio>'''
    
    def increment_view(self):
        """Increment view count"""
        StreamMedia.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
    
    def increment_download(self):
        """Increment download count"""
        StreamMedia.objects.filter(pk=self.pk).update(download_count=models.F('download_count') + 1)
    
    @property
    def duration_display(self):
        """Format duration as HH:MM:SS"""
        if not self.duration:
            return None
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    @property
    def file_size_display(self):
        """Format file size for display"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        return f"{self.file_size / (1024 * 1024 * 1024):.2f} GB"
    
    @property
    def tags_list(self):
        """Get tags as list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class MediaSubtitle(models.Model):
    """Subtitle/Caption cho media"""
    
    LANGUAGE_CHOICES = [
        ('vi', 'Tiếng Việt'),
        ('en', 'Tiếng Anh'),
        ('de', 'Tiếng Đức'),
    ]
    
    media = models.ForeignKey(
        StreamMedia, 
        on_delete=models.CASCADE, 
        related_name='subtitles',
        verbose_name='Media'
    )
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, verbose_name='Ngôn ngữ')
    label = models.CharField(max_length=100, blank=True, verbose_name='Nhãn hiển thị')
    file = models.FileField(
        upload_to='stream/subtitles/',
        validators=[FileExtensionValidator(allowed_extensions=['vtt', 'srt'])],
        verbose_name='File phụ đề'
    )
    is_default = models.BooleanField(default=False, verbose_name='Mặc định')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Phụ đề'
        verbose_name_plural = 'Phụ đề'
        unique_together = ['media', 'language']
        ordering = ['language']
    
    def __str__(self):
        return f"{self.media.title} - {self.get_language_display()}"
    
    def save(self, *args, **kwargs):
        if not self.label:
            self.label = self.get_language_display()
        super().save(*args, **kwargs)


class MediaPlaylist(models.Model):
    """Playlist cho học tập"""
    
    title = models.CharField(max_length=255, verbose_name='Tên playlist')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    # Content
    media_items = models.ManyToManyField(
        StreamMedia, 
        through='PlaylistItem',
        related_name='playlists',
        verbose_name='Media'
    )
    
    # Cover
    cover_image = models.ImageField(upload_to='stream/playlists/', null=True, blank=True,
                                     verbose_name='Ảnh bìa')
    
    # Organization
    language = models.CharField(max_length=10, choices=StreamMedia.LANGUAGE_CHOICES, 
                                 default='all', verbose_name='Ngôn ngữ')
    level = models.CharField(max_length=10, choices=StreamMedia.LEVEL_CHOICES,
                              default='all', verbose_name='Trình độ')
    
    # Access
    is_public = models.BooleanField(default=True, verbose_name='Công khai')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    
    # Meta
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_playlists',
        verbose_name='Người tạo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Playlist'
        verbose_name_plural = 'Playlists'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        return self.media_items.count()
    
    @property
    def total_duration(self):
        return self.media_items.aggregate(
            total=models.Sum('duration')
        )['total'] or 0


class PlaylistItem(models.Model):
    """Through model for playlist ordering"""
    
    playlist = models.ForeignKey(MediaPlaylist, on_delete=models.CASCADE)
    media = models.ForeignKey(StreamMedia, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['playlist', 'media']


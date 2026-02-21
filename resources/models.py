"""
Models cho ứng dụng Resources
Quản lý kho tài liệu học ngoại ngữ
Hỗ trợ n8n automation để tự động import tài liệu
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
import re
import unicodedata

from core.image_utils import WebPImageMixin
from core.base_models import N8NTrackingMixin


# Loại tài liệu - Hardcoded choices với hỗ trợ đa ngôn ngữ
RESOURCE_TYPE_CHOICES = [
    ('book', _('Sách')),
    ('ebook', _('Sách/Ebook')),
    ('audio', _('Audio')),
    ('document', _('Tài liệu')),
    ('pdf', _('PDF')),
    ('flashcard', _('Flashcard')),
    ('video', _('Video')),
]

# Map icon cho mỗi loại tài liệu
RESOURCE_TYPE_ICONS = {
    'book': 'bi-book',
    'ebook': 'bi-journal-bookmark',
    'audio': 'bi-headphones',
    'document': 'bi-file-earmark-text',
    'pdf': 'bi-file-earmark-pdf',
    'flashcard': 'bi-card-text',
    'video': 'bi-camera-video',
}


def vietnamese_slugify(text, allow_hyphen=True):
    """
    Chuyển đổi text tiếng Việt/Đức sang slug thân thiện SEO
    Ví dụ: "Học Tiếng Anh Cơ Bản" -> "hoc-tieng-anh-co-ban"
    """
    # Bảng chuyển đổi ký tự tiếng Việt
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'À': 'a', 'Á': 'a', 'Ả': 'a', 'Ã': 'a', 'Ạ': 'a',
        'Ă': 'a', 'Ằ': 'a', 'Ắ': 'a', 'Ẳ': 'a', 'Ẵ': 'a', 'Ặ': 'a',
        'Â': 'a', 'Ầ': 'a', 'Ấ': 'a', 'Ẩ': 'a', 'Ẫ': 'a', 'Ậ': 'a',
        'Đ': 'd',
        'È': 'e', 'É': 'e', 'Ẻ': 'e', 'Ẽ': 'e', 'Ẹ': 'e',
        'Ê': 'e', 'Ề': 'e', 'Ế': 'e', 'Ể': 'e', 'Ễ': 'e', 'Ệ': 'e',
        'Ì': 'i', 'Í': 'i', 'Ỉ': 'i', 'Ĩ': 'i', 'Ị': 'i',
        'Ò': 'o', 'Ó': 'o', 'Ỏ': 'o', 'Õ': 'o', 'Ọ': 'o',
        'Ô': 'o', 'Ồ': 'o', 'Ố': 'o', 'Ổ': 'o', 'Ỗ': 'o', 'Ộ': 'o',
        'Ơ': 'o', 'Ờ': 'o', 'Ớ': 'o', 'Ở': 'o', 'Ỡ': 'o', 'Ợ': 'o',
        'Ù': 'u', 'Ú': 'u', 'Ủ': 'u', 'Ũ': 'u', 'Ụ': 'u',
        'Ư': 'u', 'Ừ': 'u', 'Ứ': 'u', 'Ử': 'u', 'Ữ': 'u', 'Ự': 'u',
        'Ỳ': 'y', 'Ý': 'y', 'Ỷ': 'y', 'Ỹ': 'y', 'Ỵ': 'y',
        # German Umlauts
        'ä': 'a', 'Ä': 'a',
        'ö': 'o', 'Ö': 'o', 
        'ü': 'u', 'Ü': 'u',
        'ß': 'ss',
    }
    
    # Chuyển đổi ký tự đặc biệt
    result = ''
    for char in text:
        result += vietnamese_map.get(char, char)
    
    # Dùng slugify chuẩn của Django
    slug = slugify(result)
    
    # Nếu không cho phép gạch ngang (cho tags), xóa hết dấu gạch ngang
    if not allow_hyphen:
        slug = slug.replace('-', '')
    
    return slug


class Tag(models.Model):
    """
    Thẻ tag cho tài liệu
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên thẻ'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Đường dẫn'
    )
    
    class Meta:
        verbose_name = 'Thẻ tag'
        verbose_name_plural = 'Thẻ tag'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Luôn tự động tạo slug từ name (không có gạch ngang)
        self.slug = vietnamese_slugify(self.name, allow_hyphen=False)
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    Danh mục ngôn ngữ: Tiếng Anh, Tiếng Đức
    """
    name = models.CharField(
        max_length=50,
        verbose_name='Tên danh mục'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Đường dẫn'
    )
    icon = models.CharField(
        max_length=50,
        default='bi-translate',
        verbose_name='Icon (Bootstrap Icons)'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Mô tả'
    )
    
    class Meta:
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Resource(WebPImageMixin, N8NTrackingMixin, models.Model):
    """
    Tài liệu học tập với n8n tracking để automation
    """
    # WebP auto-conversion settings
    WEBP_FIELDS = ['cover_image']
    WEBP_SLUG_FIELD = 'slug'
    WEBP_QUALITY = 'high'
    
    # Thông tin cơ bản
    title = models.CharField(
        max_length=200,
        verbose_name='Tên tài liệu'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Đường dẫn'
    )
    description = models.TextField(
        verbose_name='Mô tả'
    )
    
    # Phân loại
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name='Danh mục'
    )
    # Loại tài liệu - Dùng CharField với choices thay vì ForeignKey
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default='document',
        verbose_name=_('Loại tài liệu')
    )
    
    # File upload (cho Sách/Ebook)
    file = models.FileField(
        upload_to='resources/',
        blank=True,
        null=True,
        verbose_name='File tài liệu'
    )
    
    # Link YouTube (cho Video)
    youtube_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link YouTube'
    )
    
    # Link ngoài (Google Drive, Dropbox, etc.)
    external_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Link tài liệu',
        help_text='Link Google Drive, Dropbox, hoặc trang web khác'
    )
    
    # Ảnh bìa
    cover_image = models.ImageField(
        upload_to='covers/',
        blank=True,
        null=True,
        verbose_name='Ảnh bìa'
    )
    
    # Metadata
    author = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tác giả'
    )
    
    # Tags
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='resources',
        verbose_name='Thẻ tag'
    )
    
    # Bookmarks - Người dùng đã lưu tài liệu này
    bookmarks = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='bookmarked_resources',
        verbose_name='Đã lưu'
    )
    
    # Trạng thái
    is_active = models.BooleanField(
        default=True,
        verbose_name='Hiển thị'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Nổi bật'
    )
    
    # Thống kê
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Lượt xem'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Lượt tải'
    )
    
    # Thời gian
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        verbose_name = 'Tài liệu'
        verbose_name_plural = 'Tài liệu'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Luôn tự động tạo slug từ title
        self.slug = vietnamese_slugify(self.title)
        
        # Đảm bảo slug là duy nhất
        original_slug = self.slug
        counter = 1
        while Resource.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('resources:detail', kwargs={'slug': self.slug})
    
    def get_cover_url(self):
        """Lấy URL ảnh bìa hoặc ảnh mặc định"""
        if self.cover_image:
            return self.cover_image.url
        return '/static/images/default-cover.png'
    
    def get_youtube_embed_url(self):
        """Chuyển đổi link YouTube sang embed URL"""
        if self.youtube_url:
            # Xử lý các định dạng URL YouTube khác nhau
            if 'watch?v=' in self.youtube_url:
                video_id = self.youtube_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in self.youtube_url:
                video_id = self.youtube_url.split('youtu.be/')[1].split('?')[0]
            else:
                return self.youtube_url
            return f'https://www.youtube.com/embed/{video_id}'
        return None
    
    def is_video(self):
        """Kiểm tra có phải là video không"""
        return bool(self.youtube_url)
    
    def is_downloadable(self):
        """Kiểm tra có file tải không"""
        return bool(self.file)
    
    def is_bookmarked_by(self, user):
        """Kiểm tra user đã bookmark tài liệu này chưa"""
        if user.is_authenticated:
            return self.bookmarks.filter(pk=user.pk).exists()
        return False
    
    @property
    def bookmark_count(self):
        """Đếm số lượng bookmark"""
        return self.bookmarks.count()
    
    def get_resource_type_icon(self):
        """Lấy icon cho loại tài liệu"""
        return RESOURCE_TYPE_ICONS.get(self.resource_type, 'bi-file-earmark')
    
    def get_resource_type_display_name(self):
        """Lấy tên hiển thị của loại tài liệu (đã dịch)"""
        return dict(RESOURCE_TYPE_CHOICES).get(self.resource_type, self.resource_type)

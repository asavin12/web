"""
Models cho Tools App
Các công cụ học tập như Flashcards, Quiz, Từ điển, v.v.
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify

from core.image_utils import WebPImageMixin


class ToolCategory(models.Model):
    """Danh mục công cụ"""
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon',
                           help_text='Tên icon (VD: FaBook, FaBrain)')
    
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục công cụ'
        verbose_name_plural = 'Danh mục công cụ'
        ordering = ['order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Tool(WebPImageMixin, models.Model):
    """Công cụ học tập"""
    
    # WebP auto-conversion settings
    WEBP_FIELDS = ['cover_image', 'featured_image']
    WEBP_SLUG_FIELD = 'slug'
    WEBP_QUALITY = 'high'
    WEBP_AUTO_THUMBNAIL = False  # Tools don't have thumbnail field
    WEBP_RESPONSIVE = True
    
    TOOL_TYPE_CHOICES = [
        ('internal', 'Công cụ nội bộ'),
        ('external', 'Link bên ngoài'),
        ('embed', 'Nhúng (iframe)'),
        ('article', 'Bài viết hướng dẫn'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Tên công cụ')
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name='Mô tả ngắn')
    
    # Nội dung bài viết (cho loại article)
    content = models.TextField(blank=True, verbose_name='Nội dung bài viết',
                               help_text='HTML content cho bài viết hướng dẫn')
    excerpt = models.TextField(blank=True, verbose_name='Tóm tắt',
                               help_text='Đoạn mô tả ngắn hiển thị trong danh sách')
    
    category = models.ForeignKey(ToolCategory, on_delete=models.SET_NULL, null=True,
                                 related_name='tools', verbose_name='Danh mục')
    
    # Tác giả
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='tools',
                               verbose_name='Tác giả')
    
    # Loại công cụ
    tool_type = models.CharField(max_length=20, choices=TOOL_TYPE_CHOICES, default='article',
                                 verbose_name='Loại công cụ')
    
    # URL hoặc component path
    url = models.CharField(max_length=500, blank=True, verbose_name='URL/Path',
                          help_text='URL bên ngoài hoặc path component nội bộ')
    embed_code = models.TextField(blank=True, verbose_name='Embed code',
                                  help_text='HTML embed code (cho loại embed)')
    
    # Hiển thị
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon')
    cover_image = models.ImageField(upload_to='tools/covers/', blank=True,
                                    verbose_name='Ảnh bìa')
    featured_image = models.ImageField(upload_to='tools/featured/', blank=True,
                                       verbose_name='Ảnh đại diện')
    cover_image_srcset = models.JSONField(default=dict, blank=True,
                                          verbose_name='Responsive images',
                                          help_text='Auto-generated responsive image URLs')
    
    # Phân loại ngôn ngữ
    LANGUAGE_CHOICES = [
        ('en', 'Tiếng Anh'),
        ('de', 'Tiếng Đức'),
        ('all', 'Tất cả'),
    ]
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='all',
                                verbose_name='Ngôn ngữ')
    
    # Trạng thái
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    is_published = models.BooleanField(default=True, verbose_name='Xuất bản')
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, verbose_name='Meta Title')
    meta_description = models.TextField(blank=True, verbose_name='Meta Description')
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0, verbose_name='Lượt xem')
    
    published_at = models.DateTimeField(blank=True, null=True, verbose_name='Ngày xuất bản')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Công cụ học tập'
        verbose_name_plural = 'Công cụ học tập'
        ordering = ['-is_featured', 'order', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class FlashcardDeck(models.Model):
    """Bộ Flashcard"""
    name = models.CharField(max_length=200, verbose_name='Tên bộ thẻ')
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    # Phân loại
    LANGUAGE_CHOICES = [
        ('en', 'Tiếng Anh'),
        ('de', 'Tiếng Đức'),
    ]
    LEVEL_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'), ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2'),
    ]
    
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='de',
                                verbose_name='Ngôn ngữ')
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='A1',
                             verbose_name='Trình độ')
    
    # Tác giả
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, related_name='flashcard_decks')
    
    # Trạng thái
    is_public = models.BooleanField(default=True, verbose_name='Công khai')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bộ Flashcard'
        verbose_name_plural = 'Bộ Flashcard'
        ordering = ['-is_featured', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def card_count(self):
        return self.cards.count()


class Flashcard(models.Model):
    """Thẻ flashcard"""
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE,
                             related_name='cards', verbose_name='Bộ thẻ')
    
    front = models.TextField(verbose_name='Mặt trước',
                             help_text='Từ vựng hoặc câu hỏi')
    back = models.TextField(verbose_name='Mặt sau',
                            help_text='Nghĩa hoặc câu trả lời')
    
    # Thông tin bổ sung
    example = models.TextField(blank=True, verbose_name='Ví dụ')
    pronunciation = models.CharField(max_length=200, blank=True, verbose_name='Phát âm')
    audio_url = models.URLField(blank=True, verbose_name='Audio URL')
    image = models.ImageField(upload_to='flashcards/', blank=True, verbose_name='Hình ảnh')
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Thẻ Flashcard'
        verbose_name_plural = 'Thẻ Flashcard'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.front[:50]}..."

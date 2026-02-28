"""
Models cho Knowledge App
Bài viết kiến thức học tập với phân loại theo ngôn ngữ và trình độ
Hỗ trợ n8n automation để tự động đăng bài
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.image_utils import WebPImageMixin
from core.base_models import N8NTrackingMixin
from core.utils import vietnamese_slugify


class Category(models.Model):
    """Danh mục kiến thức"""
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon')
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục kiến thức'
        verbose_name_plural = 'Danh mục kiến thức'
        ordering = ['order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def article_count(self):
        return self.articles.filter(is_published=True).count()


class KnowledgeArticle(WebPImageMixin, N8NTrackingMixin, models.Model):
    """Bài viết kiến thức học tập với n8n tracking"""
    
    # WebP auto-conversion settings
    WEBP_FIELDS = ['cover_image', 'thumbnail', 'og_image']
    WEBP_SLUG_FIELD = 'slug'
    WEBP_QUALITY = 'high'
    WEBP_AUTO_THUMBNAIL = True
    WEBP_RESPONSIVE = True
    
    LANGUAGE_CHOICES = [
        ('en', 'Tiếng Anh'),
        ('de', 'Tiếng Đức'),
        ('all', 'Tất cả ngôn ngữ'),
    ]
    
    LEVEL_CHOICES = [
        ('A1', 'A1 - Sơ cấp'),
        ('A2', 'A2 - Sơ trung'),
        ('B1', 'B1 - Trung cấp'),
        ('B2', 'B2 - Trung cao'),
        ('C1', 'C1 - Cao cấp'),
        ('C2', 'C2 - Thành thạo'),
        ('all', 'Mọi trình độ'),
    ]
    
    SCHEMA_TYPE_CHOICES = [
        ('Article', 'Article'),
        ('HowTo', 'HowTo (Hướng dẫn)'),
        ('FAQPage', 'FAQ Page'),
        ('Course', 'Course'),
    ]
    
    # Thông tin cơ bản
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='Tóm tắt')
    content = models.TextField(verbose_name='Nội dung')
    
    # Phân loại học tập
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,
                                 related_name='articles', verbose_name='Danh mục')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='all',
                                verbose_name='Ngôn ngữ')
    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, default='all',
                             verbose_name='Trình độ')
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, related_name='knowledge_articles')
    
    # Hình ảnh
    cover_image = models.ImageField(upload_to='knowledge/covers/', blank=True)
    thumbnail = models.ImageField(upload_to='knowledge/thumbnails/', blank=True)
    cover_image_srcset = models.JSONField(default=dict, blank=True,
                                          verbose_name='Responsive images',
                                          help_text='Auto-generated responsive image URLs')
    
    # SEO Fields
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    canonical_url = models.URLField(blank=True)
    
    # Open Graph
    og_title = models.CharField(max_length=95, blank=True)
    og_description = models.CharField(max_length=200, blank=True)
    og_image = models.ImageField(upload_to='knowledge/og/', blank=True)
    
    # Structured Data (JSON-LD)
    schema_type = models.CharField(max_length=20, choices=SCHEMA_TYPE_CHOICES, 
                                   default='Article', verbose_name='Schema Type',
                                   help_text='Loại structured data cho Google')
    
    # Trạng thái
    is_published = models.BooleanField(default=False, verbose_name='Đã xuất bản')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Tags (comma-separated, Vietnamese with diacritics)
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags',
                            help_text='Các tag cách nhau bởi dấu phẩy (VD: ngữ pháp, tiếng Đức, A1)')
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bài viết kiến thức'
        verbose_name_plural = 'Bài viết kiến thức'
        ordering = ['-is_featured', '-published_at', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slugify(self.title)
            counter = 1
            original_slug = self.slug
            while KnowledgeArticle.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-fill SEO
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        if not self.og_title:
            self.og_title = self.title[:95]
        if not self.og_description:
            self.og_description = self.excerpt[:200] if self.excerpt else self.meta_description
        
        # Auto-copy cover_image to og_image if og_image is empty
        if self.cover_image and not self.og_image:
            self.og_image = self.cover_image
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def reading_time(self):
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))
    
    def get_absolute_url(self):
        return f"/kien-thuc/{self.slug}"
    
    def increment_views(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_level_display_vi(self):
        return dict(self.LEVEL_CHOICES).get(self.level, self.level)
    
    def get_language_display_vi(self):
        return dict(self.LANGUAGE_CHOICES).get(self.language, self.language)

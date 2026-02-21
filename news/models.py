"""
Models cho News App
Bao gồm Category và Article với đầy đủ SEO fields
Hỗ trợ n8n automation để tự động đăng bài
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.image_utils import WebPImageMixin, should_convert_to_webp, convert_to_webp
from core.base_models import N8NTrackingMixin
from core.utils import vietnamese_slugify


class Category(models.Model):
    """Danh mục tin tức"""
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon',
                           help_text='Tên icon (VD: FaNewspaper)')
    
    # SEO Fields
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='SEO Title',
                                  help_text='Tiêu đề hiển thị trên Google (tối đa 70 ký tự)')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='SEO Description',
                                        help_text='Mô tả hiển thị trên Google (tối đa 160 ký tự)')
    
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục tin tức'
        verbose_name_plural = 'Danh mục tin tức'
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


class Article(WebPImageMixin, N8NTrackingMixin, models.Model):
    """Bài viết tin tức với đầy đủ SEO fields và n8n tracking"""
    
    # WebP auto-conversion settings
    WEBP_FIELDS = ['cover_image', 'thumbnail', 'og_image']
    WEBP_SLUG_FIELD = 'slug'
    WEBP_QUALITY = 'high'
    WEBP_AUTO_THUMBNAIL = True
    WEBP_RESPONSIVE = True
    
    # Thông tin cơ bản
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='Tóm tắt',
                               help_text='Đoạn giới thiệu ngắn (hiển thị trong danh sách)')
    content = models.TextField(verbose_name='Nội dung')
    
    # Phân loại
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, 
                                 related_name='articles', verbose_name='Danh mục')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, related_name='news_articles', verbose_name='Tác giả')
    
    # Hình ảnh
    cover_image = models.ImageField(upload_to='news/covers/', blank=True, 
                                    verbose_name='Ảnh bìa')
    thumbnail = models.ImageField(upload_to='news/thumbnails/', blank=True,
                                  verbose_name='Ảnh thumbnail')
    cover_image_srcset = models.JSONField(default=dict, blank=True,
                                          verbose_name='Responsive images',
                                          help_text='Auto-generated responsive image URLs')
    
    # SEO Fields
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='SEO Title',
                                  help_text='Tiêu đề hiển thị trên Google (tối đa 70 ký tự)')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='SEO Description',
                                        help_text='Mô tả hiển thị trên Google (tối đa 160 ký tự)')
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name='Keywords',
                                     help_text='Từ khóa SEO, cách nhau bởi dấu phẩy')
    canonical_url = models.URLField(blank=True, verbose_name='Canonical URL',
                                    help_text='URL chính thức (để tránh duplicate content)')
    
    # Open Graph (Social Media)
    og_title = models.CharField(max_length=95, blank=True, verbose_name='OG Title',
                                help_text='Tiêu đề khi share Facebook/Twitter')
    og_description = models.CharField(max_length=200, blank=True, verbose_name='OG Description')
    og_image = models.ImageField(upload_to='news/og/', blank=True, verbose_name='OG Image',
                                 help_text='Ảnh khi share (1200x630 px)')
    
    # Trạng thái
    is_published = models.BooleanField(default=False, verbose_name='Đã xuất bản')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Ngày xuất bản')
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0, verbose_name='Lượt xem')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bài viết'
        verbose_name_plural = 'Bài viết'
        ordering = ['-is_featured', '-published_at', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slugify(self.title)
            # Đảm bảo unique
            counter = 1
            original_slug = self.slug
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-fill SEO fields nếu trống
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
        """Ước tính thời gian đọc (200 từ/phút)"""
        word_count = len(self.content.split())
        minutes = max(1, round(word_count / 200))
        return minutes
    
    def get_absolute_url(self):
        return f"/tin-tuc/{self.slug}"
    
    def increment_views(self):
        """Tăng lượt xem"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

"""
Base Models cho UnstressVN
Abstract models với đầy đủ fields SEO, n8n tracking, content management
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .image_utils import WebPImageMixin


class TimeStampedModel(models.Model):
    """Abstract model với created_at và updated_at"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')
    
    class Meta:
        abstract = True


class N8NTrackingMixin(models.Model):
    """
    Mixin để tracking bài viết được tạo bởi n8n automation.
    Cho phép n8n tự động đăng bài và theo dõi nguồn.
    """
    SOURCE_CHOICES = [
        ('manual', 'Tạo thủ công'),
        ('n8n', 'N8N Automation'),
        ('api', 'API Import'),
        ('rss', 'RSS Feed'),
        ('scraper', 'Web Scraper'),
    ]
    
    # N8N Tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual',
                              verbose_name='Nguồn tạo',
                              help_text='Bài viết được tạo từ nguồn nào')
    source_url = models.URLField(blank=True, verbose_name='URL nguồn',
                                 help_text='Link bài viết gốc (nếu import)')
    source_id = models.CharField(max_length=100, blank=True, verbose_name='ID nguồn',
                                 help_text='ID từ hệ thống nguồn (để tránh duplicate)')
    
    # N8N workflow tracking
    n8n_workflow_id = models.CharField(max_length=50, blank=True, verbose_name='N8N Workflow ID')
    n8n_execution_id = models.CharField(max_length=100, blank=True, verbose_name='N8N Execution ID')
    n8n_created_at = models.DateTimeField(null=True, blank=True, verbose_name='N8N tạo lúc')
    
    # AI content flags
    is_ai_generated = models.BooleanField(default=False, verbose_name='AI tạo nội dung',
                                          help_text='Nội dung được tạo bởi AI')
    ai_model = models.CharField(max_length=50, blank=True, verbose_name='AI Model',
                                help_text='Model AI đã sử dụng (GPT-4, Claude, etc.)')
    human_reviewed = models.BooleanField(default=False, verbose_name='Đã review',
                                         help_text='Con người đã review nội dung')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='%(class)s_reviewed',
                                    verbose_name='Người review')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Review lúc')
    
    class Meta:
        abstract = True
    
    def mark_reviewed(self, user):
        """Đánh dấu đã được review"""
        self.human_reviewed = True
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=['human_reviewed', 'reviewed_by', 'reviewed_at'])
    
    @classmethod
    def get_by_source_id(cls, source, source_id):
        """Tìm bài viết theo source_id để tránh duplicate"""
        try:
            return cls.objects.get(source=source, source_id=source_id)
        except cls.DoesNotExist:
            return None


class SEOMixin(models.Model):
    """
    Mixin cho SEO fields chuẩn.
    Bao gồm meta tags, Open Graph, Structured Data.
    """
    # Basic SEO
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
    og_description = models.CharField(max_length=200, blank=True, verbose_name='OG Description',
                                      help_text='Mô tả khi share')
    og_image = models.ImageField(upload_to='og/', blank=True, verbose_name='OG Image',
                                 help_text='Ảnh khi share (1200x630 px)')
    
    # Indexing control
    noindex = models.BooleanField(default=False, verbose_name='No Index',
                                  help_text='Không cho Google index trang này')
    nofollow = models.BooleanField(default=False, verbose_name='No Follow',
                                   help_text='Không cho Google follow links')
    
    class Meta:
        abstract = True
    
    def get_meta_title(self, fallback=''):
        """Lấy meta title, fallback về fallback nếu trống"""
        return self.meta_title or fallback[:70]
    
    def get_meta_description(self, fallback=''):
        """Lấy meta description, fallback về fallback nếu trống"""
        return self.meta_description or fallback[:160]
    
    def get_robots_meta(self):
        """Trả về giá trị robots meta tag"""
        parts = []
        if self.noindex:
            parts.append('noindex')
        if self.nofollow:
            parts.append('nofollow')
        return ', '.join(parts) if parts else 'index, follow'


class PublishableMixin(models.Model):
    """
    Mixin cho content có thể publish/unpublish.
    Hỗ trợ scheduled publishing.
    """
    STATUS_CHOICES = [
        ('draft', 'Bản nháp'),
        ('pending', 'Chờ duyệt'),
        ('scheduled', 'Đã lên lịch'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Đã lưu trữ'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft',
                              verbose_name='Trạng thái')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Ngày xuất bản')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='Lên lịch xuất bản',
                                        help_text='Tự động publish vào thời điểm này')
    
    class Meta:
        abstract = True
    
    @property
    def is_published(self):
        """Kiểm tra đã publish chưa"""
        return self.status == 'published'
    
    def publish(self):
        """Publish bài viết"""
        self.status = 'published'
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
    
    def unpublish(self):
        """Unpublish bài viết"""
        self.status = 'draft'
        self.save(update_fields=['status'])
    
    def archive(self):
        """Lưu trữ bài viết"""
        self.status = 'archived'
        self.save(update_fields=['status'])


class BaseArticle(WebPImageMixin, TimeStampedModel, N8NTrackingMixin, SEOMixin, PublishableMixin):
    """
    Abstract base model cho tất cả các loại bài viết.
    Kết hợp tất cả các mixin cần thiết.
    
    Sử dụng:
    class MyArticle(BaseArticle):
        # Thêm fields riêng
        my_field = models.CharField(...)
        
        class Meta(BaseArticle.Meta):
            verbose_name = 'My Article'
    """
    
    # WebP auto-conversion settings (override in child class)
    WEBP_FIELDS = ['cover_image', 'thumbnail', 'og_image']
    WEBP_SLUG_FIELD = 'slug'
    WEBP_QUALITY = 'high'
    
    # Thông tin cơ bản
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    slug = models.SlugField(max_length=280, unique=True, blank=True,
                            help_text='URL-friendly version của title')
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='Tóm tắt',
                               help_text='Đoạn giới thiệu ngắn (hiển thị trong danh sách)')
    content = models.TextField(verbose_name='Nội dung',
                               help_text='Nội dung chính (hỗ trợ HTML/Markdown)')
    
    # Tác giả
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='%(class)s_articles',
                               verbose_name='Tác giả')
    
    # Hình ảnh
    cover_image = models.ImageField(upload_to='articles/covers/', blank=True,
                                    verbose_name='Ảnh bìa')
    thumbnail = models.ImageField(upload_to='articles/thumbnails/', blank=True,
                                  verbose_name='Ảnh thumbnail')
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0, verbose_name='Lượt xem')
    
    # Tags (sử dụng CharField để đơn giản, có thể upgrade lên ManyToMany sau)
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags',
                            help_text='Các tag cách nhau bởi dấu phẩy')
    
    class Meta:
        abstract = True
        ordering = ['-is_featured', '-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title)
            counter = 1
            original_slug = self.slug
            while self.__class__.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-fill SEO fields
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        if not self.og_title:
            self.og_title = self.title[:95]
        if not self.og_description:
            self.og_description = self.excerpt[:200] if self.excerpt else self.meta_description
        
        super().save(*args, **kwargs)
    
    def increment_view(self):
        """Tăng view count"""
        self.__class__.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
    
    def get_tags_list(self):
        """Trả về list các tags"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def get_reading_time(self):
        """Ước tính thời gian đọc (phút)"""
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))  # 200 words per minute
    
    @classmethod
    def get_published(cls):
        """Lấy tất cả bài đã publish"""
        return cls.objects.filter(status='published')
    
    @classmethod
    def get_featured(cls):
        """Lấy bài viết nổi bật đã publish"""
        return cls.objects.filter(status='published', is_featured=True)


class BaseCategory(TimeStampedModel):
    """
    Abstract base model cho Category.
    """
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icon',
                           help_text='Tên icon (VD: FaBook, FaNewspaper)')
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True, verbose_name='SEO Title')
    meta_description = models.CharField(max_length=160, blank=True, verbose_name='SEO Description')
    
    # Display
    order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự')
    is_active = models.BooleanField(default=True, verbose_name='Hiển thị')
    
    class Meta:
        abstract = True
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

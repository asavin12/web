"""
Models cho File Manager
Quản lý media files trên server
"""

import os
from io import BytesIO
from PIL import Image
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile


def convert_to_webp(image_file, quality=85):
    """Convert image to WebP format"""
    img = Image.open(image_file)
    
    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background for transparent images
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Save as WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, optimize=True)
    output.seek(0)
    
    return output


def upload_media_path(instance, filename):
    """Generate upload path for media files"""
    # Get file extension
    base, ext = os.path.splitext(filename)
    
    # Convert to webp for images
    if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        ext = '.webp'
    
    return f'{instance.folder}/{base}{ext}'


class MediaFile(models.Model):
    """Model để quản lý media files"""
    FOLDER_CHOICES = [
        ('images', 'Hình ảnh'),
        ('documents', 'Tài liệu'),
        ('avatars', 'Avatar'),
        ('covers', 'Ảnh bìa'),
        ('logos', 'Logo'),
        ('resources', 'Tài nguyên'),
        ('other', 'Khác'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='Tên file')
    file = models.FileField(upload_to=upload_media_path, verbose_name='File')
    folder = models.CharField(max_length=50, choices=FOLDER_CHOICES, default='images',
                              verbose_name='Thư mục')
    
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveIntegerField(default=0, verbose_name='Kích thước (bytes)')
    mime_type = models.CharField(max_length=100, blank=True, verbose_name='Loại file')
    
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name='Chiều rộng')
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name='Chiều cao')
    
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Alt text (SEO)')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='uploaded_files')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Store original filename
        if self.file and not self.original_filename:
            self.original_filename = self.file.name
        
        # Auto-generate name from filename if not set
        if not self.name and self.file:
            self.name = os.path.splitext(os.path.basename(self.file.name))[0]
        
        # Convert images to WebP before saving
        if self.file and hasattr(self.file, 'content_type'):
            if self.file.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/bmp']:
                self._convert_to_webp()
        
        super().save(*args, **kwargs)
        
        # Update file info after save
        if self.file:
            self._update_file_info()
    
    def _convert_to_webp(self):
        """Convert uploaded image to WebP"""
        try:
            webp_content = convert_to_webp(self.file)
            
            # Generate new filename
            base = os.path.splitext(self.file.name)[0]
            new_filename = f"{base}.webp"
            
            # Create new file
            self.file = ContentFile(webp_content.read(), name=new_filename)
            self.mime_type = 'image/webp'
        except Exception as e:
            print(f"Error converting to WebP: {e}")
    
    def _update_file_info(self):
        """Update file size and dimensions"""
        try:
            self.file_size = self.file.size
            
            # Get image dimensions
            if self.mime_type and self.mime_type.startswith('image/'):
                with Image.open(self.file.path) as img:
                    self.width, self.height = img.size
                    # Save without calling save() recursively
                    MediaFile.objects.filter(pk=self.pk).update(
                        file_size=self.file_size,
                        width=self.width,
                        height=self.height
                    )
        except Exception:
            pass
    
    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return ''
    
    @property
    def is_image(self):
        return self.mime_type and self.mime_type.startswith('image/')
    
    @property
    def file_size_display(self):
        """Human readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class SiteLogo(models.Model):
    """Logo variants cho website"""
    LOGO_TYPE_CHOICES = [
        ('favicon', 'Favicon (16x16, 32x32)'),
        ('icon-small', 'Icon nhỏ (< 100px, SVG)'),
        ('icon-medium', 'Icon vừa (100-200px, WebP)'),
        ('logo-header', 'Logo Header (WebP)'),
        ('logo-footer', 'Logo Footer (WebP)'),
        ('logo-full', 'Logo đầy đủ (WebP)'),
        ('og-image', 'OG Image (1200x630, WebP)'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Tên')
    logo_type = models.CharField(max_length=20, choices=LOGO_TYPE_CHOICES, unique=True,
                                 verbose_name='Loại logo')
    
    # Có thể upload SVG hoặc image
    svg_code = models.TextField(blank=True, verbose_name='SVG Code',
                                help_text='Code SVG cho logo nhỏ < 100px')
    image = models.ImageField(upload_to='logos/', blank=True, verbose_name='Image file',
                              help_text='File ảnh WebP cho logo lớn >= 100px')
    
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Logo'
        verbose_name_plural = 'Site Logos'
    
    def __str__(self):
        return f"{self.name} ({self.get_logo_type_display()})"
    
    @classmethod
    def get_logo(cls, logo_type):
        """Lấy logo theo type"""
        try:
            return cls.objects.get(logo_type=logo_type, is_active=True)
        except cls.DoesNotExist:
            return None

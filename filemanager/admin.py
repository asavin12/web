"""
Admin cho File Manager
Quản lý media files trên server
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import MediaFile, SiteLogo


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    """Admin cho quản lý Media Files"""
    list_display = ['thumbnail_preview', 'name', 'folder', 'file_size_display', 
                    'dimensions', 'mime_type', 'created_at']
    list_display_links = ['thumbnail_preview', 'name']
    list_filter = ['folder', 'mime_type', 'created_at']
    search_fields = ['name', 'original_filename', 'alt_text', 'description']
    readonly_fields = ['thumbnail_preview_large', 'original_filename', 'file_size', 
                       'width', 'height', 'mime_type', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('File', {
            'fields': ('file', 'name', 'folder')
        }),
        ('SEO & Mô tả', {
            'fields': ('alt_text', 'description')
        }),
        ('Xem trước', {
            'fields': ('thumbnail_preview_large',),
            'classes': ('collapse',)
        }),
        ('Thông tin file', {
            'fields': ('original_filename', 'file_size', 'mime_type', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        if obj.file and obj.is_image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.file.url
            )
        return format_html('<span style="color: #999;">📄</span>')
    thumbnail_preview.short_description = 'Preview'
    
    def thumbnail_preview_large(self, obj):
        if obj.file and obj.is_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.file.url
            )
        return 'Không có preview'
    thumbnail_preview_large.short_description = 'Xem trước'
    
    def dimensions(self, obj):
        if obj.width and obj.height:
            return f"{obj.width} x {obj.height}"
        return '-'
    dimensions.short_description = 'Kích thước'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.uploaded_by = request.user
        
        # Detect mime type from file
        if obj.file:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(obj.file.name)
            obj.mime_type = mime_type or 'application/octet-stream'
        
        super().save_model(request, obj, form, change)


@admin.register(SiteLogo)
class SiteLogoAdmin(admin.ModelAdmin):
    """Admin cho Site Logos"""
    list_display = ['name', 'logo_type', 'logo_preview', 'dimensions', 'is_active']
    list_filter = ['logo_type', 'is_active']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Thông tin', {
            'fields': ('name', 'logo_type')
        }),
        ('Logo Content', {
            'fields': ('svg_code', 'image'),
            'description': '''
                <strong>Hướng dẫn:</strong><br>
                • Logo < 100px: Sử dụng SVG code<br>
                • Logo >= 100px: Upload ảnh WebP<br>
            '''
        }),
        ('Kích thước', {
            'fields': ('width', 'height')
        }),
        ('Trạng thái', {
            'fields': ('is_active',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.svg_code:
            return format_html(
                '<div style="max-width: 60px; max-height: 60px; overflow: hidden;">{}</div>',
                obj.svg_code
            )
        elif obj.image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: contain;" />',
                obj.image.url
            )
        return '-'
    logo_preview.short_description = 'Preview'
    
    def dimensions(self, obj):
        if obj.width and obj.height:
            return f"{obj.width} x {obj.height}"
        return '-'
    dimensions.short_description = 'Kích thước'

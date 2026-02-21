"""
Media Stream Admin Configuration
Quản lý video/audio trong Django Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist, PlaylistItem


class MediaSubtitleInline(admin.TabularInline):
    """Inline để thêm subtitles cho media"""
    model = MediaSubtitle
    extra = 1
    fields = ['language', 'label', 'file', 'is_default']


@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    """Admin cho Media Categories"""
    list_display = ['name', 'slug', 'parent', 'media_count', 'order']
    list_editable = ['order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['parent']
    ordering = ['order', 'name']
    
    def media_count(self, obj):
        return obj.media_files.count()
    media_count.short_description = 'Số media'


@admin.register(StreamMedia)
class StreamMediaAdmin(admin.ModelAdmin):
    """Admin cho Stream Media"""
    change_list_template = 'admin/mediastream/streammedia_changelist.html'
    
    list_display = [
        'thumbnail_preview', 
        'title', 
        'media_type_badge',
        'language_badge',
        'level',
        'file_size_display', 
        'duration_display',
        'view_count',
        'is_active',
        'is_public',
        'actions_column',
    ]
    list_display_links = ['title']
    list_filter = ['media_type', 'language', 'level', 'is_active', 'is_public', 'category']
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'uid', 'file_size', 'mime_type', 
        'view_count', 'download_count',
        'created_at', 'updated_at',
        'stream_url_display', 'embed_code_display'
    ]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'media_type', 'file', 'thumbnail')
        }),
        ('Nội dung', {
            'fields': ('description', 'transcript', 'tags')
        }),
        ('Phân loại', {
            'fields': ('category', 'language', 'level')
        }),
        ('Quyền truy cập', {
            'fields': ('is_active', 'is_public', 'requires_login')
        }),
        ('Thông tin file', {
            'fields': ('uid', 'file_size', 'mime_type', 'duration', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('URLs & Embed', {
            'fields': ('stream_url_display', 'embed_code_display'),
            'classes': ('collapse',)
        }),
        ('Thống kê', {
            'fields': ('view_count', 'download_count', 'uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MediaSubtitleInline]
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width:60px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.thumbnail.url
            )
        icon = '🎬' if obj.media_type == 'video' else '🎵'
        return format_html(
            '<span style="font-size:24px;display:block;text-align:center;">{}</span>',
            icon
        )
    thumbnail_preview.short_description = ''
    
    def media_type_badge(self, obj):
        colors = {'video': '#4CAF50', 'audio': '#2196F3'}
        icons = {'video': '🎬', 'audio': '🎵'}
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">'
            '{} {}</span>',
            colors.get(obj.media_type, '#999'),
            icons.get(obj.media_type, ''),
            obj.get_media_type_display()
        )
    media_type_badge.short_description = 'Loại'
    
    def language_badge(self, obj):
        colors = {'vi': '#FF5722', 'en': '#2196F3', 'de': '#FFC107', 'all': '#9E9E9E'}
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            colors.get(obj.language, '#999'),
            obj.get_language_display()
        )
    language_badge.short_description = 'Ngôn ngữ'
    
    def stream_url_display(self, obj):
        if obj.pk:
            url = obj.get_stream_url()
            return format_html(
                '<input type="text" value="{}" readonly style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;" onclick="this.select()" />',
                url
            )
        return '-'
    stream_url_display.short_description = 'Stream URL'
    
    def embed_code_display(self, obj):
        if obj.pk:
            return format_html(
                '<textarea readonly style="width:100%;height:80px;padding:8px;border:1px solid #ddd;border-radius:4px;font-family:monospace;font-size:12px;" onclick="this.select()">{}</textarea>',
                obj.get_embed_code()
            )
        return '-'
    embed_code_display.short_description = 'Embed Code'
    
    def actions_column(self, obj):
        if obj.pk:
            play_url = obj.get_stream_url()
            return format_html(
                '<a href="{}" target="_blank" class="button" style="padding:4px 8px;font-size:11px;">▶ Play</a>',
                play_url
            )
        return '-'
    actions_column.short_description = 'Actions'
    
    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context=None):
        """Add extra context for upload panel"""
        extra_context = extra_context or {}
        extra_context['total_media'] = StreamMedia.objects.count()
        return super().changelist_view(request, extra_context=extra_context)


class PlaylistItemInline(admin.TabularInline):
    """Inline cho playlist items"""
    model = PlaylistItem
    extra = 1
    raw_id_fields = ['media']
    ordering = ['order']


@admin.register(MediaPlaylist)
class MediaPlaylistAdmin(admin.ModelAdmin):
    """Admin cho Playlists"""
    list_display = ['title', 'language', 'level', 'total_items', 'is_public', 'is_featured', 'created_by']
    list_filter = ['language', 'level', 'is_public', 'is_featured']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PlaylistItemInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


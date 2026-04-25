"""
Media Stream Admin Configuration
Quản lý video/audio trong Django Admin
"""

import logging
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist, PlaylistItem, GDriveAccount, GeminiModelEntry

logger = logging.getLogger(__name__)


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
        'storage_type_badge',
        'language_badge',
        'level',
        'file_size_col', 
        'duration_col',
        'view_count',
        'is_active',
        'is_public',
        'actions_column',
    ]
    list_display_links = ['title']
    list_filter = ['media_type', 'storage_type', 'language', 'level', 'is_active', 'is_public', 'category']
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    actions = ['fetch_youtube_metadata', 'fetch_gdrive_metadata']
    readonly_fields = [
        'uid', 'file_size', 'mime_type', 
        'view_count', 'download_count',
        'created_at', 'updated_at',
        'stream_url_display', 'embed_code_display',
        'youtube_preview',
    ]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'media_type', 'storage_type', 'file', 'thumbnail')
        }),
        ('YouTube', {
            'fields': ('youtube_id', 'youtube_preview'),
            'classes': ('collapse',),
            'description': '<strong>🎬 Đăng video YouTube:</strong><br>'
                           '1. Dán YouTube URL hoặc Video ID vào ô bên dưới<br>'
                           '2. Nhấn "Lưu" → Hệ thống tự động lấy tiêu đề, mô tả, thời lượng, thumbnail từ YouTube<br>'
                           '3. Loại media & lưu trữ sẽ tự động chuyển thành Video + YouTube<br><br>'
                           '<strong>Định dạng hỗ trợ:</strong> '
                           '<code>dQw4w9WgXcQ</code> · '
                           '<code>https://www.youtube.com/watch?v=dQw4w9WgXcQ</code> · '
                           '<code>https://youtu.be/dQw4w9WgXcQ</code>'
        }),
        ('Google Drive', {
            'fields': ('gdrive_url', 'gdrive_file_id'),
            'classes': ('collapse',),
            'description': 'Dán link Google Drive vào "GDrive URL" → File ID sẽ tự động trích xuất khi lưu. '
                           'File phải được chia sẻ "Anyone with the link".'
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
    
    class Media:
        js = ('js/admin_youtube_autofetch.js',)
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width:60px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.thumbnail.url
            )
        if obj.youtube_id:
            return format_html(
                '<img src="https://img.youtube.com/vi/{}/default.jpg" '
                'style="width:60px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.youtube_id
            )
        icons = {'video': '🎬', 'audio': '🎵', 'podcast': '🎙️'}
        icon = icons.get(obj.media_type, '🎵')
        return format_html(
            '<span style="font-size:24px;display:block;text-align:center;">{}</span>',
            icon
        )
    thumbnail_preview.short_description = ''
    
    def media_type_badge(self, obj):
        colors = {'video': '#4CAF50', 'audio': '#2196F3', 'podcast': '#9C27B0'}
        icons = {'video': '🎬', 'audio': '🎵', 'podcast': '🎙️'}
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">'
            '{} {}</span>',
            colors.get(obj.media_type, '#999'),
            icons.get(obj.media_type, ''),
            obj.get_media_type_display()
        )
    media_type_badge.short_description = 'Loại'
    
    def storage_type_badge(self, obj):
        colors = {'local': '#607D8B', 'gdrive': '#4285F4', 'youtube': '#c4302b'}
        icons = {'local': '💾', 'gdrive': '☁️', 'youtube': '▶'}
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">'
            '{} {}</span>',
            colors.get(obj.storage_type, '#999'),
            icons.get(obj.storage_type, ''),
            obj.get_storage_type_display()
        )
    storage_type_badge.short_description = 'Lưu trữ'
    
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
    
    def file_size_col(self, obj):
        """Hiển thị file size - ẩn cho YouTube"""
        if obj.storage_type == 'youtube':
            return format_html('<span style="color:#999;">—</span>')
        if not obj.file_size:
            return format_html('<span style="color:#999;">—</span>')
        return obj.file_size_display
    file_size_col.short_description = 'Kích thước'
    file_size_col.admin_order_field = 'file_size'
    
    def duration_col(self, obj):
        """Hiển thị duration đẹp hơn"""
        if obj.duration:
            return obj.duration_display
        return format_html('<span style="color:#ccc;">—</span>')
    duration_col.short_description = 'Thời lượng'
    duration_col.admin_order_field = 'duration'

    def actions_column(self, obj):
        if obj.pk:
            if obj.storage_type == 'youtube' and obj.youtube_id:
                play_url = f'https://www.youtube.com/watch?v={obj.youtube_id}'
            else:
                play_url = obj.get_stream_url()
            return format_html(
                '<a href="{}" target="_blank" class="button" style="padding:4px 8px;font-size:11px;">▶ Play</a>',
                play_url
            )
        return '-'
    actions_column.short_description = 'Actions'
    
    def youtube_preview(self, obj):
        """Xem trước video YouTube trong form"""
        if obj.youtube_id:
            return format_html(
                '<div style="max-width:560px;">'
                '<img src="https://img.youtube.com/vi/{}/hqdefault.jpg" '
                'style="width:100%;max-width:480px;border-radius:8px;margin-bottom:8px;" /><br>'
                '<a href="https://www.youtube.com/watch?v={}" target="_blank" '
                'style="color:#c4302b;font-weight:bold;text-decoration:none;">'
                '▶ Xem trên YouTube</a>'
                ' &nbsp;|&nbsp; '
                '<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;">{}</code>'
                '</div>',
                obj.youtube_id, obj.youtube_id, obj.youtube_id
            )
        return format_html(
            '<span style="color:#999;">💡 Nhập YouTube URL/ID ở trên rồi lưu để xem trước</span>'
        )
    youtube_preview.short_description = 'Xem trước YouTube'

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        
        # Auto-fetch YouTube info when youtube_id is set
        if obj.youtube_id:
            self._auto_fetch_youtube(request, obj, change)
        
        # Auto-fetch GDrive metadata when gdrive_file_id is set
        if obj.gdrive_file_id and obj.storage_type == 'gdrive':
            self._auto_fetch_gdrive(request, obj, change)
        
        super().save_model(request, obj, form, change)
    
    def _auto_fetch_youtube(self, request, obj, is_change):
        """Tự động lấy thông tin từ YouTube khi có youtube_id"""
        from core.youtube import fetch_youtube_info
        
        # Auto-fetch if new, youtube_id changed, or missing essential info
        should_fetch = False
        if not is_change:
            should_fetch = True
        elif obj.pk:
            try:
                old = StreamMedia.objects.get(pk=obj.pk)
                if old.youtube_id != obj.youtube_id:
                    should_fetch = True
                elif not obj.duration:
                    should_fetch = True  # Missing duration → re-fetch
            except StreamMedia.DoesNotExist:
                should_fetch = True
        
        if not should_fetch:
            return
        
        info = fetch_youtube_info(obj.youtube_id)
        if not info:
            messages.warning(request, '⚠️ Không thể lấy thông tin từ YouTube. Kiểm tra video ID.')
            return
        
        self._apply_youtube_info(obj, info)
        messages.success(request, f'✅ Đã lấy thông tin từ YouTube: {info.get("title", "")[:60]}')
    
    @staticmethod
    def _apply_youtube_info(obj, info):
        """Áp dụng thông tin YouTube vào object — chỉ fill các field trống"""
        if not obj.title or obj.title.strip() == '':
            obj.title = info.get('title', '')[:255]
        if not obj.description or obj.description.strip() == '':
            obj.description = info.get('description', '')
        
        # Duration: prefer duration_seconds (int), fallback to parsing string
        if not obj.duration:
            dur_secs = info.get('duration_seconds')
            if dur_secs:
                obj.duration = int(dur_secs)
            else:
                duration_str = info.get('duration', '')
                if duration_str:
                    parts = duration_str.split(':')
                    try:
                        if len(parts) == 3:
                            obj.duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2:
                            obj.duration = int(parts[0]) * 60 + int(parts[1])
                    except (ValueError, IndexError):
                        pass
        
        # Tags
        yt_tags = info.get('tags', [])
        if yt_tags and not obj.tags:
            obj.tags = ', '.join(yt_tags[:10])
        
        # View count from YouTube
        yt_views = info.get('view_count', 0)
        if yt_views and not obj.view_count:
            obj.view_count = yt_views
    
    @admin.action(description='🔄 Cập nhật thông tin YouTube')
    def fetch_youtube_metadata(self, request, queryset):
        """Batch action: re-fetch metadata cho các video YouTube đã chọn"""
        from core.youtube import fetch_youtube_info_batch
        
        yt_items = list(queryset.filter(storage_type='youtube').exclude(youtube_id=''))
        if not yt_items:
            messages.warning(request, '⚠️ Không có video YouTube nào được chọn.')
            return
        
        # Batch fetch: 1 API call cho tất cả video IDs
        video_ids = [m.youtube_id for m in yt_items]
        all_info = fetch_youtube_info_batch(video_ids)
        
        updated = 0
        failed = 0
        errors = []
        for media in yt_items:
            try:
                info = all_info.get(media.youtube_id)
                if info:
                    self._apply_youtube_info(media, info)
                    media.save()
                    updated += 1
                else:
                    failed += 1
                    errors.append(f'{media.youtube_id}: không lấy được info')
            except Exception as e:
                failed += 1
                errors.append(f'{media.youtube_id}: {e}')
                logger.error(f"Batch update error cho {media.youtube_id}: {e}")
        
        if updated:
            messages.success(request, f'✅ Đã cập nhật {updated} video từ YouTube')
        if failed:
            error_detail = '; '.join(errors[:5])
            messages.warning(request, f'⚠️ {failed} video không thể cập nhật: {error_detail}')
    
    def _auto_fetch_gdrive(self, request, obj, is_change):
        """Tự động lấy metadata + thumbnail từ Google Drive khi có gdrive_file_id"""
        from . import gdrive_oauth
        
        # Auto-fetch nếu mới, gdrive_file_id thay đổi, hoặc thiếu duration
        should_fetch = False
        if not is_change:
            should_fetch = True
        elif obj.pk:
            try:
                old = StreamMedia.objects.get(pk=obj.pk)
                if old.gdrive_file_id != obj.gdrive_file_id:
                    should_fetch = True
                elif not obj.duration:
                    should_fetch = True
            except StreamMedia.DoesNotExist:
                should_fetch = True
        
        if not should_fetch:
            return
        
        info = gdrive_oauth.fetch_gdrive_file_metadata(obj.gdrive_file_id)
        if not info:
            messages.warning(request, '⚠️ Không thể lấy metadata từ Google Drive.')
            return
        
        self._apply_gdrive_info(obj, info)
        
        # Auto-extract thumbnail nếu chưa có
        if not obj.thumbnail:
            self._extract_gdrive_thumbnail(obj, info)
        
        dur = info.get('duration_seconds', 'N/A')
        res = f"{info.get('width', '?')}x{info.get('height', '?')}"
        messages.success(request, f'✅ GDrive: {info.get("name", "")} — {dur}s, {res}')
    
    @staticmethod
    def _apply_gdrive_info(obj, info):
        """Áp dụng metadata Google Drive vào object — chỉ fill các field trống"""
        if info.get('size') and not obj.file_size:
            obj.file_size = info['size']
        
        if info.get('duration_seconds') and not obj.duration:
            obj.duration = info['duration_seconds']
        
        if info.get('mime_type') and not obj.mime_type:
            obj.mime_type = info['mime_type']
        
        if info.get('width') and not obj.width:
            obj.width = info['width']
        
        if info.get('height') and not obj.height:
            obj.height = info['height']
        
        if info.get('name') and not obj.title:
            obj.title = info['name'][:255]
    
    @staticmethod
    def _extract_gdrive_thumbnail(obj, info=None):
        """Trích xuất thumbnail random từ video GDrive"""
        import os
        from . import gdrive_oauth
        from django.core.files import File
        
        duration = info.get('duration_seconds') if info else obj.duration
        thumb_path = gdrive_oauth.extract_gdrive_thumbnail(obj.gdrive_file_id, duration)
        if thumb_path:
            try:
                filename = f"gdrive_thumb_{obj.gdrive_file_id[:20]}.jpg"
                with open(thumb_path, 'rb') as f:
                    obj.thumbnail.save(filename, File(f), save=False)
                logger.info("GDrive thumbnail saved cho %s: %s", obj.gdrive_file_id, filename)
            except Exception as e:
                logger.warning("Failed to save GDrive thumbnail: %s", e)
            finally:
                if os.path.isfile(thumb_path):
                    os.unlink(thumb_path)
    
    @admin.action(description='📁 Cập nhật metadata Google Drive')
    def fetch_gdrive_metadata(self, request, queryset):
        """Batch action: fetch metadata + thumbnail cho các video GDrive đã chọn"""
        from . import gdrive_oauth
        
        gdrive_items = list(queryset.filter(storage_type='gdrive').exclude(gdrive_file_id=''))
        if not gdrive_items:
            messages.warning(request, '⚠️ Không có video Google Drive nào được chọn.')
            return
        
        # Batch fetch metadata
        file_ids = [m.gdrive_file_id for m in gdrive_items]
        all_info = gdrive_oauth.fetch_gdrive_metadata_batch(file_ids)
        
        updated = 0
        thumbs = 0
        failed = 0
        errors = []
        for media in gdrive_items:
            try:
                info = all_info.get(media.gdrive_file_id)
                if info:
                    self._apply_gdrive_info(media, info)
                    
                    # Extract thumbnail nếu chưa có
                    if not media.thumbnail:
                        self._extract_gdrive_thumbnail(media, info)
                        if media.thumbnail:
                            thumbs += 1
                    
                    media.save()
                    updated += 1
                else:
                    failed += 1
                    errors.append(f'{media.gdrive_file_id[:15]}: không lấy được')
            except Exception as e:
                failed += 1
                errors.append(f'{media.gdrive_file_id[:15]}: {e}')
                logger.error(f"GDrive metadata error cho {media.gdrive_file_id}: {e}")
        
        parts = []
        if updated:
            parts.append(f'✅ {updated} video cập nhật')
        if thumbs:
            parts.append(f'🖼️ {thumbs} thumbnail')
        if parts:
            messages.success(request, ' | '.join(parts))
        if failed:
            error_detail = '; '.join(errors[:5])
            messages.warning(request, f'⚠️ {failed} video không thể cập nhật: {error_detail}')
    
    def changelist_view(self, request, extra_context=None):
        """Add extra context for upload panel"""
        extra_context = extra_context or {}
        extra_context['total_media'] = StreamMedia.objects.count()
        # GDrive OAuth2 accounts
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        gdrive_accounts = GDriveAccount.objects.filter(is_active=True).order_by('storage_used')
        # Pre-check token status for each account
        from . import gdrive_oauth
        accounts_with_status = []
        for a in gdrive_accounts:
            token_info = gdrive_oauth.check_token_status(a)
            a.token_valid = token_info['valid']
            a.token_error = token_info['error']
            accounts_with_status.append(a)
        extra_context['gdrive_accounts'] = accounts_with_status
        extra_context['gdrive_total_free'] = sum(a.storage_free for a in gdrive_accounts)
        extra_context['has_oauth_config'] = bool(
            config.gdrive_oauth_client_id and config.gdrive_oauth_client_secret
        )
        # News categories for auto-publish
        from news.models import Category as NewsCategory
        extra_context['news_categories'] = NewsCategory.objects.filter(is_active=True).order_by('order', 'name')
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


@admin.register(GDriveAccount)
class GDriveAccountAdmin(admin.ModelAdmin):
    """Admin cho GDrive OAuth2 Accounts"""
    list_display = ['email', 'is_active', 'storage_bar', 'storage_used_display', 'storage_total_display', 'last_used']
    list_filter = ['is_active']
    readonly_fields = ['email', 'storage_used', 'storage_total', 'root_folder_id', 'folder_mapping', 'added_at', 'last_used', 'last_storage_check']

    def storage_bar(self, obj):
        pct = obj.storage_percent
        color = '#28a745' if pct < 70 else '#ffc107' if pct < 90 else '#dc3545'
        return format_html(
            '<div style="width:120px;background:#eee;border-radius:4px;overflow:hidden;">'
            '<div style="width:{}%;background:{};height:14px;border-radius:4px;"></div>'
            '</div>'
            '<small>{}% — {} trống</small>',
            min(pct, 100), color, pct, obj.storage_free_display,
        )
    storage_bar.short_description = 'Dung lượng'

    def has_add_permission(self, request):
        return False  # Must add via OAuth2 flow


@admin.register(GeminiModelEntry)
class GeminiModelEntryAdmin(admin.ModelAdmin):
    """Admin cho Gemini AI Models"""
    list_display = ['model_id', 'display_name', 'description', 'is_active', 'sort_order', 'synced_at']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_order']
    search_fields = ['model_id', 'display_name']
    ordering = ['sort_order', 'model_id']


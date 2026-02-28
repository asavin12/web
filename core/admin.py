from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from .models import Video, NavigationLink, APIKey, SiteConfiguration
from .youtube import fetch_youtube_info
import secrets


# ============ API Key Admin ============

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin quản lý API Keys với tính năng tạo key tự động"""
    list_display = ('name', 'key_type', 'key_preview', 'is_active', 'security_status', 'usage_count', 'last_used_at', 'last_used_ip')
    list_filter = ('key_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('key_preview_full', 'key_hash', 'key_prefix', 'usage_count', 'last_used_at', 'last_used_ip', 'created_at', 'updated_at', 'generate_key_button')
    ordering = ['key_type', 'name']
    actions = ['regenerate_keys', 'reset_usage_count']
    
    fieldsets = (
        ('Thông tin Key', {
            'fields': ('name', 'key_type', 'description'),
        }),
        ('API Key', {
            'fields': ('key', 'generate_key_button', 'key_preview_full', 'key_hash', 'key_prefix'),
            'description': '💡 Để trống trường "key" để hệ thống tự động tạo key bảo mật cao. Key tự động hash bằng HMAC-SHA256.'
        }),
        ('Bảo mật', {
            'fields': ('is_active', 'allowed_ips', 'rate_limit', 'expires_at'),
            'description': '🛡️ Giới hạn IP, rate limit, và thời hạn key.'
        }),
        ('Thống kê sử dụng', {
            'fields': ('usage_count', 'last_used_at', 'last_used_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    class Media:
        js = ('admin/js/api_key_generator.js',)
    
    def key_preview(self, obj):
        """Hiển thị key đã che bớt"""
        if obj.key:
            hidden = obj.key[:8] + '...' + obj.key[-4:]
            return format_html(
                '<code style="background: #f4f4f4; padding: 2px 6px; border-radius: 3px;">{}</code>',
                hidden
            )
        return '-'
    key_preview.short_description = 'Key'

    def security_status(self, obj):
        """Show security indicators"""
        badges = []
        if obj.key_hash:
            badges.append('<span style="background:#d1fae5;color:#065f46;padding:2px 6px;border-radius:3px;font-size:11px;">🔒 Hashed</span>')
        else:
            badges.append('<span style="background:#fee2e2;color:#991b1b;padding:2px 6px;border-radius:3px;font-size:11px;">⚠️ No Hash</span>')
        if obj.allowed_ips:
            badges.append('<span style="background:#dbeafe;color:#1e40af;padding:2px 6px;border-radius:3px;font-size:11px;">🌐 IP Lock</span>')
        if obj.rate_limit > 0:
            badges.append(f'<span style="background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:3px;font-size:11px;">⏱ {obj.rate_limit}/min</span>')
        if obj.is_expired:
            badges.append('<span style="background:#fee2e2;color:#991b1b;padding:2px 6px;border-radius:3px;font-size:11px;">❌ Expired</span>')
        elif obj.expires_at:
            badges.append('<span style="background:#e0e7ff;color:#3730a3;padding:2px 6px;border-radius:3px;font-size:11px;">📅 Expiry Set</span>')
        return format_html(' '.join(badges)) if badges else '-'
    security_status.short_description = 'Security'
    
    def key_preview_full(self, obj):
        """Hiển thị full key với nút copy"""
        if obj.key:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<code id="api-key-{}" style="background: #e8f4e8; padding: 8px 12px; border-radius: 4px; '
                'font-family: monospace; font-size: 13px;">{}</code>'
                '<button type="button" onclick="copyToClipboard(\'{}\')" '
                'style="padding: 6px 12px; background: #417690; color: white; border: none; '
                'border-radius: 4px; cursor: pointer;">📋 Copy</button>'
                '</div>'
                '<script>function copyToClipboard(text) {{ navigator.clipboard.writeText(text); '
                'alert("Đã copy API Key!"); }}</script>',
                obj.pk, obj.key, obj.key
            )
        return 'Chưa có key - hệ thống sẽ tự tạo khi lưu'
    key_preview_full.short_description = 'API Key đầy đủ'
    
    def generate_key_button(self, obj):
        """Nút để tạo key mới ngẫu nhiên"""
        new_key = secrets.token_urlsafe(32)
        return format_html(
            '''<div style="margin: 5px 0; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
                <button type="button" onclick="generateRandomKey()" 
                    style="padding: 10px 20px; background: linear-gradient(135deg, #28a745, #20903d); 
                    color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;
                    box-shadow: 0 2px 8px rgba(40,167,69,0.3); transition: all 0.2s;"
                    onmouseover="this.style.transform='translateY(-2px)'" 
                    onmouseout="this.style.transform='translateY(0)'">
                    🔐 Tạo Key Ngẫu Nhiên
                </button>
                <span style="color: #666; font-size: 13px;">
                    hoặc nhập key tùy chỉnh
                </span>
            </div>
            <script>
            function generateRandomKey() {{
                // Generate secure random key using Web Crypto API
                const array = new Uint8Array(32);
                crypto.getRandomValues(array);
                const key = btoa(String.fromCharCode.apply(null, array))
                    .replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
                
                const keyInput = document.getElementById('id_key');
                if (keyInput) {{
                    keyInput.value = key;
                    keyInput.style.background = '#e8f4e8';
                    keyInput.style.transition = 'background 0.3s';
                    setTimeout(() => keyInput.style.background = '', 1000);
                    
                    // Show notification
                    const msg = document.createElement('div');
                    msg.innerHTML = '✅ Đã tạo key ngẫu nhiên mới!';
                    msg.style.cssText = 'position:fixed;top:80px;right:20px;background:#28a745;color:white;' +
                        'padding:12px 20px;border-radius:8px;z-index:9999;font-weight:600;' +
                        'box-shadow:0 4px 15px rgba(0,0,0,0.2);animation:slideIn 0.3s ease';
                    document.body.appendChild(msg);
                    setTimeout(() => msg.remove(), 3000);
                }}
            }}
            </script>''',
        )
    generate_key_button.short_description = 'Tạo key mới'
    
    @admin.action(description='🔄 Tạo lại key mới')
    def regenerate_keys(self, request, queryset):
        """Tạo lại key mới cho các key đã chọn"""
        count = 0
        for api_key in queryset:
            api_key.key = secrets.token_urlsafe(32)
            api_key.save()
            count += 1
        messages.success(request, f'✅ Đã tạo lại {count} API Key mới')
    
    @admin.action(description='🔢 Reset số lần sử dụng')
    def reset_usage_count(self, request, queryset):
        """Reset usage count về 0"""
        queryset.update(usage_count=0)
        messages.success(request, f'✅ Đã reset số lần sử dụng')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin cho Video - Tự động lấy thông tin từ YouTube"""
    list_display = ('thumbnail_preview', 'title', 'language', 'level', 'duration', 
                    'view_count', 'is_featured', 'is_active')
    list_display_links = ('thumbnail_preview', 'title')
    list_filter = ('language', 'level', 'is_featured', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_featured', 'is_active')
    readonly_fields = ('thumbnail_preview_large', 'view_count', 'created_at', 'updated_at', 'fetch_info_button')
    ordering = ['-is_featured', '-created_at']
    actions = ['fetch_youtube_metadata']
    
    fieldsets = (
        ('Thông tin video', {
            'fields': ('youtube_id', 'fetch_info_button', 'title', 'description'),
            'description': '''
                <strong>🎬 Tự động lấy thông tin từ YouTube:</strong><br>
                1. Nhập YouTube URL hoặc Video ID<br>
                2. Để trống tiêu đề và mô tả<br>
                3. Nhấn "Lưu" - hệ thống sẽ tự động điền thông tin<br><br>
                <strong>Định dạng hỗ trợ:</strong><br>
                • ID thuần: <code>dQw4w9WgXcQ</code><br>
                • URL đầy đủ: <code>https://www.youtube.com/watch?v=dQw4w9WgXcQ</code><br>
                • URL rút gọn: <code>https://youtu.be/dQw4w9WgXcQ</code>
            '''
        }),
        ('Phân loại', {
            'fields': ('language', 'level', 'duration')
        }),
        ('Hiển thị', {
            'fields': ('is_featured', 'is_active')
        }),
        ('Xem trước', {
            'fields': ('thumbnail_preview_large',),
            'classes': ('collapse',)
        }),
        ('Thống kê', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        js = ('js/admin_youtube_autofetch.js',)
    
    def thumbnail_preview(self, obj):
        """Ảnh nhỏ trong danh sách"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 80px; height: 45px; object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail
            )
        return '-'
    thumbnail_preview.short_description = 'Ảnh'
    
    def thumbnail_preview_large(self, obj):
        """Xem trước video trong form edit"""
        if obj.youtube_id:
            return format_html(
                '<div style="max-width: 560px;">'
                '<img src="https://img.youtube.com/vi/{}/hqdefault.jpg" style="width: 100%; border-radius: 8px; margin-bottom: 10px;" />'
                '<br><a href="https://www.youtube.com/watch?v={}" target="_blank" '
                'style="color: #c4302b; font-weight: bold;">▶ Xem trên YouTube</a>'
                '</div>',
                obj.youtube_id, obj.youtube_id
            )
        return 'Chưa có YouTube ID'
    thumbnail_preview_large.short_description = 'Xem trước'
    
    def fetch_info_button(self, obj):
        """Nút để fetch thông tin từ YouTube"""
        if obj.pk and obj.youtube_id:
            return format_html(
                '<a class="button" href="{}?action=fetch_youtube" '
                'style="background: #417690; color: white; padding: 5px 15px; border-radius: 4px; text-decoration: none;">'
                '🔄 Cập nhật từ YouTube</a>',
                f'/admin/core/video/{obj.pk}/change/'
            )
        return format_html(
            '<span style="color: #666;">💡 Nhập YouTube URL/ID rồi lưu để tự động lấy thông tin</span>'
        )
    fetch_info_button.short_description = 'Tự động điền'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Handle fetch_youtube action from button"""
        if request.GET.get('action') == 'fetch_youtube':
            obj = self.get_object(request, object_id)
            if obj and obj.youtube_id:
                info = fetch_youtube_info(obj.youtube_id)
                if info:
                    obj.title = info.get('title', obj.title)[:255]
                    obj.description = info.get('description', obj.description)
                    obj.duration = info.get('duration', obj.duration)
                    if info.get('thumbnail'):
                        obj.thumbnail = info.get('thumbnail')
                    obj.save(auto_fetch_youtube=False)
                    messages.success(request, f'✅ Đã cập nhật thông tin từ YouTube: {obj.title}')
                else:
                    messages.warning(request, '⚠️ Không thể lấy thông tin từ YouTube. Kiểm tra API key hoặc video ID.')
        return super().change_view(request, object_id, form_url, extra_context)
    
    @admin.action(description='🔄 Cập nhật thông tin từ YouTube')
    def fetch_youtube_metadata(self, request, queryset):
        """Batch action để fetch metadata cho nhiều video"""
        updated = 0
        failed = 0
        for video in queryset:
            if video.youtube_id:
                if video.fetch_youtube_metadata():
                    updated += 1
                else:
                    failed += 1
        
        if updated:
            messages.success(request, f'✅ Đã cập nhật {updated} video từ YouTube')
        if failed:
            messages.warning(request, f'⚠️ {failed} video không thể cập nhật')


@admin.register(NavigationLink)
class NavigationLinkAdmin(admin.ModelAdmin):
    """
    Admin quản lý chuyên nghiệp links điều hướng cho navbar và footer.
    Hỗ trợ menu phân cấp (parent → children), đa ngôn ngữ, badge, coming-soon.
    """
    list_display = (
        'display_name', 'url_preview', 'location_badge',
        'parent_link', 'icon_display', 'badge_info',
        'is_active', 'order',
    )
    list_filter = ('location', 'footer_section', 'is_active', 'is_coming_soon', 'open_in_new_tab')
    search_fields = ('name', 'name_vi', 'name_en', 'name_de', 'url')
    list_editable = ('is_active', 'order')
    ordering = ['location', 'parent__order', 'order']
    list_per_page = 50
    
    class Media:
        css = {
            'all': ('admin/css/navigation_admin.css',)
        }
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'url', 'icon'),
            'description': '📝 Tên chính (dùng cho admin) và URL đích.',
        }),
        ('🌐 Đa ngôn ngữ', {
            'fields': ('name_vi', 'name_en', 'name_de'),
            'description': 'Tên hiển thị theo ngôn ngữ. Nếu để trống sẽ dùng "Tên hiển thị" ở trên.',
            'classes': ('collapse',),
        }),
        ('📍 Vị trí & Phân cấp', {
            'fields': ('location', 'footer_section', 'parent'),
            'description': (
                '• <b>Navbar</b>: link xuất hiện trên thanh nav.<br>'
                '• <b>Footer</b>: link xuất hiện ở chân trang, chia nhóm theo "Phần trong Footer".<br>'
                '• <b>Menu cha</b>: để trống nếu là menu gốc (dropdown header), chọn parent nếu là submenu.'
            ),
        }),
        ('⚙️ Tuỳ chọn hiển thị', {
            'fields': ('open_in_new_tab', 'is_coming_soon', 'badge_text', 'is_active', 'order'),
            'description': (
                '• <b>Sắp ra mắt</b>: vô hiệu hoá link, hiển thị badge "Soon".<br>'
                '• <b>Badge</b>: text tuỳ chỉnh trên badge (VD: New, Hot). Để trống = không badge.'
            ),
        }),
    )
    
    def display_name(self, obj):
        """Hiển thị tên có indent cho children, hỗ trợ font tiếng Việt"""
        name_style = (
            'font-family: "Segoe UI", "Noto Sans", "Roboto", -apple-system, '
            'BlinkMacSystemFont, sans-serif;'
        )
        if obj.parent:
            return format_html(
                '<span style="color:#888; margin-right:4px; padding-left:24px;">└─</span>'
                '<span style="font-size:12px; {}">{}</span>',
                name_style, obj.name
            )
        children_count = obj.children.filter(is_active=True).count()
        name_html = format_html(
            '<strong style="font-size:13px; {}">{}</strong>',
            name_style, obj.name
        )
        if children_count > 0:
            return format_html(
                '{} <span style="color:#6366f1; font-size:10px; '
                'padding:1px 5px; background:#eef2ff; border-radius:3px;">'
                '▼ {}</span>',
                name_html, children_count
            )
        return name_html
    display_name.short_description = 'Tên menu'
    display_name.admin_order_field = 'name'
    
    def url_preview(self, obj):
        """Hiển thị URL với icon external nếu cần"""
        if obj.is_external:
            return format_html(
                '<a href="{}" target="_blank" style="color: #417690;">{} 🔗</a>',
                obj.url, obj.url[:40] + '...' if len(obj.url) > 40 else obj.url
            )
        return format_html(
            '<code style="background:#f0f0f0; padding:2px 6px; border-radius:3px; font-size:12px;">{}</code>',
            obj.url
        )
    url_preview.short_description = 'URL'
    
    def location_badge(self, obj):
        """Badge màu cho location"""
        colors = {
            'navbar': ('#dbeafe', '#1e40af', '📌'),
            'footer': ('#f3e8ff', '#6b21a8', '📄'),
            'both': ('#dcfce7', '#166534', '🔗'),
        }
        bg, fg, emoji = colors.get(obj.location, ('#f3f4f6', '#374151', ''))
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;">'
            '{} {}</span>',
            bg, fg, emoji, obj.get_location_display()
        )
    location_badge.short_description = 'Vị trí'
    location_badge.admin_order_field = 'location'
    
    def parent_link(self, obj):
        """Hiển thị parent menu"""
        if obj.parent:
            return format_html(
                '<span style="color:#059669; font-weight:500;">↑ {}</span>',
                obj.parent.name
            )
        children_count = obj.children.filter(is_active=True).count()
        if children_count > 0:
            return format_html(
                '<span style="color:#6366f1; font-weight:500;">📂 {} mục con</span>',
                children_count
            )
        return format_html('<span style="color:#9ca3af;">—</span>')
    parent_link.short_description = 'Cấp menu'
    
    def icon_display(self, obj):
        """Hiển thị icon name ngắn gọn"""
        if obj.icon:
            return format_html(
                '<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:11px;">{}</code>',
                obj.icon
            )
        return format_html('<span style="color:#ccc;">—</span>')
    icon_display.short_description = 'Icon'

    def badge_info(self, obj):
        """Hiển thị badge + trạng thái đặc biệt"""
        parts = []
        if obj.is_coming_soon:
            parts.append(
                '<span style="background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:3px;font-size:10px;">⏳ Soon</span>'
            )
        if obj.badge_text:
            parts.append(
                f'<span style="background:#fee2e2;color:#991b1b;padding:2px 6px;border-radius:3px;font-size:10px;">🏷️ {obj.badge_text}</span>'
            )
        if obj.open_in_new_tab:
            parts.append(
                '<span style="background:#dbeafe;color:#1e40af;padding:2px 6px;border-radius:3px;font-size:10px;">🔗 New tab</span>'
            )
        return format_html(' '.join(parts)) if parts else ''
    badge_info.short_description = 'Badge'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Lọc parent chỉ hiển thị menu không có parent (menu gốc)"""
        if db_field.name == "parent":
            kwargs["queryset"] = NavigationLink.objects.filter(parent__isnull=True).order_by('location', 'order')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        """Optimise queries — prefetch parent + children count"""
        return super().get_queryset(request).select_related('parent').prefetch_related('children')


# ============ Site Configuration Admin (Singleton) ============

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """
    Trang quản lý CẤU HÌNH HỆ THỐNG — tất cả cài đặt website tại 1 nơi.
    Singleton: chỉ có 1 bản ghi duy nhất.
    Dữ liệu nhạy cảm (🔒) được mã hoá Fernet trước khi lưu vào database.
    """

    fieldsets = (
        ('🌐 Thông tin website', {
            'fields': ('site_name', 'site_description', 'contact_email'),
        }),
        ('⚙️ Chế độ hoạt động', {
            'fields': ('debug_mode', 'maintenance_mode'),
            'description': (
                '<div style="padding:10px;background:#fff3cd;border-radius:6px;margin-bottom:10px;">'
                '<strong>⚠️ QUAN TRỌNG:</strong> Tắt Debug Mode khi deploy lên production. '
                'Hệ thống tự động bật HTTPS, HSTS, Secure Cookies khi Debug = OFF.'
                '</div>'
            ),
        }),
        ('🔒 Bảo mật & Network', {
            'fields': ('allowed_hosts', 'csrf_trusted_origins', 'cors_allowed_origins'),
            'description': 'Phân cách nhiều giá trị bằng dấu phẩy.',
        }),
        ('📧 Email SMTP', {
            'fields': (
                'email_host', 'email_port', 'email_use_tls',
                'email_host_user', 'email_host_password', 'default_from_email',
            ),
            'classes': ('collapse',),
            'description': (
                'Cấu hình gửi email (Gmail App Password, SendGrid, etc.). '
                'Khi Debug = ON, email in ra console thay vì gửi thật.'
            ),
        }),
        ('🔑 API Keys', {
            'fields': ('youtube_api_key', 'gemini_api_key'),
            'classes': ('collapse',),
            'description': (
                'API keys cho dịch vụ bên ngoài. '
                'Giá trị được mã hoá Fernet trước khi lưu vào database.'
            ),
        }),
        ('☁️ MinIO/S3 Storage', {
            'fields': (
                'minio_endpoint_url', 'minio_access_key', 'minio_secret_key',
                'minio_media_bucket', 'minio_region', 'minio_custom_domain',
            ),
            'classes': ('collapse',),
            'description': 'Cloud storage cho media files. Để trống = local storage.',
        }),
        ('🔍 Elasticsearch', {
            'fields': ('elasticsearch_url', 'elasticsearch_autosync'),
            'classes': ('collapse',),
        }),
        ('📡 Redis', {
            'fields': ('redis_url',),
            'classes': ('collapse',),
            'description': 'Channel layer cho WebSocket. Để trống = InMemory (dev).',
        }),
        ('🔗 Mạng xã hội', {
            'fields': ('facebook_url', 'youtube_channel_url', 'tiktok_url', 'github_url'),
            'classes': ('collapse',),
        }),
        ('📊 Thông tin hệ thống', {
            'fields': ('updated_at', 'encryption_status'),
        }),
    )

    readonly_fields = ('updated_at', 'encryption_status')

    def has_add_permission(self, request):
        """Chỉ cho tạo 1 bản ghi duy nhất."""
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Auto-redirect đến trang edit (singleton)."""
        obj = SiteConfiguration.get_instance()
        from django.urls import reverse
        return redirect(reverse('admin:core_siteconfiguration_change', args=[obj.pk]))

    def encryption_status(self, obj):
        """Hiển thị trạng thái mã hoá."""
        encrypted_fields = []
        if obj.email_host_password:
            encrypted_fields.append('Mật khẩu SMTP')
        if obj.youtube_api_key:
            encrypted_fields.append('YouTube API Key')
        if obj.minio_access_key:
            encrypted_fields.append('MinIO Access Key')
        if obj.minio_secret_key:
            encrypted_fields.append('MinIO Secret Key')

        if encrypted_fields:
            items = ''.join(f'<li>✅ {f}</li>' for f in encrypted_fields)
            return format_html(
                '<div style="padding:10px;background:#d4edda;border-radius:6px;">'
                '<strong>🔒 Các trường đang được mã hoá Fernet trong database:</strong>'
                '<ul style="margin:5px 0 0 0;">{}</ul></div>',
                mark_safe(items),
            )
        return format_html(
            '<div style="padding:10px;background:#f8f9fa;border-radius:6px;">'
            'Chưa có dữ liệu nhạy cảm nào được lưu.</div>'
        )
    encryption_status.short_description = 'Trạng thái mã hoá'

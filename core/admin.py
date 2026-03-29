from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.db import models
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


class NavigationChildInline(admin.TabularInline):
    """Inline: thêm/sửa submenu trực tiếp trong form parent menu"""
    model = NavigationLink
    fk_name = 'parent'
    extra = 1
    fields = ('name', 'name_vi', 'name_en', 'url', 'icon', 'description', 'badge_text', 'is_coming_soon', 'open_in_new_tab', 'is_active', 'order')
    ordering = ['order']
    verbose_name = 'Mục con'
    verbose_name_plural = '📂 Mục con (Submenu)'
    classes = ['collapse']
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(parent__isnull=False)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'name':
            field.widget.attrs['style'] = 'width:120px'
        elif db_field.name == 'url':
            field.widget.attrs['style'] = 'width:150px'
        elif db_field.name in ('icon', 'badge_text', 'description'):
            field.widget.attrs['style'] = 'width:100px'
        elif db_field.name in ('name_vi', 'name_en'):
            field.widget.attrs['style'] = 'width:100px'
        return field


@admin.register(NavigationLink)
class NavigationLinkAdmin(admin.ModelAdmin):
    """
    Admin quản lý menu điều hướng — tree view, icon picker, live preview.
    Hỗ trợ menu phân cấp (parent → children), đa ngôn ngữ, badge, coming-soon.
    """
    change_list_template = 'admin/core/navigationlink/change_list.html'
    inlines = [NavigationChildInline]
    
    list_display = (
        'tree_display', 'url_preview', 'location_badge',
        'parent_link', 'icon_display', 'badge_info',
        'is_active', 'order',
    )
    list_filter = ('location', 'footer_section', 'is_active', 'is_coming_soon', 'open_in_new_tab')
    search_fields = ('name', 'name_vi', 'name_en', 'name_de', 'url')
    list_editable = ('is_active', 'order')
    ordering = ['location', 'parent__order', 'order']
    list_per_page = 100
    actions = ['enable_selected', 'disable_selected', 'auto_reorder', 'duplicate_selected']
    
    class Media:
        css = {
            'all': ('admin/css/navigation_admin.css',)
        }
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'url', 'description', 'icon'),
            'description': (
                '📝 Tên chính (dùng cho admin) và URL đích.<br>'
                '<b>Icon</b>: Nhập tên Lucide icon — xem danh sách đầy đủ tại '
                '<a href="https://lucide.dev/icons/" target="_blank">lucide.dev/icons</a>'
            ),
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
    
    def get_inline_instances(self, request, obj=None):
        """Chỉ hiển thị inline khi edit parent (không phải child, không phải add new)"""
        if obj and obj.parent is None:
            return super().get_inline_instances(request, obj)
        return []
    
    # ── List Display Methods ──
    
    def tree_display(self, obj):
        """Hiển thị tree view — menu cha: bold, children: indent + └─"""
        name_style = (
            'font-family: "Segoe UI", "Noto Sans", "Roboto", -apple-system, '
            'BlinkMacSystemFont, sans-serif;'
        )
        if obj.parent:
            return format_html(
                '<span style="color:#888; padding-left:24px;">└─</span>'
                '<span style="font-size:12px; {style}">{name}</span>'
                '{desc}',
                style=name_style,
                name=obj.name,
                desc=format_html(
                    ' <span style="color:#9ca3af;font-size:10px;">{}</span>', obj.description
                ) if obj.description else '',
            )
        children_count = obj.children.filter(is_active=True).count()
        name_html = format_html(
            '<strong style="font-size:13px; {}">{}</strong>',
            name_style, obj.name
        )
        if children_count > 0:
            return format_html(
                '{name} <span style="color:#6366f1; font-size:10px; '
                'padding:1px 5px; background:#eef2ff; border-radius:3px;">'
                '▼ {count}</span>{desc}',
                name=name_html,
                count=children_count,
                desc=format_html(
                    ' <span style="color:#9ca3af;font-size:10px;">{}</span>', obj.description
                ) if obj.description else '',
            )
        return format_html(
            '{name}{desc}',
            name=name_html,
            desc=format_html(
                ' <span style="color:#9ca3af;font-size:10px;">{}</span>', obj.description
            ) if obj.description else '',
        )
    tree_display.short_description = 'Tên menu'
    tree_display.admin_order_field = 'name'
    
    def url_preview(self, obj):
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
        if obj.icon:
            return format_html(
                '<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:11px;">{}</code>',
                obj.icon
            )
        return format_html('<span style="color:#ccc;">—</span>')
    icon_display.short_description = 'Icon'

    def badge_info(self, obj):
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
    
    # ── Admin Actions ──
    
    @admin.action(description='✅ Bật hiển thị các mục đã chọn')
    def enable_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'✅ Đã bật {count} mục menu.', messages.SUCCESS)
    
    @admin.action(description='❌ Tắt hiển thị các mục đã chọn')
    def disable_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'❌ Đã tắt {count} mục menu.', messages.WARNING)
    
    @admin.action(description='🔄 Tự động sắp xếp thứ tự (theo vị trí)')
    def auto_reorder(self, request, queryset):
        """Sắp xếp lại order tự động: parent items theo thứ tự hiện tại, children theo parent order"""
        navbar_parents = NavigationLink.objects.filter(
            parent__isnull=True, location__in=['navbar', 'both']
        ).order_by('order', 'name')
        footer_parents = NavigationLink.objects.filter(
            parent__isnull=True, location__in=['footer', 'both']
        ).order_by('footer_section', 'order', 'name')
        
        idx = 0
        for parent in navbar_parents:
            idx += 1
            NavigationLink.objects.filter(pk=parent.pk).update(order=idx * 10)
            for child_idx, child in enumerate(parent.children.order_by('order', 'name'), 1):
                NavigationLink.objects.filter(pk=child.pk).update(order=idx * 10 + child_idx)
        
        for parent in footer_parents:
            idx += 1
            NavigationLink.objects.filter(pk=parent.pk).update(order=idx * 10)
            for child_idx, child in enumerate(parent.children.order_by('order', 'name'), 1):
                NavigationLink.objects.filter(pk=child.pk).update(order=idx * 10 + child_idx)
        
        self.message_user(request, '🔄 Đã sắp xếp lại thứ tự tất cả menu items.', messages.SUCCESS)
    
    @admin.action(description='📋 Nhân đôi các mục đã chọn')
    def duplicate_selected(self, request, queryset):
        count = 0
        for item in queryset:
            item.pk = None
            item.name = f'{item.name} (copy)'
            item.is_active = False
            item.order = item.order + 1
            item.save()
            count += 1
        self.message_user(request, f'📋 Đã nhân đôi {count} mục menu (mặc định tắt hiển thị).', messages.SUCCESS)
    
    # ── Overrides ──
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = NavigationLink.objects.filter(parent__isnull=True).order_by('location', 'order')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent').prefetch_related('children')
    
    def changelist_view(self, request, extra_context=None):
        """Thêm context cho change_list template — menu tree + stats"""
        extra_context = extra_context or {}
        
        # Stats cho header
        total = NavigationLink.objects.count()
        active = NavigationLink.objects.filter(is_active=True).count()
        navbar_count = NavigationLink.objects.filter(location__in=['navbar', 'both'], parent__isnull=True).count()
        footer_count = NavigationLink.objects.filter(location__in=['footer', 'both'], parent__isnull=True).count()
        
        # Tree data cho navbar preview
        navbar_tree = []
        navbar_parents = NavigationLink.objects.filter(
            is_active=True, location__in=['navbar', 'both'], parent__isnull=True
        ).prefetch_related(
            models.Prefetch('children', queryset=NavigationLink.objects.filter(is_active=True).order_by('order'))
        ).order_by('order')
        
        for parent in navbar_parents:
            children = list(parent.children.all())
            navbar_tree.append({
                'name': parent.name,
                'url': parent.url,
                'icon': parent.icon,
                'has_children': len(children) > 0,
                'children': [{'name': c.name, 'url': c.url, 'icon': c.icon, 'badge': c.badge_text, 'coming_soon': c.is_coming_soon} for c in children],
            })
        
        # Footer data cho footer preview
        footer_sections = {}
        section_labels = {
            'resources': 'Khám phá', 'company': 'Hỗ trợ',
            'legal': 'Pháp lý', 'social': 'Mạng xã hội', 'community': 'Cộng đồng',
        }
        footer_links = NavigationLink.objects.filter(
            is_active=True, location__in=['footer', 'both'], parent__isnull=True
        ).order_by('footer_section', 'order')
        for link in footer_links:
            section = link.footer_section or 'other'
            if section not in footer_sections:
                footer_sections[section] = {'label': section_labels.get(section, section), 'items': []}
            footer_sections[section]['items'].append({'name': link.name, 'url': link.url, 'icon': link.icon})
        
        # Icon list for reference
        available_icons = [
            'Home', 'Newspaper', 'BookOpen', 'FileText', 'GraduationCap',
            'Languages', 'Users', 'Wrench', 'MessageSquare', 'Music',
            'Video', 'Radio', 'Globe', 'Heart', 'Star', 'Bookmark',
            'Compass', 'Mail', 'MapPin', 'Search', 'Info', 'Phone',
            'Settings', 'Link', 'Play', 'HelpCircle', 'Lock', 'Shield',
            'Calendar', 'Bell', 'Clipboard', 'Pen', 'Download', 'Upload',
            'Image', 'Camera', 'Mic', 'Headphones', 'Code', 'Database',
            'Trophy', 'Map', 'ExternalLink', 'Library', 'Facebook',
            'Youtube', 'Instagram', 'Twitter',
        ]
        
        import json
        extra_context.update({
            'nav_total': total,
            'nav_active': active,
            'nav_inactive': total - active,
            'nav_navbar': navbar_count,
            'nav_footer': footer_count,
            'navbar_tree_json': json.dumps(navbar_tree, ensure_ascii=False),
            'footer_sections_json': json.dumps(footer_sections, ensure_ascii=False),
            'available_icons_json': json.dumps(available_icons),
        })
        
        return super().changelist_view(request, extra_context=extra_context)


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
        ('☁️ Google Drive', {
            'fields': ('gdrive_service_account_json', 'gdrive_folder_id', 'gdrive_folder_mapping'),
            'description': (
                'Cấu hình upload media lên Google Drive qua Service Account. '
                'Dán nội dung JSON credentials hoặc upload file .json. '
                'Có thể dán link thư mục Google Drive — tự động trích xuất Folder ID.<br>'
                '<strong>Folder Mapping:</strong> Tự động tạo thư mục Video/Audio/Podcast '
                'bên trong thư mục gốc khi upload. Không cần chỉnh sửa thủ công.'
            ),
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
        """Hiển thị trạng thái mã hoá + phát hiện lỗi giải mã."""
        from .encryption import _get_fernet
        from cryptography.fernet import InvalidToken
        
        FERNET_PREFIX = 'gAAAAA'
        fernet = _get_fernet()
        
        encrypted_fields_map = {
            'email_host_password': 'Mật khẩu SMTP',
            'youtube_api_key': 'YouTube API Key',
            'gemini_api_key': 'Gemini API Key',
            'gdrive_service_account_json': 'Google Drive Service Account',
        }
        
        ok_fields = []
        corrupt_fields = []
        empty_fields = []
        
        for field_name, display_name in encrypted_fields_map.items():
            value = getattr(obj, field_name, '')
            if not value:
                empty_fields.append(display_name)
            elif value.startswith(FERNET_PREFIX):
                # Value is still ciphertext — decrypt failed (wrong SECRET_KEY)
                corrupt_fields.append(display_name)
            else:
                # Value is plaintext — decrypted successfully
                ok_fields.append(display_name)
        
        html_parts = []
        
        if corrupt_fields:
            items = ''.join(f'<li>⚠️ {f} — <b>KHÔNG THỂ GIẢI MÃ</b></li>' for f in corrupt_fields)
            html_parts.append(
                '<div style="padding:10px;background:#f8d7da;border-radius:6px;margin-bottom:8px;">'
                '<strong>🔴 CẢNH BÁO: SECRET_KEY có thể đã thay đổi!</strong><br>'
                'Các trường sau chứa dữ liệu mã hoá nhưng không thể giải mã:'
                f'<ul style="margin:5px 0 0 0;">{items}</ul>'
                '<small>💡 Đặt SECRET_KEY cố định trong Coolify Environment Variables để tránh mất dữ liệu.</small>'
                '</div>'
            )
        
        if ok_fields:
            items = ''.join(f'<li>✅ {f}</li>' for f in ok_fields)
            html_parts.append(
                '<div style="padding:10px;background:#d4edda;border-radius:6px;margin-bottom:8px;">'
                '<strong>🔒 Đang mã hoá Fernet:</strong>'
                f'<ul style="margin:5px 0 0 0;">{items}</ul></div>'
            )
        
        if not ok_fields and not corrupt_fields:
            html_parts.append(
                '<div style="padding:10px;background:#f8f9fa;border-radius:6px;">'
                'Chưa có dữ liệu nhạy cảm nào được lưu.</div>'
            )
        
        return format_html(mark_safe(''.join(html_parts)))
    encryption_status.short_description = 'Trạng thái mã hoá'

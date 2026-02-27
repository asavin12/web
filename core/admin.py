from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from .models import Video, NavigationLink, APIKey, SiteSettings, SiteConfiguration
from .youtube import fetch_youtube_info
import secrets


# ============ API Key Admin ============

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """Admin quản lý API Keys với tính năng tạo key tự động"""
    list_display = ('name', 'key_type', 'key_preview', 'is_active', 'usage_count', 'last_used_at')
    list_filter = ('key_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('key_preview_full', 'usage_count', 'last_used_at', 'created_at', 'updated_at', 'generate_key_button')
    ordering = ['key_type', 'name']
    actions = ['regenerate_keys', 'reset_usage_count']
    
    fieldsets = (
        ('Thông tin Key', {
            'fields': ('name', 'key_type', 'description'),
        }),
        ('API Key', {
            'fields': ('key', 'generate_key_button', 'key_preview_full'),
            'description': '💡 Để trống trường "key" để hệ thống tự động tạo key bảo mật cao.'
        }),
        ('Trạng thái', {
            'fields': ('is_active',),
        }),
        ('Thống kê sử dụng', {
            'fields': ('usage_count', 'last_used_at', 'created_at', 'updated_at'),
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


# ============ Site Settings Admin ============

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin quản lý Site Settings - Database, Email, MinIO Storage configs"""
    list_display = ('name', 'setting_type', 'value_preview', 'is_secret', 'status_badge', 'updated_at')
    list_filter = ('setting_type', 'is_secret')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'generate_password_button', 'connection_status')
    ordering = ['setting_type', 'name']
    actions = ['generate_new_passwords', 'test_minio_connection']
    
    fieldsets = (
        ('Thông tin', {
            'fields': ('name', 'setting_type', 'description'),
        }),
        ('Giá trị', {
            'fields': ('value', 'is_secret', 'generate_password_button'),
            'description': '⚠️ Nếu là password, hãy đánh dấu "Là mật khẩu/secret" để bảo mật.'
        }),
        ('Trạng thái kết nối', {
            'fields': ('connection_status',),
            'classes': ('collapse',),
            'description': 'Kiểm tra kết nối cho MinIO/Database settings'
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        """Thêm MinIO status vào changelist"""
        extra_context = extra_context or {}
        
        # Get MinIO status
        minio_config = SiteSettings.get_minio_config()
        if minio_config and minio_config.get('endpoint_url'):
            extra_context['minio_configured'] = True
            extra_context['minio_endpoint'] = minio_config.get('endpoint_url')
            extra_context['minio_bucket'] = minio_config.get('bucket')
            
            # Test connection
            try:
                import boto3
                from botocore.config import Config
                
                s3_client = boto3.client(
                    's3',
                    endpoint_url=minio_config.get('endpoint_url'),
                    aws_access_key_id=minio_config.get('access_key'),
                    aws_secret_access_key=minio_config.get('secret_key'),
                    region_name=minio_config.get('region', 'us-east-1'),
                    config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=5)
                )
                s3_client.list_buckets()
                extra_context['minio_status'] = 'connected'
            except Exception as e:
                extra_context['minio_status'] = 'error'
                extra_context['minio_error'] = str(e)[:100]
        else:
            extra_context['minio_configured'] = False
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def status_badge(self, obj):
        """Hiển thị badge trạng thái cho storage settings"""
        if obj.setting_type != 'storage':
            return '-'
        
        if obj.name == 'minio_endpoint_url':
            if obj.value:
                return format_html(
                    '<span style="background: #28a745; color: white; padding: 2px 8px; '
                    'border-radius: 10px; font-size: 11px;">Đã cấu hình</span>'
                )
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px;">Chưa cấu hình</span>'
            )
        return '-'
    status_badge.short_description = 'Trạng thái'
    
    def connection_status(self, obj):
        """Kiểm tra kết nối cho storage settings"""
        if obj.setting_type != 'storage' or obj.name != 'minio_endpoint_url':
            return format_html('<span style="color: #666;">Không áp dụng cho setting này</span>')
        
        if not obj.value:
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border-radius: 4px; margin: 5px 0;">'
                '<strong>⚠️ Chưa cấu hình MinIO</strong><br>'
                '<span style="color: #666;">Nhập MinIO Endpoint URL để sử dụng cloud storage</span>'
                '</div>'
            )
        
        # Test MinIO connection
        minio_config = SiteSettings.get_minio_config()
        if not minio_config:
            return format_html('<span style="color: red;">❌ Không thể đọc config</span>')
        
        try:
            import boto3
            from botocore.config import Config
            
            s3_client = boto3.client(
                's3',
                endpoint_url=minio_config.get('endpoint_url'),
                aws_access_key_id=minio_config.get('access_key'),
                aws_secret_access_key=minio_config.get('secret_key'),
                region_name=minio_config.get('region', 'us-east-1'),
                config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=5)
            )
            
            # List buckets to test
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response.get('Buckets', [])]
            target_bucket = minio_config.get('bucket', 'mediastream')
            
            bucket_exists = target_bucket in buckets
            
            return format_html(
                '<div style="padding: 10px; background: #d4edda; border-radius: 4px; margin: 5px 0;">'
                '<strong>✅ Kết nối thành công!</strong><br>'
                '<span>Endpoint: <code>{}</code></span><br>'
                '<span>Buckets: {}</span><br>'
                '<span>Target bucket <code>{}</code>: {}</span>'
                '</div>',
                minio_config.get('endpoint_url'),
                ', '.join(buckets) if buckets else '(trống)',
                target_bucket,
                '✅ Tồn tại' if bucket_exists else '⚠️ Chưa tạo'
            )
        except Exception as e:
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 4px; margin: 5px 0;">'
                '<strong>❌ Lỗi kết nối</strong><br>'
                '<span style="color: #721c24;">{}</span><br>'
                '<small>Kiểm tra lại endpoint URL, access key và secret key</small>'
                '</div>',
                str(e)[:200]
            )
    connection_status.short_description = 'Kiểm tra kết nối MinIO'
    
    def value_preview(self, obj):
        """Hiển thị giá trị, ẩn nếu là secret"""
        if obj.is_secret:
            return format_html(
                '<span style="color: #999;">●●●●●●●● </span>'
                '<span style="font-size: 11px; color: #666;">(hidden)</span>'
            )
        if not obj.value:
            return format_html('<span style="color: #999;">(chưa cấu hình)</span>')
        if len(obj.value) > 50:
            return obj.value[:50] + '...'
        return obj.value
    value_preview.short_description = 'Giá trị'
    
    def generate_password_button(self, obj):
        """Gợi ý password mới"""
        new_pass = SiteSettings.generate_secure_password()
        return format_html(
            '<div style="margin: 5px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">'
            '<strong>🔐 Gợi ý password bảo mật:</strong><br>'
            '<code id="suggested-pw" style="background: #fff3cd; padding: 6px 10px; display: inline-block; '
            'margin-top: 5px; font-size: 13px; border-radius: 3px;">{}</code>'
            '<button type="button" onclick="copyToClipboard(\'{}\')" '
            'style="margin-left: 10px; padding: 5px 10px; background: #28a745; color: white; '
            'border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📋 Copy</button>'
            '</div>'
            '<script>function copyToClipboard(text) {{ navigator.clipboard.writeText(text); '
            'alert("Đã copy password!"); }}</script>',
            new_pass, new_pass
        )
    generate_password_button.short_description = 'Tạo password mới'
    
    @admin.action(description='🔐 Tạo password mới cho các secret')
    def generate_new_passwords(self, request, queryset):
        """Tạo password mới cho các secret settings"""
        count = 0
        for setting in queryset.filter(is_secret=True):
            setting.value = SiteSettings.generate_secure_password()
            setting.save()
            count += 1
        if count:
            messages.success(request, f'✅ Đã tạo {count} password mới')
        else:
            messages.warning(request, '⚠️ Không có setting nào được đánh dấu là secret')
    
    @admin.action(description='🔌 Test kết nối MinIO')
    def test_minio_connection(self, request, queryset):
        """Test kết nối MinIO"""
        minio_config = SiteSettings.get_minio_config()
        if not minio_config or not minio_config.get('endpoint_url'):
            messages.warning(request, '⚠️ MinIO chưa được cấu hình. Vui lòng nhập minio_endpoint_url.')
            return
        
        try:
            import boto3
            from botocore.config import Config
            
            s3_client = boto3.client(
                's3',
                endpoint_url=minio_config.get('endpoint_url'),
                aws_access_key_id=minio_config.get('access_key'),
                aws_secret_access_key=minio_config.get('secret_key'),
                region_name=minio_config.get('region', 'us-east-1'),
                config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=5)
            )
            
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response.get('Buckets', [])]
            messages.success(request, f'✅ Kết nối MinIO thành công! Buckets: {", ".join(buckets) if buckets else "(trống)"}')
        except Exception as e:
            messages.error(request, f'❌ Lỗi kết nối MinIO: {str(e)[:100]}')


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
    """Admin quản lý links điều hướng cho navbar và footer"""
    list_display = ('name', 'url_preview', 'location', 'footer_section', 'parent', 
                    'icon', 'open_in_new_tab', 'is_active', 'order')
    list_filter = ('location', 'footer_section', 'is_active', 'open_in_new_tab')
    search_fields = ('name', 'url')
    list_editable = ('is_active', 'order')
    ordering = ['location', 'footer_section', 'order']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'url', 'icon')
        }),
        ('Vị trí', {
            'fields': ('location', 'footer_section', 'parent')
        }),
        ('Tuỳ chọn', {
            'fields': ('open_in_new_tab', 'is_active', 'order')
        }),
    )
    
    def url_preview(self, obj):
        """Hiển thị URL với icon external nếu cần"""
        if obj.is_external:
            return format_html(
                '<a href="{}" target="_blank" style="color: #417690;">{} 🔗</a>',
                obj.url, obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
            )
        return obj.url
    url_preview.short_description = 'URL'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Lọc parent chỉ hiển thị menu không có parent (menu gốc)"""
        if db_field.name == "parent":
            kwargs["queryset"] = NavigationLink.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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

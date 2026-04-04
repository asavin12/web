"""
Runtime configuration loader — đọc SiteConfiguration từ database
và áp dụng vào django.conf.settings.

Flow:
1. Django khởi động → settings.py chạy với default "an toàn"
2. CoreConfig.ready() → gọi apply_dynamic_settings()
3. SiteConfiguration được đọc từ DB → ghi đè vào django.conf.settings
4. Khi admin sửa config → signal gọi invalidate_cache() → apply lại
"""

import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

_cache = None


def get_config():
    """Lấy SiteConfiguration instance (cached trong memory)."""
    global _cache
    if _cache is not None:
        return _cache
    try:
        from core.models import SiteConfiguration
        _cache = SiteConfiguration.get_instance()
        return _cache
    except Exception:
        return None


def invalidate_cache():
    """Xoá cache khi config thay đổi — gọi bởi SiteConfiguration.save()."""
    global _cache
    _cache = None
    apply_dynamic_settings()


def apply_dynamic_settings():
    """
    Đọc cấu hình từ database và áp dụng vào Django settings.
    Nếu bảng chưa tồn tại (chưa migrate), bỏ qua.
    """
    try:
        from django.db import connection
        tables = connection.introspection.table_names()
        if 'core_siteconfiguration' not in tables:
            return
    except Exception:
        return

    config = get_config()
    if config is None:
        return

    # === Debug mode ===
    settings.DEBUG = config.debug_mode

    # === Allowed Hosts ===
    if config.allowed_hosts:
        hosts = [h.strip() for h in config.allowed_hosts.split(',') if h.strip()]
        # Merge env var ALLOWED_HOSTS (cần cho deploy trước khi cấu hình SiteConfiguration)
        env_hosts = os.environ.get('ALLOWED_HOSTS', '')
        if env_hosts:
            for h in env_hosts.split(','):
                h = h.strip()
                if h and h not in hosts:
                    hosts.append(h)
        # Luôn giữ localhost cho Docker healthcheck
        for _h in ['localhost', '127.0.0.1']:
            if _h not in hosts:
                hosts.append(_h)
        settings.ALLOWED_HOSTS = hosts

    # === CSRF ===
    if config.csrf_trusted_origins:
        origins = [o.strip() for o in config.csrf_trusted_origins.split(',') if o.strip()]
        # Merge env var CSRF_TRUSTED_ORIGINS
        env_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
        if env_csrf:
            for o in env_csrf.split(','):
                o = o.strip()
                if o and o not in origins:
                    origins.append(o)
        settings.CSRF_TRUSTED_ORIGINS = origins

    # === CORS ===
    if config.cors_allowed_origins:
        cors_origins = [o.strip() for o in config.cors_allowed_origins.split(',') if o.strip()]
        # Merge env var CORS_ALLOWED_ORIGINS
        env_cors = os.environ.get('CORS_ALLOWED_ORIGINS', '')
        if env_cors:
            for o in env_cors.split(','):
                o = o.strip()
                if o and o not in cors_origins:
                    cors_origins.append(o)
        settings.CORS_ALLOWED_ORIGINS = cors_origins

    # === Direct Upload Domain (bypass Cloudflare) ===
    upload_domain = getattr(config, 'direct_upload_domain', '').strip()
    if upload_domain:
        # Auto-add upload subdomain to ALLOWED_HOSTS
        if upload_domain not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append(upload_domain)
        # Auto-add to CSRF_TRUSTED_ORIGINS
        upload_origin = f'https://{upload_domain}'
        if not hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
            settings.CSRF_TRUSTED_ORIGINS = []
        if upload_origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(upload_origin)
        # Auto-add main site origins to CORS so browser allows cross-origin XHR
        # Request: from unstressvn.com → to upload.unstressvn.com
        if not hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            settings.CORS_ALLOWED_ORIGINS = []
        if config.allowed_hosts:
            for host in config.allowed_hosts.split(','):
                host = host.strip()
                if host and host not in ('localhost', '127.0.0.1', 'host.docker.internal'):
                    origin = f'https://{host}'
                    if origin not in settings.CORS_ALLOWED_ORIGINS:
                        settings.CORS_ALLOWED_ORIGINS.append(origin)
        if upload_origin not in settings.CORS_ALLOWED_ORIGINS:
            settings.CORS_ALLOWED_ORIGINS.append(upload_origin)
        logger.info('📤 Direct upload domain: %s', upload_domain)

    # === Email ===
    settings.EMAIL_HOST = config.email_host
    settings.EMAIL_PORT = config.email_port
    settings.EMAIL_USE_TLS = config.email_use_tls
    settings.EMAIL_HOST_USER = config.email_host_user or ''
    settings.EMAIL_HOST_PASSWORD = config.email_host_password or ''
    settings.DEFAULT_FROM_EMAIL = config.default_from_email
    if config.debug_mode:
        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    else:
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    # === YouTube ===
    settings.YOUTUBE_API_KEY = config.youtube_api_key or ''

    # === Security (production) ===
    if not config.debug_mode:
        settings.SECURE_SSL_REDIRECT = True
        settings.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
        settings.SECURE_HSTS_SECONDS = 31536000
        settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        settings.SECURE_HSTS_PRELOAD = True
        settings.SESSION_COOKIE_SECURE = True
        settings.CSRF_COOKIE_SECURE = True
        settings.SESSION_COOKIE_HTTPONLY = True
        settings.CSRF_COOKIE_HTTPONLY = True
        settings.SECURE_CONTENT_TYPE_NOSNIFF = True
        settings.SECURE_BROWSER_XSS_FILTER = True
        settings.X_FRAME_OPTIONS = 'DENY'
    else:
        settings.SECURE_SSL_REDIRECT = False

    # === Contact email ===
    settings.CONTACT_EMAIL = config.contact_email

    logger.info(
        '✅ Cấu hình đã tải từ database (debug=%s, hosts=%s)',
        config.debug_mode,
        config.allowed_hosts[:50],
    )

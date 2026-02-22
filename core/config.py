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

    # === Elasticsearch ===
    settings.ELASTICSEARCH_DSL = {
        'default': {
            'hosts': config.elasticsearch_url or 'http://localhost:9200',
        },
    }
    settings.ELASTICSEARCH_DSL_AUTOSYNC = config.elasticsearch_autosync

    # === Redis / Channels ===
    if config.redis_url:
        settings.CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {"hosts": [config.redis_url]},
            },
        }
    else:
        settings.CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            },
        }

    # === MinIO/S3 ===
    minio_cfg = config.get_minio_config()
    if minio_cfg:
        apps_list = list(settings.INSTALLED_APPS)
        if 'storages' not in apps_list:
            apps_list.append('storages')
            settings.INSTALLED_APPS = apps_list
        settings.AWS_S3_ENDPOINT_URL = minio_cfg['endpoint_url']
        settings.AWS_ACCESS_KEY_ID = minio_cfg['access_key']
        settings.AWS_SECRET_ACCESS_KEY = minio_cfg['secret_key']
        settings.AWS_STORAGE_BUCKET_NAME = minio_cfg['bucket']
        settings.AWS_S3_REGION_NAME = minio_cfg['region']
        settings.AWS_S3_SIGNATURE_VERSION = 's3v4'
        settings.AWS_S3_FILE_OVERWRITE = False
        settings.AWS_DEFAULT_ACL = 'private'
        settings.AWS_QUERYSTRING_AUTH = True
        settings.AWS_QUERYSTRING_EXPIRE = 3600

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

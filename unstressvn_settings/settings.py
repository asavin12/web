"""
Cấu hình Django cho dự án UnstressVN.
Ứng dụng học ngoại ngữ (Tiếng Anh/Tiếng Đức)

KIẾN TRÚC CẤU HÌNH:
  - SECRET_KEY: tự động tạo, lưu trong .secret_key (không commit lên git)
  - Database bootstrap: hardcoded defaults (localhost:5433/unstressvn)
  - TẤT CẢ cấu hình khác: lưu trong database → quản lý qua Admin
  - Dữ liệu nhạy cảm: mã hoá Fernet trước khi lưu vào database
  - KHÔNG cần file .env
"""

import os
import mimetypes
from pathlib import Path

# =============================================
# MIME TYPES — Đảm bảo đúng trong Docker slim
# python:3.12-slim thiếu /etc/mime.types
# Cần đăng ký trước khi Django serve media files
# =============================================
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('application/javascript', '.mjs')

# Đường dẫn gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================
# SECRET_KEY — Ưu tiên env var, sau đó file
# Trong Docker: đặt SECRET_KEY env var trong Coolify
# để key không đổi giữa các lần rebuild
# =============================================
_SECRET_KEY_FILE = BASE_DIR / '.secret_key'


def _get_or_create_secret_key():
    """Đọc SECRET_KEY: env var > file > tự tạo mới."""
    # 1. Ưu tiên biến môi trường (Docker / Coolify)
    env_key = os.environ.get('SECRET_KEY', '').strip()
    if env_key:
        return env_key

    # 2. Đọc từ file
    if _SECRET_KEY_FILE.exists():
        key = _SECRET_KEY_FILE.read_text().strip()
        if key:
            return key

    # 3. Tạo key mới và lưu file
    from django.core.management.utils import get_random_secret_key
    key = get_random_secret_key()
    try:
        _SECRET_KEY_FILE.write_text(key)
    except OSError:
        pass  # Read-only filesystem in Docker
    return key


SECRET_KEY = _get_or_create_secret_key()


# =============================================
# DEFAULTS — Giá trị mặc định (override bởi DB)
# =============================================
# Các giá trị dưới đây sẽ bị SiteConfiguration ghi đè
# khi CoreConfig.ready() chạy.

DEBUG = True  # Default dev, DB override

# Hỗ trợ ALLOWED_HOSTS từ env var (cần cho deploy lần đầu trước khi cấu hình SiteConfiguration)
_env_hosts = os.environ.get('ALLOWED_HOSTS', '')
if _env_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _env_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'host.docker.internal']
# Luôn giữ localhost cho Docker healthcheck (curl localhost:8000/...)
for _h in ['localhost', '127.0.0.1']:
    if _h not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_h)

# Hỗ trợ CSRF_TRUSTED_ORIGINS từ env var
_env_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _env_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://host.docker.internal:8000',
    ]

# =============================================
# INSTALLED APPS
# =============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',  # SEO Sitemaps

    # Third party apps
    'corsheaders',  # CORS headers for React frontend
    'rest_framework',
    'rest_framework.authtoken',  # Token Authentication
    'django_filters',
    'drf_spectacular',  # API Documentation

    # Local apps — Ứng dụng của dự án
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'resources.apps.ResourcesConfig',
    'api.apps.ApiConfig',  # REST API
    # 'search.apps.SearchConfig',  # Search — placeholder, chưa triển khai
    'news.apps.NewsConfig',  # News/Blog
    'knowledge.apps.KnowledgeConfig',  # Knowledge Base
    'tools.apps.ToolsConfig',  # Learning Tools
    'filemanager.apps.FilemanagerConfig',  # File Manager
    'mediastream.apps.MediastreamConfig',  # Media Streaming with referrer protection
]

# =============================================
# MIDDLEWARE
# =============================================
MIDDLEWARE = [
    'unstressvn_settings.middleware.PublicMediaMiddleware',  # Public media headers — must be FIRST
    'corsheaders.middleware.CorsMiddleware',  # CORS — must be before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Đa ngôn ngữ
    'unstressvn_settings.middleware.AdminVietnameseMiddleware',
    'unstressvn_settings.middleware.ForceDefaultLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'unstressvn_settings.middleware.AdminAccessMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'unstressvn_settings.middleware.Custom404Middleware',
]

ROOT_URLCONF = 'unstressvn_settings.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'unstressvn_settings.wsgi.application'
ASGI_APPLICATION = 'unstressvn_settings.asgi.application'

# =============================================
# CHANNEL LAYERS — Default (override bởi DB)
# =============================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# =============================================
# DATABASE — Bootstrap defaults
# =============================================
# Có thể override bằng biến môi trường HỆ THỐNG (không phải .env)
# cho trường hợp deploy với DB credentials khác.
import dj_database_url

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'unstressvn'),
        'USER': os.environ.get('DB_USER', 'unstressvn'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'unstressvn'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5433'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Override với DATABASE_URL nếu có (cho cloud deployment)
_DATABASE_URL = os.environ.get('DATABASE_URL')
if _DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(_DATABASE_URL, conn_max_age=600)

# =============================================
# AUTH
# =============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================
# INTERNATIONALIZATION
# =============================================
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ('vi', _('Tiếng Việt')),
    ('en', _('English')),
    ('de', _('Deutsch')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# =============================================
# STATIC & MEDIA
# =============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'frontend' / 'dist',  # React SPA build output
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
FRONTEND_DIR = BASE_DIR / 'frontend' / 'dist'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================
# PROXY & SECURITY (behind Traefik / Cloudflare)
# =============================================
# Luôn tin tưởng header X-Forwarded-Proto do reverse proxy gửi
# Đảm bảo request.is_secure() trả về True khi truy cập qua HTTPS
# → DRF tạo URL đúng https:// thay vì http://
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# =============================================
# AUTHENTICATION
# =============================================
LOGIN_URL = '/api/v1/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================
# EMAIL — Defaults (override bởi DB)
# =============================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'UnstressVN <unstressvn@gmail.com>'
CONTACT_EMAIL = 'unstressvn@gmail.com'

# =============================================
# REST FRAMEWORK
# =============================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'EXCEPTION_HANDLER': 'api.exception_handler.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/minute',
    },
}

# =============================================
# DRF SPECTACULAR
# =============================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'UnstressVN API',
    'DESCRIPTION': 'API cho nền tảng học ngoại ngữ UnstressVN',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Auth', 'description': 'Xác thực người dùng'},
        {'name': 'Resources', 'description': 'Tài liệu học tập'},
        {'name': 'Videos', 'description': 'Video bài giảng'},
        {'name': 'News', 'description': 'Tin tức'},
        {'name': 'Knowledge', 'description': 'Kiến thức'},
        {'name': 'Tools', 'description': 'Công cụ học tập'},
        {'name': 'Utility', 'description': 'Tiện ích'},
    ],
}

# =============================================
# LOGGING
# =============================================
# Tạo thư mục logs nếu chưa có
(BASE_DIR / 'logs').mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'n8n_api': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================
# CORS — Defaults (override bởi DB)
# =============================================
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:8000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',  # Cho N8N automation API
]

# =============================================
# ELASTICSEARCH — Defaults (override bởi DB)
# =============================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'http://localhost:9200',
    },
}
ELASTICSEARCH_DSL_AUTOSYNC = False
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.BaseSignalProcessor'

# =============================================
# YOUTUBE — Default (override bởi DB)
# =============================================
YOUTUBE_API_KEY = ''

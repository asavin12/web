"""
Cấu hình URL cho dự án UnstressVN - Headless Mode
Django chỉ phục vụ:
1. Admin Panel (/admin)
2. REST API (/api/v1/)
3. Media files (/media/)
4. SEO (sitemap.xml, robots.txt)
5. React SPA (tất cả routes khác)
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.sitemaps.views import sitemap

from .spa_views import spa_view, admin_gateway
from .seo import sitemaps, robots_txt


urlpatterns = [
    # Favicon redirect
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),
    
    # ============================================
    # SEO - Sitemap và Robots.txt
    # ============================================
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    
    # ============================================
    # ADMIN GATEWAY - Cổng bảo mật vào admin
    # ============================================
    path('admin-gateway/', admin_gateway, name='admin_gateway'),
    
    # ============================================
    # FILE MANAGER - Admin File Management (MUST be before admin/)
    # ============================================
    path('admin/filemanager/', include('filemanager.urls')),
    
    # ============================================
    # POSTGRESQL DASHBOARD - Database Management (MUST be before admin/)
    # ============================================
    path('admin/', include('core.admin_urls')),
    
    # ============================================
    # DJANGO ADMIN - Quản trị hệ thống
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # REST API - Dữ liệu JSON cho Frontend
    # ============================================
    path('api/v1/', include('api.urls')),
    
    # ============================================
    # MEDIA STREAM - Protected Video/Audio Streaming
    # ============================================
    path('media-stream/', include('mediastream.urls')),
    
    # ============================================
    # REACT SPA - Frontend Application
    # ============================================
    # Root redirect to SPA
    path('', spa_view, name='home'),
    
    # Tất cả routes khác được handle bởi React Router
    re_path(r'^(?P<path>.*)$', spa_view, name='spa_catch_all'),
]

# Phục vụ Media files trong development
if settings.DEBUG:
    urlpatterns = [
        # Admin và API trước
        path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),
        path('admin-gateway/', admin_gateway, name='admin_gateway'),
        # FileManager phải đứng TRƯỚC admin/ để không bị override
        path('admin/filemanager/', include('filemanager.urls')),
        # PostgreSQL Dashboard
        path('admin/', include('core.admin_urls')),
        path('admin/', admin.site.urls),
        path('api/v1/', include('api.urls')),
        # Media Stream với referrer protection
        path('media-stream/', include('mediastream.urls')),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
        # SPA routes cuối cùng
        path('', spa_view, name='home'),
        re_path(r'^(?P<path>.*)$', spa_view, name='spa_catch_all'),
    ]


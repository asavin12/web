"""
Media Stream URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views
from . import translation_views

app_name = 'mediastream'

# REST API Router
router = DefaultRouter()
router.register(r'api/media', api_views.StreamMediaViewSet, basename='api-media')
router.register(r'api/categories', api_views.MediaCategoryViewSet, basename='api-categories')
router.register(r'api/playlists', api_views.MediaPlaylistViewSet, basename='api-playlists')

urlpatterns = [
    # ===== REST API =====
    path('', include(router.urls)),
    
    # ===== Streaming URLs (Protected by referrer) =====
    path('play/<uuid:uid>/', views.stream_media, name='stream'),
    path('download/<uuid:uid>/', views.download_media, name='download'),
    path('subtitle/<int:subtitle_id>/', views.get_subtitle, name='subtitle'),
    
    # ===== Public API URLs (Legacy) =====
    path('info/<uuid:uid>/', views.media_info, name='info'),
    path('list/', views.list_media, name='list'),
    path('categories/', views.list_categories, name='categories'),
    
    # ===== Translation API (Gemini) =====
    path('translate/', translation_views.translate_subtitle, name='translate'),
    
    # ===== Admin URLs =====
    # Upload page đã chuyển vào Django Admin (/admin/mediastream/streammedia/)
    # Video chỉ được upload bởi admin hoặc n8n automation
    # path('admin/upload/', views.upload_page, name='admin_upload'),  # DEPRECATED - Sử dụng Django Admin
    path('admin/upload/api/', views.upload_media, name='admin_upload_api'),  # API cho admin changelist và n8n
    path('admin/manage/', views.manage_page, name='admin_manage'),
    path('admin/delete/<uuid:uid>/', views.delete_media, name='admin_delete'),
]

"""
Media Stream URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views
from . import translation_views
from . import smart_upload

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
    
    # ===== Smart Upload (AI-powered) =====
    path('smart-upload/', smart_upload.smart_upload_api, name='smart-upload'),
    path('analyze-subtitle/', smart_upload.analyze_subtitle_api, name='analyze-subtitle'),
    path('api/gemini-key-status/', smart_upload.gemini_key_status, name='gemini-key-status'),
    path('api/gemini-key/', smart_upload.save_gemini_key, name='gemini-key-save'),

    # ===== Google Drive Credentials (admin) =====
    path('api/gdrive-status/', smart_upload.gdrive_status, name='gdrive-status'),
    path('api/gdrive-credentials/', smart_upload.save_gdrive_credentials, name='gdrive-credentials'),
    path('api/gdrive-check/', smart_upload.gdrive_check_connection, name='gdrive-check'),

    path('api/gdrive-ensure-folders/', smart_upload.gdrive_ensure_folders, name='gdrive-ensure-folders'),
    path('api/gdrive-folder-mapping/', smart_upload.gdrive_folder_mapping, name='gdrive-folder-mapping'),
    
    # ===== Admin URLs =====
    # Upload qua Django Admin (/admin/mediastream/streammedia/)
    path('admin/upload/api/', views.upload_media, name='admin_upload_api'),  # API cho admin changelist và n8n
    path('admin/upload/chunk/', views.upload_chunk, name='admin_upload_chunk'),
    path('admin/upload/complete/', views.upload_complete, name='admin_upload_complete'),
    path('admin/manage/', views.manage_page, name='admin_manage'),
    path('admin/delete/<uuid:uid>/', views.delete_media, name='admin_delete'),
]

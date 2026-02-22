"""
URL configuration cho REST API
"""

from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from . import views
from . import n8n_views

app_name = 'api'

# Router cho ViewSets
router = DefaultRouter()
router.register(r'resources', views.ResourceViewSet, basename='resource')
# Đã xóa: profiles endpoint - thông tin người dùng luôn private

urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Authentication (csrf_exempt for external API calls)
    path('auth/login/', csrf_exempt(views.api_login), name='login'),
    path('auth/logout/', csrf_exempt(views.api_logout), name='logout'),
    path('auth/register/', csrf_exempt(views.api_register), name='register'),
    path('auth/password/change/', csrf_exempt(views.api_change_password), name='change-password'),
    path('auth/token/', csrf_exempt(obtain_auth_token), name='token'),
    
    # Backward compatibility: also support /login/ directly
    path('login/', csrf_exempt(views.api_login), name='login-alt'),
    
    # User
    path('me/', views.api_me, name='me'),
    path('my-profile/', views.MyProfileView.as_view(), name='my-profile'),
    
    # Admin Access (chỉ superuser)
    path('admin-access/', views.api_admin_access, name='admin-access'),
    
    # Utility
    path('choices/', views.api_choices, name='choices'),
    path('stats/', views.api_stats, name='stats'),
    
    # Contact form
    path('contact/', views.contact_submit, name='contact'),
    
    # Video API (core.Video model)
    path('videos/', views.video_list, name='video-list'),
    path('videos/<slug:slug>/', views.video_detail, name='video-detail'),
    
    # News
    path('news/', include('news.urls', namespace='news')),
    
    # Knowledge
    path('knowledge/', include('knowledge.urls', namespace='knowledge')),
    
    # Tools - Công cụ học tập
    path('tools/', include('tools.urls', namespace='tools')),
    
    # Navigation
    path('navigation/', views.navigation_links, name='navigation-links'),
    
    # ============ N8N Automation API ============
    # Để n8n tự động đăng bài, sử dụng header X-API-Key
    path('n8n/health/', n8n_views.n8n_health_check, name='n8n-health'),
    path('n8n/categories/', n8n_views.n8n_get_categories, name='n8n-categories'),
    path('n8n/news/', n8n_views.n8n_create_news_article, name='n8n-create-news'),
    path('n8n/news/<str:identifier>/', n8n_views.n8n_update_news_article, name='n8n-update-news'),
    path('n8n/knowledge/', n8n_views.n8n_create_knowledge_article, name='n8n-create-knowledge'),
    path('n8n/knowledge/<str:identifier>/', n8n_views.n8n_update_knowledge_article, name='n8n-update-knowledge'),
    path('n8n/resources/', n8n_views.n8n_create_resource, name='n8n-create-resource'),
    path('n8n/videos/', n8n_views.n8n_create_video, name='n8n-create-video'),
]

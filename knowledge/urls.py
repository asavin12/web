from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, KnowledgeArticleViewSet

app_name = 'knowledge'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'articles', KnowledgeArticleViewSet, basename='article')

urlpatterns = [
    path('', include(router.urls)),
]

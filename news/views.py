from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Category, Article
from .serializers import CategorySerializer, ArticleListSerializer, ArticleDetailSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho danh mục tin tức"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    pagination_class = None  # Disable pagination for categories
    
    @method_decorator(cache_page(60 * 15))  # Cache 15 phút
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho bài viết tin tức"""
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__slug', 'is_featured']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'view_count', 'created_at']
    ordering = ['-published_at']
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Article.objects.filter(is_published=True).select_related('category', 'author__profile')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Tăng lượt xem
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Lấy bài viết nổi bật"""
        featured = self.get_queryset().filter(is_featured=True)[:5]
        serializer = ArticleListSerializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Lấy bài viết mới nhất"""
        latest = self.get_queryset()[:10]
        serializer = ArticleListSerializer(latest, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Lấy bài viết liên quan"""
        article = self.get_object()
        limit = int(request.query_params.get('limit', 4))
        
        # Lấy bài viết cùng danh mục, trừ bài hiện tại
        related = self.get_queryset().filter(
            category=article.category
        ).exclude(pk=article.pk)[:limit]
        
        # Nếu không đủ, lấy thêm bài viết khác
        if related.count() < limit:
            remaining = limit - related.count()
            more_articles = self.get_queryset().exclude(
                pk__in=[article.pk] + list(related.values_list('pk', flat=True))
            )[:remaining]
            related = list(related) + list(more_articles)
        
        serializer = ArticleListSerializer(related, many=True)
        return Response(serializer.data)

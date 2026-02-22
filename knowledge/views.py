from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from .models import Category, KnowledgeArticle
from .serializers import (CategorySerializer, KnowledgeArticleListSerializer, 
                          KnowledgeArticleDetailSerializer)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho danh mục kiến thức"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    pagination_class = None  # Disable pagination for categories
    
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class KnowledgeArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho bài viết kiến thức"""
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category__slug', 'language', 'level', 'is_featured']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'view_count', 'created_at']
    ordering = ['-published_at']
    lookup_field = 'slug'
    
    def get_queryset(self):
        return KnowledgeArticle.objects.filter(is_published=True).select_related('category', 'author__profile')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return KnowledgeArticleDetailSerializer
        return KnowledgeArticleListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Lấy bài viết nổi bật"""
        featured = self.get_queryset().filter(is_featured=True)[:5]
        serializer = KnowledgeArticleListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_language(self, request):
        """Lấy bài viết theo ngôn ngữ"""
        language = request.query_params.get('lang', 'all')
        queryset = self.get_queryset()
        if language != 'all':
            queryset = queryset.filter(language__in=[language, 'all'])
        serializer = KnowledgeArticleListSerializer(queryset[:20], many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Lấy bài viết theo trình độ"""
        level = request.query_params.get('level', 'all')
        queryset = self.get_queryset()
        if level != 'all':
            queryset = queryset.filter(level__in=[level, 'all'])
        serializer = KnowledgeArticleListSerializer(queryset[:20], many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def top(self, request):
        """Lấy top bài viết theo tiêu chí
        Params:
        - sort: most_viewed, newest, oldest, most_featured (default: most_viewed)
        - limit: số bài viết (default: 5)
        """
        sort = request.query_params.get('sort', 'most_viewed')
        limit = int(request.query_params.get('limit', 5))
        
        queryset = self.get_queryset()
        
        if sort == 'newest':
            queryset = queryset.order_by('-published_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort == 'most_featured':
            queryset = queryset.filter(is_featured=True).order_by('-view_count')
        else:  # most_viewed
            queryset = queryset.order_by('-view_count')
        
        serializer = KnowledgeArticleListSerializer(queryset[:limit], many=True, context={'request': request})
        return Response(serializer.data)

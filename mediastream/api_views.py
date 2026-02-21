"""
REST API Views cho MediaStream
Cung cấp API để frontend lấy danh sách media, categories, playlists
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist
from .serializers import (
    StreamMediaSerializer, StreamMediaDetailSerializer,
    MediaCategorySerializer, MediaPlaylistSerializer
)


class MediaCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint để lấy danh sách categories
    """
    queryset = MediaCategory.objects.all()
    serializer_class = MediaCategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class StreamMediaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint để lấy danh sách media items
    
    Filters:
    - media_type: video, audio
    - language: vi, en, zh, ja, ko, fr, de
    - level: beginner, elementary, intermediate, upper_intermediate, advanced, native
    - category: category slug
    
    Search:
    - search: tìm theo title, description
    
    Ordering:
    - ordering: created_at, view_count, title
    """
    queryset = StreamMedia.objects.filter(is_active=True, is_public=True)
    serializer_class = StreamMediaSerializer
    permission_classes = [AllowAny]
    lookup_field = 'uid'
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['media_type', 'language', 'level', 'category__slug']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'view_count', 'title', 'duration']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StreamMediaDetailSerializer
        return StreamMediaSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Lấy chi tiết media và tăng view count"""
        instance = self.get_object()
        # Tăng view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_language(self, request):
        """Lấy media theo ngôn ngữ"""
        language = request.query_params.get('lang', 'vi')
        queryset = self.get_queryset().filter(language=language)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Lấy media theo trình độ"""
        level = request.query_params.get('level', 'beginner')
        queryset = self.get_queryset().filter(level=level)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Lấy media nổi bật (view cao nhất)"""
        queryset = self.get_queryset().order_by('-view_count')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Lấy media mới nhất"""
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MediaPlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint để lấy danh sách playlists
    """
    queryset = MediaPlaylist.objects.filter(is_public=True)
    serializer_class = MediaPlaylistSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['language', 'level']
    search_fields = ['title', 'description']
    ordering = ['-created_at']

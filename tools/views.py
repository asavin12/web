"""
Views cho Tools App
API endpoints cho công cụ học tập
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from .models import ToolCategory, Tool, FlashcardDeck, Flashcard
from .serializers import (
    ToolCategorySerializer, ToolSerializer, ToolListSerializer,
    FlashcardDeckSerializer, FlashcardDeckDetailSerializer, FlashcardSerializer
)


class ToolCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint cho danh mục công cụ"""
    queryset = ToolCategory.objects.filter(is_active=True)
    serializer_class = ToolCategorySerializer
    lookup_field = 'slug'
    pagination_class = None  # Disable pagination for categories
    
    def get_queryset(self):
        from django.db.models import Q
        return ToolCategory.objects.filter(is_active=True).annotate(
            tool_count=Count('tools', filter=Q(tools__is_active=True))
        )


class ToolViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint cho công cụ học tập"""
    queryset = Tool.objects.filter(is_active=True)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'tool_type', 'language', 'is_featured']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'view_count', 'order']
    ordering = ['-is_featured', 'order', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ToolListSerializer
        return ToolSerializer
    
    def get_queryset(self):
        return Tool.objects.filter(is_active=True).select_related('category', 'author__profile')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Tăng lượt xem
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Lấy danh sách công cụ nổi bật"""
        featured = self.get_queryset().filter(is_featured=True)[:6]
        serializer = ToolListSerializer(featured, many=True)
        return Response(serializer.data)


class FlashcardDeckViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint cho bộ flashcard"""
    queryset = FlashcardDeck.objects.filter(is_public=True)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['language', 'level', 'is_featured']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'view_count']
    ordering = ['-is_featured', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FlashcardDeckDetailSerializer
        return FlashcardDeckSerializer
    
    def get_queryset(self):
        # Annotate card_count để tránh N+1 query
        return FlashcardDeck.objects.filter(is_public=True).select_related('author').annotate(
            card_count=Count('cards')
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Tăng lượt xem
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Lấy danh sách bộ flashcard nổi bật"""
        featured = self.get_queryset().filter(is_featured=True)[:6]
        serializer = FlashcardDeckSerializer(featured, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def cards(self, request, slug=None):
        """Lấy tất cả thẻ của một bộ"""
        deck = self.get_object()
        cards = deck.cards.all()
        serializer = FlashcardSerializer(cards, many=True)
        return Response(serializer.data)

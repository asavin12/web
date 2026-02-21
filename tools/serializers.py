"""
Serializers cho Tools App
"""

from rest_framework import serializers
from .models import ToolCategory, Tool, FlashcardDeck, Flashcard


class ToolCategorySerializer(serializers.ModelSerializer):
    # Sử dụng annotated field từ queryset để tránh N+1 query
    tool_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ToolCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'tool_count']


class ToolSerializer(serializers.ModelSerializer):
    category = ToolCategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    author_avatar = serializers.SerializerMethodField()
    cover_image_srcset = serializers.JSONField(read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'slug', 'description', 'content', 'excerpt',
            'category', 'author', 'author_name', 'author_avatar',
            'tool_type', 'url', 'embed_code', 'icon', 'cover_image', 'featured_image',
            'cover_image_srcset',
            'language', 'is_featured', 'is_published', 'is_active', 'view_count',
            'meta_title', 'meta_description',
            'published_at', 'created_at', 'updated_at'
        ]
    
    def get_author_avatar(self, obj):
        if obj.author and hasattr(obj.author, 'profile') and obj.author.profile:
            if hasattr(obj.author.profile, 'avatar') and obj.author.profile.avatar:
                return obj.author.profile.avatar.url
        return None


class ToolListSerializer(serializers.ModelSerializer):
    """Serializer cho danh sách công cụ - hiển thị như bài viết"""
    category = ToolCategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    cover_image_srcset = serializers.JSONField(read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'slug', 'description', 'excerpt', 'category',
            'author', 'author_name',
            'tool_type', 'url', 'icon', 'cover_image', 'featured_image',
            'cover_image_srcset', 'language',
            'is_featured', 'is_published', 'is_active', 'view_count',
            'published_at', 'created_at'
        ]


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = [
            'id', 'front', 'back', 'example', 'pronunciation',
            'audio_url', 'image', 'order'
        ]


class FlashcardDeckSerializer(serializers.ModelSerializer):
    card_count = serializers.IntegerField(read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = FlashcardDeck
        fields = [
            'id', 'name', 'slug', 'description', 'language', 'level',
            'author', 'author_name', 'is_public', 'is_featured',
            'card_count', 'view_count', 'created_at'
        ]


class FlashcardDeckDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết bao gồm cả các thẻ"""
    cards = FlashcardSerializer(many=True, read_only=True)
    card_count = serializers.IntegerField(read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = FlashcardDeck
        fields = [
            'id', 'name', 'slug', 'description', 'language', 'level',
            'author', 'author_name', 'is_public', 'is_featured',
            'card_count', 'view_count', 'created_at', 'cards'
        ]

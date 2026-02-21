from rest_framework import serializers
from .models import Category, Article


class CategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'article_count',
                  'meta_title', 'meta_description']


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer cho danh sách bài viết (nhẹ hơn)"""
    category = CategorySerializer(read_only=True)
    author = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    reading_time = serializers.IntegerField(read_only=True)
    featured_image = serializers.ImageField(source='cover_image', read_only=True)
    cover_image_srcset = serializers.JSONField(read_only=True)
    
    def get_author(self, obj):
        if obj.author:
            avatar = None
            if hasattr(obj.author, 'profile') and obj.author.profile and obj.author.profile.avatar:
                avatar = obj.author.profile.avatar.url
            return {
                'id': obj.author.id,
                'username': obj.author.username,
                'avatar': avatar
            }
        return None
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'excerpt', 'category', 'author', 'author_name',
                  'featured_image', 'cover_image', 'thumbnail', 'cover_image_srcset',
                  'is_featured', 'published_at',
                  'view_count', 'reading_time', 'created_at']


class ArticleDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết bài viết với đầy đủ SEO fields"""
    category = CategorySerializer(read_only=True)
    author = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    reading_time = serializers.IntegerField(read_only=True)
    featured_image = serializers.ImageField(source='cover_image', read_only=True)
    cover_image_srcset = serializers.JSONField(read_only=True)
    
    def get_author(self, obj):
        if obj.author:
            avatar = None
            if hasattr(obj.author, 'profile') and obj.author.profile and obj.author.profile.avatar:
                avatar = obj.author.profile.avatar.url
            return {
                'id': obj.author.id,
                'username': obj.author.username,
                'avatar': avatar
            }
        return None
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'category', 'author',
                  'author_name', 'featured_image', 'cover_image', 'thumbnail',
                  'cover_image_srcset',
                  'meta_title', 'meta_description', 'meta_keywords', 'canonical_url',
                  'og_title', 'og_description', 'og_image',
                  'is_featured', 'published_at', 'view_count', 'reading_time',
                  'created_at', 'updated_at']

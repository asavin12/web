"""
Serializers cho MediaStream API
"""
from rest_framework import serializers
from .models import StreamMedia, MediaCategory, MediaSubtitle, MediaPlaylist


class MediaCategorySerializer(serializers.ModelSerializer):
    """Serializer cho danh mục media"""
    media_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'media_count']
    
    def get_media_count(self, obj):
        return obj.media_files.filter(is_active=True, is_public=True).count()


class MediaSubtitleSerializer(serializers.ModelSerializer):
    """Serializer cho phụ đề"""
    subtitle_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaSubtitle
        fields = ['id', 'language', 'label', 'subtitle_url']
    
    def get_subtitle_url(self, obj):
        return f"/media-stream/subtitle/{obj.id}/"


class StreamMediaSerializer(serializers.ModelSerializer):
    """Serializer cho media item"""
    stream_url = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    subtitles = MediaSubtitleSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = StreamMedia
        fields = [
            'id', 'uid', 'title', 'slug', 'description',
            'media_type', 'language', 'level',
            'category', 'category_name',
            'thumbnail_url', 'duration', 'duration_formatted',
            'stream_url', 'subtitles',
            'view_count', 'created_at'
        ]
    
    def get_stream_url(self, obj):
        return f"/media-stream/play/{obj.uid}/"
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None
    
    def get_duration_formatted(self, obj):
        if not obj.duration:
            return None
        minutes, seconds = divmod(obj.duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class StreamMediaDetailSerializer(StreamMediaSerializer):
    """Serializer chi tiết cho media item"""
    embed_code = serializers.SerializerMethodField()
    
    class Meta(StreamMediaSerializer.Meta):
        fields = StreamMediaSerializer.Meta.fields + [
            'embed_code', 'tags', 'transcript'
        ]
    
    def get_embed_code(self, obj):
        if obj.media_type == 'video':
            return f'''<video controls poster="{obj.thumbnail.url if obj.thumbnail else ''}">
  <source src="/media-stream/play/{obj.uid}/" type="video/mp4">
  Your browser does not support the video tag.
</video>'''
        else:
            return f'''<audio controls>
  <source src="/media-stream/play/{obj.uid}/" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>'''


class MediaPlaylistSerializer(serializers.ModelSerializer):
    """Serializer cho playlist"""
    media_items = StreamMediaSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaPlaylist
        fields = [
            'id', 'title', 'slug', 'description', 'cover_image',
            'language', 'level', 'item_count', 'total_duration',
            'is_public', 'media_items', 'created_at'
        ]
    
    def get_item_count(self, obj):
        return obj.media_items.count()
    
    def get_total_duration(self, obj):
        total = sum(m.duration or 0 for m in obj.media_items.all())
        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

"""
Serializers cho REST API
Chuyển đổi models sang JSON và ngược lại
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import UserProfile
from resources.models import Resource, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer cho Tag model"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho User model - CHỈ dành cho user sở hữu (xem thông tin của chính mình).
    KHÔNG BAO GIỜ expose cho người khác xem.
    """
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'date_joined', 'is_staff', 'is_superuser']


# ĐÃ XÓA: PublicUserSerializer
# Lý do: Không có API nào cho phép xem thông tin người dùng khác


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho UserProfile - CHỈ dành cho user sở hữu (xem/sửa profile của mình).
    KHÔNG BAO GIỜ expose cho người khác xem.
    Profile luôn là PRIVATE - không có API nào cho phép xem profile người khác.
    """
    user = UserSerializer(read_only=True)
    language_display = serializers.CharField(source='get_target_language_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    skill_display = serializers.CharField(source='get_skill_focus_display', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'avatar', 'avatar_url',
            'target_language', 'language_display',
            'level', 'level_display',
            'skill_focus', 'skill_display',
            'updated_at'
        ]
        # Đã bỏ is_public vì tất cả profile đều private
        read_only_fields = ['id', 'updated_at']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


# ĐÃ XÓA: PublicUserProfileSerializer, UserProfileListSerializer
# Lý do: Thông tin người dùng luôn phải private
# Không ai được xem profile của người khác


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer cho Resource model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    resource_type_name = serializers.CharField(source='resource_type.name', read_only=True)
    file_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    youtube_embed_url = serializers.SerializerMethodField()
    is_video = serializers.BooleanField(read_only=True)
    is_downloadable = serializers.BooleanField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'slug', 'description',
            'category', 'category_name',
            'resource_type', 'resource_type_name',
            'file', 'file_url',
            'youtube_url', 'youtube_embed_url',
            'cover_image', 'cover_url',
            'author', 'is_active', 'is_featured',
            'view_count', 'download_count',
            'is_video', 'is_downloadable',
            'tags',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'view_count', 'download_count', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_cover_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
    def get_youtube_embed_url(self, obj):
        return obj.get_youtube_embed_url()


class ResourceListSerializer(serializers.ModelSerializer):
    """Serializer cho danh sách Resource (nhẹ hơn)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    resource_type_name = serializers.CharField(source='resource_type.name', read_only=True)
    cover_url = serializers.SerializerMethodField()
    is_video = serializers.BooleanField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'slug',
            'category', 'category_name',
            'resource_type', 'resource_type_name',
            'cover_url', 'author', 'is_featured',
            'view_count', 'download_count',
            'is_video', 'tags', 'created_at'
        ]
    
    def get_cover_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer để đăng ký user mới"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    target_language = serializers.ChoiceField(choices=UserProfile.LANGUAGE_CHOICES, required=False)
    level = serializers.ChoiceField(choices=UserProfile.LEVEL_CHOICES, required=False)
    skill_focus = serializers.ChoiceField(choices=UserProfile.SKILL_CHOICES, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 
                  'first_name', 'last_name', 'target_language', 'level', 'skill_focus']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Mật khẩu không khớp"})
        return data
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email đã được sử dụng")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        target_language = validated_data.pop('target_language', 'en')
        level = validated_data.pop('level', 'A1')
        skill_focus = validated_data.pop('skill_focus', 'all')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Update or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.target_language = target_language
        profile.level = level
        profile.skill_focus = skill_focus
        profile.save()
        
        return user


# ============================================
# Navigation Serializers
# ============================================

from core.models import NavigationLink


class NavigationLinkChildSerializer(serializers.ModelSerializer):
    """Serializer cho submenu items"""
    is_external = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NavigationLink
        fields = [
            'id', 'name', 'name_vi', 'name_en', 'name_de',
            'url', 'icon', 'open_in_new_tab', 'is_external',
            'is_coming_soon', 'badge_text', 'order'
        ]


class NavigationLinkSerializer(serializers.ModelSerializer):
    """Serializer cho NavigationLink model — bao gồm children cho dropdown"""
    children = NavigationLinkChildSerializer(many=True, read_only=True)
    is_external = serializers.BooleanField(read_only=True)
    has_children = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NavigationLink
        fields = [
            'id', 'name', 'name_vi', 'name_en', 'name_de',
            'url', 'icon', 'location', 'footer_section',
            'open_in_new_tab', 'is_external', 'is_coming_soon',
            'badge_text', 'has_children', 'order', 'children'
        ]


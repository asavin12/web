"""
API Views cho UnstressVN
Sử dụng Django REST Framework
"""

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from accounts.models import UserProfile
from resources.models import Resource, Category, RESOURCE_TYPE_CHOICES

from .serializers import (
    UserSerializer, UserProfileSerializer,
    ResourceSerializer, ResourceListSerializer,
    UserRegistrationSerializer
)


# Custom pagination class that supports page_size query parameter
class FlexiblePageNumberPagination(PageNumberPagination):
    """Pagination class that allows custom page_size from query params"""
    page_size = 20  # default
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission: chỉ owner mới có thể edit"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if obj has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        return False


# Custom throttle class cho login
from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """Giới hạn số lần đăng nhập để chống brute force"""
    scope = 'login'


# ============ Authentication APIs ============

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    API đăng nhập, trả về token.
    Rate limited: 5 requests/minute để chống brute force.
    """
    # Apply throttle manually for function-based view
    throttle = LoginRateThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {'error': 'Quá nhiều lần thử đăng nhập. Vui lòng đợi 1 phút.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Vui lòng cung cấp username và password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    
    return Response(
        {'error': 'Thông tin đăng nhập không chính xác'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API đăng xuất, xóa token"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Đã đăng xuất thành công'})
    except Exception:
        return Response({'message': 'Đã đăng xuất'})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """API đăng ký tài khoản mới"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'message': 'Đăng ký thành công!'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    """API đổi mật khẩu"""
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'detail': 'Vui lòng cung cấp mật khẩu cũ và mới'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    if not user.check_password(old_password):
        return Response(
            {'old_password': ['Mật khẩu hiện tại không đúng']},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'new_password': ['Mật khẩu mới phải có ít nhất 8 ký tự']},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Đổi mật khẩu thành công'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    """API lấy thông tin user hiện tại"""
    serializer = UserProfileSerializer(
        request.user.profile,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_admin_access(request):
    """
    API lấy URL để truy cập admin panel.
    CHỈ cho phép superuser hoặc staff truy cập.
    Trả về URL với secret key và auth token để vào admin gateway.
    """
    from core.models import APIKey
    
    user = request.user
    
    # Staff hoặc superuser mới được truy cập
    if not user.is_staff:
        return Response(
            {'error': 'Không có quyền truy cập'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Lấy admin secret key từ database (APIKey model)
    admin_secret_key = APIKey.get_key('admin_secret_key')
    
    # Nếu chưa có key, tự động tạo
    if not admin_secret_key:
        created_keys = APIKey.create_default_keys()
        admin_secret_key = APIKey.get_key('admin_secret_key')
    
    if not admin_secret_key:
        return Response(
            {'error': 'Admin key chưa được cấu hình. Vui lòng tạo key "admin_secret_key" trong Admin > API Keys'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Lấy auth token của user
    try:
        token = Token.objects.get(user=user)
        auth_token = token.key
    except Token.DoesNotExist:
        # Tự động tạo token nếu chưa có
        token = Token.objects.create(user=user)
        auth_token = token.key
    
    # Luôn qua admin-gateway để set session đúng cách
    admin_url = f"/admin-gateway/?key={admin_secret_key}&token={auth_token}"
    
    return Response({
        'admin_url': admin_url,
        'message': 'URL này sẽ hết hạn sau 30 phút sử dụng'
    })


# ============ Resource ViewSet ============

class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet cho Resource (chỉ đọc - admin quản lý qua Django Admin)
    GET /api/resources/ - Danh sách tài liệu
    GET /api/resources/{slug}/ - Chi tiết tài liệu
    POST /api/resources/{slug}/download/ - Track download
    """
    queryset = Resource.objects.filter(is_active=True).select_related('category').order_by('-created_at')
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FlexiblePageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'resource_type', 'is_featured']
    search_fields = ['title', 'description', 'author']
    ordering_fields = ['created_at', 'download_count', 'view_count', 'title']
    lookup_field = 'slug'  # Use slug instead of pk for detail views
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ResourceListSerializer
        return ResourceSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Tăng view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def download(self, request, slug=None):
        """Endpoint để track download"""
        resource = self.get_object()
        resource.download_count += 1
        resource.save(update_fields=['download_count'])
        
        serializer = ResourceSerializer(resource, context={'request': request})
        return Response({
            'message': 'Download tracked',
            'file_url': serializer.data.get('file_url'),
            'download_count': resource.download_count
        })


# ============ UserProfile - CHỈ CHO CHÍNH MÌNH ============
# Đã xóa UserProfileViewSet - không ai được xem profile của người khác


class MyProfileView(generics.RetrieveUpdateAPIView):
    """
    API để xem và cập nhật profile của user hiện tại
    GET /api/my-profile/
    PUT/PATCH /api/my-profile/
    
    Bảo mật: Chỉ user đã đăng nhập mới có thể truy cập profile của CHÍNH MÌNH
    Không có API nào cho phép xem profile của người khác
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile


# ============ Utility APIs ============

@api_view(['GET'])
@permission_classes([AllowAny])
def api_choices(request):
    """API trả về các choices để dùng trong forms"""
    # Get categories from database
    categories = [{'value': str(cat.id), 'label': cat.name} for cat in Category.objects.all()]
    # Resource types as array
    resource_types = [{'value': k, 'label': v} for k, v in RESOURCE_TYPE_CHOICES]
    
    return Response({
        'languages': [{'value': k, 'label': v} for k, v in UserProfile.LANGUAGE_CHOICES],
        'levels': [{'value': k, 'label': v} for k, v in UserProfile.LEVEL_CHOICES],
        'skills': [{'value': k, 'label': v} for k, v in UserProfile.SKILL_CHOICES],
        'resource_categories': categories,
        'resource_types': resource_types,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_stats(request):
    """API trả về thống kê bài viết - tập trung vào nội dung bài viết"""
    from core.models import Video
    from knowledge.models import KnowledgeArticle
    from news.models import Article as NewsArticle
    from django.db.models import Sum
    from datetime import timedelta
    from django.utils import timezone
    
    # Thống kê bài viết (Knowledge + News)
    total_knowledge = KnowledgeArticle.objects.filter(is_published=True).count()
    total_news = NewsArticle.objects.filter(is_published=True).count()
    
    # Tổng lượt xem bài viết
    knowledge_views = KnowledgeArticle.objects.filter(is_published=True).aggregate(
        total=Sum('view_count'))['total'] or 0
    news_views = NewsArticle.objects.filter(is_published=True).aggregate(
        total=Sum('view_count'))['total'] or 0
    total_views = knowledge_views + news_views
    
    # Bài viết mới trong 7 ngày
    week_ago = timezone.now() - timedelta(days=7)
    new_knowledge = KnowledgeArticle.objects.filter(is_published=True, created_at__gte=week_ago).count()
    new_news = NewsArticle.objects.filter(is_published=True, created_at__gte=week_ago).count()
    
    # Tổng lượt tải tài liệu
    total_downloads = Resource.objects.filter(is_active=True).aggregate(
        total=Sum('download_count'))['total'] or 0
    
    return Response({
        # Thống kê bài viết
        'total_articles': total_knowledge + total_news,
        'total_views': total_views,
        'new_articles': new_knowledge + new_news,
        'total_downloads': total_downloads,
        # Legacy fields
        'resources': Resource.objects.filter(is_active=True).count(),
        'videos': Video.objects.filter(is_active=True).count(),
        'knowledge': total_knowledge,
        'news': total_news,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def video_list(request):
    """API lấy danh sách video từ core.Video model"""
    from core.models import Video
    from django.db.models import Q
    
    queryset = Video.objects.filter(is_active=True)
    
    # Filter theo ngôn ngữ
    language = request.GET.get('language')
    if language and language != 'all':
        queryset = queryset.filter(language=language)
    
    # Filter theo trình độ
    level = request.GET.get('level')
    if level and level != 'all':
        queryset = queryset.filter(level=level)
    
    # Tìm kiếm theo từ khóa
    search = request.GET.get('q')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    queryset = queryset.order_by('-is_featured', 'order', '-created_at')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 12))
    total = queryset.count()
    
    start = (page - 1) * page_size
    end = start + page_size
    videos = queryset[start:end]
    
    # Serialize
    data = []
    for video in videos:
        data.append({
            'id': video.pk,
            'slug': video.slug,
            'title': video.title,
            'description': video.description[:200] if video.description else '',
            'youtube_id': video.youtube_id,
            'youtube_url': video.youtube_url,
            'embed_url': video.embed_url,
            'thumbnail': video.thumbnail or f"https://img.youtube.com/vi/{video.youtube_id}/hqdefault.jpg",
            'duration': video.duration,
            'language': video.language,
            'language_display': video.get_language_display(),
            'level': video.level,
            'level_display': video.get_level_display(),
            'view_count': video.view_count,
            'is_featured': video.is_featured,
            'created_at': video.created_at.strftime('%Y-%m-%d') if video.created_at else '',
        })
    
    return Response({
        'results': data,
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'language_choices': Video.LANGUAGE_CHOICES,
        'level_choices': Video.LEVEL_CHOICES,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def video_detail(request, slug):
    """API lấy chi tiết video"""
    from core.models import Video
    from django.shortcuts import get_object_or_404
    
    video = get_object_or_404(Video, slug=slug, is_active=True)
    
    # Tăng view count
    video.view_count += 1
    video.save(update_fields=['view_count'], auto_fetch_youtube=False)
    
    data = {
        'id': video.pk,
        'slug': video.slug,
        'title': video.title,
        'description': video.description,
        'youtube_id': video.youtube_id,
        'youtube_url': video.youtube_url,
        'embed_url': video.embed_url,
        'thumbnail': video.thumbnail or f"https://img.youtube.com/vi/{video.youtube_id}/hqdefault.jpg",
        'duration': video.duration,
        'language': video.language,
        'language_display': video.get_language_display(),
        'level': video.level,
        'level_display': video.get_level_display(),
        'view_count': video.view_count,
        'is_featured': video.is_featured,
        'bookmark_count': video.bookmark_count,
        'created_at': video.created_at.strftime('%Y-%m-%d') if video.created_at else '',
    }
    
    # Check bookmark status nếu user đã login
    if request.user.is_authenticated:
        data['is_bookmarked'] = video.is_bookmarked_by(request.user)
    
    return Response(data)


# ============================================
# Navigation API
# ============================================

from core.models import NavigationLink
from .serializers import NavigationLinkSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def navigation_links(request):
    """
    API lấy tất cả navigation links cho frontend
    
    Returns:
        navbar: list các link cho navbar
        footer: dict các link cho footer, grouped by section
    """
    # Lấy navbar links
    navbar_links = NavigationLink.objects.filter(
        is_active=True,
        location__in=['navbar', 'both'],
        parent__isnull=True
    ).prefetch_related('children').order_by('order')
    
    # Lấy footer links
    footer_links = NavigationLink.objects.filter(
        is_active=True,
        location__in=['footer', 'both'],
        parent__isnull=True
    ).order_by('footer_section', 'order')
    
    # Group footer links by section
    footer_grouped = {}
    for link in footer_links:
        section = link.footer_section or 'other'
        if section not in footer_grouped:
            footer_grouped[section] = []
        footer_grouped[section].append(NavigationLinkSerializer(link).data)
    
    return Response({
        'navbar': NavigationLinkSerializer(navbar_links, many=True).data,
        'footer': footer_grouped
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def contact_submit(request):
    """
    API endpoint để nhận form liên hệ từ frontend.
    Gửi email thông báo tới admin.
    """
    from django.core.mail import send_mail
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError as DjangoValidationError

    name = request.data.get('name', '').strip()
    email = request.data.get('email', '').strip()
    subject = request.data.get('subject', '').strip()
    message = request.data.get('message', '').strip()

    # Validate required fields
    errors = {}
    if not name:
        errors['name'] = 'Vui lòng nhập họ tên.'
    if not email:
        errors['email'] = 'Vui lòng nhập email.'
    else:
        try:
            validate_email(email)
        except DjangoValidationError:
            errors['email'] = 'Email không hợp lệ.'
    if not subject:
        errors['subject'] = 'Vui lòng nhập tiêu đề.'
    if not message:
        errors['message'] = 'Vui lòng nhập nội dung.'

    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # Send email notification to admin
    try:
        admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'unstressvn@gmail.com')
        send_mail(
            subject=f'[UnstressVN Contact] {subject}',
            message=f'Từ: {name} <{email}>\n\nTiêu đề: {subject}\n\n{message}',
            from_email=admin_email,
            recipient_list=[admin_email],
            fail_silently=True,
        )
    except Exception:
        pass  # Don't fail if email sending fails

    return Response({
        'message': 'Cảm ơn bạn đã liên hệ! Chúng tôi sẽ phản hồi sớm nhất có thể.'
    }, status=status.HTTP_200_OK)

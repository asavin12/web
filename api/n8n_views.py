"""
N8N Automation API Views
Cho phép n8n tự động đăng bài lên website qua API
Xác thực bằng API Key (header: X-API-Key)
API Keys được lưu trong database (core.models.APIKey)

Image Support:
- cover_image_url: URL ảnh bìa (sẽ auto download, convert WebP, tạo responsive sizes)
- Nếu không có ảnh, sẽ tự động tạo placeholder image từ title
- Hỗ trợ multipart/form-data để upload ảnh trực tiếp (field: cover_image)
"""

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from core.image_utils import (
    download_image_from_url, convert_to_webp, generate_placeholder_image,
    generate_image_filename
)


# ============ Custom Authentication ============

import logging
n8n_logger = logging.getLogger('n8n_api')


class APIKeyAuthentication(BaseAuthentication):
    """
    Xác thực bằng API Key trong header X-API-Key.
    Hỗ trợ cả header chuẩn và nhiều format n8n hay dùng.
    API Key được lưu trong database (core.models.APIKey).
    """
    
    def authenticate(self, request):
        from core.models import APIKey
        
        # Hỗ trợ nhiều header format mà n8n có thể gửi
        api_key = (
            request.META.get('HTTP_X_API_KEY')
            or request.headers.get('X-API-Key')
            or request.headers.get('X-Api-Key')
            or request.headers.get('Api-Key')
        )
        
        # Fallback: check Authorization: Bearer <key>
        if not api_key:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:].strip()
        
        if not api_key:
            n8n_logger.debug(f'No API key in request to {request.path}')
            return None  # No API key provided, skip this auth
        
        # Kiểm tra key từ database
        if not APIKey.verify_key('n8n_api_key', api_key, request=request):
            n8n_logger.warning(f'Invalid API key attempt: {api_key[:8]}... from {request.META.get("REMOTE_ADDR")}')
            raise AuthenticationFailed('API Key không hợp lệ hoặc đã hết hạn')
        
        # Return bot user for automation — atomic get_or_create to avoid race condition
        bot_user, created = User.objects.get_or_create(
            username='automation_bot',
            defaults={'email': 'unstressvn@gmail.com', 'is_staff': True}
        )
        if created:
            n8n_logger.info('Created automation_bot user')
        
        return (bot_user, None)


def safe_truncate(value, max_length, default=''):
    """Truncate string field to max_length, preventing DB DataError."""
    if not value:
        return default
    value = str(value).strip()
    return value[:max_length] if len(value) > max_length else value


def vietnamese_slugify(text, max_length=250):
    """
    Chuyển đổi text tiếng Việt sang slug
    """
    # Bảng chuyển đổi ký tự tiếng Việt
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
    }
    
    # Convert uppercase variants
    text = text.lower()
    result = ''
    for char in text:
        result += vietnamese_map.get(char, char)
    
    slug = slugify(result)
    return slug[:max_length]


# ============ SEO Content Validation ============

def validate_seo_content(data, strict=True):
    """
    Kiểm tra nội dung bài viết có tuân thủ form chuẩn SEO hay không.
    Tham chiếu: docs/SEO_CONTENT_TEMPLATE.md
    
    Args:
        data: dict chứa các trường bài viết
        strict: True = trả lỗi nếu vi phạm, False = chỉ cảnh báo
    
    Returns:
        (is_valid: bool, warnings: list[str], errors: list[str])
    """
    import re
    
    warnings = []
    errors = []
    
    title = data.get('title', '')
    content = data.get('content', '')
    excerpt = data.get('excerpt', '')
    meta_title = data.get('meta_title', '')
    meta_description = data.get('meta_description', '')
    meta_keywords = data.get('meta_keywords', '')
    
    # --- Title validation ---
    if len(title) < 10:
        errors.append(f'title quá ngắn ({len(title)} ký tự, tối thiểu 10)')
    elif len(title) < 40:
        warnings.append(f'title nên dài 40-65 ký tự (hiện tại: {len(title)})')
    elif len(title) > 65:
        warnings.append(f'title quá dài ({len(title)} ký tự, tối ưu 40-65)')
    
    # --- Content validation ---
    if not content:
        errors.append('content không được để trống')
    else:
        # Đếm số từ (loại bỏ HTML tags)
        text_only = re.sub(r'<[^>]+>', ' ', content)
        word_count = len(text_only.split())
        
        if word_count < 100:
            errors.append(f'content quá ngắn ({word_count} từ, tối thiểu 600)')
        elif word_count < 600:
            warnings.append(f'content nên dài ≥ 600 từ (hiện tại: {word_count} từ)')
        
        # Kiểm tra H1 (KHÔNG được dùng)
        if re.search(r'<h1[\s>]', content, re.IGNORECASE):
            errors.append('content KHÔNG được chứa thẻ <h1> (đã có title)')
        
        # Kiểm tra H2 (tối thiểu 3)
        h2_count = len(re.findall(r'<h2[\s>]', content, re.IGNORECASE))
        if h2_count == 0:
            errors.append('content phải có ít nhất 3 thẻ <h2> (hiện tại: 0)')
        elif h2_count < 3:
            warnings.append(f'content nên có ít nhất 3 thẻ <h2> (hiện tại: {h2_count})')
        
        # Kiểm tra H2 có id (cho anchor links)
        h2_with_id = len(re.findall(r'<h2\s+id=', content, re.IGNORECASE))
        if h2_count > 0 and h2_with_id < h2_count:
            warnings.append(f'Chỉ {h2_with_id}/{h2_count} thẻ H2 có id="" (tối ưu anchor link)')
        
        # Kiểm tra danh sách (tối thiểu 1)
        has_list = bool(re.search(r'<[uo]l[\s>]', content, re.IGNORECASE))
        if not has_list:
            warnings.append('content nên có ít nhất 1 danh sách (<ul> hoặc <ol>)')
        
        # Kiểm tra kết luận
        has_conclusion = bool(re.search(r'<h2[^>]*>.*?(kết luận|conclusion|tổng kết)', content, re.IGNORECASE))
        if not has_conclusion:
            warnings.append('content nên có phần kết luận (<h2>Kết luận</h2>)')
        
        # Kiểm tra inline styles (KHÔNG được dùng)
        if re.search(r'style\s*=\s*["\']', content, re.IGNORECASE):
            errors.append('content KHÔNG được chứa inline styles (style="...")')
        
        # Kiểm tra thẻ lỗi thời
        deprecated_tags = re.findall(r'<(font|center|marquee)\b', content, re.IGNORECASE)
        if deprecated_tags:
            errors.append(f'content chứa thẻ HTML lỗi thời: {", ".join(set(deprecated_tags))}')
        
        # Kiểm tra đoạn mở đầu (phải bắt đầu bằng <p>)
        content_stripped = content.strip()
        if not content_stripped.startswith('<p'):
            warnings.append('content nên bắt đầu bằng đoạn mở đầu <p> chứa từ khóa chính')
    
    # --- Excerpt validation ---
    if excerpt:
        if len(excerpt) < 40:
            warnings.append(f'excerpt quá ngắn ({len(excerpt)} ký tự, tối ưu 80-200)')
        elif len(excerpt) > 500:
            warnings.append(f'excerpt quá dài ({len(excerpt)} ký tự, tối ưu 80-200)')
    else:
        warnings.append('excerpt nên được cung cấp (80-200 ký tự)')
    
    # --- Meta Title ---
    if meta_title:
        if len(meta_title) > 60:
            warnings.append(f'meta_title quá dài ({len(meta_title)} ký tự, tối ưu 50-60)')
    else:
        warnings.append('meta_title nên được cung cấp (50-60 ký tự)')
    
    # --- Meta Description ---
    if meta_description:
        if len(meta_description) < 80:
            warnings.append(f'meta_description quá ngắn ({len(meta_description)} ký tự, tối ưu 120-155)')
        elif len(meta_description) > 160:
            warnings.append(f'meta_description quá dài ({len(meta_description)} ký tự, tối ưu 120-155)')
    else:
        warnings.append('meta_description nên được cung cấp (120-155 ký tự)')
    
    # --- Meta Keywords ---
    if meta_keywords:
        keywords = [k.strip() for k in meta_keywords.split(',') if k.strip()]
        if len(keywords) < 3:
            warnings.append(f'meta_keywords nên có 3-7 từ khóa (hiện tại: {len(keywords)})')
        elif len(keywords) > 10:
            warnings.append(f'meta_keywords quá nhiều ({len(keywords)}, tối ưu 3-7)')
    else:
        warnings.append('meta_keywords nên được cung cấp (3-7 từ khóa)')
    
    is_valid = len(errors) == 0
    return is_valid, warnings, errors


def process_article_image(request, slug, upload_to='news/covers/'):
    """
    Process cover image for article from n8n request.
    Supports 3 methods (in priority order):
    1. Direct file upload (multipart/form-data, field: cover_image)
    2. Image URL download (JSON field: cover_image_url)  
    3. Auto-generated placeholder from title
    
    Args:
        request: DRF request object
        slug: Article slug for image naming
        upload_to: Directory to store images (e.g., 'news/covers/')
        
    Returns:
        (ContentFile or None, image_source: str)
        image_source: 'upload', 'url', 'placeholder', or 'none'
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Method 1: Direct file upload
    cover_file = request.FILES.get('cover_image')
    if cover_file:
        logger.info(f"Processing uploaded cover image for '{slug}'")
        webp = convert_to_webp(cover_file, quality='high', slug=slug, suffix='cover')
        if webp:
            return webp, 'upload'
    
    # Method 2: Download from URL
    cover_url = request.data.get('cover_image_url')
    if cover_url:
        logger.info(f"Downloading cover image from URL for '{slug}': {cover_url}")
        img_buffer, original_name = download_image_from_url(cover_url)
        if img_buffer:
            webp = convert_to_webp(img_buffer, quality='high', slug=slug, suffix='cover')
            if webp:
                return webp, 'url'
            logger.warning(f"Could not convert downloaded image to WebP for '{slug}'")
        else:
            logger.warning(f"Could not download image from {cover_url} for '{slug}'")
    
    # Method 3: Generate placeholder
    title = request.data.get('title', slug)
    auto_placeholder = request.data.get('auto_placeholder', True)
    if auto_placeholder:
        logger.info(f"Generating placeholder image for '{slug}'")
        placeholder = generate_placeholder_image(title)
        if placeholder:
            # Rename with proper slug
            filename = generate_image_filename(slug=slug, suffix='cover', ext='.webp')
            placeholder.name = filename
            return placeholder, 'placeholder'
    
    return None, 'none'


# ============ N8N API Endpoints ============

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_create_news_article(request):
    """
    Tạo bài viết News từ n8n (có hỗ trợ ảnh)
    
    Headers:
        X-API-Key: <N8N_API_KEY>
    
    Body (JSON hoặc multipart/form-data):
        {
            "title": "Tiêu đề bài viết",
            "content": "Nội dung HTML của bài viết",
            "excerpt": "Mô tả ngắn (tùy chọn)",
            "category": "slug-category hoặc id",
            "cover_image_url": "https://example.com/image.jpg (tùy chọn)",
            "auto_placeholder": true,
            "is_featured": false,
            "is_published": true,
            "meta_title": "SEO title (tùy chọn)",
            "meta_description": "SEO description (tùy chọn)",
            "meta_keywords": "keyword1, keyword2 (tùy chọn)"
        }
    
    Image support:
        - cover_image_url: URL ảnh bìa (auto download + convert WebP)
        - cover_image: File upload trực tiếp (multipart)
        - auto_placeholder: true (default) = tạo placeholder nếu không có ảnh
    
    Returns:
        {
            "success": true,
            "article": {...},
            "image_source": "url|upload|placeholder|none",
            "message": "Đã tạo bài viết thành công"
        }
    """
    from news.models import Article, Category
    
    # Validate required fields
    title = request.data.get('title')
    content = request.data.get('content')
    
    if not title:
        return Response(
            {'success': False, 'error': 'Thiếu trường "title"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not content:
        return Response(
            {'success': False, 'error': 'Thiếu trường "content"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate SEO content (tham chiếu: docs/SEO_CONTENT_TEMPLATE.md)
    skip_validation = request.data.get('skip_seo_validation', False)
    seo_valid, seo_warnings, seo_errors = validate_seo_content(request.data)
    
    if not seo_valid and not skip_validation:
        return Response({
            'success': False,
            'error': 'Nội dung không đạt chuẩn SEO. Xem docs/SEO_CONTENT_TEMPLATE.md',
            'seo_errors': seo_errors,
            'seo_warnings': seo_warnings,
            'hint': 'Gửi skip_seo_validation=true để bỏ qua kiểm tra (không khuyến nghị)'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create category
    category_input = request.data.get('category')
    category = None
    
    if category_input:
        # Try to find by slug first, then by id
        try:
            if isinstance(category_input, int) or category_input.isdigit():
                category = Category.objects.get(id=int(category_input))
            else:
                category = Category.objects.get(slug=category_input)
        except Category.DoesNotExist:
            # Create new category
            category = Category.objects.create(
                name=category_input,
                slug=vietnamese_slugify(category_input)
            )
    
    # Generate unique slug
    base_slug = vietnamese_slugify(title)
    slug = base_slug
    counter = 1
    while Article.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Process cover image (download from URL, upload, or generate placeholder)
    cover_image, image_source = process_article_image(
        request, slug, upload_to='news/covers/'
    )
    
    # Create article — field truncation to prevent DataError
    try:
        article = Article.objects.create(
            title=safe_truncate(title, 255),
            slug=slug,
            content=content,
            excerpt=safe_truncate(request.data.get('excerpt', ''), 500),
            category=category,
            author=request.user,
            is_featured=request.data.get('is_featured', False),
            is_published=request.data.get('is_published', True),
            published_at=timezone.now() if request.data.get('is_published', True) else None,
            meta_title=safe_truncate(request.data.get('meta_title', ''), 70),
            meta_description=safe_truncate(request.data.get('meta_description', ''), 160),
            meta_keywords=safe_truncate(request.data.get('meta_keywords', ''), 255),
            # N8N tracking fields
            source='n8n',
            source_url=safe_truncate(request.data.get('source_url', ''), 200),
            source_id=safe_truncate(request.data.get('source_id', ''), 100),
            n8n_workflow_id=safe_truncate(request.data.get('workflow_id', ''), 50),
            n8n_execution_id=safe_truncate(request.data.get('execution_id', ''), 100),
            n8n_created_at=timezone.now(),
            is_ai_generated=request.data.get('is_ai_generated', False),
            ai_model=safe_truncate(request.data.get('ai_model', ''), 50),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create news article: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo bài viết: {type(e).__name__}: {str(e)[:500]}',
            'hint': 'Kiểm tra dữ liệu gửi từ n8n — có thể trường quá dài hoặc dữ liệu không hợp lệ'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Assign cover image after creation (triggers WebP conversion + responsive generation in save())
    if cover_image:
        try:
            article.cover_image = cover_image
            article.save()
        except Exception as e:
            n8n_logger.warning(f'Cover image save failed for article {article.id}: {e}')
            # Article was created OK, just no image — don't fail the whole request
    
    response_data = {
        'success': True,
        'article': {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'url': f'/tin-tuc/{article.slug}',
            'is_published': article.is_published,
            'created_at': article.created_at.isoformat(),
            'cover_image': article.cover_image.url if article.cover_image else None,
            'thumbnail': article.thumbnail.url if article.thumbnail else None,
            'has_responsive_images': bool(article.cover_image_srcset),
        },
        'image_source': image_source,
        'message': 'Đã tạo bài viết tin tức thành công'
    }
    
    # Đính kèm cảnh báo SEO (nếu có)
    if seo_warnings:
        response_data['seo_warnings'] = seo_warnings
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_create_knowledge_article(request):
    """
    Tạo bài viết Knowledge từ n8n (có hỗ trợ ảnh)
    
    Headers:
        X-API-Key: <N8N_API_KEY>
    
    Body (JSON hoặc multipart/form-data):
        {
            "title": "Tiêu đề bài viết",
            "content": "Nội dung HTML của bài viết",
            "excerpt": "Mô tả ngắn (tùy chọn)",
            "category": "slug-category hoặc id",
            "language": "de/en/all",
            "level": "A1/A2/B1/B2/C1/C2/all",
            "cover_image_url": "https://example.com/image.jpg (tùy chọn)",
            "auto_placeholder": true,
            "is_published": true,
            "meta_title": "SEO title (tùy chọn)",
            "meta_description": "SEO description (tùy chọn)",
            "meta_keywords": "keyword1, keyword2 (tùy chọn)"
        }
    
    Image support:
        - cover_image_url: URL ảnh bìa (auto download + convert WebP)
        - cover_image: File upload trực tiếp (multipart)
        - auto_placeholder: true (default) = tạo placeholder nếu không có ảnh
    
    Returns:
        {
            "success": true,
            "article": {...},
            "image_source": "url|upload|placeholder|none",
            "message": "Đã tạo bài viết thành công"
        }
    """
    from knowledge.models import KnowledgeArticle, Category
    
    # Validate required fields
    title = request.data.get('title')
    content = request.data.get('content')
    
    if not title:
        return Response(
            {'success': False, 'error': 'Thiếu trường "title"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not content:
        return Response(
            {'success': False, 'error': 'Thiếu trường "content"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate SEO content (tham chiếu: docs/SEO_CONTENT_TEMPLATE.md)
    skip_validation = request.data.get('skip_seo_validation', False)
    seo_valid, seo_warnings, seo_errors = validate_seo_content(request.data)
    
    if not seo_valid and not skip_validation:
        return Response({
            'success': False,
            'error': 'Nội dung không đạt chuẩn SEO. Xem docs/SEO_CONTENT_TEMPLATE.md',
            'seo_errors': seo_errors,
            'seo_warnings': seo_warnings,
            'hint': 'Gửi skip_seo_validation=true để bỏ qua kiểm tra (không khuyến nghị)'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create category
    category_input = request.data.get('category')
    category = None
    
    if category_input:
        try:
            if isinstance(category_input, int) or category_input.isdigit():
                category = Category.objects.get(id=int(category_input))
            else:
                category = Category.objects.get(slug=category_input)
        except Category.DoesNotExist:
            category = Category.objects.create(
                name=category_input,
                slug=vietnamese_slugify(category_input)
            )
    
    # Generate unique slug
    base_slug = vietnamese_slugify(title)
    slug = base_slug
    counter = 1
    while KnowledgeArticle.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Validate language and level
    language = request.data.get('language', 'all')
    if language not in ['de', 'en', 'all']:
        language = 'all'
    
    level = request.data.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'
    
    # Process cover image
    cover_image, image_source = process_article_image(
        request, slug, upload_to='knowledge/covers/'
    )
    
    # Create article — field truncation to prevent DataError
    try:
        article = KnowledgeArticle.objects.create(
            title=safe_truncate(title, 255),
            slug=slug,
            content=content,
            excerpt=safe_truncate(request.data.get('excerpt', ''), 500),
            category=category,
            language=language,
            level=level,
            author=request.user,
            is_featured=request.data.get('is_featured', False),
            is_published=request.data.get('is_published', True),
            published_at=timezone.now() if request.data.get('is_published', True) else None,
            meta_title=safe_truncate(request.data.get('meta_title', ''), 70),
            meta_description=safe_truncate(request.data.get('meta_description', ''), 160),
            meta_keywords=safe_truncate(request.data.get('meta_keywords', ''), 255),
            # N8N tracking fields
            source='n8n',
            source_url=safe_truncate(request.data.get('source_url', ''), 200),
            source_id=safe_truncate(request.data.get('source_id', ''), 100),
            n8n_workflow_id=safe_truncate(request.data.get('workflow_id', ''), 50),
            n8n_execution_id=safe_truncate(request.data.get('execution_id', ''), 100),
            n8n_created_at=timezone.now(),
            is_ai_generated=request.data.get('is_ai_generated', False),
            ai_model=safe_truncate(request.data.get('ai_model', ''), 50),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create knowledge article: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo bài viết kiến thức: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Assign cover image after creation (triggers WebP conversion + responsive generation)
    if cover_image:
        try:
            article.cover_image = cover_image
            article.save()
        except Exception as e:
            n8n_logger.warning(f'Cover image save failed for knowledge article {article.id}: {e}')
    
    response_data = {
        'success': True,
        'article': {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'language': article.language,
            'level': article.level,
            'url': f'/kien-thuc/{article.slug}',
            'is_published': article.is_published,
            'created_at': article.created_at.isoformat(),
            'cover_image': article.cover_image.url if article.cover_image else None,
            'thumbnail': article.thumbnail.url if article.thumbnail else None,
            'has_responsive_images': bool(article.cover_image_srcset),
        },
        'image_source': image_source,
        'message': 'Đã tạo bài viết kiến thức thành công'
    }
    
    if seo_warnings:
        response_data['seo_warnings'] = seo_warnings
    
    return Response(response_data, status=status.HTTP_201_CREATED)


# ============ N8N UPDATE Endpoints ============

def _update_article(request, article, model_name, url_prefix):
    """
    Helper chung để cập nhật bài viết (News hoặc Knowledge).
    Trả về Response.
    """
    data = request.data
    updated_fields = []

    # Updatable text fields — with truncation for safety
    text_field_limits = {
        'title': ('title', 255),
        'content': ('content', None),  # TextField, no limit
        'excerpt': ('excerpt', 500),
        'meta_title': ('meta_title', 70),
        'meta_description': ('meta_description', 160),
        'meta_keywords': ('meta_keywords', 255),
    }
    for param, (field, max_len) in text_field_limits.items():
        if param in data:
            value = data[param]
            if max_len and value:
                value = safe_truncate(value, max_len)
            setattr(article, field, value)
            updated_fields.append(field)

    # Boolean fields
    if 'is_featured' in data:
        article.is_featured = data['is_featured']
        updated_fields.append('is_featured')

    if 'is_published' in data:
        was_published = article.is_published
        article.is_published = data['is_published']
        updated_fields.append('is_published')
        # Auto-set published_at khi publish lần đầu
        if data['is_published'] and not was_published and not article.published_at:
            article.published_at = timezone.now()
            updated_fields.append('published_at')

    # Category
    if 'category' in data:
        category_input = data['category']
        if category_input:
            if model_name == 'news':
                from news.models import Category
            else:
                from knowledge.models import Category
            try:
                if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
                    article.category = Category.objects.get(id=int(category_input))
                else:
                    article.category = Category.objects.get(slug=category_input)
                updated_fields.append('category')
            except Category.DoesNotExist:
                return Response(
                    {'success': False, 'error': f'Category "{category_input}" không tồn tại'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            article.category = None
            updated_fields.append('category')

    # Knowledge-specific fields
    if model_name == 'knowledge':
        if 'language' in data:
            language = data['language']
            if language in ['de', 'en', 'all']:
                article.language = language
                updated_fields.append('language')
        if 'level' in data:
            level = data['level']
            if level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
                article.level = level
                updated_fields.append('level')

    # Slug update (nếu title thay đổi và yêu cầu regenerate)
    if 'regenerate_slug' in data and data['regenerate_slug'] and 'title' in data:
        Model = type(article)
        base_slug = vietnamese_slugify(data['title'])
        slug = base_slug
        counter = 1
        while Model.objects.filter(slug=slug).exclude(id=article.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        article.slug = slug
        updated_fields.append('slug')

    # N8N tracking fields update
    n8n_fields = {
        'source_url': 'source_url',
        'source_id': 'source_id',
        'workflow_id': 'n8n_workflow_id',
        'execution_id': 'n8n_execution_id',
        'is_ai_generated': 'is_ai_generated',
        'ai_model': 'ai_model',
    }
    for param, field in n8n_fields.items():
        if param in data:
            setattr(article, field, data[param])
            updated_fields.append(field)

    # SEO validation (optional)
    skip_validation = data.get('skip_seo_validation', True)  # Default skip cho update
    if not skip_validation:
        # Merge existing data with updates for validation
        validate_data = {
            'title': article.title,
            'content': article.content,
            'excerpt': article.excerpt,
            'meta_title': article.meta_title,
            'meta_description': article.meta_description,
        }
        seo_valid, seo_warnings, seo_errors = validate_seo_content(validate_data)
        if not seo_valid:
            return Response({
                'success': False,
                'error': 'Nội dung không đạt chuẩn SEO',
                'seo_errors': seo_errors,
                'seo_warnings': seo_warnings,
            }, status=status.HTTP_400_BAD_REQUEST)

    # Cover image update
    image_source = 'unchanged'
    if 'cover_image' in request.FILES or 'cover_image_url' in data:
        cover_image, image_source = process_article_image(
            request, article.slug,
            upload_to=f'{model_name}/covers/'
        )
        if cover_image:
            article.cover_image = cover_image
            updated_fields.append('cover_image')

    if not updated_fields:
        return Response(
            {'success': False, 'error': 'Không có trường nào được cập nhật'},
            status=status.HTTP_400_BAD_REQUEST
        )

    article.save()

    response_data = {
        'success': True,
        'article': {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'url': f'/{url_prefix}/{article.slug}',
            'is_published': article.is_published,
            'is_featured': article.is_featured,
            'updated_at': article.updated_at.isoformat(),
            'cover_image': article.cover_image.url if article.cover_image else None,
        },
        'updated_fields': updated_fields,
        'image_source': image_source,
        'message': f'Đã cập nhật bài viết {model_name} thành công',
    }

    return Response(response_data, status=status.HTTP_200_OK)


def _find_article(Model, identifier):
    """
    Tìm bài viết bằng slug, id, hoặc source_id (n8n).
    Trả về (article, None) hoặc (None, error_response).
    """
    article = None

    # Try by slug
    article = Model.objects.filter(slug=identifier).first()
    if article:
        return article, None

    # Try by id
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        article = Model.objects.filter(id=int(identifier)).first()
        if article:
            return article, None

    # Try by source_id (n8n tracking)
    article = Model.objects.filter(source='n8n', source_id=identifier).first()
    if article:
        return article, None

    return None, Response(
        {'success': False, 'error': f'Không tìm thấy bài viết với identifier "{identifier}"'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['PUT', 'PATCH'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_update_news_article(request, identifier):
    """
    Cập nhật bài viết News từ n8n

    URL: /api/v1/n8n/news/<identifier>/
    identifier: slug, id, hoặc source_id

    Methods:
        PUT: Cập nhật toàn bộ
        PATCH: Cập nhật một phần

    Headers:
        X-API-Key: <N8N_API_KEY>

    Body (JSON hoặc multipart/form-data):
        {
            "title": "Tiêu đề mới (tùy chọn)",
            "content": "Nội dung mới (tùy chọn)",
            "excerpt": "Mô tả mới (tùy chọn)",
            "category": "slug-category hoặc id (tùy chọn)",
            "is_featured": true/false,
            "is_published": true/false,
            "cover_image_url": "URL ảnh mới (tùy chọn)",
            "meta_title": "SEO title mới",
            "meta_description": "SEO description mới",
            "meta_keywords": "keywords mới",
            "regenerate_slug": false,
            "skip_seo_validation": true
        }

    Returns:
        {
            "success": true,
            "article": {...},
            "updated_fields": ["title", "content", ...],
            "message": "Đã cập nhật bài viết thành công"
        }
    """
    from news.models import Article

    article, error = _find_article(Article, identifier)
    if error:
        return error

    return _update_article(request, article, 'news', 'tin-tuc')


@api_view(['PUT', 'PATCH'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_update_knowledge_article(request, identifier):
    """
    Cập nhật bài viết Knowledge từ n8n

    URL: /api/v1/n8n/knowledge/<identifier>/
    identifier: slug, id, hoặc source_id

    Methods:
        PUT: Cập nhật toàn bộ
        PATCH: Cập nhật một phần

    Headers:
        X-API-Key: <N8N_API_KEY>

    Body (JSON hoặc multipart/form-data):
        {
            "title": "Tiêu đề mới (tùy chọn)",
            "content": "Nội dung mới (tùy chọn)",
            "excerpt": "Mô tả mới (tùy chọn)",
            "category": "slug-category hoặc id (tùy chọn)",
            "language": "de/en/all (tùy chọn)",
            "level": "A1/A2/B1/B2/C1/C2/all (tùy chọn)",
            "is_featured": true/false,
            "is_published": true/false,
            "cover_image_url": "URL ảnh mới (tùy chọn)",
            "meta_title": "SEO title mới",
            "meta_description": "SEO description mới",
            "meta_keywords": "keywords mới",
            "regenerate_slug": false,
            "skip_seo_validation": true
        }

    Returns:
        {
            "success": true,
            "article": {...},
            "updated_fields": ["title", "content", "language", ...],
            "message": "Đã cập nhật bài viết thành công"
        }
    """
    from knowledge.models import KnowledgeArticle

    article, error = _find_article(KnowledgeArticle, identifier)
    if error:
        return error

    return _update_article(request, article, 'knowledge', 'kien-thuc')


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def n8n_create_resource(request):
    """
    Tạo tài liệu Resource từ n8n
    
    Headers:
        X-API-Key: <N8N_API_KEY>
    
    Body (JSON):
        {
            "title": "Tên tài liệu",
            "description": "Mô tả tài liệu",
            "category": "slug-category hoặc id",
            "resource_type": "ebook/pdf/audio/video/document/flashcard",
            "external_url": "https://drive.google.com/...",
            "youtube_url": "https://youtube.com/... (cho video)",
            "author": "Tác giả (tùy chọn)",
            "is_featured": false
        }
    
    Returns:
        {
            "success": true,
            "resource": {...},
            "message": "Đã tạo tài liệu thành công"
        }
    """
    from resources.models import Resource, Category
    
    # Validate required fields
    title = request.data.get('title')
    description = request.data.get('description')
    
    if not title:
        return Response(
            {'success': False, 'error': 'Thiếu trường "title"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not description:
        return Response(
            {'success': False, 'error': 'Thiếu trường "description"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create category
    category_input = request.data.get('category')
    category = None
    
    if category_input:
        try:
            if isinstance(category_input, int) or category_input.isdigit():
                category = Category.objects.get(id=int(category_input))
            else:
                category = Category.objects.get(slug=category_input)
        except Category.DoesNotExist:
            category = Category.objects.create(
                name=category_input,
                slug=vietnamese_slugify(category_input)
            )
    
    # Generate unique slug
    base_slug = vietnamese_slugify(title)
    slug = base_slug
    counter = 1
    while Resource.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Validate resource_type
    resource_type = request.data.get('resource_type', 'document')
    valid_types = ['ebook', 'book', 'pdf', 'audio', 'video', 'document', 'flashcard']
    if resource_type not in valid_types:
        resource_type = 'document'
    
    # Create resource — field truncation to prevent DataError
    try:
        resource = Resource.objects.create(
            title=safe_truncate(title, 200),
            slug=slug,
            description=description,
            category=category,
            resource_type=resource_type,
            external_url=safe_truncate(request.data.get('external_url', ''), 200),
            youtube_url=safe_truncate(request.data.get('youtube_url', ''), 200),
            author=safe_truncate(request.data.get('author', ''), 100),
            is_featured=request.data.get('is_featured', False),
            is_active=True,
            # N8N tracking fields
            source='n8n',
            source_url=safe_truncate(request.data.get('source_url', ''), 200),
            source_id=safe_truncate(request.data.get('source_id', ''), 100),
            n8n_workflow_id=safe_truncate(request.data.get('workflow_id', ''), 50),
            n8n_execution_id=safe_truncate(request.data.get('execution_id', ''), 100),
            n8n_created_at=timezone.now(),
            is_ai_generated=request.data.get('is_ai_generated', False),
            ai_model=safe_truncate(request.data.get('ai_model', ''), 50),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create resource: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo tài liệu: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': True,
        'resource': {
            'id': resource.id,
            'title': resource.title,
            'slug': resource.slug,
            'resource_type': resource.resource_type,
            'url': f'/tai-lieu/{resource.slug}',
            'created_at': resource.created_at.isoformat(),
        },
        'message': 'Đã tạo tài liệu thành công'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_get_categories(request):
    """
    Lấy danh sách categories cho n8n
    
    Query params:
        type: news/knowledge/resources
    
    Returns:
        {
            "success": true,
            "categories": [...]
        }
    """
    category_type = request.query_params.get('type', 'all')
    
    categories = []
    
    if category_type in ['news', 'all']:
        from news.models import Category as NewsCategory
        for cat in NewsCategory.objects.filter(is_active=True):
            categories.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'type': 'news'
            })
    
    if category_type in ['knowledge', 'all']:
        from knowledge.models import Category as KnowledgeCategory
        for cat in KnowledgeCategory.objects.filter(is_active=True):
            categories.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'type': 'knowledge'
            })
    
    if category_type in ['resources', 'all']:
        from resources.models import Category as ResourceCategory
        for cat in ResourceCategory.objects.all():
            categories.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'type': 'resources'
            })
    
    return Response({
        'success': True,
        'categories': categories
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def n8n_health_check(request):
    """
    Health check endpoint cho n8n
    Không cần authentication
    """
    return Response({
        'status': 'ok',
        'service': 'UnstressVN API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def n8n_create_video(request):
    """
    Tạo Video từ n8n
    
    Headers:
        X-API-Key: <N8N_API_KEY>
    
    Body (JSON):
        {
            "youtube_id": "Video ID hoặc URL YouTube",
            "title": "Tiêu đề (tùy chọn - auto fetch từ YouTube)",
            "description": "Mô tả (tùy chọn)",
            "language": "en/de/all",
            "level": "A1/A2/B1/B2/C1/C2/all",
            "is_featured": false,
            "source_url": "URL nguồn gốc",
            "source_id": "ID từ nguồn (để tránh duplicate)",
            "workflow_id": "N8N workflow ID",
            "execution_id": "N8N execution ID",
            "is_ai_generated": false,
            "ai_model": "Tên model AI (nếu có)"
        }
    
    Returns:
        {
            "success": true,
            "video": {...},
            "message": "Đã tạo video thành công"
        }
    """
    from core.models import Video
    from core.youtube import extract_youtube_id
    
    # Validate required fields
    youtube_input = request.data.get('youtube_id')
    
    if not youtube_input:
        return Response(
            {'success': False, 'error': 'Thiếu trường "youtube_id"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Extract YouTube ID
    youtube_id = extract_youtube_id(youtube_input)
    
    if not youtube_id:
        return Response(
            {'success': False, 'error': 'Không thể trích xuất YouTube ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check duplicate by youtube_id
    if Video.objects.filter(youtube_id=youtube_id).exists():
        existing = Video.objects.get(youtube_id=youtube_id)
        return Response({
            'success': True,
            'video': {
                'id': existing.id,
                'title': existing.title,
                'slug': existing.slug,
                'youtube_id': existing.youtube_id,
            },
            'message': 'Video đã tồn tại',
            'action': 'skipped'
        })
    
    # Check duplicate by source_id
    source_id = request.data.get('source_id')
    if source_id:
        existing = Video.objects.filter(source='n8n', source_id=source_id).first()
        if existing:
            return Response({
                'success': True,
                'video': {
                    'id': existing.id,
                    'title': existing.title,
                    'slug': existing.slug,
                },
                'message': 'Video đã tồn tại với source_id này',
                'action': 'skipped'
            })
    
    # Validate language and level
    language = request.data.get('language', 'en')
    if language not in ['de', 'en', 'all']:
        language = 'en'
    
    level = request.data.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'
    
    # Create video — field truncation to prevent DataError
    try:
        video = Video.objects.create(
            youtube_id=youtube_id,
            title=safe_truncate(request.data.get('title', ''), 255),
            description=request.data.get('description', ''),
            language=language,
            level=level,
            is_featured=request.data.get('is_featured', False),
            is_active=True,
            # N8N tracking fields
            source='n8n',
            source_url=safe_truncate(request.data.get('source_url', ''), 200),
            source_id=safe_truncate(source_id or '', 100),
            n8n_workflow_id=safe_truncate(request.data.get('workflow_id', ''), 50),
            n8n_execution_id=safe_truncate(request.data.get('execution_id', ''), 100),
            n8n_created_at=timezone.now(),
            is_ai_generated=request.data.get('is_ai_generated', False),
            ai_model=safe_truncate(request.data.get('ai_model', ''), 50),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create video: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo video: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': True,
        'video': {
            'id': video.id,
            'title': video.title,
            'slug': video.slug,
            'youtube_id': video.youtube_id,
            'youtube_url': video.youtube_url,
            'thumbnail': video.thumbnail,
            'url': f'/videos/{video.slug}',
            'created_at': video.created_at.isoformat(),
        },
        'message': 'Đã tạo video thành công',
        'action': 'created'
    }, status=status.HTTP_201_CREATED)


# ============================================================================
# LIST Endpoints — Cho n8n kiểm tra nội dung đã có
# ============================================================================

def _serialize_article(article, url_prefix):
    """Serialize cơ bản cho News/Knowledge article"""
    data = {
        'id': article.id,
        'title': article.title,
        'slug': article.slug,
        'url': f'/{url_prefix}/{article.slug}',
        'is_published': article.is_published,
        'is_featured': article.is_featured,
        'view_count': article.view_count,
        'created_at': article.created_at.isoformat(),
        'updated_at': article.updated_at.isoformat(),
        'category': article.category.slug if article.category else None,
        'cover_image': article.cover_image.url if article.cover_image else None,
        'source': getattr(article, 'source', ''),
        'source_id': getattr(article, 'source_id', ''),
    }
    if hasattr(article, 'language'):
        data['language'] = article.language
        data['level'] = article.level
    return data


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_list_news(request):
    """
    Danh sách bài viết News — cho n8n kiểm tra trước khi tạo

    GET /api/v1/n8n/news/list/
    Headers: X-API-Key: <key>
    Query params:
        - page (default: 1)
        - page_size (default: 20, max: 100)
        - category (slug)
        - is_published (true/false)
        - search (tìm trong title)
        - source (n8n / admin / ...)
    """
    from news.models import Article
    qs = Article.objects.select_related('category').order_by('-created_at')

    # Filters
    if request.query_params.get('category'):
        qs = qs.filter(category__slug=request.query_params['category'])
    if request.query_params.get('is_published'):
        qs = qs.filter(is_published=request.query_params['is_published'].lower() == 'true')
    if request.query_params.get('search'):
        qs = qs.filter(Q(title__icontains=request.query_params['search']))
    if request.query_params.get('source'):
        qs = qs.filter(source=request.query_params['source'])

    # Pagination
    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    total = qs.count()
    articles = qs[(page - 1) * page_size:page * page_size]

    return Response({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [_serialize_article(a, 'tin-tuc') for a in articles],
    })


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_list_knowledge(request):
    """
    Danh sách bài viết Knowledge

    GET /api/v1/n8n/knowledge/list/
    Headers: X-API-Key: <key>
    Query params:
        - page, page_size, category, is_published, search, source
        - language (de/en/all)
        - level (A1-C2/all)
    """
    from knowledge.models import KnowledgeArticle
    qs = KnowledgeArticle.objects.select_related('category').order_by('-created_at')

    if request.query_params.get('category'):
        qs = qs.filter(category__slug=request.query_params['category'])
    if request.query_params.get('is_published'):
        qs = qs.filter(is_published=request.query_params['is_published'].lower() == 'true')
    if request.query_params.get('search'):
        qs = qs.filter(Q(title__icontains=request.query_params['search']))
    if request.query_params.get('source'):
        qs = qs.filter(source=request.query_params['source'])
    if request.query_params.get('language'):
        qs = qs.filter(language=request.query_params['language'])
    if request.query_params.get('level'):
        qs = qs.filter(level=request.query_params['level'])

    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    total = qs.count()
    articles = qs[(page - 1) * page_size:page * page_size]

    return Response({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [_serialize_article(a, 'kien-thuc') for a in articles],
    })


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_list_resources(request):
    """
    Danh sách Resources

    GET /api/v1/n8n/resources/list/
    Headers: X-API-Key: <key>
    Query params:
        - page, page_size, category, search, source
        - resource_type (ebook/pdf/audio/video/document/flashcard)
    """
    from resources.models import Resource
    qs = Resource.objects.select_related('category').order_by('-created_at')

    if request.query_params.get('category'):
        qs = qs.filter(category__slug=request.query_params['category'])
    if request.query_params.get('search'):
        qs = qs.filter(Q(title__icontains=request.query_params['search']))
    if request.query_params.get('source'):
        qs = qs.filter(source=request.query_params['source'])
    if request.query_params.get('resource_type'):
        qs = qs.filter(resource_type=request.query_params['resource_type'])

    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    total = qs.count()
    resources = qs[(page - 1) * page_size:page * page_size]

    return Response({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [{
            'id': r.id,
            'title': r.title,
            'slug': r.slug,
            'resource_type': r.resource_type,
            'category': r.category.slug if r.category else None,
            'is_active': r.is_active,
            'is_featured': r.is_featured,
            'url': f'/tai-lieu/{r.slug}',
            'created_at': r.created_at.isoformat(),
            'source': getattr(r, 'source', ''),
            'source_id': getattr(r, 'source_id', ''),
        } for r in resources],
    })


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_list_tools(request):
    """
    Danh sách Tools

    GET /api/v1/n8n/tools/list/
    Headers: X-API-Key: <key>
    Query params:
        - page, page_size, category, search
        - tool_type (internal/external/embed/article)
        - language (en/de/all)
        - is_published (true/false)
    """
    from tools.models import Tool
    qs = Tool.objects.select_related('category').order_by('-created_at')

    if request.query_params.get('category'):
        qs = qs.filter(category__slug=request.query_params['category'])
    if request.query_params.get('search'):
        qs = qs.filter(Q(name__icontains=request.query_params['search']))
    if request.query_params.get('tool_type'):
        qs = qs.filter(tool_type=request.query_params['tool_type'])
    if request.query_params.get('language'):
        qs = qs.filter(language=request.query_params['language'])
    if request.query_params.get('is_published'):
        qs = qs.filter(is_published=request.query_params['is_published'].lower() == 'true')

    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    total = qs.count()
    tools = qs[(page - 1) * page_size:page * page_size]

    return Response({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [{
            'id': t.id,
            'name': t.name,
            'slug': t.slug,
            'tool_type': t.tool_type,
            'language': t.language,
            'category': t.category.slug if t.category else None,
            'is_published': t.is_published,
            'is_active': t.is_active,
            'url': f'/cong-cu/{t.slug}',
            'created_at': t.created_at.isoformat(),
        } for t in tools],
    })


@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
def n8n_list_videos(request):
    """
    Danh sách Videos (core.Video)

    GET /api/v1/n8n/videos/list/
    Headers: X-API-Key: <key>
    Query params:
        - page, page_size, search, source
        - language (en/de/all)
        - level (A1-C2/all)
    """
    from core.models import Video
    qs = Video.objects.order_by('-created_at')

    if request.query_params.get('search'):
        qs = qs.filter(Q(title__icontains=request.query_params['search']))
    if request.query_params.get('source'):
        qs = qs.filter(source=request.query_params['source'])
    if request.query_params.get('language'):
        qs = qs.filter(language=request.query_params['language'])
    if request.query_params.get('level'):
        qs = qs.filter(level=request.query_params['level'])

    page = max(1, int(request.query_params.get('page', 1)))
    page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
    total = qs.count()
    videos = qs[(page - 1) * page_size:page * page_size]

    return Response({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': [{
            'id': v.id,
            'title': v.title,
            'slug': v.slug,
            'youtube_id': v.youtube_id,
            'language': v.language,
            'level': v.level,
            'is_active': v.is_active,
            'url': f'/videos/{v.slug}',
            'created_at': v.created_at.isoformat(),
            'source': getattr(v, 'source', ''),
            'source_id': getattr(v, 'source_id', ''),
        } for v in videos],
    })


# ============================================================================
# Tools CRUD — Tạo & cập nhật công cụ học tập
# ============================================================================

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_create_tool(request):
    """
    Tạo Tool từ n8n

    POST /api/v1/n8n/tools/
    Headers: X-API-Key: <key>

    Body (JSON hoặc multipart/form-data):
        {
            "name": "Tên công cụ" (bắt buộc),
            "description": "Mô tả" (bắt buộc),
            "content": "Nội dung HTML (cho tool_type=article)",
            "excerpt": "Mô tả ngắn",
            "category": "slug hoặc id",
            "tool_type": "internal|external|embed|article" (default: "article"),
            "url": "URL công cụ bên ngoài (cho external)",
            "embed_code": "Iframe/embed HTML (cho embed)",
            "icon": "Tên icon (lucide-react)",
            "language": "en|de|all" (default: "all"),
            "cover_image_url": "URL ảnh bìa",
            "auto_placeholder": true,
            "is_featured": false,
            "is_published": true,
            "meta_title": "SEO title",
            "meta_description": "SEO description",
            "skip_seo_validation": false
        }

    Returns:
        {
            "success": true,
            "tool": {...},
            "image_source": "url|upload|placeholder|none",
            "message": "Đã tạo công cụ thành công"
        }
    """
    from tools.models import Tool, ToolCategory

    name = request.data.get('name')
    description = request.data.get('description')

    if not name:
        return Response(
            {'success': False, 'error': 'Thiếu trường "name"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not description:
        return Response(
            {'success': False, 'error': 'Thiếu trường "description"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Tool type validation
    tool_type = request.data.get('tool_type', 'article')
    valid_types = ['internal', 'external', 'embed', 'article']
    if tool_type not in valid_types:
        return Response(
            {'success': False, 'error': f'tool_type phải là: {", ".join(valid_types)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # External required URL
    if tool_type == 'external' and not request.data.get('url'):
        return Response(
            {'success': False, 'error': 'tool_type "external" cần trường "url"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Article type = SEO validation
    content = request.data.get('content', '')
    if tool_type == 'article' and content:
        skip_validation = request.data.get('skip_seo_validation', False)
        seo_valid, seo_warnings, seo_errors = validate_seo_content({
            'title': name,
            'content': content,
            'excerpt': request.data.get('excerpt', ''),
            'meta_title': request.data.get('meta_title', ''),
            'meta_description': request.data.get('meta_description', ''),
        })
        if not seo_valid and not skip_validation:
            return Response({
                'success': False,
                'error': 'Nội dung không đạt chuẩn SEO',
                'seo_errors': seo_errors,
                'seo_warnings': seo_warnings,
                'hint': 'Gửi skip_seo_validation=true để bỏ qua'
            }, status=status.HTTP_400_BAD_REQUEST)

    # Category
    category_input = request.data.get('category')
    category = None
    if category_input:
        try:
            if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
                category = ToolCategory.objects.get(id=int(category_input))
            else:
                category = ToolCategory.objects.get(slug=category_input)
        except ToolCategory.DoesNotExist:
            category = ToolCategory.objects.create(
                name=category_input,
                slug=vietnamese_slugify(category_input)
            )

    # Generate unique slug
    base_slug = vietnamese_slugify(name)
    slug = base_slug
    counter = 1
    while Tool.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Language
    language = request.data.get('language', 'all')
    if language not in ['de', 'en', 'all']:
        language = 'all'

    # Process cover image
    cover_image, image_source = process_article_image(
        request, slug, upload_to='tools/covers/'
    )

    is_published = request.data.get('is_published', True)

    try:
        tool = Tool.objects.create(
            name=safe_truncate(name, 200),
            slug=slug,
            description=description,
            content=content,
            excerpt=request.data.get('excerpt', ''),
            category=category,
            author=request.user,
            tool_type=tool_type,
            url=safe_truncate(request.data.get('url', ''), 500),
            embed_code=request.data.get('embed_code', ''),
            icon=safe_truncate(request.data.get('icon', ''), 50),
            language=language,
            is_featured=request.data.get('is_featured', False),
            is_published=is_published,
            is_active=True,
            published_at=timezone.now() if is_published else None,
            meta_title=safe_truncate(request.data.get('meta_title', ''), 200),
            meta_description=request.data.get('meta_description', ''),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create tool: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo công cụ: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if cover_image:
        try:
            tool.cover_image = cover_image
            tool.save()
        except Exception as e:
            n8n_logger.warning(f'Cover image save failed for tool {tool.id}: {e}')

    response_data = {
        'success': True,
        'tool': {
            'id': tool.id,
            'name': tool.name,
            'slug': tool.slug,
            'tool_type': tool.tool_type,
            'language': tool.language,
            'url': f'/cong-cu/{tool.slug}',
            'is_published': tool.is_published,
            'cover_image': tool.cover_image.url if tool.cover_image else None,
            'created_at': tool.created_at.isoformat(),
        },
        'image_source': image_source,
        'message': 'Đã tạo công cụ thành công',
    }

    if tool_type == 'article' and content:
        _, seo_warnings_final, _ = validate_seo_content({
            'title': name, 'content': content,
            'excerpt': request.data.get('excerpt', ''),
        })
        if seo_warnings_final:
            response_data['seo_warnings'] = seo_warnings_final

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_update_tool(request, identifier):
    """
    Cập nhật Tool từ n8n

    PUT/PATCH /api/v1/n8n/tools/<identifier>/
    identifier: slug hoặc id

    Body (JSON):
        Bất kỳ trường nào của Tool (name, description, content, category,
        tool_type, url, embed_code, icon, language, is_featured, is_published,
        is_active, meta_title, meta_description, cover_image_url,
        regenerate_slug)
    """
    from tools.models import Tool, ToolCategory

    # Find tool
    tool = Tool.objects.filter(slug=identifier).first()
    if not tool and (isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit())):
        tool = Tool.objects.filter(id=int(identifier)).first()
    if not tool:
        return Response(
            {'success': False, 'error': f'Không tìm thấy tool "{identifier}"'},
            status=status.HTTP_404_NOT_FOUND
        )

    data = request.data
    updated_fields = []

    # Text fields
    for param in ['name', 'description', 'content', 'excerpt', 'url', 'embed_code',
                   'icon', 'meta_title', 'meta_description']:
        if param in data:
            setattr(tool, param, data[param])
            updated_fields.append(param)

    # Tool type
    if 'tool_type' in data:
        valid_types = ['internal', 'external', 'embed', 'article']
        if data['tool_type'] in valid_types:
            tool.tool_type = data['tool_type']
            updated_fields.append('tool_type')

    # Language
    if 'language' in data:
        if data['language'] in ['de', 'en', 'all']:
            tool.language = data['language']
            updated_fields.append('language')

    # Booleans
    for param in ['is_featured', 'is_published', 'is_active']:
        if param in data:
            was_published = tool.is_published
            setattr(tool, param, data[param])
            updated_fields.append(param)
            if param == 'is_published' and data[param] and not was_published and not tool.published_at:
                tool.published_at = timezone.now()
                updated_fields.append('published_at')

    # Category
    if 'category' in data:
        category_input = data['category']
        if category_input:
            try:
                if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
                    tool.category = ToolCategory.objects.get(id=int(category_input))
                else:
                    tool.category = ToolCategory.objects.get(slug=category_input)
                updated_fields.append('category')
            except ToolCategory.DoesNotExist:
                return Response(
                    {'success': False, 'error': f'Category "{category_input}" không tồn tại'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            tool.category = None
            updated_fields.append('category')

    # Slug regeneration
    if data.get('regenerate_slug') and 'name' in data:
        base_slug = vietnamese_slugify(data['name'])
        slug = base_slug
        counter = 1
        while Tool.objects.filter(slug=slug).exclude(id=tool.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        tool.slug = slug
        updated_fields.append('slug')

    # Cover image
    image_source = 'unchanged'
    if 'cover_image' in request.FILES or 'cover_image_url' in data:
        cover_image, image_source = process_article_image(
            request, tool.slug, upload_to='tools/covers/'
        )
        if cover_image:
            tool.cover_image = cover_image
            updated_fields.append('cover_image')

    if not updated_fields:
        return Response(
            {'success': False, 'error': 'Không có trường nào được cập nhật'},
            status=status.HTTP_400_BAD_REQUEST
        )

    tool.save()

    return Response({
        'success': True,
        'tool': {
            'id': tool.id,
            'name': tool.name,
            'slug': tool.slug,
            'tool_type': tool.tool_type,
            'url': f'/cong-cu/{tool.slug}',
            'is_published': tool.is_published,
            'cover_image': tool.cover_image.url if tool.cover_image else None,
            'updated_at': tool.updated_at.isoformat(),
        },
        'updated_fields': updated_fields,
        'image_source': image_source,
        'message': 'Đã cập nhật công cụ thành công',
    })


# ============================================================================
# Flashcard CRUD — Tạo bộ flashcard với các thẻ
# ============================================================================

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def n8n_create_flashcard_deck(request):
    """
    Tạo bộ Flashcard (deck + cards) từ n8n

    POST /api/v1/n8n/flashcards/
    Headers: X-API-Key: <key>

    Body (JSON):
        {
            "name": "Tên bộ flashcard" (bắt buộc),
            "description": "Mô tả",
            "language": "en|de" (bắt buộc),
            "level": "A1|A2|B1|B2|C1|C2" (bắt buộc),
            "is_public": true,
            "is_featured": false,
            "cards": [
                {
                    "front": "Hello" (bắt buộc),
                    "back": "Xin chào" (bắt buộc),
                    "example": "Hello, how are you?",
                    "pronunciation": "/həˈloʊ/",
                    "audio_url": "https://..."
                },
                ...
            ]
        }

    Returns:
        {
            "success": true,
            "deck": {...},
            "cards_created": 10,
            "message": "Đã tạo bộ flashcard thành công"
        }
    """
    from tools.models import FlashcardDeck, Flashcard

    name = request.data.get('name')
    language = request.data.get('language')
    level = request.data.get('level')

    if not name:
        return Response(
            {'success': False, 'error': 'Thiếu trường "name"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not language or language not in ['en', 'de']:
        return Response(
            {'success': False, 'error': 'Trường "language" bắt buộc (en hoặc de)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not level or level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        return Response(
            {'success': False, 'error': 'Trường "level" bắt buộc (A1-C2)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generate unique slug
    base_slug = vietnamese_slugify(name)
    slug = base_slug
    counter = 1
    while FlashcardDeck.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Check duplicate by name + language + level
    existing = FlashcardDeck.objects.filter(
        name=name, language=language, level=level
    ).first()
    if existing:
        return Response({
            'success': True,
            'deck': {
                'id': existing.id,
                'name': existing.name,
                'slug': existing.slug,
                'card_count': existing.cards.count(),
            },
            'message': 'Bộ flashcard đã tồn tại',
            'action': 'skipped'
        })

    # Create deck
    try:
        deck = FlashcardDeck.objects.create(
            name=safe_truncate(name, 200),
            slug=slug,
            description=request.data.get('description', ''),
            language=language,
            level=level,
            author=request.user,
            is_public=request.data.get('is_public', True),
            is_featured=request.data.get('is_featured', False),
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create flashcard deck: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo bộ flashcard: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create cards
    cards_data = request.data.get('cards', [])
    cards_created = 0
    card_errors = []

    for i, card_data in enumerate(cards_data):
        front = card_data.get('front', '').strip()
        back = card_data.get('back', '').strip()
        if not front or not back:
            card_errors.append(f'Card {i + 1}: thiếu front hoặc back')
            continue

        try:
            Flashcard.objects.create(
                deck=deck,
                front=front,
                back=back,
                example=card_data.get('example', ''),
                pronunciation=safe_truncate(card_data.get('pronunciation', ''), 200),
                audio_url=safe_truncate(card_data.get('audio_url', ''), 200),
                order=i,
            )
            cards_created += 1
        except Exception as e:
            card_errors.append(f'Card {i + 1}: {type(e).__name__}: {str(e)[:200]}')

    response_data = {
        'success': True,
        'deck': {
            'id': deck.id,
            'name': deck.name,
            'slug': deck.slug,
            'language': deck.language,
            'level': deck.level,
            'url': f'/cong-cu/flashcards/{deck.slug}',
            'created_at': deck.created_at.isoformat(),
        },
        'cards_created': cards_created,
        'message': f'Đã tạo bộ flashcard với {cards_created} thẻ',
        'action': 'created',
    }

    if card_errors:
        response_data['card_errors'] = card_errors

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@authentication_classes([APIKeyAuthentication])
def n8n_update_flashcard_deck(request, identifier):
    """
    Cập nhật bộ Flashcard từ n8n

    PUT/PATCH /api/v1/n8n/flashcards/<identifier>/
    identifier: slug hoặc id

    Body (JSON):
        {
            "name": "Tên mới",
            "description": "Mô tả mới",
            "is_public": true,
            "is_featured": false,
            "add_cards": [...],     // Thêm thẻ mới
            "replace_cards": [...]  // Xoá tất cả thẻ cũ, thay bằng mới
        }
    """
    from tools.models import FlashcardDeck, Flashcard

    deck = FlashcardDeck.objects.filter(slug=identifier).first()
    if not deck and (isinstance(identifier, str) and identifier.isdigit()):
        deck = FlashcardDeck.objects.filter(id=int(identifier)).first()
    if not deck:
        return Response(
            {'success': False, 'error': f'Không tìm thấy FlashcardDeck "{identifier}"'},
            status=status.HTTP_404_NOT_FOUND
        )

    data = request.data
    updated_fields = []

    for field in ['name', 'description']:
        if field in data:
            setattr(deck, field, data[field])
            updated_fields.append(field)

    for field in ['is_public', 'is_featured']:
        if field in data:
            setattr(deck, field, data[field])
            updated_fields.append(field)

    if 'language' in data and data['language'] in ['en', 'de']:
        deck.language = data['language']
        updated_fields.append('language')
    if 'level' in data and data['level'] in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        deck.level = data['level']
        updated_fields.append('level')

    deck.save()

    # Replace all cards
    cards_created = 0
    if 'replace_cards' in data:
        deck.cards.all().delete()
        for i, card_data in enumerate(data['replace_cards']):
            front = card_data.get('front', '').strip()
            back = card_data.get('back', '').strip()
            if front and back:
                Flashcard.objects.create(
                    deck=deck, front=front, back=back,
                    example=card_data.get('example', ''),
                    pronunciation=card_data.get('pronunciation', ''),
                    audio_url=card_data.get('audio_url', ''),
                    order=i,
                )
                cards_created += 1
        updated_fields.append(f'replace_cards({cards_created})')

    # Add cards
    elif 'add_cards' in data:
        max_order = deck.cards.order_by('-order').values_list('order', flat=True).first() or 0
        for i, card_data in enumerate(data['add_cards']):
            front = card_data.get('front', '').strip()
            back = card_data.get('back', '').strip()
            if front and back:
                Flashcard.objects.create(
                    deck=deck, front=front, back=back,
                    example=card_data.get('example', ''),
                    pronunciation=card_data.get('pronunciation', ''),
                    audio_url=card_data.get('audio_url', ''),
                    order=max_order + i + 1,
                )
                cards_created += 1
        updated_fields.append(f'add_cards({cards_created})')

    return Response({
        'success': True,
        'deck': {
            'id': deck.id,
            'name': deck.name,
            'slug': deck.slug,
            'card_count': deck.cards.count(),
            'updated_at': deck.updated_at.isoformat(),
        },
        'updated_fields': updated_fields,
        'cards_modified': cards_created,
        'message': 'Đã cập nhật bộ flashcard thành công',
    })


# ============================================================================
# Resource UPDATE
# ============================================================================

@api_view(['PUT', 'PATCH'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_update_resource(request, identifier):
    """
    Cập nhật Resource từ n8n

    PUT/PATCH /api/v1/n8n/resources/<identifier>/
    identifier: slug, id, hoặc source_id

    Body (JSON):
        {
            "title": "Tên mới",
            "description": "Mô tả mới",
            "category": "slug hoặc id",
            "resource_type": "ebook|pdf|audio|video|document|flashcard",
            "external_url": "URL mới",
            "youtube_url": "YouTube URL mới",
            "author": "Tác giả mới",
            "is_featured": true/false,
            "is_active": true/false,
            "cover_image_url": "URL ảnh mới",
            "regenerate_slug": false
        }
    """
    from resources.models import Resource, Category

    # Find resource
    resource, error = _find_article(Resource, identifier)
    if error:
        return error

    data = request.data
    updated_fields = []

    for param in ['title', 'description', 'external_url', 'youtube_url', 'author']:
        if param in data:
            setattr(resource, param, data[param])
            updated_fields.append(param)

    for param in ['is_featured', 'is_active']:
        if param in data:
            setattr(resource, param, data[param])
            updated_fields.append(param)

    if 'resource_type' in data:
        valid_types = ['ebook', 'book', 'pdf', 'audio', 'video', 'document', 'flashcard']
        if data['resource_type'] in valid_types:
            resource.resource_type = data['resource_type']
            updated_fields.append('resource_type')

    if 'category' in data:
        category_input = data['category']
        if category_input:
            try:
                if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
                    resource.category = Category.objects.get(id=int(category_input))
                else:
                    resource.category = Category.objects.get(slug=category_input)
                updated_fields.append('category')
            except Category.DoesNotExist:
                return Response(
                    {'success': False, 'error': f'Category "{category_input}" không tồn tại'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    if data.get('regenerate_slug') and 'title' in data:
        base_slug = vietnamese_slugify(data['title'])
        slug = base_slug
        counter = 1
        while Resource.objects.filter(slug=slug).exclude(id=resource.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        resource.slug = slug
        updated_fields.append('slug')

    # N8N tracking
    for param, field in {'source_url': 'source_url', 'source_id': 'source_id',
                         'workflow_id': 'n8n_workflow_id', 'execution_id': 'n8n_execution_id'}.items():
        if param in data:
            setattr(resource, field, data[param])
            updated_fields.append(field)

    # Cover image
    image_source = 'unchanged'
    if 'cover_image' in request.FILES or 'cover_image_url' in data:
        cover_image, image_source = process_article_image(
            request, resource.slug, upload_to='resources/covers/'
        )
        if cover_image:
            resource.cover_image = cover_image
            updated_fields.append('cover_image')

    if not updated_fields:
        return Response(
            {'success': False, 'error': 'Không có trường nào được cập nhật'},
            status=status.HTTP_400_BAD_REQUEST
        )

    resource.save()

    return Response({
        'success': True,
        'resource': {
            'id': resource.id,
            'title': resource.title,
            'slug': resource.slug,
            'resource_type': resource.resource_type,
            'url': f'/tai-lieu/{resource.slug}',
            'updated_at': resource.updated_at.isoformat(),
        },
        'updated_fields': updated_fields,
        'image_source': image_source,
        'message': 'Đã cập nhật tài liệu thành công',
    })


# ============================================================================
# Stream Media — Tạo video streaming (GDrive / local)
# ============================================================================

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def n8n_create_stream_media(request):
    """
    Tạo StreamMedia từ n8n (hỗ trợ Google Drive)

    POST /api/v1/n8n/stream-media/
    Headers: X-API-Key: <key>

    Body (JSON):
        {
            "title": "Tiêu đề video" (bắt buộc),
            "description": "Mô tả",
            "media_type": "video|audio" (default: "video"),
            "storage_type": "gdrive|local" (default: "gdrive"),
            "gdrive_url": "https://drive.google.com/file/d/xxx/view" (cho gdrive),
            "category": "slug hoặc id",
            "language": "vi|en|de|all" (default: "all"),
            "level": "A1|A2|B1|B2|C1|C2|all" (default: "all"),
            "tags": "tag1, tag2, tag3",
            "transcript": "Nội dung transcript",
            "is_public": true,
            "requires_login": false
        }

    Returns:
        {
            "success": true,
            "media": {...},
            "message": "Đã tạo stream media thành công"
        }
    """
    from mediastream.models import StreamMedia, MediaCategory

    title = request.data.get('title')
    if not title:
        return Response(
            {'success': False, 'error': 'Thiếu trường "title"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    storage_type = request.data.get('storage_type', 'gdrive')
    if storage_type not in ['gdrive', 'local']:
        storage_type = 'gdrive'

    # GDrive validation
    gdrive_url = request.data.get('gdrive_url', '')
    if storage_type == 'gdrive' and not gdrive_url:
        return Response(
            {'success': False, 'error': 'storage_type "gdrive" cần trường "gdrive_url"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check duplicate by gdrive_url
    if gdrive_url:
        existing = StreamMedia.objects.filter(gdrive_url=gdrive_url).first()
        if existing:
            return Response({
                'success': True,
                'media': {
                    'id': existing.id,
                    'uid': str(existing.uid),
                    'title': existing.title,
                    'stream_url': f'/media-stream/play/{existing.uid}/',
                },
                'message': 'Video đã tồn tại với GDrive URL này',
                'action': 'skipped',
            })

    # Category
    category_input = request.data.get('category')
    category = None
    if category_input:
        try:
            if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
                category = MediaCategory.objects.get(id=int(category_input))
            else:
                category = MediaCategory.objects.get(slug=category_input)
        except MediaCategory.DoesNotExist:
            category = MediaCategory.objects.create(
                name=category_input,
                slug=vietnamese_slugify(category_input)
            )

    # Generate unique slug
    base_slug = vietnamese_slugify(title)
    slug = base_slug
    counter = 1
    while StreamMedia.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Language & Level
    language = request.data.get('language', 'all')
    if language not in ['vi', 'en', 'de', 'all']:
        language = 'all'
    level = request.data.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'

    media_type = request.data.get('media_type', 'video')
    if media_type not in ['video', 'audio']:
        media_type = 'video'

    try:
        media = StreamMedia.objects.create(
            title=safe_truncate(title, 255),
            slug=slug,
            description=request.data.get('description', ''),
            media_type=media_type,
            storage_type=storage_type,
            gdrive_url=safe_truncate(gdrive_url, 500),
            category=category,
            language=language,
            level=level,
            tags=safe_truncate(request.data.get('tags', ''), 500),
            transcript=request.data.get('transcript', ''),
            is_public=request.data.get('is_public', True),
            is_active=True,
            requires_login=request.data.get('requires_login', False),
            uploaded_by=request.user,
        )
    except Exception as e:
        n8n_logger.error(f'Failed to create stream media: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo stream media: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': True,
        'media': {
            'id': media.id,
            'uid': str(media.uid),
            'title': media.title,
            'slug': media.slug,
            'storage_type': media.storage_type,
            'gdrive_file_id': media.gdrive_file_id or '',
            'media_type': media.media_type,
            'stream_url': f'/media-stream/play/{media.uid}/',
            'language': media.language,
            'level': media.level,
            'created_at': media.created_at.isoformat(),
        },
        'message': 'Đã tạo stream media thành công',
        'action': 'created',
    }, status=status.HTTP_201_CREATED)


# ============================================================================
# DELETE — Xoá nội dung (soft delete: is_active=False)
# ============================================================================

@api_view(['DELETE'])
@authentication_classes([APIKeyAuthentication])
def n8n_delete_content(request, content_type, identifier):
    """
    Xoá nội dung (soft delete: đặt is_active/is_published = False)

    DELETE /api/v1/n8n/<content_type>/<identifier>/delete/
    Headers: X-API-Key: <key>

    content_type: news | knowledge | resources | tools | videos | stream-media | flashcards
    identifier: slug, id, hoặc source_id

    Query params:
        - hard=true: Xoá vĩnh viễn (KHÔNG THỂ HOÀN TÁC)

    Returns:
        {
            "success": true,
            "action": "soft_delete" | "hard_delete",
            "message": "Đã xoá thành công"
        }
    """
    hard_delete = request.query_params.get('hard', '').lower() == 'true'

    # Model mapping
    model_map = {
        'news': ('news.models', 'Article', 'is_published'),
        'knowledge': ('knowledge.models', 'KnowledgeArticle', 'is_published'),
        'resources': ('resources.models', 'Resource', 'is_active'),
        'tools': ('tools.models', 'Tool', 'is_active'),
        'videos': ('core.models', 'Video', 'is_active'),
        'stream-media': ('mediastream.models', 'StreamMedia', 'is_active'),
        'flashcards': ('tools.models', 'FlashcardDeck', 'is_public'),
    }

    if content_type not in model_map:
        return Response(
            {'success': False, 'error': f'content_type không hợp lệ. Hỗ trợ: {", ".join(model_map.keys())}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    module_path, model_name, deactivate_field = model_map[content_type]

    import importlib
    module = importlib.import_module(module_path)
    Model = getattr(module, model_name)

    # Find object
    obj = None
    # Try slug first
    if hasattr(Model, 'slug'):
        obj = Model.objects.filter(slug=identifier).first()
    # Try by id
    if not obj and (isinstance(identifier, str) and identifier.isdigit()):
        obj = Model.objects.filter(id=int(identifier)).first()
    # Try by uid (StreamMedia)
    if not obj and content_type == 'stream-media':
        obj = Model.objects.filter(uid=identifier).first()
    # Try by source_id (n8n tracking)
    if not obj and hasattr(Model, 'source_id'):
        obj = Model.objects.filter(source='n8n', source_id=identifier).first()

    if not obj:
        return Response(
            {'success': False, 'error': f'Không tìm thấy {content_type} "{identifier}"'},
            status=status.HTTP_404_NOT_FOUND
        )

    title = getattr(obj, 'title', None) or getattr(obj, 'name', str(obj))

    if hard_delete:
        obj.delete()
        return Response({
            'success': True,
            'action': 'hard_delete',
            'message': f'Đã xoá vĩnh viễn "{title}"',
        })
    else:
        setattr(obj, deactivate_field, False)
        obj.save(update_fields=[deactivate_field])
        return Response({
            'success': True,
            'action': 'soft_delete',
            'field_changed': deactivate_field,
            'message': f'Đã ẩn "{title}" (soft delete: {deactivate_field}=False)',
        })


# ============================================================================
# Categories EXPANDED — Thêm tools + media categories
# ============================================================================

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
def n8n_create_category(request):
    """
    Tạo category mới cho bất kỳ loại nội dung nào

    POST /api/v1/n8n/categories/create/
    Headers: X-API-Key: <key>

    Body (JSON):
        {
            "type": "news|knowledge|resources|tools|media" (bắt buộc),
            "name": "Tên category" (bắt buộc),
            "slug": "slug-tuy-chon",
            "description": "Mô tả",
            "icon": "Icon (emoji hoặc lucide-react name)"
        }
    """
    cat_type = request.data.get('type')
    name = request.data.get('name')

    if not cat_type:
        return Response(
            {'success': False, 'error': 'Thiếu trường "type" (news/knowledge/resources/tools/media)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not name:
        return Response(
            {'success': False, 'error': 'Thiếu trường "name"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    slug = request.data.get('slug') or vietnamese_slugify(name)
    description = request.data.get('description', '')
    icon = request.data.get('icon', '')

    category_models = {
        'news': 'news.models.Category',
        'knowledge': 'knowledge.models.Category',
        'resources': 'resources.models.Category',
        'tools': 'tools.models.ToolCategory',
        'media': 'mediastream.models.MediaCategory',
    }

    if cat_type not in category_models:
        return Response(
            {'success': False, 'error': f'type phải là: {", ".join(category_models.keys())}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    import importlib
    module_path, class_name = category_models[cat_type].rsplit('.', 1)
    module = importlib.import_module(module_path)
    Model = getattr(module, class_name)

    # Check existing
    existing = Model.objects.filter(slug=slug).first()
    if existing:
        return Response({
            'success': True,
            'category': {'id': existing.id, 'name': existing.name, 'slug': existing.slug},
            'message': 'Category đã tồn tại',
            'action': 'skipped',
        })

    kwargs = {
        'name': safe_truncate(name, 100),
        'slug': safe_truncate(slug, 120),
        'description': description,
    }
    if hasattr(Model, 'icon'):
        kwargs['icon'] = safe_truncate(icon, 50)

    try:
        cat = Model.objects.create(**kwargs)
    except Exception as e:
        n8n_logger.error(f'Failed to create category: {type(e).__name__}: {e}', exc_info=True)
        return Response({
            'success': False,
            'error': f'Lỗi tạo category: {type(e).__name__}: {str(e)[:500]}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': True,
        'category': {'id': cat.id, 'name': cat.name, 'slug': cat.slug, 'type': cat_type},
        'message': f'Đã tạo category {cat_type} thành công',
        'action': 'created',
    }, status=status.HTTP_201_CREATED)


# ============================================================================
# BULK Operations — Tạo nhiều nội dung cùng lúc
# ============================================================================

@api_view(['POST'])
@authentication_classes([APIKeyAuthentication])
@parser_classes([JSONParser])
def n8n_bulk_create(request):
    """
    Tạo nhiều nội dung cùng lúc (batch operation)

    POST /api/v1/n8n/bulk/
    Headers: X-API-Key: <key>

    Body (JSON):
        {
            "content_type": "news|knowledge|resources|tools|videos|flashcards|stream-media",
            "items": [
                { ... item 1 ... },
                { ... item 2 ... },
                ...
            ],
            "skip_seo_validation": true
        }

    Mỗi item có cùng format như endpoint tạo đơn lẻ tương ứng.
    Max 50 items/request.

    Returns:
        {
            "success": true,
            "total": 10,
            "created": 8,
            "skipped": 1,
            "failed": 1,
            "results": [
                {"index": 0, "status": "created", "id": 1, "title": "..."},
                {"index": 1, "status": "skipped", "reason": "duplicate"},
                {"index": 2, "status": "failed", "error": "..."},
                ...
            ]
        }
    """
    content_type = request.data.get('content_type')
    items = request.data.get('items', [])

    if not content_type:
        return Response(
            {'success': False, 'error': 'Thiếu trường "content_type"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not items or not isinstance(items, list):
        return Response(
            {'success': False, 'error': 'Trường "items" phải là danh sách không rỗng'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(items) > 50:
        return Response(
            {'success': False, 'error': 'Tối đa 50 items/request'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Route to appropriate create function
    handler_map = {
        'news': _bulk_create_news,
        'knowledge': _bulk_create_knowledge,
        'resources': _bulk_create_resource,
        'tools': _bulk_create_tool,
        'videos': _bulk_create_video,
        'flashcards': _bulk_create_flashcard,
        'stream-media': _bulk_create_stream_media,
    }

    if content_type not in handler_map:
        return Response(
            {'success': False, 'error': f'content_type phải là: {", ".join(handler_map.keys())}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    skip_validation = request.data.get('skip_seo_validation', True)
    handler = handler_map[content_type]

    results = []
    created = 0
    skipped = 0
    failed = 0

    for i, item in enumerate(items):
        try:
            result = handler(item, request.user, skip_validation)
            results.append({'index': i, **result})
            if result['status'] == 'created':
                created += 1
            elif result['status'] == 'skipped':
                skipped += 1
            else:
                failed += 1
        except Exception as e:
            results.append({'index': i, 'status': 'failed', 'error': str(e)})
            failed += 1

    return Response({
        'success': True,
        'content_type': content_type,
        'total': len(items),
        'created': created,
        'skipped': skipped,
        'failed': failed,
        'results': results,
    }, status=status.HTTP_201_CREATED if created > 0 else status.HTTP_200_OK)


# --- Bulk helpers (internal) ---

def _generate_unique_slug(Model, title, slug_field='slug'):
    base_slug = vietnamese_slugify(title)
    slug = base_slug
    counter = 1
    while Model.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _resolve_category(Model, category_input):
    if not category_input:
        return None
    try:
        if isinstance(category_input, int) or (isinstance(category_input, str) and category_input.isdigit()):
            return Model.objects.get(id=int(category_input))
        return Model.objects.get(slug=category_input)
    except Model.DoesNotExist:
        return Model.objects.create(
            name=category_input,
            slug=vietnamese_slugify(category_input)
        )


def _bulk_create_news(item, user, skip_validation):
    from news.models import Article, Category
    title = item.get('title', '')
    if not title:
        return {'status': 'failed', 'error': 'Thiếu title'}
    if not item.get('content'):
        return {'status': 'failed', 'error': 'Thiếu content'}

    # Duplicate check
    slug_check = vietnamese_slugify(title)
    if Article.objects.filter(slug=slug_check).exists():
        existing = Article.objects.get(slug=slug_check)
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.title}

    if not skip_validation:
        valid, warnings, errors = validate_seo_content(item)
        if not valid:
            return {'status': 'failed', 'error': f'SEO errors: {"; ".join(errors)}'}

    slug = _generate_unique_slug(Article, title)
    category = _resolve_category(Category, item.get('category'))
    is_published = item.get('is_published', True)

    article = Article.objects.create(
        title=title, slug=slug, content=item.get('content', ''),
        excerpt=item.get('excerpt', ''), category=category, author=user,
        is_featured=item.get('is_featured', False), is_published=is_published,
        published_at=timezone.now() if is_published else None,
        meta_title=item.get('meta_title', ''), meta_description=item.get('meta_description', ''),
        meta_keywords=item.get('meta_keywords', ''),
        source='n8n', source_id=item.get('source_id', ''),
        n8n_workflow_id=item.get('workflow_id', ''),
        n8n_execution_id=item.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=item.get('is_ai_generated', False),
        ai_model=item.get('ai_model', ''),
    )
    return {'status': 'created', 'id': article.id, 'title': article.title, 'slug': article.slug}


def _bulk_create_knowledge(item, user, skip_validation):
    from knowledge.models import KnowledgeArticle, Category
    title = item.get('title', '')
    if not title:
        return {'status': 'failed', 'error': 'Thiếu title'}
    if not item.get('content'):
        return {'status': 'failed', 'error': 'Thiếu content'}

    slug_check = vietnamese_slugify(title)
    if KnowledgeArticle.objects.filter(slug=slug_check).exists():
        existing = KnowledgeArticle.objects.get(slug=slug_check)
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.title}

    if not skip_validation:
        valid, warnings, errors = validate_seo_content(item)
        if not valid:
            return {'status': 'failed', 'error': f'SEO errors: {"; ".join(errors)}'}

    slug = _generate_unique_slug(KnowledgeArticle, title)
    category = _resolve_category(Category, item.get('category'))
    is_published = item.get('is_published', True)

    language = item.get('language', 'all')
    if language not in ['de', 'en', 'all']:
        language = 'all'
    level = item.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'

    article = KnowledgeArticle.objects.create(
        title=title, slug=slug, content=item.get('content', ''),
        excerpt=item.get('excerpt', ''), category=category, author=user,
        language=language, level=level,
        is_featured=item.get('is_featured', False), is_published=is_published,
        published_at=timezone.now() if is_published else None,
        meta_title=item.get('meta_title', ''), meta_description=item.get('meta_description', ''),
        meta_keywords=item.get('meta_keywords', ''),
        source='n8n', source_id=item.get('source_id', ''),
        n8n_workflow_id=item.get('workflow_id', ''),
        n8n_execution_id=item.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=item.get('is_ai_generated', False),
        ai_model=item.get('ai_model', ''),
    )
    return {'status': 'created', 'id': article.id, 'title': article.title, 'slug': article.slug}


def _bulk_create_resource(item, user, skip_validation):
    from resources.models import Resource, Category
    title = item.get('title', '')
    if not title:
        return {'status': 'failed', 'error': 'Thiếu title'}
    if not item.get('description'):
        return {'status': 'failed', 'error': 'Thiếu description'}

    slug_check = vietnamese_slugify(title)
    if Resource.objects.filter(slug=slug_check).exists():
        existing = Resource.objects.get(slug=slug_check)
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.title}

    slug = _generate_unique_slug(Resource, title)
    category = _resolve_category(Category, item.get('category'))
    resource_type = item.get('resource_type', 'document')
    if resource_type not in ['ebook', 'book', 'pdf', 'audio', 'video', 'document', 'flashcard']:
        resource_type = 'document'

    resource = Resource.objects.create(
        title=title, slug=slug, description=item.get('description', ''),
        category=category, resource_type=resource_type,
        external_url=item.get('external_url', ''), youtube_url=item.get('youtube_url', ''),
        author=item.get('author', ''), is_featured=item.get('is_featured', False), is_active=True,
        source='n8n', source_id=item.get('source_id', ''),
        n8n_workflow_id=item.get('workflow_id', ''),
        n8n_execution_id=item.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=item.get('is_ai_generated', False),
        ai_model=item.get('ai_model', ''),
    )
    return {'status': 'created', 'id': resource.id, 'title': resource.title, 'slug': resource.slug}


def _bulk_create_tool(item, user, skip_validation):
    from tools.models import Tool, ToolCategory
    name = item.get('name', '')
    if not name:
        return {'status': 'failed', 'error': 'Thiếu name'}
    if not item.get('description'):
        return {'status': 'failed', 'error': 'Thiếu description'}

    slug_check = vietnamese_slugify(name)
    if Tool.objects.filter(slug=slug_check).exists():
        existing = Tool.objects.get(slug=slug_check)
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.name}

    slug = _generate_unique_slug(Tool, name)
    category = _resolve_category(ToolCategory, item.get('category'))
    tool_type = item.get('tool_type', 'article')
    if tool_type not in ['internal', 'external', 'embed', 'article']:
        tool_type = 'article'
    language = item.get('language', 'all')
    if language not in ['de', 'en', 'all']:
        language = 'all'
    is_published = item.get('is_published', True)

    tool = Tool.objects.create(
        name=name, slug=slug, description=item.get('description', ''),
        content=item.get('content', ''), excerpt=item.get('excerpt', ''),
        category=category, author=user, tool_type=tool_type,
        url=item.get('url', ''), embed_code=item.get('embed_code', ''),
        icon=item.get('icon', ''), language=language,
        is_featured=item.get('is_featured', False), is_published=is_published, is_active=True,
        published_at=timezone.now() if is_published else None,
        meta_title=item.get('meta_title', ''), meta_description=item.get('meta_description', ''),
    )
    return {'status': 'created', 'id': tool.id, 'title': tool.name, 'slug': tool.slug}


def _bulk_create_video(item, user, skip_validation):
    from core.models import Video
    from core.youtube import extract_youtube_id
    youtube_input = item.get('youtube_id', '')
    if not youtube_input:
        return {'status': 'failed', 'error': 'Thiếu youtube_id'}

    youtube_id = extract_youtube_id(youtube_input)
    if not youtube_id:
        return {'status': 'failed', 'error': 'YouTube ID không hợp lệ'}

    if Video.objects.filter(youtube_id=youtube_id).exists():
        existing = Video.objects.get(youtube_id=youtube_id)
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.title}

    language = item.get('language', 'en')
    if language not in ['de', 'en', 'all']:
        language = 'en'
    level = item.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'

    video = Video.objects.create(
        youtube_id=youtube_id, title=item.get('title', ''),
        description=item.get('description', ''), language=language, level=level,
        is_featured=item.get('is_featured', False), is_active=True,
        source='n8n', source_id=item.get('source_id', ''),
        n8n_workflow_id=item.get('workflow_id', ''),
        n8n_execution_id=item.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=item.get('is_ai_generated', False),
        ai_model=item.get('ai_model', ''),
    )
    return {'status': 'created', 'id': video.id, 'title': video.title, 'slug': video.slug}


def _bulk_create_flashcard(item, user, skip_validation):
    from tools.models import FlashcardDeck, Flashcard
    name = item.get('name', '')
    if not name:
        return {'status': 'failed', 'error': 'Thiếu name'}

    language = item.get('language', '')
    level = item.get('level', '')
    if language not in ['en', 'de']:
        return {'status': 'failed', 'error': 'language phải là en hoặc de'}
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        return {'status': 'failed', 'error': 'level phải là A1-C2'}

    existing = FlashcardDeck.objects.filter(name=name, language=language, level=level).first()
    if existing:
        return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.name}

    slug = _generate_unique_slug(FlashcardDeck, name)
    deck = FlashcardDeck.objects.create(
        name=name, slug=slug, description=item.get('description', ''),
        language=language, level=level, author=user,
        is_public=item.get('is_public', True), is_featured=item.get('is_featured', False),
    )

    cards_created = 0
    for i, card_data in enumerate(item.get('cards', [])):
        front = card_data.get('front', '').strip()
        back = card_data.get('back', '').strip()
        if front and back:
            Flashcard.objects.create(
                deck=deck, front=front, back=back,
                example=card_data.get('example', ''),
                pronunciation=card_data.get('pronunciation', ''),
                audio_url=card_data.get('audio_url', ''),
                order=i,
            )
            cards_created += 1

    return {'status': 'created', 'id': deck.id, 'title': deck.name, 'slug': deck.slug,
            'cards_created': cards_created}


def _bulk_create_stream_media(item, user, skip_validation):
    from mediastream.models import StreamMedia, MediaCategory
    title = item.get('title', '')
    if not title:
        return {'status': 'failed', 'error': 'Thiếu title'}

    gdrive_url = item.get('gdrive_url', '')
    storage_type = item.get('storage_type', 'gdrive')

    if storage_type == 'gdrive' and not gdrive_url:
        return {'status': 'failed', 'error': 'gdrive cần trường gdrive_url'}

    if gdrive_url:
        existing = StreamMedia.objects.filter(gdrive_url=gdrive_url).first()
        if existing:
            return {'status': 'skipped', 'reason': 'duplicate', 'id': existing.id, 'title': existing.title}

    slug = _generate_unique_slug(StreamMedia, title)
    category = _resolve_category(MediaCategory, item.get('category'))

    language = item.get('language', 'all')
    if language not in ['vi', 'en', 'de', 'all']:
        language = 'all'
    level = item.get('level', 'all')
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'all']:
        level = 'all'

    media = StreamMedia.objects.create(
        title=title, slug=slug, description=item.get('description', ''),
        media_type=item.get('media_type', 'video'),
        storage_type=storage_type, gdrive_url=gdrive_url,
        category=category, language=language, level=level,
        tags=item.get('tags', ''), transcript=item.get('transcript', ''),
        is_public=item.get('is_public', True), is_active=True,
        requires_login=item.get('requires_login', False),
        uploaded_by=user,
    )
    return {'status': 'created', 'id': media.id, 'uid': str(media.uid),
            'title': media.title, 'slug': media.slug}


# ============================================================================
# DIAGNOSTIC — Kiểm tra trạng thái hệ thống
# ============================================================================


def _fix_sequences(request):
    """Fix all PostgreSQL sequences to prevent duplicate key errors."""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DO $$
                DECLARE
                    r RECORD;
                    max_id BIGINT;
                    fixed INT := 0;
                BEGIN
                    FOR r IN
                        SELECT s.relname AS seq_name, t.relname AS table_name, a.attname AS column_name
                        FROM pg_class s
                        JOIN pg_depend d ON d.objid = s.oid
                        JOIN pg_class t ON d.refobjid = t.oid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
                        WHERE s.relkind = 'S'
                    LOOP
                        EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', r.column_name, r.table_name) INTO max_id;
                        EXECUTE format('SELECT setval(%L, GREATEST(%s + 1, 1), false)', r.seq_name, max_id);
                        fixed := fixed + 1;
                    END LOOP;
                    RAISE NOTICE 'Fixed % sequences', fixed;
                END $$;
            """)
        return Response({'status': 'ok', 'message': 'All sequences synced successfully.'})
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def n8n_diagnostic(request):
    """
    Endpoint chẩn đoán — kiểm tra trạng thái hệ thống.
    Yêu cầu API key qua header X-API-Key hoặc query param ?key=.
    Không trả về thông tin nhạy cảm (keys, secrets, gateway URLs).

    GET  /api/v1/n8n/diagnostic/                → system status
    POST /api/v1/n8n/diagnostic/?action=fix_sequences → fix all PG sequences
    Headers: X-API-Key: <n8n_api_key>
    """
    # Authenticate
    from core.models import APIKey
    api_key = request.META.get('HTTP_X_API_KEY', '') or request.query_params.get('key', '')
    if not api_key or not APIKey.verify_key('n8n_api_key', api_key):
        return Response({'error': 'Authentication required. Provide X-API-Key header.'}, status=status.HTTP_401_UNAUTHORIZED)

    # POST actions
    if request.method == 'POST':
        action = request.query_params.get('action', '')
        if action == 'fix_sequences':
            return _fix_sequences(request)
        return Response({'error': f'Unknown action: {action}'}, status=status.HTTP_400_BAD_REQUEST)

    import sys
    from django.conf import settings
    from django.db import connection

    checks = {}

    # 1. Python + Django version
    import django
    checks['python_version'] = sys.version.split()[0]
    checks['django_version'] = django.__version__
    checks['debug_mode'] = settings.DEBUG

    # 2. Database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e}'

    # 3. Tables exist
    try:
        tables = connection.introspection.table_names()
        checks['tables_count'] = len(tables)
        checks['core_apikey_table'] = 'core_apikey' in tables
        checks['core_siteconfiguration_table'] = 'core_siteconfiguration' in tables
    except Exception as e:
        checks['tables'] = f'error: {e}'

    # 4. APIKey model
    try:
        from core.models import APIKey
        count = APIKey.objects.count()
        keys = list(APIKey.objects.values('id', 'name', 'key_type', 'is_active'))
        # Mask key values for security
        checks['apikey_count'] = count
        checks['apikey_list'] = keys
    except Exception as e:
        checks['apikey'] = f'error: {e}'

    # 5. SiteConfiguration
    try:
        from core.models import SiteConfiguration
        config = SiteConfiguration.get_instance()
        checks['site_config'] = {
            'site_name': config.site_name,
            'debug_mode': config.debug_mode,
            'allowed_hosts': config.allowed_hosts[:100] if config.allowed_hosts else '',
        }
    except Exception as e:
        checks['site_config'] = f'error: {e}'

    # 6. Encryption check
    try:
        from core.encryption import encrypt_value, decrypt_value
        test_val = 'test_encryption_123'
        encrypted = encrypt_value(test_val)
        decrypted = decrypt_value(encrypted)
        checks['encryption'] = 'ok' if decrypted == test_val else f'mismatch: got {decrypted}'
    except Exception as e:
        checks['encryption'] = f'error: {e}'

    # 7. Migrations
    try:
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('showmigrations', 'core', stdout=out, no_color=True)
        migrations_output = out.getvalue()
        unapplied = [line.strip() for line in migrations_output.split('\n')
                      if line.strip().startswith('[ ]')]
        checks['unapplied_migrations'] = unapplied if unapplied else 'all applied'
    except Exception as e:
        checks['migrations'] = f'error: {e}'

    # 8. Admin imports
    try:
        from core import admin as core_admin
        checks['admin_import'] = 'ok'
    except Exception as e:
        checks['admin_import'] = f'error: {e}'

    # 8b. Recent error log (last 50 lines)
    try:
        import pathlib
        log_file = pathlib.Path(settings.BASE_DIR) / 'logs' / 'django.log'
        if log_file.exists():
            lines = log_file.read_text(errors='replace').strip().split('\n')
            checks['error_log_lines'] = len(lines)
            checks['error_log_tail'] = lines[-50:] if len(lines) > 50 else lines
        else:
            checks['error_log'] = 'file not found'
    except Exception as e:
        checks['error_log'] = f'error: {e}'

    # 9. Config.py os import
    try:
        from core.config import apply_dynamic_settings
        checks['config_module'] = 'ok'
    except Exception as e:
        checks['config_module'] = f'error: {e}'

    return Response({
        'status': 'diagnostic',
        'timestamp': timezone.now().isoformat(),
        'checks': checks,
    })


# ============================================================================
# API KEY INFO — REMOVED (security risk)
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def n8n_api_key_info(request):
    """Endpoint removed for security. Use admin panel to view API keys."""
    return Response({'error': 'Endpoint removed. Use admin panel.'}, status=status.HTTP_410_GONE)


# ============================================================================
# ADMIN DEBUG — REMOVED (security risk — exposed keys, gateway URLs, secrets)
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def n8n_admin_debug(request):
    """Endpoint removed for security. Use admin panel for diagnostics."""
    return Response({'error': 'Endpoint removed. Use admin panel.'}, status=status.HTTP_410_GONE)

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
from rest_framework.permissions import AllowAny
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

class APIKeyAuthentication(BaseAuthentication):
    """
    Xác thực bằng API Key trong header X-API-Key
    API Key được lưu trong database (core.models.APIKey)
    """
    
    def authenticate(self, request):
        from core.models import APIKey
        
        api_key = request.META.get('HTTP_X_API_KEY') or request.headers.get('X-API-Key')
        
        if not api_key:
            return None  # No API key provided, skip this auth
        
        # Kiểm tra key từ database
        if not APIKey.verify_key('n8n_api_key', api_key):
            raise AuthenticationFailed('API Key không hợp lệ')
        
        # Return bot user for automation
        try:
            bot_user = User.objects.get(username='automation_bot')
        except User.DoesNotExist:
            # Create automation bot user if not exists
            bot_user = User.objects.create_user(
                username='automation_bot',
                email='unstressvn@gmail.com',
                is_staff=True
            )
        
        return (bot_user, None)


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
    
    # Create article
    article = Article.objects.create(
        title=title,
        slug=slug,
        content=content,
        excerpt=request.data.get('excerpt', ''),
        category=category,
        author=request.user,
        is_featured=request.data.get('is_featured', False),
        is_published=request.data.get('is_published', True),
        published_at=timezone.now() if request.data.get('is_published', True) else None,
        meta_title=request.data.get('meta_title', ''),
        meta_description=request.data.get('meta_description', ''),
        meta_keywords=request.data.get('meta_keywords', ''),
        # N8N tracking fields
        source='n8n',
        source_url=request.data.get('source_url', ''),
        source_id=request.data.get('source_id', ''),
        n8n_workflow_id=request.data.get('workflow_id', ''),
        n8n_execution_id=request.data.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=request.data.get('is_ai_generated', False),
        ai_model=request.data.get('ai_model', ''),
    )
    
    # Assign cover image after creation (triggers WebP conversion + responsive generation in save())
    if cover_image:
        article.cover_image = cover_image
        article.save()
    
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
    
    # Create article
    article = KnowledgeArticle.objects.create(
        title=title,
        slug=slug,
        content=content,
        excerpt=request.data.get('excerpt', ''),
        category=category,
        language=language,
        level=level,
        author=request.user,
        is_featured=request.data.get('is_featured', False),
        is_published=request.data.get('is_published', True),
        published_at=timezone.now() if request.data.get('is_published', True) else None,
        meta_title=request.data.get('meta_title', ''),
        meta_description=request.data.get('meta_description', ''),
        meta_keywords=request.data.get('meta_keywords', ''),
        # N8N tracking fields
        source='n8n',
        source_url=request.data.get('source_url', ''),
        source_id=request.data.get('source_id', ''),
        n8n_workflow_id=request.data.get('workflow_id', ''),
        n8n_execution_id=request.data.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=request.data.get('is_ai_generated', False),
        ai_model=request.data.get('ai_model', ''),
    )
    
    # Assign cover image after creation (triggers WebP conversion + responsive generation)
    if cover_image:
        article.cover_image = cover_image
        article.save()
    
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

    # Updatable text fields
    text_fields = {
        'title': 'title',
        'content': 'content',
        'excerpt': 'excerpt',
        'meta_title': 'meta_title',
        'meta_description': 'meta_description',
        'meta_keywords': 'meta_keywords',
    }
    for param, field in text_fields.items():
        if param in data:
            setattr(article, field, data[param])
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
    
    # Create resource
    resource = Resource.objects.create(
        title=title,
        slug=slug,
        description=description,
        category=category,
        resource_type=resource_type,
        external_url=request.data.get('external_url', ''),
        youtube_url=request.data.get('youtube_url', ''),
        author=request.data.get('author', ''),
        is_featured=request.data.get('is_featured', False),
        is_active=True,
        # N8N tracking fields
        source='n8n',
        source_url=request.data.get('source_url', ''),
        source_id=request.data.get('source_id', ''),
        n8n_workflow_id=request.data.get('workflow_id', ''),
        n8n_execution_id=request.data.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=request.data.get('is_ai_generated', False),
        ai_model=request.data.get('ai_model', ''),
    )
    
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
    
    # Create video
    video = Video.objects.create(
        youtube_id=youtube_id,
        title=request.data.get('title', ''),  # Auto fetch from YouTube if empty
        description=request.data.get('description', ''),
        language=language,
        level=level,
        is_featured=request.data.get('is_featured', False),
        is_active=True,
        # N8N tracking fields
        source='n8n',
        source_url=request.data.get('source_url', ''),
        source_id=source_id or '',
        n8n_workflow_id=request.data.get('workflow_id', ''),
        n8n_execution_id=request.data.get('execution_id', ''),
        n8n_created_at=timezone.now(),
        is_ai_generated=request.data.get('is_ai_generated', False),
        ai_model=request.data.get('ai_model', ''),
    )
    
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

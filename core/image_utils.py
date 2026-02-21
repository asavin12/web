"""
Utility functions for image processing and WebP conversion.
Supports:
- Auto WebP conversion on model save
- Responsive image generation (multiple sizes for srcset)
- Image download from URL (for n8n automation)
- Auto thumbnail generation
- Placeholder image generation
"""

import os
import re
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils.text import slugify

logger = logging.getLogger(__name__)

# Image formats to convert to WebP
CONVERTIBLE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

# Maximum image dimensions
MAX_IMAGE_SIZE = (1920, 1920)

# WebP quality settings
WEBP_QUALITY = {
    'high': 90,
    'medium': 80,
    'low': 70,
    'thumbnail': 60,
}

# Prefix for uploaded images
IMAGE_PREFIX = 'unstressvn'

# Responsive image breakpoints (width in px)
RESPONSIVE_SIZES = {
    'sm': 480,
    'md': 768,
    'lg': 1200,
    'xl': 1920,
}

# Default thumbnail size
THUMBNAIL_SIZE = (400, 267)

# Placeholder image colors (vintage theme)
PLACEHOLDER_COLORS = [
    ('#6B4F3A', '#D4C5A9'),  # Brown / Cream
    ('#2D4A3E', '#A8C5B8'),  # Dark Green / Light Green
    ('#4A3B5C', '#C5B8D4'),  # Purple / Lavender
    ('#5C3B3B', '#D4B8B8'),  # Dark Red / Pink
    ('#3B4A5C', '#B8C5D4'),  # Navy / Light Blue
]


def sanitize_filename(filename):
    """Sanitize filename to be safe for filesystem"""
    # Remove extension for processing
    name, ext = os.path.splitext(filename)
    # Convert to slug-friendly format
    safe_name = slugify(name, allow_unicode=False)
    if not safe_name:
        safe_name = 'image'
    return safe_name


def generate_image_filename(slug=None, original_name=None, suffix='', ext='.webp'):
    """
    Generate standardized image filename with unstressvn prefix
    
    Args:
        slug: Article/post slug (optional)
        original_name: Original filename (used if no slug)
        suffix: Additional suffix (e.g., 'thumb', 'og')
        ext: File extension
    
    Returns:
        Filename like 'unstressvn-my-article-slug.webp'
    """
    if slug:
        base_name = slugify(slug)
    elif original_name:
        base_name = sanitize_filename(original_name)
    else:
        base_name = 'image'
    
    # Build filename
    parts = [IMAGE_PREFIX, base_name]
    if suffix:
        parts.append(suffix)
    
    filename = '-'.join(parts) + ext
    return filename


def should_convert_to_webp(filename):
    """Check if file should be converted to WebP"""
    if not filename:
        return False
    ext = os.path.splitext(filename.lower())[1]
    return ext in CONVERTIBLE_FORMATS


def convert_to_webp(image_field, quality='medium', max_size=None, preserve_alpha=True, 
                    slug=None, suffix=''):
    """
    Convert an image field to WebP format
    
    Args:
        image_field: Django ImageField or File object
        quality: 'high', 'medium', 'low', 'thumbnail' or int (1-100)
        max_size: Tuple (width, height) to resize to, None for no resize
        preserve_alpha: Keep transparency if present
        slug: Article/post slug for naming (prefix: unstressvn-)
        suffix: Additional suffix for filename (e.g., 'thumb', 'og')
        
    Returns:
        ContentFile with WebP image or None on error
    """
    if not image_field:
        return None
    
    try:
        # Get quality value
        if isinstance(quality, str):
            quality_value = WEBP_QUALITY.get(quality, 80)
        else:
            quality_value = quality
        
        # Open image
        img = Image.open(image_field)
        
        # Get original filename for fallback
        if hasattr(image_field, 'name'):
            original_name = os.path.splitext(os.path.basename(image_field.name))[0]
        else:
            original_name = 'image'
        
        # Resize if max_size specified
        if max_size:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        elif img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
            img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Handle transparency
        if preserve_alpha and img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality_value, optimize=True)
        output.seek(0)
        
        # Generate filename with unstressvn prefix
        new_filename = generate_image_filename(
            slug=slug, 
            original_name=original_name, 
            suffix=suffix,
            ext='.webp'
        )
        
        return ContentFile(output.read(), name=new_filename)
        
    except Exception as e:
        logger.error(f"Error converting to WebP: {e}")
        return None


def create_thumbnail(image_field, size=(300, 300), quality='thumbnail', slug=None):
    """
    Create a thumbnail from image
    
    Args:
        image_field: Django ImageField or File object
        size: Tuple (width, height) for thumbnail
        quality: WebP quality setting
        slug: Article/post slug for naming
        
    Returns:
        ContentFile with thumbnail or None on error
    """
    if not image_field:
        return None
    
    try:
        # Get quality value
        if isinstance(quality, str):
            quality_value = WEBP_QUALITY.get(quality, 60)
        else:
            quality_value = quality
        
        # Open image
        img = Image.open(image_field)
        
        # Get original filename for fallback
        if hasattr(image_field, 'name'):
            original_name = os.path.splitext(os.path.basename(image_field.name))[0]
        else:
            original_name = 'image'
        
        # Create thumbnail
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert mode
        if img.mode in ('RGBA', 'LA', 'P'):
            if img.mode == 'P':
                img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality_value, optimize=True)
        output.seek(0)
        
        # Generate thumbnail filename
        new_filename = generate_image_filename(
            slug=slug,
            original_name=original_name,
            suffix='thumb',
            ext='.webp'
        )
        
        return ContentFile(output.read(), name=new_filename)
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {e}")
        return None


def download_image_from_url(url, timeout=30):
    """
    Download image from URL and return as BytesIO.
    Used by n8n API to fetch images from external URLs.
    
    Args:
        url: Image URL to download
        timeout: Request timeout in seconds
        
    Returns:
        (BytesIO, original_filename) tuple or (None, None) on error
    """
    import urllib.request
    import urllib.error
    from urllib.parse import urlparse
    
    if not url:
        return None, None
    
    try:
        # Parse URL for filename
        parsed = urlparse(url)
        path = parsed.path
        original_filename = os.path.basename(path) or 'downloaded-image.jpg'
        
        # Download image
        req = urllib.request.Request(url, headers={
            'User-Agent': 'UnstressVN-Bot/1.0',
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            image_data = response.read()
        
        # Validate it's actually an image
        img_buffer = BytesIO(image_data)
        img = Image.open(img_buffer)
        img.verify()  # Verify it's a valid image
        
        # Reset buffer for actual use
        img_buffer.seek(0)
        
        logger.info(f"Downloaded image from {url} ({len(image_data)} bytes)")
        return img_buffer, original_filename
        
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {e}")
        return None, None


def generate_placeholder_image(title, width=1200, height=630):
    """
    Generate a placeholder cover image with the article title.
    Uses vintage theme colors matching the site design.
    
    Args:
        title: Article title text to display
        width: Image width
        height: Image height
        
    Returns:
        ContentFile with WebP placeholder image
    """
    import hashlib
    
    # Choose color based on title hash for consistency
    color_index = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(PLACEHOLDER_COLORS)
    bg_color, text_color = PLACEHOLDER_COLORS[color_index]
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default
    font_size = 48
    small_font_size = 24
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", small_font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
        small_font = font
    
    # Draw decorative border
    border = 20
    draw.rectangle(
        [border, border, width - border, height - border],
        outline=text_color, width=2
    )
    
    # Draw "UnstressVN" brand at top
    brand_text = "UnstressVN"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=small_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(((width - brand_w) / 2, 40), brand_text, fill=text_color, font=small_font)
    
    # Draw decorative line under brand
    line_y = 80
    draw.line([(width // 4, line_y), (3 * width // 4, line_y)], fill=text_color, width=1)
    
    # Word-wrap title text
    max_chars_per_line = 30
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if len(test_line) <= max_chars_per_line:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Limit to 4 lines max
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] = lines[-1][:max_chars_per_line - 3] + "..."
    
    # Calculate text position (centered vertically)
    line_height = font_size + 10
    total_text_height = len(lines) * line_height
    start_y = (height - total_text_height) / 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) / 2
        y = start_y + i * line_height
        draw.text((x, y), line, fill=text_color, font=font)
    
    # Draw decorative line at bottom
    draw.line([(width // 4, height - 60), (3 * width // 4, height - 60)], fill=text_color, width=1)
    
    # Save as WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=85, optimize=True)
    output.seek(0)
    
    return ContentFile(output.read(), name='placeholder.webp')


def generate_responsive_images(image_field, slug, upload_to, quality='medium'):
    """
    Generate multiple responsive image sizes for srcset.
    Saves images to storage and returns a dict of size → URL.
    
    Args:
        image_field: Django ImageField or File object with image data
        slug: Article slug for naming
        upload_to: Base directory (e.g., 'news/covers/')
        quality: WebP quality setting
        
    Returns:
        dict like {'sm': '/media/news/covers/unstressvn-slug-cover-480w.webp', ...}
        or empty dict on error
    """
    if not image_field:
        return {}
    
    try:
        # Get quality value
        if isinstance(quality, str):
            quality_value = WEBP_QUALITY.get(quality, 80)
        else:
            quality_value = quality
        
        # Open image
        if hasattr(image_field, 'read'):
            image_field.seek(0)
        img = Image.open(image_field)
        original_width = img.size[0]
        
        srcset = {}
        
        for size_name, target_width in RESPONSIVE_SIZES.items():
            # Skip sizes larger than original
            if target_width >= original_width:
                continue
            
            # Resize maintaining aspect ratio
            ratio = target_width / original_width
            target_height = int(img.size[1] * ratio)
            resized = img.copy()
            resized = resized.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Convert mode for WebP
            if resized.mode in ('RGBA', 'LA', 'P'):
                if resized.mode == 'P':
                    resized = resized.convert('RGBA')
            elif resized.mode != 'RGB':
                resized = resized.convert('RGB')
            
            # Save to buffer
            output = BytesIO()
            resized.save(output, format='WEBP', quality=quality_value, optimize=True)
            output.seek(0)
            
            # Generate filename
            filename = generate_image_filename(
                slug=slug,
                suffix=f'cover-{target_width}w',
                ext='.webp'
            )
            
            # Save to storage
            filepath = os.path.join(upload_to.rstrip('/'), filename)
            saved_path = default_storage.save(filepath, ContentFile(output.read()))
            srcset[size_name] = default_storage.url(saved_path)
        
        # Add the original/full-size URL (will be set by caller from cover_image.url)
        # The 'xl' key is reserved for the original cover_image URL
        
        logger.info(f"Generated {len(srcset)} responsive images for '{slug}'")
        return srcset
        
    except Exception as e:
        logger.error(f"Error generating responsive images: {e}")
        return {}


def cleanup_responsive_images(srcset_dict):
    """
    Delete responsive image files from storage when article is updated/deleted.
    
    Args:
        srcset_dict: Dict of size → URL from cover_image_srcset field
    """
    if not srcset_dict:
        return
    
    for size_name, url in srcset_dict.items():
        try:
            # Extract path from URL
            if url.startswith('/media/'):
                filepath = url[len('/media/'):]
            elif url.startswith('http'):
                from urllib.parse import urlparse
                filepath = urlparse(url).path
                if filepath.startswith('/media/'):
                    filepath = filepath[len('/media/'):]
            else:
                filepath = url
            
            if default_storage.exists(filepath):
                default_storage.delete(filepath)
                logger.info(f"Deleted responsive image: {filepath}")
        except Exception as e:
            logger.warning(f"Could not delete responsive image {url}: {e}")


class WebPImageMixin:
    """
    Mixin for Django models to auto-convert images to WebP with unstressvn- prefix.
    
    Features:
    - Auto WebP conversion on save
    - Auto thumbnail generation from cover_image
    - Auto responsive image generation (srcset)
    
    Usage:
        class MyModel(WebPImageMixin, models.Model):
            title = models.CharField(max_length=255)
            slug = models.SlugField()
            cover_image = models.ImageField(upload_to='images/')
            thumbnail = models.ImageField(upload_to='images/thumbs/', blank=True)
            cover_image_srcset = models.JSONField(default=dict, blank=True)
            
            WEBP_FIELDS = ['cover_image', 'thumbnail']
            WEBP_SLUG_FIELD = 'slug'
            WEBP_AUTO_THUMBNAIL = True  # Auto-generate thumbnail from cover_image
            WEBP_RESPONSIVE = True       # Auto-generate responsive sizes
    """
    
    WEBP_FIELDS = []
    WEBP_QUALITY = 'high'
    WEBP_MAX_SIZE = MAX_IMAGE_SIZE
    WEBP_SLUG_FIELD = 'slug'
    WEBP_THUMBNAIL_FIELDS = []
    WEBP_AUTO_THUMBNAIL = True  # Auto-generate thumbnail from cover_image
    WEBP_RESPONSIVE = True       # Auto-generate responsive images for srcset
    
    def _get_slug_for_image(self):
        """Get slug value for image naming"""
        slug_field = getattr(self, 'WEBP_SLUG_FIELD', 'slug')
        return getattr(self, slug_field, None) or ''
    
    def _is_new_upload(self, field):
        """Check if this field has a new file upload"""
        if not field:
            return False
        if hasattr(field, 'file') and hasattr(field.file, 'content_type'):
            return True
        return False
    
    def save(self, *args, **kwargs):
        slug = self._get_slug_for_image()
        cover_image_updated = False
        
        for field_name in self.WEBP_FIELDS:
            field = getattr(self, field_name, None)
            if field and should_convert_to_webp(field.name):
                if self._is_new_upload(field):
                    # Determine suffix based on field name
                    suffix = ''
                    if 'thumb' in field_name:
                        suffix = 'thumb'
                    elif 'og' in field_name:
                        suffix = 'og'
                    elif 'cover' in field_name:
                        suffix = 'cover'
                    
                    webp_content = convert_to_webp(
                        field, 
                        quality=self.WEBP_QUALITY,
                        max_size=self.WEBP_MAX_SIZE,
                        slug=slug,
                        suffix=suffix
                    )
                    if webp_content:
                        setattr(self, field_name, webp_content)
                        if field_name == 'cover_image':
                            cover_image_updated = True
        
        # Auto-generate thumbnail from cover_image
        if getattr(self, 'WEBP_AUTO_THUMBNAIL', True) and cover_image_updated:
            cover = getattr(self, 'cover_image', None)
            if cover and hasattr(self, 'thumbnail'):
                thumb = create_thumbnail(cover, size=THUMBNAIL_SIZE, slug=slug)
                if thumb:
                    self.thumbnail = thumb
        
        # Generate thumbnails for specified fields (legacy support)
        for field_name in getattr(self, 'WEBP_THUMBNAIL_FIELDS', []):
            field = getattr(self, field_name, None)
            thumbnail_field = f"{field_name.replace('_image', '')}_thumbnail"
            if field and hasattr(self, thumbnail_field):
                if hasattr(field, 'file'):
                    thumb = create_thumbnail(field, slug=slug)
                    if thumb:
                        setattr(self, thumbnail_field, thumb)
        
        # Save the model first to get cover_image URL
        super().save(*args, **kwargs)
        
        # Generate responsive images after save (needs cover_image URL)
        if getattr(self, 'WEBP_RESPONSIVE', True) and cover_image_updated:
            self._generate_responsive_set()
    
    def _generate_responsive_set(self):
        """Generate responsive image sizes and store srcset data"""
        cover = getattr(self, 'cover_image', None)
        if not cover or not hasattr(self, 'cover_image_srcset'):
            return
        
        slug = self._get_slug_for_image()
        upload_to = cover.field.upload_to if hasattr(cover, 'field') else 'images/'
        
        # Clean up old responsive images
        old_srcset = getattr(self, 'cover_image_srcset', None)
        if old_srcset:
            cleanup_responsive_images(old_srcset)
        
        # Generate new responsive images
        try:
            cover.open('rb')
            srcset = generate_responsive_images(
                cover, slug, upload_to, quality=self.WEBP_QUALITY
            )
            cover.close()
        except Exception as e:
            logger.warning(f"Could not generate responsive images: {e}")
            srcset = {}
        
        # Add the original (xl) URL
        if cover:
            srcset['xl'] = cover.url
        
        # Update the srcset field without triggering save() again
        if srcset:
            type(self).objects.filter(pk=self.pk).update(cover_image_srcset=srcset)
            self.cover_image_srcset = srcset

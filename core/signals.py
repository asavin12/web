"""
Signals để tự động convert images sang WebP khi upload
"""

import os
from io import BytesIO
from PIL import Image
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from accounts.models import UserProfile
from resources.models import Resource


def convert_image_to_webp(image_field, quality=85):
    """Convert an image field to WebP format"""
    if not image_field:
        return None
    
    try:
        # Open image
        img = Image.open(image_field)
        
        # Get original filename
        original_name = os.path.splitext(image_field.name)[0]
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            # Keep alpha channel for WebP
            if img.mode == 'P':
                img = img.convert('RGBA')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        
        # Create new filename with .webp extension
        new_filename = f"{original_name}.webp"
        
        return ContentFile(output.read(), name=new_filename)
    except Exception as e:
        print(f"Error converting to WebP: {e}")
        return None


def should_convert_to_webp(filename):
    """Check if file should be converted to WebP"""
    if not filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']


@receiver(pre_save, sender=UserProfile)
def convert_avatar_to_webp(sender, instance, **kwargs):
    """Convert avatar to WebP before saving"""
    if not instance.avatar or not should_convert_to_webp(instance.avatar.name):
        return
    try:
        # Only convert newly uploaded files (not existing files from storage)
        if hasattr(instance.avatar.file, 'content_type'):
            webp_content = convert_image_to_webp(instance.avatar)
            if webp_content:
                instance.avatar = webp_content
    except (FileNotFoundError, ValueError, OSError):
        # File doesn't exist on disk or storage error — skip conversion
        pass


@receiver(pre_save, sender=Resource)
def convert_resource_cover_to_webp(sender, instance, **kwargs):
    """Convert resource cover to WebP before saving"""
    if instance.cover_image and should_convert_to_webp(instance.cover_image.name):
        if hasattr(instance.cover_image.file, 'content_type'):
            webp_content = convert_image_to_webp(instance.cover_image)
            if webp_content:
                instance.cover_image = webp_content

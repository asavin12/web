#!/usr/bin/env python
"""
Script để convert tất cả ảnh trong thư mục media sang WebP
và đổi tên theo chuẩn unstressvn-[slug].webp
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

import django
django.setup()

from PIL import Image
from django.conf import settings
from django.utils.text import slugify


# Image formats to convert
CONVERTIBLE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}

# WebP quality
WEBP_QUALITY = 85


def sanitize_filename(filename):
    """Convert filename to slug-friendly format"""
    name = os.path.splitext(filename)[0]
    safe_name = slugify(name, allow_unicode=False)
    return safe_name if safe_name else 'image'


def convert_image_to_webp(source_path, delete_original=True):
    """
    Convert an image to WebP format with unstressvn- prefix
    
    Args:
        source_path: Path to source image
        delete_original: Whether to delete original file after conversion
        
    Returns:
        New file path or None on error
    """
    try:
        source_path = Path(source_path)
        ext = source_path.suffix.lower()
        
        if ext not in CONVERTIBLE_FORMATS:
            return None
        
        # Generate new filename
        original_name = source_path.stem
        safe_name = sanitize_filename(original_name)
        new_name = f"unstressvn-{safe_name}.webp"
        new_path = source_path.parent / new_name
        
        # Handle duplicate names
        counter = 1
        while new_path.exists():
            new_name = f"unstressvn-{safe_name}-{counter}.webp"
            new_path = source_path.parent / new_name
            counter += 1
        
        # Open and convert
        with Image.open(source_path) as img:
            # Handle transparency
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = (1920, 1920)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as WebP
            img.save(new_path, format='WEBP', quality=WEBP_QUALITY, optimize=True)
        
        print(f"✅ {source_path.name} -> {new_name}")
        
        # Delete original if requested
        if delete_original:
            source_path.unlink()
            print(f"   🗑️ Deleted: {source_path.name}")
        
        return new_path
        
    except Exception as e:
        print(f"❌ Error converting {source_path}: {e}")
        return None


def scan_and_convert(directory, delete_original=True):
    """
    Scan directory and convert all images to WebP
    
    Args:
        directory: Directory to scan
        delete_original: Whether to delete original files
        
    Returns:
        Tuple (converted_count, error_count)
    """
    directory = Path(directory)
    converted = 0
    errors = 0
    
    print(f"\n📂 Scanning: {directory}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in CONVERTIBLE_FORMATS:
                source_path = Path(root) / filename
                result = convert_image_to_webp(source_path, delete_original)
                if result:
                    converted += 1
                else:
                    errors += 1
    
    return converted, errors


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert media images to WebP')
    parser.add_argument('--keep-original', action='store_true', 
                        help='Keep original files after conversion')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be converted without actually converting')
    args = parser.parse_args()
    
    media_root = Path(settings.MEDIA_ROOT)
    
    if args.dry_run:
        print("🔍 DRY RUN - Scanning for images to convert...")
        count = 0
        for root, dirs, files in os.walk(media_root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in CONVERTIBLE_FORMATS:
                    print(f"  Would convert: {os.path.join(root, filename)}")
                    count += 1
        print(f"\n📊 Total: {count} files would be converted")
        return
    
    print("🖼️ UnstressVN Media WebP Converter")
    print("=" * 60)
    print(f"Media root: {media_root}")
    print(f"Delete originals: {not args.keep_original}")
    
    # Confirm before proceeding
    response = input("\n⚠️ This will convert all images. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    converted, errors = scan_and_convert(media_root, not args.keep_original)
    
    print("\n" + "=" * 60)
    print(f"✅ Converted: {converted} files")
    print(f"❌ Errors: {errors} files")
    print("\n💡 Remember to update database references if needed!")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Convert PNG logo to SVG and WebP formats
Generates multiple sizes while maintaining aspect ratio (zoom in/out only)
"""

import os
import sys
import base64
from pathlib import Path
from io import BytesIO

# Add project to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# Output directories
OUTPUT_DIR = project_root / 'static' / 'logos'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Source logo
SOURCE_LOGO = project_root / 'logo-source.png'


def get_logo_image():
    """Load and return the source logo image"""
    if not SOURCE_LOGO.exists():
        print(f"Error: Source logo not found: {SOURCE_LOGO}")
        return None
    
    img = Image.open(SOURCE_LOGO)
    print(f"Source logo: {SOURCE_LOGO}")
    print(f"Original size: {img.size[0]}x{img.size[1]}")
    
    # Ensure RGBA mode
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    return img


def resize_maintain_aspect(img, target_size):
    """
    Resize image maintaining aspect ratio (zoom in/out)
    target_size can be:
    - int: create square with this as max dimension
    - tuple (w, h): fit within this box
    """
    if isinstance(target_size, int):
        target_size = (target_size, target_size)
    
    original_w, original_h = img.size
    target_w, target_h = target_size
    
    # Calculate scale to fit within target, maintaining aspect ratio
    scale = min(target_w / original_w, target_h / original_h)
    
    new_w = int(original_w * scale)
    new_h = int(original_h * scale)
    
    # Use high-quality resampling
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    return resized


def create_webp(img, output_path, quality=90):
    """Save image as WebP with transparency support"""
    try:
        img.save(output_path, format='WEBP', quality=quality, lossless=False)
        print(f"✓ Created: {output_path.name} ({img.size[0]}x{img.size[1]})")
        return True
    except Exception as e:
        print(f"✗ Error creating {output_path.name}: {e}")
        return False


def create_svg_from_png(img, output_path, embed_size=None):
    """
    Create SVG with embedded PNG (base64)
    This preserves all details and supports transparency
    """
    if embed_size:
        img = resize_maintain_aspect(img, embed_size)
    
    w, h = img.size
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Create SVG with embedded image
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{w}" height="{h}" 
     viewBox="0 0 {w} {h}">
  <image width="{w}" height="{h}" 
         xlink:href="data:image/png;base64,{base64_data}"/>
</svg>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"✓ Created: {output_path.name} ({w}x{h})")
    return True


def create_vector_favicon(output_path, size=32):
    """
    Create a pure vector SVG favicon (simplified design)
    This is lightweight and scales infinitely
    """
    # Colors from UnstressVN theme
    olive = '#6B705C'
    tan = '#A5A58D'
    
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{olive}"/>
      <stop offset="100%" style="stop-color:{tan}"/>
    </linearGradient>
  </defs>
  <!-- Background -->
  <rect x="2" y="2" width="{size-4}" height="{size-4}" rx="6" fill="url(#bg)"/>
  <!-- Letter U -->
  <path d="M {size*0.28} {size*0.25} 
           L {size*0.28} {size*0.55} 
           Q {size*0.28} {size*0.75} {size*0.5} {size*0.75} 
           Q {size*0.72} {size*0.75} {size*0.72} {size*0.55} 
           L {size*0.72} {size*0.25}" 
        stroke="white" 
        stroke-width="{size*0.1}" 
        stroke-linecap="round" 
        fill="none"/>
</svg>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"✓ Created: {output_path.name} (vector {size}x{size})")
    return True


def main():
    """Generate all logo variants"""
    print("\n" + "="*50)
    print("  UnstressVN Logo Generator")
    print("="*50 + "\n")
    
    # Load source logo
    img = get_logo_image()
    if img is None:
        return
    
    print("\n--- Generating WebP variants ---")
    
    # WebP variants (maintain aspect ratio)
    webp_sizes = {
        'unstressvn-logo-full.webp': 512,      # Full size for about page
        'unstressvn-logo-header.webp': 150,    # Header/navbar
        'unstressvn-logo-footer.webp': 120,    # Footer
        'unstressvn-icon-medium.webp': 80,     # Medium icon
        'unstressvn-og-image.webp': 400,       # Open Graph / social share
    }
    
    for filename, size in webp_sizes.items():
        resized = resize_maintain_aspect(img, size)
        create_webp(resized, OUTPUT_DIR / filename)
    
    print("\n--- Generating SVG variants ---")
    
    # SVG with embedded PNG (for high quality display)
    create_svg_from_png(img, OUTPUT_DIR / 'unstressvn-logo.svg', embed_size=200)
    create_svg_from_png(img, OUTPUT_DIR / 'unstressvn-header.svg', embed_size=150)
    create_svg_from_png(img, OUTPUT_DIR / 'unstressvn-footer.svg', embed_size=120)
    
    # Pure vector favicon (lightweight)
    create_vector_favicon(OUTPUT_DIR / 'favicon.svg', size=32)
    create_vector_favicon(OUTPUT_DIR / 'icon-small.svg', size=24)
    
    # OG image as SVG
    create_svg_from_png(img, OUTPUT_DIR / 'unstressvn-og.svg', embed_size=400)
    
    print("\n" + "="*50)
    print(f"✅ All logos generated in: {OUTPUT_DIR}")
    print("="*50 + "\n")
    
    # Run collectstatic
    print("Running collectstatic...")
    os.chdir(project_root)
    os.system(f"{sys.executable} manage.py collectstatic --noinput")


if __name__ == '__main__':
    main()

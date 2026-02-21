#!/usr/bin/env python3
"""
Convert PNG logo to SVG format
Since PNG is raster and SVG is vector, we'll create a clean SVG logo
with text and simple shapes instead of tracing the bitmap
"""

import svgwrite
from pathlib import Path

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'static' / 'logos'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_logo_svg(size=200, include_text=True):
    """Create a clean vector SVG logo for UnstressVN"""
    
    dwg = svgwrite.Drawing(
        str(OUTPUT_DIR / 'unstressvn-logo.svg'),
        size=(size, size),
        viewBox=f"0 0 {size} {size}"
    )
    
    # Define colors
    olive = '#6B705C'
    tan = '#A5A58D'
    cream = '#F5F5DC'
    brown = '#8B7355'
    
    # Create gradient
    gradient = dwg.defs.add(dwg.linearGradient(
        id='logoGradient',
        x1='0%', y1='0%', x2='100%', y2='100%'
    ))
    gradient.add_stop_color(offset='0%', color=olive)
    gradient.add_stop_color(offset='100%', color=tan)
    
    # Background rounded rectangle
    padding = size * 0.1
    corner_radius = size * 0.15
    
    dwg.add(dwg.rect(
        insert=(padding, padding),
        size=(size - 2*padding, size - 2*padding),
        rx=corner_radius, ry=corner_radius,
        fill='url(#logoGradient)'
    ))
    
    # Letter "U" - main icon
    u_group = dwg.g(fill='white')
    
    # U shape using path
    u_size = size * 0.45
    u_x = size * 0.275
    u_y = size * 0.25
    stroke_width = size * 0.08
    
    # Create U path
    u_path = dwg.path(
        d=f"M {u_x} {u_y} "
          f"L {u_x} {u_y + u_size * 0.6} "
          f"Q {u_x} {u_y + u_size} {u_x + u_size * 0.5} {u_y + u_size} "
          f"Q {u_x + u_size} {u_y + u_size} {u_x + u_size} {u_y + u_size * 0.6} "
          f"L {u_x + u_size} {u_y}",
        stroke='white',
        stroke_width=stroke_width,
        stroke_linecap='round',
        fill='none'
    )
    dwg.add(u_path)
    
    dwg.save()
    print(f"✓ Created: {OUTPUT_DIR / 'unstressvn-logo.svg'}")
    return str(OUTPUT_DIR / 'unstressvn-logo.svg')


def create_favicon_svg(size=32):
    """Create favicon SVG"""
    
    dwg = svgwrite.Drawing(
        str(OUTPUT_DIR / 'favicon.svg'),
        size=(size, size),
        viewBox=f"0 0 {size} {size}"
    )
    
    # Colors
    olive = '#6B705C'
    tan = '#A5A58D'
    
    # Gradient
    gradient = dwg.defs.add(dwg.linearGradient(
        id='favGradient',
        x1='0%', y1='0%', x2='100%', y2='100%'
    ))
    gradient.add_stop_color(offset='0%', color=olive)
    gradient.add_stop_color(offset='100%', color=tan)
    
    # Background
    corner = size * 0.2
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=(size, size),
        rx=corner, ry=corner,
        fill='url(#favGradient)'
    ))
    
    # Letter U
    dwg.add(dwg.text(
        'U',
        insert=(size/2, size * 0.72),
        text_anchor='middle',
        font_size=size * 0.6,
        font_family='Georgia, serif',
        font_weight='bold',
        fill='white'
    ))
    
    dwg.save()
    print(f"✓ Created: {OUTPUT_DIR / 'favicon.svg'}")


def create_header_logo_svg():
    """Create header logo with text"""
    
    width = 200
    height = 50
    
    dwg = svgwrite.Drawing(
        str(OUTPUT_DIR / 'unstressvn-header.svg'),
        size=(width, height),
        viewBox=f"0 0 {width} {height}"
    )
    
    # Colors
    olive = '#6B705C'
    tan = '#A5A58D'
    
    # Gradient for icon
    gradient = dwg.defs.add(dwg.linearGradient(
        id='headerGradient',
        x1='0%', y1='0%', x2='100%', y2='100%'
    ))
    gradient.add_stop_color(offset='0%', color=olive)
    gradient.add_stop_color(offset='100%', color=tan)
    
    # Icon background
    icon_size = 40
    icon_x = 5
    icon_y = 5
    
    dwg.add(dwg.rect(
        insert=(icon_x, icon_y),
        size=(icon_size, icon_size),
        rx=8, ry=8,
        fill='url(#headerGradient)'
    ))
    
    # Letter U in icon
    dwg.add(dwg.text(
        'U',
        insert=(icon_x + icon_size/2, icon_y + icon_size * 0.72),
        text_anchor='middle',
        font_size=24,
        font_family='Georgia, serif',
        font_weight='bold',
        fill='white'
    ))
    
    # Text "UnstressVN"
    dwg.add(dwg.text(
        'UnstressVN',
        insert=(55, 32),
        font_size=22,
        font_family='Georgia, serif',
        font_weight='bold',
        fill=olive
    ))
    
    # Tagline
    dwg.add(dwg.text(
        'HỌC NGOẠI NGỮ DỄ DÀNG',
        insert=(55, 44),
        font_size=7,
        font_family='Arial, sans-serif',
        font_weight='bold',
        letter_spacing='2px',
        fill=tan
    ))
    
    dwg.save()
    print(f"✓ Created: {OUTPUT_DIR / 'unstressvn-header.svg'}")


def create_footer_logo_svg():
    """Create footer logo (white version)"""
    
    width = 180
    height = 45
    
    dwg = svgwrite.Drawing(
        str(OUTPUT_DIR / 'unstressvn-footer.svg'),
        size=(width, height),
        viewBox=f"0 0 {width} {height}"
    )
    
    # Colors for dark background
    cream = '#F5F5DC'
    tan = '#D4C5A9'
    olive = '#6B705C'
    
    # Icon background
    icon_size = 35
    icon_x = 5
    icon_y = 5
    
    dwg.add(dwg.rect(
        insert=(icon_x, icon_y),
        size=(icon_size, icon_size),
        rx=7, ry=7,
        fill=olive
    ))
    
    # Letter U
    dwg.add(dwg.text(
        'U',
        insert=(icon_x + icon_size/2, icon_y + icon_size * 0.72),
        text_anchor='middle',
        font_size=20,
        font_family='Georgia, serif',
        font_weight='bold',
        fill=cream
    ))
    
    # Text
    dwg.add(dwg.text(
        'UnstressVN',
        insert=(48, 28),
        font_size=20,
        font_family='Georgia, serif',
        font_weight='bold',
        fill=cream
    ))
    
    # Tagline
    dwg.add(dwg.text(
        'HỌC NGOẠI NGỮ DỄ DÀNG',
        insert=(48, 40),
        font_size=6,
        font_family='Arial, sans-serif',
        font_weight='bold',
        letter_spacing='1.5px',
        fill=tan
    ))
    
    dwg.save()
    print(f"✓ Created: {OUTPUT_DIR / 'unstressvn-footer.svg'}")


def create_og_image_svg():
    """Create OG image for social sharing"""
    
    width = 1200
    height = 630
    
    dwg = svgwrite.Drawing(
        str(OUTPUT_DIR / 'unstressvn-og.svg'),
        size=(width, height),
        viewBox=f"0 0 {width} {height}"
    )
    
    # Colors
    olive = '#6B705C'
    tan = '#A5A58D'
    cream = '#F5F5DC'
    dark = '#2D2D2D'
    
    # Background gradient
    bg_gradient = dwg.defs.add(dwg.linearGradient(
        id='bgGradient',
        x1='0%', y1='0%', x2='100%', y2='100%'
    ))
    bg_gradient.add_stop_color(offset='0%', color=cream)
    bg_gradient.add_stop_color(offset='100%', color='#E8E4D9')
    
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=(width, height),
        fill='url(#bgGradient)'
    ))
    
    # Decorative border
    dwg.add(dwg.rect(
        insert=(20, 20),
        size=(width-40, height-40),
        rx=20, ry=20,
        fill='none',
        stroke=tan,
        stroke_width=3
    ))
    
    # Logo icon gradient
    logo_gradient = dwg.defs.add(dwg.linearGradient(
        id='logoGrad',
        x1='0%', y1='0%', x2='100%', y2='100%'
    ))
    logo_gradient.add_stop_color(offset='0%', color=olive)
    logo_gradient.add_stop_color(offset='100%', color=tan)
    
    # Logo icon
    icon_size = 120
    icon_x = width/2 - icon_size/2
    icon_y = 150
    
    dwg.add(dwg.rect(
        insert=(icon_x, icon_y),
        size=(icon_size, icon_size),
        rx=25, ry=25,
        fill='url(#logoGrad)'
    ))
    
    # Letter U
    dwg.add(dwg.text(
        'U',
        insert=(width/2, icon_y + icon_size * 0.72),
        text_anchor='middle',
        font_size=72,
        font_family='Georgia, serif',
        font_weight='bold',
        fill='white'
    ))
    
    # Main title
    dwg.add(dwg.text(
        'UnstressVN',
        insert=(width/2, 360),
        text_anchor='middle',
        font_size=80,
        font_family='Georgia, serif',
        font_weight='bold',
        fill=olive
    ))
    
    # Tagline
    dwg.add(dwg.text(
        'Học Ngoại Ngữ Dễ Dàng',
        insert=(width/2, 430),
        text_anchor='middle',
        font_size=36,
        font_family='Georgia, serif',
        font_style='italic',
        fill=tan
    ))
    
    # Features
    features = ['📚 Tài liệu phong phú', '🎬 Video bài giảng', '📰 Tin tức & Kiến thức']
    for i, feature in enumerate(features):
        dwg.add(dwg.text(
            feature,
            insert=(width/2, 500 + i*40),
            text_anchor='middle',
            font_size=24,
            font_family='Arial, sans-serif',
            fill=dark
        ))
    
    dwg.save()
    print(f"✓ Created: {OUTPUT_DIR / 'unstressvn-og.svg'}")


if __name__ == '__main__':
    print("=" * 50)
    print("Creating SVG logos for UnstressVN")
    print("=" * 50)
    
    create_logo_svg()
    create_favicon_svg()
    create_header_logo_svg()
    create_footer_logo_svg()
    create_og_image_svg()
    
    print("\n✅ All SVG logos created successfully!")
    print(f"📁 Output directory: {OUTPUT_DIR}")

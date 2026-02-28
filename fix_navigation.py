#!/usr/bin/env python3
"""
Fix navigation data — Sửa URLs, thêm Stream Media, thêm dropdown submenus,
fix footer links, thêm i18n names.
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import NavigationLink

def fix_navigation():
    print("=" * 60)
    print("🔧 FIX NAVIGATION DATA")
    print("=" * 60)
    
    # ════════════════════════════════════════
    # 1. FIX NAVBAR LINKS — correct URLs & icons
    # ════════════════════════════════════════
    
    fixes = {
        # id: {fields to update}
        1: {'icon': 'Home', 'name_vi': 'Trang chủ', 'name_en': 'Home', 'name_de': 'Startseite'},
        2: {'url': '/video', 'icon': 'Video', 'name': 'Video', 'name_vi': 'Video', 'name_en': 'Videos', 'name_de': 'Videos'},
        3: {'url': '/tai-lieu', 'icon': 'BookOpen', 'name': 'Thư viện', 'name_vi': 'Thư viện', 'name_en': 'Library', 'name_de': 'Bibliothek'},
        21: {'icon': 'Newspaper', 'name_vi': 'Tin tức', 'name_en': 'News', 'name_de': 'Nachrichten'},
        22: {'icon': 'GraduationCap', 'name_vi': 'Kiến thức', 'name_en': 'Knowledge', 'name_de': 'Wissen'},
        23: {'icon': 'Wrench', 'name_vi': 'Công cụ', 'name_en': 'Tools', 'name_de': 'Werkzeuge'},
    }
    
    for link_id, updates in fixes.items():
        try:
            link = NavigationLink.objects.get(id=link_id)
            for field, value in updates.items():
                setattr(link, field, value)
            link.save()
            print(f"  ✅ Fixed navbar #{link_id}: {link.name} → {link.url}")
        except NavigationLink.DoesNotExist:
            print(f"  ⚠️ Navbar #{link_id} not found")
    
    # ════════════════════════════════════════
    # 2. ADD STREAM MEDIA to navbar (order=7)
    # ════════════════════════════════════════
    
    stream_link, created = NavigationLink.objects.get_or_create(
        url='/stream',
        location='navbar',
        parent__isnull=True,
        defaults={
            'name': 'Xem phim',
            'name_vi': 'Xem phim',
            'name_en': 'Watch',
            'name_de': 'Ansehen',
            'icon': 'Play',
            'order': 7,
            'is_active': True,
        }
    )
    if created:
        print(f"  ✅ Created navbar: Xem phim → /stream (id={stream_link.id})")
    else:
        stream_link.name = 'Xem phim'
        stream_link.name_vi = 'Xem phim'
        stream_link.name_en = 'Watch'
        stream_link.name_de = 'Ansehen'
        stream_link.icon = 'Play'
        stream_link.order = 7
        stream_link.is_active = True
        stream_link.save()
        print(f"  ✅ Updated navbar: Xem phim → /stream (id={stream_link.id})")
    
    # ════════════════════════════════════════
    # 3. FIX FOOTER LINKS — correct URLs
    # ════════════════════════════════════════
    
    footer_fixes = {
        6: {'url': '/gioi-thieu', 'name_vi': 'Giới thiệu', 'name_en': 'About', 'name_de': 'Über uns'},
        7: {'url': '/lien-he', 'name_vi': 'Liên hệ', 'name_en': 'Contact', 'name_de': 'Kontakt'},
        9: {'url': '/video?language=en', 'name_vi': 'Video tiếng Anh', 'name_en': 'English Videos', 'name_de': 'Englische Videos'},
        10: {'url': '/video?language=de', 'name_vi': 'Video tiếng Đức', 'name_en': 'German Videos', 'name_de': 'Deutsche Videos'},
        11: {'url': '/tai-lieu', 'name': 'Tài liệu miễn phí', 'name_vi': 'Tài liệu miễn phí', 'name_en': 'Free Resources', 'name_de': 'Kostenlose Materialien'},
        15: {'url': '/dieu-khoan', 'name_vi': 'Điều khoản sử dụng', 'name_en': 'Terms of Use', 'name_de': 'Nutzungsbedingungen'},
        16: {'url': '/chinh-sach-bao-mat', 'name_vi': 'Chính sách bảo mật', 'name_en': 'Privacy Policy', 'name_de': 'Datenschutz'},
    }
    
    for link_id, updates in footer_fixes.items():
        try:
            link = NavigationLink.objects.get(id=link_id)
            for field, value in updates.items():
                setattr(link, field, value)
            link.save()
            print(f"  ✅ Fixed footer #{link_id}: {link.name} → {link.url}")
        except NavigationLink.DoesNotExist:
            print(f"  ⚠️ Footer #{link_id} not found")
    
    # Deactivate non-existent footer links
    for link_id in [8, 14]:  # Việc làm (/careers), Phòng học nhóm (/study-rooms)
        try:
            link = NavigationLink.objects.get(id=link_id)
            link.is_active = False
            link.is_coming_soon = True
            link.badge_text = 'Soon'
            link.save()
            print(f"  ⚠️ Deactivated footer #{link_id}: {link.name} (page doesn't exist yet)")
        except NavigationLink.DoesNotExist:
            pass
    
    # Add Stream to footer resources section
    stream_footer, created = NavigationLink.objects.get_or_create(
        url='/stream',
        location='footer',
        defaults={
            'name': 'Xem phim học ngoại ngữ',
            'name_vi': 'Xem phim học ngoại ngữ',
            'name_en': 'Watch & Learn',
            'name_de': 'Filme zum Lernen',
            'icon': 'Play',
            'footer_section': 'resources',
            'order': 4,
            'is_active': True,
        }
    )
    if created:
        print(f"  ✅ Created footer: Xem phim học ngoại ngữ → /stream")
    else:
        print(f"  ✅ Footer stream already exists")
    
    # Add i18n to social links
    social_i18n = {
        17: {'name_vi': 'Facebook', 'name_en': 'Facebook', 'name_de': 'Facebook', 'icon': 'Facebook'},
        18: {'name_vi': 'YouTube', 'name_en': 'YouTube', 'name_de': 'YouTube', 'icon': 'Youtube'},
        19: {'name_vi': 'TikTok', 'name_en': 'TikTok', 'name_de': 'TikTok', 'icon': 'Music'},
        20: {'name_vi': 'Zalo', 'name_en': 'Zalo', 'name_de': 'Zalo', 'icon': 'MessageSquare'},
    }
    for link_id, updates in social_i18n.items():
        try:
            link = NavigationLink.objects.get(id=link_id)
            for field, value in updates.items():
                setattr(link, field, value)
            link.save()
        except NavigationLink.DoesNotExist:
            pass
    print("  ✅ Updated i18n for social links")
    
    # ════════════════════════════════════════
    # 4. VERIFY FINAL STATE
    # ════════════════════════════════════════
    print()
    print("=" * 60)
    print("📋 FINAL NAVIGATION STATE")
    print("=" * 60)
    
    print("\n── NAVBAR ──")
    navbar = NavigationLink.objects.filter(
        is_active=True, location__in=['navbar', 'both'], parent__isnull=True
    ).order_by('order')
    for l in navbar:
        children = l.children.filter(is_active=True).order_by('order')
        status = "🟢"
        if l.is_coming_soon:
            status = "🟡"
        ch_count = children.count()
        print(f"  {status} {l.order}. {l.name} → {l.url} [{l.icon}]" + (f" ({ch_count} children)" if ch_count else ""))
        for c in children:
            print(f"       └─ {c.name} → {c.url} [{c.icon}]")
    
    print("\n── FOOTER ──")
    footer = NavigationLink.objects.filter(
        is_active=True, location__in=['footer', 'both'], parent__isnull=True
    ).order_by('footer_section', 'order')
    current_section = None
    for l in footer:
        if l.footer_section != current_section:
            current_section = l.footer_section
            print(f"  [{current_section}]")
        print(f"    {l.name} → {l.url}")
    
    print("\n✅ Navigation fix complete!")


if __name__ == '__main__':
    fix_navigation()

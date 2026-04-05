"""
Setup navigation dropdown menus for Stream and Resources.
Run on production: python manage.py shell < scripts/setup_nav_dropdowns.py
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstressvn_settings.settings')
django.setup()

from mediastream.models import MediaCategory
from core.models import NavigationLink

# ===== 1. Create Media Categories =====
stream_cats = [
    ('Luyện nghe', 'luyen-nghe', 'Luyện nghe tiếng Đức, tiếng Anh qua video & audio', 'headphones', 1),
    ('Phim & Series', 'phim', 'Xem phim, series để cải thiện khả năng nghe hiểu', 'film', 2),
    ('Âm nhạc', 'am-nhac', 'Học ngoại ngữ qua bài hát và MV', 'music', 3),
    ('Podcast', 'podcast', 'Podcast học ngoại ngữ đa dạng chủ đề', 'mic', 4),
    ('Bài giảng', 'bai-giang', 'Bài giảng, hướng dẫn ngữ pháp và từ vựng', 'book-open', 5),
]
for name, slug, desc, icon, order in stream_cats:
    obj, c = MediaCategory.objects.get_or_create(
        slug=slug, defaults={'name': name, 'description': desc, 'icon': icon, 'order': order}
    )
    print(f'MediaCategory: {"NEW" if c else "OK"} — {name}')

existing = MediaCategory.objects.filter(slug='thu-gian').first()
if existing:
    existing.order = 6
    existing.save(update_fields=['order'])

# ===== 2. Stream dropdown =====
stream_parent = NavigationLink.objects.filter(url='/stream', parent__isnull=True).first()
if not stream_parent:
    stream_parent = NavigationLink.objects.filter(name='Xem phim', parent__isnull=True).first()
print(f'Stream parent: {stream_parent}')

if stream_parent:
    NavigationLink.objects.get_or_create(
        url='/stream', parent=stream_parent,
        defaults={'name': 'Tất cả media', 'name_vi': 'Tất cả media', 'name_en': 'All Media',
                  'name_de': 'Alle Medien', 'icon': 'LayoutGrid', 'location': 'navbar', 'order': 0}
    )
    for url, name_vi, name_en, name_de, icon, order in [
        ('/stream?category=luyen-nghe', 'Luyện nghe', 'Listening', 'Hörverständnis', 'Headphones', 1),
        ('/stream?category=phim', 'Phim & Series', 'Movies & Series', 'Filme & Serien', 'Film', 2),
        ('/stream?category=am-nhac', 'Âm nhạc', 'Music', 'Musik', 'Music', 3),
        ('/stream?category=podcast', 'Podcast', 'Podcast', 'Podcast', 'Mic', 4),
        ('/stream?category=bai-giang', 'Bài giảng', 'Lessons', 'Unterricht', 'BookOpen', 5),
        ('/stream?category=thu-gian', 'Thư giãn', 'Relaxation', 'Entspannung', 'Coffee', 6),
    ]:
        obj, c = NavigationLink.objects.get_or_create(
            url=url, parent=stream_parent,
            defaults={'name': name_vi, 'name_vi': name_vi, 'name_en': name_en,
                      'name_de': name_de, 'icon': icon, 'location': 'navbar', 'order': order}
        )
        print(f'  Stream: {"NEW" if c else "OK"} — {name_vi}')

# ===== 3. Library dropdown =====
lib_parent = NavigationLink.objects.filter(url='/tai-lieu', parent__isnull=True).first()
if not lib_parent:
    lib_parent = NavigationLink.objects.filter(name__icontains='thư viện', parent__isnull=True).first()
print(f'Library parent: {lib_parent}')

if lib_parent:
    NavigationLink.objects.get_or_create(
        url='/tai-lieu', parent=lib_parent,
        defaults={'name': 'Tất cả tài liệu', 'name_vi': 'Tất cả tài liệu', 'name_en': 'All Resources',
                  'name_de': 'Alle Materialien', 'icon': 'LayoutGrid', 'location': 'navbar', 'order': 0}
    )
    for slug, name_vi, name_en, name_de, icon, order in [
        ('tieng-duc', 'Tiếng Đức', 'German', 'Deutsch', 'GraduationCap', 1),
        ('tieng-anh', 'Tiếng Anh', 'English', 'Englisch', 'Globe', 2),
        ('goethe', 'Goethe', 'Goethe', 'Goethe', 'Award', 3),
        ('ielts', 'IELTS', 'IELTS', 'IELTS', 'Target', 4),
        ('tong-hop', 'Tổng hợp', 'General', 'Allgemein', 'FolderOpen', 5),
    ]:
        url = f'/tai-lieu?category={slug}'
        obj, c = NavigationLink.objects.get_or_create(
            url=url, parent=lib_parent,
            defaults={'name': name_vi, 'name_vi': name_vi, 'name_en': name_en,
                      'name_de': name_de, 'icon': icon, 'location': 'navbar', 'order': order}
        )
        print(f'  Lib: {"NEW" if c else "OK"} — {name_vi}')

print('DONE')

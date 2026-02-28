"""
Management command: Seed NavigationLink dữ liệu ban đầu
Tạo toàn bộ menu navbar + footer dựa trên cấu trúc hiện tại.

Usage:
    python manage.py seed_navigation          # tạo mới (skip nếu đã tồn tại)
    python manage.py seed_navigation --reset  # xoá hết rồi tạo lại
"""

from django.core.management.base import BaseCommand
from core.models import NavigationLink


class Command(BaseCommand):
    help = 'Seed NavigationLink data — tạo menu navbar + footer ban đầu'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Xoá toàn bộ NavigationLink rồi tạo lại từ đầu',
        )

    def handle(self, *args, **options):
        if options['reset']:
            count = NavigationLink.objects.count()
            NavigationLink.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'🗑️  Đã xoá {count} NavigationLink'))

        if NavigationLink.objects.exists():
            self.stdout.write(self.style.NOTICE(
                '⚠️  NavigationLink đã có dữ liệu. Dùng --reset để tạo lại từ đầu.'
            ))
            return

        self._seed_navbar()
        self._seed_footer()

        total = NavigationLink.objects.count()
        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo {total} NavigationLink thành công!'))

    def _seed_navbar(self):
        """Seed navbar links — direct links + dropdown menus"""
        self.stdout.write('📌 Tạo navbar links...')

        # ── Direct links (không có children) ──
        direct_links = [
            {'name': 'Trang chủ', 'name_vi': 'Trang chủ', 'name_en': 'Home', 'name_de': 'Startseite',
             'url': '/', 'icon': '', 'order': 1},
            {'name': 'Thư viện', 'name_vi': 'Thư viện', 'name_en': 'Library', 'name_de': 'Bibliothek',
             'url': '/tai-lieu', 'icon': '', 'order': 2},
            {'name': 'Video', 'name_vi': 'Video', 'name_en': 'Videos', 'name_de': 'Videos',
             'url': '/video', 'icon': '', 'order': 3},
            {'name': 'Stream', 'name_vi': 'Stream', 'name_en': 'Stream', 'name_de': 'Stream',
             'url': '/stream', 'icon': '', 'order': 4},
        ]
        for d in direct_links:
            NavigationLink.objects.create(location='navbar', **d)

        # ── Tin tức dropdown ──
        news_parent = NavigationLink.objects.create(
            name='Tin tức', name_vi='Tin tức', name_en='News', name_de='Nachrichten',
            url='/tin-tuc', icon='Newspaper', location='navbar', order=5,
        )
        news_children = [
            {'name': 'Tất cả tin tức', 'name_vi': 'Tất cả tin tức', 'name_en': 'All news', 'name_de': 'Alle Nachrichten',
             'url': '/tin-tuc', 'icon': 'Newspaper', 'order': 1},
            {'name': 'Học tiếng Đức', 'name_vi': 'Học tiếng Đức', 'name_en': 'Learn German', 'name_de': 'Deutsch lernen',
             'url': '/tin-tuc/hoc-tieng-duc', 'icon': 'FileText', 'order': 2},
            {'name': 'Học tiếng Anh', 'name_vi': 'Học tiếng Anh', 'name_en': 'Learn English', 'name_de': 'Englisch lernen',
             'url': '/tin-tuc/hoc-tieng-anh', 'icon': 'FileText', 'order': 3},
            {'name': 'Du học', 'name_vi': 'Du học', 'name_en': 'Study Abroad', 'name_de': 'Auslandsstudium',
             'url': '/tin-tuc/du-hoc', 'icon': 'GraduationCap', 'order': 4},
            {'name': 'Sự kiện', 'name_vi': 'Sự kiện', 'name_en': 'Events', 'name_de': 'Veranstaltungen',
             'url': '/tin-tuc/su-kien', 'icon': 'Users', 'order': 5},
        ]
        for c in news_children:
            NavigationLink.objects.create(parent=news_parent, location='navbar', **c)

        # ── Kiến thức dropdown ──
        knowledge_parent = NavigationLink.objects.create(
            name='Kiến thức', name_vi='Kiến thức', name_en='Knowledge', name_de='Wissen',
            url='/kien-thuc', icon='BookOpen', location='navbar', order=6,
        )
        knowledge_children = [
            {'name': 'Tất cả kiến thức', 'name_vi': 'Tất cả kiến thức', 'name_en': 'All knowledge', 'name_de': 'Alle Wissen',
             'url': '/kien-thuc', 'icon': 'BookOpen', 'order': 1},
            {'name': 'Ngữ pháp', 'name_vi': 'Ngữ pháp', 'name_en': 'Grammar', 'name_de': 'Grammatik',
             'url': '/kien-thuc/ngu-phap', 'icon': 'FileText', 'order': 2},
            {'name': 'Bài giảng', 'name_vi': 'Bài giảng', 'name_en': 'Lectures', 'name_de': 'Vorlesungen',
             'url': '/kien-thuc/bai-giang', 'icon': 'GraduationCap', 'order': 3},
            {'name': 'Từ vựng', 'name_vi': 'Từ vựng', 'name_en': 'Vocabulary', 'name_de': 'Vokabeln',
             'url': '/kien-thuc/tu-vung', 'icon': 'Languages', 'order': 4},
            {'name': 'Luyện thi', 'name_vi': 'Luyện thi', 'name_en': 'Exam prep', 'name_de': 'Prüfungsvorbereitung',
             'url': '/kien-thuc/luyen-thi', 'icon': 'BookOpen', 'order': 5},
            {'name': 'Văn hóa', 'name_vi': 'Văn hóa', 'name_en': 'Culture', 'name_de': 'Kultur',
             'url': '/kien-thuc/van-hoa', 'icon': 'Users', 'order': 6},
            {'name': 'Mẹo học', 'name_vi': 'Mẹo học', 'name_en': 'Tips', 'name_de': 'Tipps',
             'url': '/kien-thuc/meo-hoc', 'icon': 'FileText', 'order': 7},
        ]
        for c in knowledge_children:
            NavigationLink.objects.create(parent=knowledge_parent, location='navbar', **c)

        # ── Công cụ dropdown ──
        tools_parent = NavigationLink.objects.create(
            name='Công cụ hỗ trợ', name_vi='Công cụ hỗ trợ', name_en='Tools', name_de='Werkzeuge',
            url='/cong-cu', icon='Wrench', location='navbar', order=7,
        )
        tools_children = [
            {'name': 'Tất cả công cụ', 'name_vi': 'Tất cả công cụ', 'name_en': 'All tools', 'name_de': 'Alle Werkzeuge',
             'url': '/cong-cu', 'icon': 'Wrench', 'order': 1},
            {'name': 'Dịch thuật', 'name_vi': 'Dịch thuật', 'name_en': 'Translation', 'name_de': 'Übersetzung',
             'url': '/cong-cu/dich-thuat', 'icon': 'Languages', 'order': 2},
            {'name': 'Từ điển', 'name_vi': 'Từ điển', 'name_en': 'Dictionary', 'name_de': 'Wörterbuch',
             'url': '/cong-cu/tu-dien', 'icon': 'BookOpen', 'order': 3},
            {'name': 'Luyện tập', 'name_vi': 'Luyện tập', 'name_en': 'Practice', 'name_de': 'Übungen',
             'url': '/cong-cu/luyen-tap', 'icon': 'GraduationCap', 'order': 4},
            {'name': 'Phần mềm hỗ trợ', 'name_vi': 'Phần mềm hỗ trợ', 'name_en': 'Software', 'name_de': 'Software',
             'url': '/cong-cu/phan-mem', 'icon': 'Wrench', 'order': 5},
        ]
        for c in tools_children:
            NavigationLink.objects.create(parent=tools_parent, location='navbar', **c)

        # ── Cộng đồng dropdown ──
        community_parent = NavigationLink.objects.create(
            name='Cộng đồng', name_vi='Cộng đồng', name_en='Community', name_de='Gemeinschaft',
            url='/cong-dong', icon='Users', location='navbar', order=8,
        )
        community_children = [
            {'name': 'Discord', 'name_vi': 'Discord', 'name_en': 'Discord', 'name_de': 'Discord',
             'url': 'https://discord.gg/unstressvn', 'icon': 'Users',
             'open_in_new_tab': True, 'order': 1},
            {'name': 'Diễn đàn', 'name_vi': 'Diễn đàn', 'name_en': 'Forum', 'name_de': 'Forum',
             'url': '/dien-dan', 'icon': 'MessageSquare',
             'is_coming_soon': True, 'badge_text': 'Soon', 'order': 2},
        ]
        for c in community_children:
            NavigationLink.objects.create(parent=community_parent, location='navbar', **c)

    def _seed_footer(self):
        """Seed footer links — grouped by section"""
        self.stdout.write('📌 Tạo footer links...')

        # ── Khám phá (resources) ──
        footer_explore = [
            {'name': 'Kiến thức', 'name_vi': 'Kiến thức', 'name_en': 'Knowledge', 'name_de': 'Wissen',
             'url': '/kien-thuc', 'footer_section': 'resources', 'order': 1},
            {'name': 'Thư viện', 'name_vi': 'Thư viện', 'name_en': 'Library', 'name_de': 'Bibliothek',
             'url': '/tai-lieu', 'footer_section': 'resources', 'order': 2},
            {'name': 'Công cụ', 'name_vi': 'Công cụ', 'name_en': 'Tools', 'name_de': 'Werkzeuge',
             'url': '/cong-cu', 'footer_section': 'resources', 'order': 3},
            {'name': 'Tin tức', 'name_vi': 'Tin tức', 'name_en': 'News', 'name_de': 'Nachrichten',
             'url': '/tin-tuc', 'footer_section': 'resources', 'order': 4},
        ]
        for d in footer_explore:
            NavigationLink.objects.create(location='footer', **d)

        # ── Hỗ trợ (company) ──
        footer_support = [
            {'name': 'Giới thiệu', 'name_vi': 'Giới thiệu', 'name_en': 'About', 'name_de': 'Über uns',
             'url': '/gioi-thieu', 'footer_section': 'company', 'order': 1},
            {'name': 'Liên hệ', 'name_vi': 'Liên hệ', 'name_en': 'Contact', 'name_de': 'Kontakt',
             'url': '/lien-he', 'footer_section': 'company', 'order': 2},
            {'name': 'Điều khoản', 'name_vi': 'Điều khoản', 'name_en': 'Terms', 'name_de': 'AGB',
             'url': '/dieu-khoan', 'footer_section': 'legal', 'order': 1},
            {'name': 'Chính sách bảo mật', 'name_vi': 'Chính sách bảo mật', 'name_en': 'Privacy', 'name_de': 'Datenschutz',
             'url': '/chinh-sach-bao-mat', 'footer_section': 'legal', 'order': 2},
        ]
        for d in footer_support:
            NavigationLink.objects.create(location='footer', **d)

        # ── Social links ──
        social_links = [
            {'name': 'Facebook', 'url': 'https://facebook.com/unstressvn',
             'icon': 'Facebook', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 1},
            {'name': 'YouTube', 'url': 'https://youtube.com/@unstressvn',
             'icon': 'Youtube', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 2},
            {'name': 'TikTok', 'url': 'https://tiktok.com/@unstressvn',
             'icon': 'Music', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 3},
            {'name': 'Discord', 'url': 'https://discord.gg/unstressvn',
             'icon': 'Users', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 4},
        ]
        for d in social_links:
            NavigationLink.objects.create(location='footer', **d)

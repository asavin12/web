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
        ]
        for d in direct_links:
            NavigationLink.objects.create(location='navbar', **d)

        # ── Video dropdown ──
        video_parent = NavigationLink.objects.create(
            name='Video', name_vi='Video', name_en='Videos', name_de='Videos',
            url='/video', icon='Play', location='navbar', order=3,
        )
        video_children = [
            {'name': 'Tất cả video', 'name_vi': 'Tất cả video', 'name_en': 'All videos', 'name_de': 'Alle Videos',
             'url': '/video', 'icon': 'Play', 'order': 1},
            {'name': 'Bài giảng', 'name_vi': 'Bài giảng', 'name_en': 'Lectures', 'name_de': 'Vorlesungen',
             'url': '/video/bai-giang', 'icon': 'GraduationCap', 'order': 2},
            {'name': 'Bài học', 'name_vi': 'Bài học', 'name_en': 'Lessons', 'name_de': 'Lektionen',
             'url': '/video/bai-hoc', 'icon': 'BookOpen', 'order': 3},
            {'name': 'Phim', 'name_vi': 'Phim', 'name_en': 'Movies', 'name_de': 'Filme',
             'url': '/video/phim', 'icon': 'Film', 'order': 4},
            {'name': 'Ca nhạc', 'name_vi': 'Ca nhạc', 'name_en': 'Music Videos', 'name_de': 'Musikvideos',
             'url': '/video/ca-nhac', 'icon': 'Music', 'order': 5},
        ]
        for c in video_children:
            NavigationLink.objects.create(parent=video_parent, location='navbar', **c)

        # ── Audio & Podcast dropdown ──
        audio_parent = NavigationLink.objects.create(
            name='Audio & Podcast', name_vi='Audio & Podcast', name_en='Audio & Podcast', name_de='Audio & Podcast',
            url='/audio', icon='Headphones', location='navbar', order=4,
        )
        audio_children = [
            {'name': 'Tất cả audio', 'name_vi': 'Tất cả audio', 'name_en': 'All audio', 'name_de': 'Alle Audio',
             'url': '/audio', 'icon': 'Headphones', 'order': 1},
            {'name': 'Podcast', 'name_vi': 'Podcast', 'name_en': 'Podcast', 'name_de': 'Podcast',
             'url': '/audio/podcast', 'icon': 'Mic', 'order': 2},
            {'name': 'Nghe chậm', 'name_vi': 'Nghe chậm', 'name_en': 'Slow listening', 'name_de': 'Langsam hören',
             'url': '/audio/nghe-cham', 'icon': 'Volume2', 'order': 3},
            {'name': 'Nhạc', 'name_vi': 'Nhạc', 'name_en': 'Music', 'name_de': 'Musik',
             'url': '/audio/nhac', 'icon': 'Music', 'order': 4},
        ]
        for c in audio_children:
            NavigationLink.objects.create(parent=audio_parent, location='navbar', **c)

        # ── Stream ──
        NavigationLink.objects.create(
            name='Stream', name_vi='Stream', name_en='Stream', name_de='Stream',
            url='/stream', icon='', location='navbar', order=5,
        )

        # ── Tin tức dropdown ──
        news_parent = NavigationLink.objects.create(
            name='Tin tức', name_vi='Tin tức', name_en='News', name_de='Nachrichten',
            url='/tin-tuc', icon='Newspaper', location='navbar', order=6,
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
            url='/kien-thuc', icon='BookOpen', location='navbar', order=7,
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
            url='/cong-cu', icon='Wrench', location='navbar', order=8,
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
            url='/cong-dong', icon='Users', location='navbar', order=9,
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
        """Seed footer links — grouped by section, SEO-optimized"""
        self.stdout.write('📌 Tạo footer links...')

        # ── Học tập (resources) ──
        footer_resources = [
            {'name': 'Video học ngoại ngữ', 'name_vi': 'Video học ngoại ngữ', 'name_en': 'Learning Videos', 'name_de': 'Lernvideos',
             'url': '/video', 'icon': 'Video', 'footer_section': 'resources', 'order': 1},
            {'name': 'Thư viện tài liệu', 'name_vi': 'Thư viện tài liệu', 'name_en': 'Resource Library', 'name_de': 'Bibliothek',
             'url': '/tai-lieu', 'icon': 'BookOpen', 'footer_section': 'resources', 'order': 2},
            {'name': 'Xem phim học ngoại ngữ', 'name_vi': 'Xem phim học ngoại ngữ', 'name_en': 'Watch & Learn', 'name_de': 'Filme & Lernen',
             'url': '/stream', 'icon': 'Play', 'footer_section': 'resources', 'order': 3},
            {'name': 'Kiến thức & Bài giảng', 'name_vi': 'Kiến thức & Bài giảng', 'name_en': 'Knowledge', 'name_de': 'Wissen',
             'url': '/kien-thuc', 'icon': 'GraduationCap', 'footer_section': 'resources', 'order': 4},
            {'name': 'Tin tức giáo dục', 'name_vi': 'Tin tức giáo dục', 'name_en': 'Education News', 'name_de': 'Bildungsnachrichten',
             'url': '/tin-tuc', 'icon': 'Newspaper', 'footer_section': 'resources', 'order': 5},
            {'name': 'Công cụ học tập', 'name_vi': 'Công cụ học tập', 'name_en': 'Learning Tools', 'name_de': 'Lernwerkzeuge',
             'url': '/cong-cu', 'icon': 'Wrench', 'footer_section': 'resources', 'order': 6},
        ]
        for d in footer_resources:
            NavigationLink.objects.create(location='footer', **d)

        # ── Về chúng tôi (company) ──
        footer_company = [
            {'name': 'Giới thiệu', 'name_vi': 'Giới thiệu', 'name_en': 'About', 'name_de': 'Über uns',
             'url': '/gioi-thieu', 'footer_section': 'company', 'order': 1},
            {'name': 'Liên hệ', 'name_vi': 'Liên hệ', 'name_en': 'Contact', 'name_de': 'Kontakt',
             'url': '/lien-he', 'footer_section': 'company', 'order': 2},
            {'name': 'Câu hỏi thường gặp', 'name_vi': 'Câu hỏi thường gặp', 'name_en': 'FAQ', 'name_de': 'Häufige Fragen',
             'url': '/gioi-thieu#faq', 'icon': 'HelpCircle', 'footer_section': 'company', 'order': 3},
        ]
        for d in footer_company:
            NavigationLink.objects.create(location='footer', **d)

        # ── Cộng đồng (community) ──
        footer_community = [
            {'name': 'Discord', 'name_vi': 'Discord', 'name_en': 'Discord', 'name_de': 'Discord',
             'url': 'https://discord.gg/unstressvn', 'icon': 'Users', 'footer_section': 'community',
             'open_in_new_tab': True, 'order': 1},
            {'name': 'Phòng học nhóm', 'name_vi': 'Phòng học nhóm', 'name_en': 'Study Rooms', 'name_de': 'Lernräume',
             'url': '/study-rooms', 'footer_section': 'community',
             'is_coming_soon': True, 'badge_text': 'Soon', 'order': 2},
        ]
        for d in footer_community:
            NavigationLink.objects.create(location='footer', **d)

        # ── Pháp lý (legal) ──
        footer_legal = [
            {'name': 'Điều khoản sử dụng', 'name_vi': 'Điều khoản sử dụng', 'name_en': 'Terms of Use', 'name_de': 'Nutzungsbedingungen',
             'url': '/dieu-khoan', 'footer_section': 'legal', 'order': 1},
            {'name': 'Chính sách bảo mật', 'name_vi': 'Chính sách bảo mật', 'name_en': 'Privacy Policy', 'name_de': 'Datenschutz',
             'url': '/chinh-sach-bao-mat', 'footer_section': 'legal', 'order': 2},
        ]
        for d in footer_legal:
            NavigationLink.objects.create(location='footer', **d)

        # ── Social links ──
        social_links = [
            {'name': 'Facebook', 'url': 'https://facebook.com/unstressvn',
             'icon': 'Facebook', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 1},
            {'name': 'YouTube', 'url': 'https://youtube.com/@unstressvn',
             'icon': 'Youtube', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 2},
            {'name': 'TikTok', 'url': 'https://tiktok.com/@unstressvn',
             'icon': 'Music', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 3},
            {'name': 'Zalo', 'url': 'https://zalo.me/unstressvn',
             'icon': 'MessageSquare', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 4},
            {'name': 'Telegram', 'url': 'https://t.me/unstressvn',
             'icon': 'MessageSquare', 'footer_section': 'social', 'open_in_new_tab': True, 'order': 5},
        ]
        for d in social_links:
            NavigationLink.objects.create(location='footer', **d)

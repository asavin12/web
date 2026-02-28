"""
Management command: Upgrade NavigationLink data
- Fix icon names: FontAwesome (Fa*) → Lucide names
- Fill multilingual names (name_vi, name_en, name_de)
- Create dropdown children cho Tin tức, Kiến thức, Công cụ, Cộng đồng
- Preserve existing footer customizations

Usage:
    python manage.py upgrade_navigation          # upgrade + thêm children
    python manage.py upgrade_navigation --dry-run # xem trước thay đổi
"""

from django.core.management.base import BaseCommand
from core.models import NavigationLink


# FontAwesome → Lucide icon mapping
FA_TO_LUCIDE = {
    'FaHome': 'Home',
    'FaVideo': 'Video',
    'FaBook': 'BookOpen',
    'FaNewspaper': 'Newspaper',
    'FaLightbulb': 'BookOpen',
    'FaTools': 'Wrench',
    'FaUsers': 'Users',
    'FaFacebook': 'Facebook',
    'FaYoutube': 'Youtube',
    'FaTiktok': 'Music',
    'FaDiscord': 'Users',
    'FaInstagram': 'Instagram',
    'FaTwitter': 'Twitter',
    'FaGlobe': 'Globe',
    'FaFile': 'FileText',
    'FaFileAlt': 'FileText',
    'FaGraduationCap': 'GraduationCap',
    'FaLanguage': 'Languages',
    'FaWrench': 'Wrench',
    'FaHeart': 'Heart',
    'FaStar': 'Star',
    'FaBookmark': 'Bookmark',
    'FaCompass': 'Compass',
    'FaEnvelope': 'Mail',
    'FaMapMarker': 'MapPin',
    'FaMusic': 'Music',
    'FaRadio': 'Radio',
    'FaExternalLink': 'ExternalLink',
    'FaComment': 'MessageSquare',
    'FaSearch': 'Search',
    'FaInfo': 'Info',
    'FaPhone': 'Phone',
    'FaCog': 'Settings',
    'FaLink': 'Link',
    'FaPlay': 'Play',
    'FaQuestion': 'HelpCircle',
    'FaLock': 'Lock',
    'FaShield': 'Shield',
    'FaCalendar': 'Calendar',
    'FaBell': 'Bell',
    'FaClipboard': 'Clipboard',
    'FaPen': 'Pen',
    'FaDownload': 'Download',
    'FaUpload': 'Upload',
    'FaImage': 'Image',
    'FaCamera': 'Camera',
    'FaMicrophone': 'Mic',
    'FaHeadphones': 'Headphones',
    'FaCode': 'Code',
    'FaDatabase': 'Database',
    'FaTrophy': 'Trophy',
    'FaMap': 'Map',
    'FaFilePdf': 'FileText',
}

# Multilingual names for known pages
KNOWN_NAMES = {
    '/': {'vi': 'Trang chủ', 'en': 'Home', 'de': 'Startseite'},
    '/videos': {'vi': 'Video', 'en': 'Videos', 'de': 'Videos'},
    '/video': {'vi': 'Video', 'en': 'Videos', 'de': 'Videos'},
    '/resources': {'vi': 'Tài liệu', 'en': 'Resources', 'de': 'Ressourcen'},
    '/tai-lieu': {'vi': 'Thư viện', 'en': 'Library', 'de': 'Bibliothek'},
    '/tin-tuc': {'vi': 'Tin tức', 'en': 'News', 'de': 'Nachrichten'},
    '/kien-thuc': {'vi': 'Kiến thức', 'en': 'Knowledge', 'de': 'Wissen'},
    '/cong-cu': {'vi': 'Công cụ', 'en': 'Tools', 'de': 'Werkzeuge'},
    '/cong-dong': {'vi': 'Cộng đồng', 'en': 'Community', 'de': 'Gemeinschaft'},
    '/stream': {'vi': 'Stream', 'en': 'Stream', 'de': 'Stream'},
    '/about': {'vi': 'Giới thiệu', 'en': 'About', 'de': 'Über uns'},
    '/gioi-thieu': {'vi': 'Giới thiệu', 'en': 'About', 'de': 'Über uns'},
    '/contact': {'vi': 'Liên hệ', 'en': 'Contact', 'de': 'Kontakt'},
    '/lien-he': {'vi': 'Liên hệ', 'en': 'Contact', 'de': 'Kontakt'},
    '/terms': {'vi': 'Điều khoản sử dụng', 'en': 'Terms of Service', 'de': 'Nutzungsbedingungen'},
    '/dieu-khoan': {'vi': 'Điều khoản', 'en': 'Terms', 'de': 'AGB'},
    '/privacy': {'vi': 'Chính sách bảo mật', 'en': 'Privacy Policy', 'de': 'Datenschutz'},
    '/chinh-sach-bao-mat': {'vi': 'Chính sách bảo mật', 'en': 'Privacy', 'de': 'Datenschutz'},
    '/careers': {'vi': 'Việc làm', 'en': 'Careers', 'de': 'Karriere'},
    '/study-rooms': {'vi': 'Phòng học nhóm', 'en': 'Study Rooms', 'de': 'Lernräume'},
}

# Dropdown children definitions
DROPDOWN_CHILDREN = {
    'tin-tuc': {
        'parent_url': '/tin-tuc',
        'children': [
            {'name': 'Tất cả tin tức', 'name_vi': 'Tất cả tin tức', 'name_en': 'All News', 'name_de': 'Alle Nachrichten',
             'url': '/tin-tuc', 'icon': 'Newspaper', 'order': 1},
            {'name': 'Du học Đức', 'name_vi': 'Du học Đức', 'name_en': 'Study in Germany', 'name_de': 'Studium in Deutschland',
             'url': '/tin-tuc?category=du-hoc-duc', 'icon': 'GraduationCap', 'order': 2},
            {'name': 'Học bổng', 'name_vi': 'Học bổng', 'name_en': 'Scholarships', 'name_de': 'Stipendien',
             'url': '/tin-tuc?category=hoc-bong', 'icon': 'Star', 'order': 3},
            {'name': 'Đời sống Đức', 'name_vi': 'Đời sống Đức', 'name_en': 'Life in Germany', 'name_de': 'Leben in Deutschland',
             'url': '/tin-tuc?category=doi-song-duc', 'icon': 'Globe', 'order': 4},
            {'name': 'Kinh nghiệm', 'name_vi': 'Kinh nghiệm', 'name_en': 'Experience', 'name_de': 'Erfahrungen',
             'url': '/tin-tuc?category=kinh-nghiem', 'icon': 'Heart', 'order': 5},
        ]
    },
    'kien-thuc': {
        'parent_url': '/kien-thuc',
        'children': [
            {'name': 'Tất cả kiến thức', 'name_vi': 'Tất cả kiến thức', 'name_en': 'All Knowledge', 'name_de': 'Alle Wissen',
             'url': '/kien-thuc', 'icon': 'BookOpen', 'order': 1},
            {'name': 'Ngữ pháp', 'name_vi': 'Ngữ pháp', 'name_en': 'Grammar', 'name_de': 'Grammatik',
             'url': '/kien-thuc?category=ngu-phap', 'icon': 'FileText', 'order': 2},
            {'name': 'Từ vựng', 'name_vi': 'Từ vựng', 'name_en': 'Vocabulary', 'name_de': 'Vokabeln',
             'url': '/kien-thuc?category=tu-vung', 'icon': 'Languages', 'order': 3},
            {'name': 'Luyện thi', 'name_vi': 'Luyện thi', 'name_en': 'Exam Prep', 'name_de': 'Prüfungsvorbereitung',
             'url': '/kien-thuc?category=luyen-thi', 'icon': 'GraduationCap', 'order': 4},
            {'name': 'Kỹ năng', 'name_vi': 'Kỹ năng', 'name_en': 'Skills', 'name_de': 'Fähigkeiten',
             'url': '/kien-thuc?category=ky-nang', 'icon': 'Compass', 'order': 5},
            {'name': 'Văn hóa Đức', 'name_vi': 'Văn hóa Đức', 'name_en': 'German Culture', 'name_de': 'Deutsche Kultur',
             'url': '/kien-thuc?category=van-hoa-duc', 'icon': 'Globe', 'order': 6},
        ]
    },
    'cong-cu': {
        'parent_url': '/cong-cu',
        'children': [
            {'name': 'Tất cả công cụ', 'name_vi': 'Tất cả công cụ', 'name_en': 'All Tools', 'name_de': 'Alle Werkzeuge',
             'url': '/cong-cu', 'icon': 'Wrench', 'order': 1},
            {'name': 'Flashcard', 'name_vi': 'Flashcard', 'name_en': 'Flashcards', 'name_de': 'Lernkarten',
             'url': '/cong-cu/flashcards', 'icon': 'Bookmark', 'order': 2},
            {'name': 'Từ điển', 'name_vi': 'Từ điển', 'name_en': 'Dictionary', 'name_de': 'Wörterbuch',
             'url': '/cong-cu?category=tu-dien', 'icon': 'BookOpen', 'order': 3},
            {'name': 'Luyện tập', 'name_vi': 'Luyện tập', 'name_en': 'Practice', 'name_de': 'Übungen',
             'url': '/cong-cu?category=luyen-tap', 'icon': 'GraduationCap', 'order': 4},
        ]
    },
    'cong-dong': {
        'parent_url': '/cong-dong',
        'children': [
            {'name': 'Discord', 'name_vi': 'Discord', 'name_en': 'Discord', 'name_de': 'Discord',
             'url': 'https://discord.gg/unstressvn', 'icon': 'Users', 'open_in_new_tab': True, 'order': 1},
            {'name': 'Diễn đàn', 'name_vi': 'Diễn đàn', 'name_en': 'Forum', 'name_de': 'Forum',
             'url': '/dien-dan', 'icon': 'MessageSquare', 'is_coming_soon': True, 'badge_text': 'Soon', 'order': 2},
            {'name': 'Phòng học nhóm', 'name_vi': 'Phòng học nhóm', 'name_en': 'Study Rooms', 'name_de': 'Lernräume',
             'url': '/study-rooms', 'icon': 'Users', 'is_coming_soon': True, 'badge_text': 'Soon', 'order': 3},
        ]
    },
}


class Command(BaseCommand):
    help = 'Upgrade NavigationLink data — fix icons, add multilingual names, create dropdown children'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Chỉ xem trước thay đổi, không thực hiện',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN — không thay đổi dữ liệu\n'))

        self._fix_icons(dry_run)
        self._fill_multilingual(dry_run)
        self._ensure_dropdowns(dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN hoàn tất. Chạy lại KHÔNG có --dry-run để áp dụng.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Upgrade NavigationLink hoàn tất!'))

    def _fix_icons(self, dry_run):
        """Fix FontAwesome icon names → Lucide names"""
        self.stdout.write('🔧 Fix icon names...')
        fixed = 0
        for link in NavigationLink.objects.all():
            if link.icon and link.icon in FA_TO_LUCIDE:
                new_icon = FA_TO_LUCIDE[link.icon]
                self.stdout.write(f'  {link.name}: {link.icon} → {new_icon}')
                if not dry_run:
                    link.icon = new_icon
                    link.save(update_fields=['icon'])
                fixed += 1
        self.stdout.write(f'  → Fixed {fixed} icons\n')

    def _fill_multilingual(self, dry_run):
        """Fill name_vi/name_en/name_de where missing"""
        self.stdout.write('🌐 Fill multilingual names...')
        filled = 0
        for link in NavigationLink.objects.all():
            url_key = link.url.split('?')[0].rstrip('/')  # normalize URL
            if not url_key:
                url_key = '/'
            names = KNOWN_NAMES.get(url_key)
            changed = False
            if names:
                if not link.name_vi and names.get('vi'):
                    link.name_vi = names['vi']
                    changed = True
                if not link.name_en and names.get('en'):
                    link.name_en = names['en']
                    changed = True
                if not link.name_de and names.get('de'):
                    link.name_de = names['de']
                    changed = True
            # For social links, name_vi/en/de = name (same across languages)
            if link.url.startswith('http'):
                social_name = link.name  # Facebook, YouTube, etc.
                if not link.name_vi:
                    link.name_vi = social_name
                    changed = True
                if not link.name_en:
                    link.name_en = social_name
                    changed = True
                if not link.name_de:
                    link.name_de = social_name
                    changed = True

            if changed:
                self.stdout.write(
                    f'  {link.name}: vi={link.name_vi}, en={link.name_en}, de={link.name_de}')
                if not dry_run:
                    link.save(update_fields=['name_vi', 'name_en', 'name_de'])
                filled += 1
        self.stdout.write(f'  → Filled {filled} links\n')

    def _ensure_dropdowns(self, dry_run):
        """Create dropdown children for navbar menus that should be dropdowns"""
        self.stdout.write('📂 Ensure dropdown children...')

        for key, config in DROPDOWN_CHILDREN.items():
            parent_url = config['parent_url']
            # Find parent by URL
            parent = NavigationLink.objects.filter(
                url=parent_url,
                location__in=['navbar', 'both'],
                parent__isnull=True,
            ).first()

            if not parent:
                # Check if parent exists but URL is slightly different
                # e.g. user might have /cong-dong or not
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  Không tìm thấy parent "{parent_url}" trong navbar. '
                    f'Tạo mới...'
                ))
                if not dry_run:
                    name_data = KNOWN_NAMES.get(parent_url, {})
                    parent = NavigationLink.objects.create(
                        name=name_data.get('vi', key),
                        name_vi=name_data.get('vi', key),
                        name_en=name_data.get('en', key),
                        name_de=name_data.get('de', key),
                        url=parent_url,
                        icon=config['children'][0]['icon'] if config['children'] else '',
                        location='navbar',
                        order=NavigationLink.objects.filter(
                            location__in=['navbar', 'both'], parent__isnull=True
                        ).count() + 1,
                    )
                    self.stdout.write(f'  ✅ Tạo parent: {parent.name} ({parent_url})')
                else:
                    self.stdout.write(f'  [DRY] Sẽ tạo parent: {parent_url}')
                    continue

            # Check if already has children
            existing_children = parent.children.count()
            if existing_children > 0:
                self.stdout.write(f'  ✅ {parent.name} đã có {existing_children} mục con — skip')
                continue

            # Create children
            self.stdout.write(f'  📂 Tạo children cho: {parent.name}')
            for child_data in config['children']:
                self.stdout.write(f'     └─ {child_data["name"]} → {child_data["url"]}')
                if not dry_run:
                    NavigationLink.objects.create(
                        parent=parent,
                        location='navbar',
                        name=child_data['name'],
                        name_vi=child_data.get('name_vi', child_data['name']),
                        name_en=child_data.get('name_en', child_data['name']),
                        name_de=child_data.get('name_de', child_data['name']),
                        url=child_data['url'],
                        icon=child_data.get('icon', ''),
                        order=child_data.get('order', 0),
                        open_in_new_tab=child_data.get('open_in_new_tab', False),
                        is_coming_soon=child_data.get('is_coming_soon', False),
                        badge_text=child_data.get('badge_text', ''),
                    )

        self.stdout.write('')

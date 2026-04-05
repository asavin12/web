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
    '/tai-lieu': {'vi': 'Tài liệu', 'en': 'Resources', 'de': 'Ressourcen'},
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
    '/tuyen-dung': {'vi': 'Tuyển dụng', 'en': 'Careers', 'de': 'Karriere'},
    '/study-rooms': {'vi': 'Phòng học nhóm', 'en': 'Study Rooms', 'de': 'Lernräume'},
    '/phong-hoc-nhom': {'vi': 'Phòng học nhóm', 'en': 'Study Rooms', 'de': 'Lernräume'},
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
    'stream': {
        'parent_url': '/stream',
        'children': [
            {'name': 'Tất cả video', 'name_vi': 'Tất cả video', 'name_en': 'All Videos', 'name_de': 'Alle Videos',
             'url': '/stream', 'icon': 'LayoutGrid', 'order': 0},
            {'name': 'Luyện nghe', 'name_vi': 'Luyện nghe', 'name_en': 'Listening', 'name_de': 'Hörverständnis',
             'url': '/stream?category=luyen-nghe', 'icon': 'Headphones', 'order': 1},
            {'name': 'Phim & Series', 'name_vi': 'Phim & Series', 'name_en': 'Movies & Series', 'name_de': 'Filme & Serien',
             'url': '/stream?category=phim', 'icon': 'Film', 'order': 2},
            {'name': 'Âm nhạc', 'name_vi': 'Âm nhạc', 'name_en': 'Music', 'name_de': 'Musik',
             'url': '/stream?category=am-nhac', 'icon': 'Music', 'order': 3},
            {'name': 'Podcast', 'name_vi': 'Podcast', 'name_en': 'Podcast', 'name_de': 'Podcast',
             'url': '/stream?category=podcast', 'icon': 'Mic', 'order': 4},
            {'name': 'Bài giảng', 'name_vi': 'Bài giảng', 'name_en': 'Lessons', 'name_de': 'Unterricht',
             'url': '/stream?category=bai-giang', 'icon': 'BookOpen', 'order': 5},
            {'name': 'Thư giãn', 'name_vi': 'Thư giãn', 'name_en': 'Relaxation', 'name_de': 'Entspannung',
             'url': '/stream?category=thu-gian', 'icon': 'Coffee', 'order': 6},
            {'name': 'YouTube', 'name_vi': 'YouTube', 'name_en': 'YouTube', 'name_de': 'YouTube',
             'url': '/stream?category=youtube', 'icon': 'Youtube', 'order': 7},
        ]
    },
    'tai-lieu': {
        'parent_url': '/tai-lieu',
        'children': [
            {'name': 'Tất cả tài liệu', 'name_vi': 'Tất cả tài liệu', 'name_en': 'All Resources', 'name_de': 'Alle Materialien',
             'url': '/tai-lieu', 'icon': 'LayoutGrid', 'order': 0},
            {'name': 'Tiếng Đức', 'name_vi': 'Tiếng Đức', 'name_en': 'German', 'name_de': 'Deutsch',
             'url': '/tai-lieu?category=tieng-duc', 'icon': 'GraduationCap', 'order': 1},
            {'name': 'Tiếng Anh', 'name_vi': 'Tiếng Anh', 'name_en': 'English', 'name_de': 'Englisch',
             'url': '/tai-lieu?category=tieng-anh', 'icon': 'Globe', 'order': 2},
            {'name': 'Goethe', 'name_vi': 'Goethe', 'name_en': 'Goethe', 'name_de': 'Goethe',
             'url': '/tai-lieu?category=goethe', 'icon': 'Award', 'order': 3},
            {'name': 'IELTS', 'name_vi': 'IELTS', 'name_en': 'IELTS', 'name_de': 'IELTS',
             'url': '/tai-lieu?category=ielts', 'icon': 'Target', 'order': 4},
            {'name': 'Tổng hợp', 'name_vi': 'Tổng hợp', 'name_en': 'General', 'name_de': 'Allgemein',
             'url': '/tai-lieu?category=tong-hop', 'icon': 'FolderOpen', 'order': 5},
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

        self._fix_urls(dry_run)
        self._fix_icons(dry_run)
        self._fill_multilingual(dry_run)
        self._merge_video_into_stream(dry_run)
        self._ensure_dropdowns(dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN hoàn tất. Chạy lại KHÔNG có --dry-run để áp dụng.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Upgrade NavigationLink hoàn tất!'))

    # URL corrections: old URLs → correct frontend route URLs
    URL_FIXES = {
        '/videos': '/stream',
        '/video': '/stream',
        '/resources': '/tai-lieu',
        '/about': '/gioi-thieu',
        '/contact': '/lien-he',
        '/terms': '/dieu-khoan',
        '/privacy': '/chinh-sach-bao-mat',
        '/careers': '/tuyen-dung',
        '/study-rooms': '/phong-hoc-nhom',
        # Footer resource links with query params
        '/videos?language=en': '/stream?language=en',
        '/videos?language=de': '/stream?language=de',
        '/video?language=en': '/stream?language=en',
        '/video?language=de': '/stream?language=de',
    }

    def _merge_video_into_stream(self, dry_run):
        """Remove old Video/Audio nav links — Stream is now the single media section."""
        self.stdout.write('🎬 Merge Video/Audio → Stream...')

        # Deactivate "Audio & Podcast" nav if exists (Stream covers audio)
        audio_links = NavigationLink.objects.filter(
            name__icontains='audio', location__in=['navbar', 'both'],
            parent__isnull=True, is_active=True
        )
        for link in audio_links:
            self.stdout.write(f'  Deactivate: #{link.id} "{link.name}"')
            if not dry_run:
                link.is_active = False
                link.save(update_fields=['is_active'])
                link.children.update(is_active=False)

        # Find all top-level navbar links pointing to /stream
        stream_links = list(NavigationLink.objects.filter(
            url='/stream', location__in=['navbar', 'both'], parent__isnull=True, is_active=True
        ).order_by('id'))

        if len(stream_links) <= 1:
            if stream_links:
                link = stream_links[0]
                # Rename to "Video" if still called "Stream" or "Xem phim"
                if link.name in ('Video', 'Xem phim'):
                    self.stdout.write(f'  Rename: {link.name} → Stream')
                    if not dry_run:
                        link.name = 'Stream'
                        link.name_vi = 'Stream'
                        link.name_en = 'Stream'
                        link.name_de = 'Stream'
                        link.save(update_fields=['name', 'name_vi', 'name_en', 'name_de'])
            self.stdout.write('  → OK\n')
            return

        # Multiple links to /stream — keep the one with most children, deactivate others
        best = max(stream_links, key=lambda l: l.children.filter(is_active=True).count())
        deactivated = 0
        for link in stream_links:
            if link.id != best.id:
                self.stdout.write(f'  Deactivate duplicate: #{link.id} "{link.name}" ({link.children.count()} children)')
                if not dry_run:
                    link.is_active = False
                    link.save(update_fields=['is_active'])
                    link.children.update(is_active=False)
                deactivated += 1

        # Rename the kept link to "Video"
        if best.name in ('Video', 'Xem phim'):
            self.stdout.write(f'  Rename: {best.name} → Stream')
            if not dry_run:
                best.name = 'Stream'
                best.name_vi = 'Stream'
                best.name_en = 'Stream'
                best.name_de = 'Stream'
                best.save(update_fields=['name', 'name_vi', 'name_en', 'name_de'])

        self.stdout.write(f'  → Deactivated {deactivated} duplicates\n')

    def _fix_urls(self, dry_run):
        """Fix navigation URLs to match frontend routes"""
        self.stdout.write('🔗 Fix navigation URLs...')
        fixed = 0
        for link in NavigationLink.objects.all():
            if link.url in self.URL_FIXES:
                new_url = self.URL_FIXES[link.url]
                self.stdout.write(f'  {link.name}: {link.url} → {new_url}')
                if not dry_run:
                    link.url = new_url
                    link.save(update_fields=['url'])
                fixed += 1
        self.stdout.write(f'  → Fixed {fixed} URLs\n')

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
        """Sync dropdown children — update existing by URL, add missing, remove stale"""
        self.stdout.write('📂 Sync dropdown children...')

        for key, config in DROPDOWN_CHILDREN.items():
            parent_url = config['parent_url']
            parent = NavigationLink.objects.filter(
                url=parent_url,
                location__in=['navbar', 'both'],
                parent__isnull=True,
                is_active=True,
            ).first()

            if not parent:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  Parent "{parent_url}" not found. Creating...'
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
                else:
                    continue

            # Build desired URLs set
            desired_urls = {c['url'] for c in config['children']}
            existing_by_url = {c.url: c for c in parent.children.all()}

            updated = 0
            created = 0

            for child_data in config['children']:
                url = child_data['url']
                if url in existing_by_url:
                    # Update existing child
                    child = existing_by_url[url]
                    changed = False
                    for field in ['name', 'name_vi', 'name_en', 'name_de', 'icon', 'order']:
                        new_val = child_data.get(field, '')
                        if field == 'order':
                            new_val = child_data.get('order', 0)
                        if getattr(child, field) != new_val:
                            setattr(child, field, new_val)
                            changed = True
                    # Ensure active
                    if not child.is_active:
                        child.is_active = True
                        changed = True
                    if changed:
                        self.stdout.write(f'     ✏️  Update: {child_data["name"]}')
                        if not dry_run:
                            child.save()
                        updated += 1
                else:
                    # Create new child
                    self.stdout.write(f'     ➕ Create: {child_data["name"]} → {url}')
                    if not dry_run:
                        NavigationLink.objects.create(
                            parent=parent,
                            location='navbar',
                            name=child_data['name'],
                            name_vi=child_data.get('name_vi', child_data['name']),
                            name_en=child_data.get('name_en', child_data['name']),
                            name_de=child_data.get('name_de', child_data['name']),
                            url=url,
                            icon=child_data.get('icon', ''),
                            order=child_data.get('order', 0),
                            open_in_new_tab=child_data.get('open_in_new_tab', False),
                            is_coming_soon=child_data.get('is_coming_soon', False),
                            badge_text=child_data.get('badge_text', ''),
                        )
                    created += 1

            # Deactivate children not in desired set
            stale = 0
            for url, child in existing_by_url.items():
                if url not in desired_urls and child.is_active:
                    self.stdout.write(f'     ❌ Deactivate stale: {child.name} ({url})')
                    if not dry_run:
                        child.is_active = False
                        child.save(update_fields=['is_active'])
                    stale += 1

            self.stdout.write(
                f'  📂 {parent.name}: {updated} updated, {created} created, {stale} removed'
            )

        self.stdout.write('')

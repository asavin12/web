"""
Xoá dữ liệu mẫu / test data cho website UnstressVN.

Cách dùng:
    # Xem dữ liệu mẫu (không xoá)
    python manage.py cleanup_sample_data --dry-run

    # Xoá tất cả dữ liệu mẫu
    python manage.py cleanup_sample_data --all --confirm

    # Xoá theo loại (có thể chọn nhiều loại)
    python manage.py cleanup_sample_data --type news --type knowledge --confirm

    # Xoá vĩnh viễn (hard delete, KHÔNG thể hoàn tác)
    python manage.py cleanup_sample_data --all --hard --confirm

Các loại hỗ trợ:
    news, knowledge, tools, resources, videos, flashcards,
    stream-media, categories, users, navigation, all
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

# Usernames mẫu từ các sample data scripts
SAMPLE_USERNAMES = {
    'nguyenvan', 'tranlinh', 'lehoa', 'phamminh', 'vuthao',
    'automation_bot',
}

# Username không được xoá (luôn giữ)
PROTECTED_USERNAMES = {'admin', 'automation_bot'}

# Mẫu slug dữ liệu mẫu — slug phải chứa CHÍNH XÁC từ keyword
# (dùng word-boundary check để tránh false positive như "testdaf")
SAMPLE_SLUG_PATTERNS = [
    'sample', 'mau-', '-mau', 'example', 'demo', 'lorem', 'placeholder',
    'dummy', 'test-tu-', '-test-tu-', 'du-lieu-mau', 'bai-viet-test',
]

# Mẫu title dữ liệu mẫu
SAMPLE_TITLE_PATTERNS = [
    'sample', 'mẫu', 'ví dụ', 'example', 'demo', 'lorem',
    'placeholder', 'dummy', 'thử nghiệm', 'dữ liệu mẫu',
    'bài viết test từ', 'test bài viết',
]


def _is_sample_data(obj, title_field='title'):
    """Kiểm tra xem object có phải dữ liệu mẫu không."""
    title = getattr(obj, title_field, '') or ''
    slug = getattr(obj, 'slug', '') or ''
    source = getattr(obj, 'source', '') or ''

    title_lower = title.lower()
    slug_lower = slug.lower()

    # N8N tracking
    if source == 'n8n':
        return True, f"source=n8n"

    # AI generated content
    if getattr(obj, 'is_ai_generated', False):
        return True, f"is_ai_generated=True"

    # Sample slug patterns
    for kw in SAMPLE_SLUG_PATTERNS:
        if kw in slug_lower:
            return True, f"slug chứa '{kw}'"

    # Sample title patterns
    for kw in SAMPLE_TITLE_PATTERNS:
        if kw in title_lower:
            return True, f"title chứa '{kw}'"

    # Created by sample user (not admin)
    author = getattr(obj, 'author', None)
    if author and hasattr(author, 'username'):
        if author.username in SAMPLE_USERNAMES and author.username not in PROTECTED_USERNAMES:
            return True, f"author={author.username}"

    return False, None


class Command(BaseCommand):
    help = 'Xoá dữ liệu mẫu / test data cho UnstressVN'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type', '-t',
            action='append',
            dest='types',
            choices=[
                'news', 'knowledge', 'tools', 'resources', 'videos',
                'flashcards', 'stream-media', 'categories', 'users',
                'navigation', 'all',
            ],
            help='Loại nội dung cần xoá (có thể chọn nhiều). Dùng "all" cho tất cả.',
        )
        parser.add_argument(
            '--all', '-a',
            action='store_true',
            dest='delete_all',
            help='Xoá TẤT CẢ nội dung (không chỉ sample data). NGUY HIỂM!',
        )
        parser.add_argument(
            '--hard',
            action='store_true',
            help='Xoá vĩnh viễn (hard delete). Mặc định: soft delete (ẩn).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị, không xoá.',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Xác nhận xoá (bỏ qua hỏi yes/no).',
        )
        parser.add_argument(
            '--include-real',
            action='store_true',
            help='Bao gồm cả nội dung thật (không chỉ sample). Kết hợp với --type.',
        )

    def handle(self, *args, **options):
        types = options.get('types') or []
        delete_all_content = options['delete_all']
        hard = options['hard']
        dry_run = options['dry_run']
        confirm = options['confirm']
        include_real = options['include_real']

        # If --all flag but no types specified, treat as all types
        if delete_all_content and not types:
            types = ['all']

        if not types:
            # Default to listing all types
            if not dry_run:
                dry_run = True
                self.stdout.write(self.style.WARNING(
                    'Không chỉ định --type. Chạy dry-run cho tất cả loại...\n'
                ))
            types = ['all']

        if 'all' in types:
            types = [
                'news', 'knowledge', 'tools', 'resources', 'videos',
                'flashcards', 'stream-media', 'categories', 'users',
                'navigation',
            ]

        # Collect stats
        total_found = 0
        total_deleted = 0
        summary = {}

        self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 60))
        self.stdout.write(self.style.HTTP_INFO(
            '  UNSTRESSVN — XOÁ DỮ LIỆU MẪU'
        ))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        mode = 'DRY-RUN' if dry_run else ('HARD DELETE' if hard else 'SOFT DELETE')
        scope = 'TẤT CẢ NỘI DUNG' if (delete_all_content or include_real) else 'CHỈ DỮ LIỆU MẪU'
        self.stdout.write(f'  Mode: {mode}')
        self.stdout.write(f'  Scope: {scope}')
        self.stdout.write(f'  Types: {", ".join(types)}')
        self.stdout.write('')

        # Process each type
        for content_type in types:
            found, items = self._scan_type(
                content_type, delete_all_content or include_real
            )
            total_found += found
            summary[content_type] = {'found': found, 'deleted': 0, 'items': items}

        # Show summary
        self.stdout.write(self.style.HTTP_INFO('\n' + '-' * 60))
        self.stdout.write(self.style.HTTP_INFO('  TỔNG KẾT'))
        self.stdout.write(self.style.HTTP_INFO('-' * 60))

        for ct, info in summary.items():
            style = self.style.WARNING if info['found'] > 0 else self.style.SUCCESS
            self.stdout.write(style(f"  {ct:15s} → {info['found']:3d} items"))

        self.stdout.write(self.style.HTTP_INFO('-' * 60))
        self.stdout.write(f'  TỔNG: {total_found} items\n')

        if dry_run or total_found == 0:
            if total_found == 0:
                self.stdout.write(self.style.SUCCESS('✅ Không có dữ liệu mẫu nào.'))
            else:
                self.stdout.write(self.style.WARNING(
                    '⚠️  Chạy lại với --confirm để xoá. Thêm --hard để xoá vĩnh viễn.'
                ))
            return

        # Confirm
        if not confirm:
            action = 'XOÁ VĨNH VIỄN' if hard else 'ẨN (soft delete)'
            self.stdout.write(self.style.ERROR(
                f'\n⚠️  Bạn sắp {action} {total_found} items.'
            ))
            answer = input('Nhập "yes" để xác nhận: ')
            if answer.lower() != 'yes':
                self.stdout.write(self.style.WARNING('❌ Đã huỷ.'))
                return

        # Execute deletion
        self.stdout.write(self.style.HTTP_INFO('\n🗑️  Đang xoá...\n'))

        for ct, info in summary.items():
            deleted = self._delete_items(ct, info['items'], hard)
            info['deleted'] = deleted
            total_deleted += deleted

        # Final report
        self.stdout.write(self.style.HTTP_INFO('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS(
            f'  ✅ ĐÃ XOÁ: {total_deleted}/{total_found} items'
        ))
        action_desc = 'hard delete' if hard else 'soft delete (is_active/is_published=False)'
        self.stdout.write(f'  Action: {action_desc}')
        self.stdout.write(self.style.HTTP_INFO('=' * 60 + '\n'))

    def _scan_type(self, content_type, include_all):
        """Quét và trả về danh sách items cần xoá."""
        handler = getattr(self, f'_scan_{content_type.replace("-", "_")}', None)
        if not handler:
            self.stdout.write(self.style.ERROR(f'  ❌ Không hỗ trợ type: {content_type}'))
            return 0, []

        items = handler(include_all)
        count = len(items)

        if count > 0:
            self.stdout.write(self.style.WARNING(
                f'\n📋 {content_type.upper()} — {count} items:'
            ))
            for obj, reason, title_field in items:
                title = getattr(obj, title_field, '') or str(obj)
                pk = obj.pk
                slug = getattr(obj, 'slug', '-')
                reason_str = f' [{reason}]' if reason else ''
                self.stdout.write(f'  [{pk:>4}] {title[:60]:60s} /{slug}{reason_str}')
        else:
            self.stdout.write(f'\n📋 {content_type.upper()} — 0 items')

        return count, items

    # ======================================================
    # SCAN methods — từng loại nội dung
    # ======================================================

    def _scan_news(self, include_all):
        from news.models import Article
        return self._scan_generic(Article, include_all, title_field='title')

    def _scan_knowledge(self, include_all):
        from knowledge.models import KnowledgeArticle
        return self._scan_generic(KnowledgeArticle, include_all, title_field='title')

    def _scan_tools(self, include_all):
        from tools.models import Tool
        return self._scan_generic(Tool, include_all, title_field='name')

    def _scan_resources(self, include_all):
        from resources.models import Resource
        return self._scan_generic(Resource, include_all, title_field='title')

    def _scan_videos(self, include_all):
        from core.models import Video
        return self._scan_generic(Video, include_all, title_field='title')

    def _scan_flashcards(self, include_all):
        from tools.models import FlashcardDeck
        return self._scan_generic(FlashcardDeck, include_all, title_field='name')

    def _scan_stream_media(self, include_all):
        from mediastream.models import StreamMedia
        return self._scan_generic(StreamMedia, include_all, title_field='title')

    def _scan_categories(self, include_all):
        """Quét tất cả category tables."""
        items = []
        category_models = []

        try:
            from news.models import Category as NewsCategory
            category_models.append(('news', NewsCategory))
        except ImportError:
            pass
        try:
            from knowledge.models import Category as KnowledgeCategory
            category_models.append(('knowledge', KnowledgeCategory))
        except ImportError:
            pass
        try:
            from resources.models import Category as ResourceCategory
            category_models.append(('resources', ResourceCategory))
        except ImportError:
            pass
        try:
            from tools.models import ToolCategory
            category_models.append(('tools', ToolCategory))
        except ImportError:
            pass
        try:
            from mediastream.models import MediaCategory
            category_models.append(('media', MediaCategory))
        except ImportError:
            pass

        for prefix, Model in category_models:
            for obj in Model.objects.all():
                if include_all:
                    items.append((obj, f'{prefix} category', 'name'))
                else:
                    is_sample, reason = _is_sample_data(obj, title_field='name')
                    if is_sample:
                        items.append((obj, reason, 'name'))
        return items

    def _scan_users(self, include_all):
        """Quét sample users (BẢO VỆ admin và superuser)."""
        items = []
        for user in User.objects.all():
            if user.username in PROTECTED_USERNAMES:
                continue
            if user.is_superuser:
                continue

            if include_all:
                items.append((user, 'delete_all', 'username'))
            elif user.username in SAMPLE_USERNAMES:
                items.append((user, 'sample user', 'username'))
            elif user.email and 'example.com' in user.email:
                items.append((user, 'example.com email', 'username'))
        return items

    def _scan_navigation(self, include_all):
        """Quét navigation links."""
        try:
            from core.models import NavigationLink
            items = []
            for obj in NavigationLink.objects.all():
                if include_all:
                    items.append((obj, 'delete_all', 'title'))
                else:
                    is_sample, reason = _is_sample_data(obj, title_field='title')
                    if is_sample:
                        items.append((obj, reason, 'title'))
            return items
        except (ImportError, Exception):
            return []

    def _scan_generic(self, Model, include_all, title_field='title'):
        """Quét generic: tìm sample data dựa trên heuristics."""
        items = []
        for obj in Model.objects.all():
            if include_all:
                items.append((obj, 'delete_all', title_field))
            else:
                is_sample, reason = _is_sample_data(obj, title_field=title_field)
                if is_sample:
                    items.append((obj, reason, title_field))
        return items

    # ======================================================
    # DELETE methods
    # ======================================================

    def _delete_items(self, content_type, items, hard):
        """Xoá danh sách items."""
        deleted = 0
        for obj, reason, title_field in items:
            title = getattr(obj, title_field, '') or str(obj)
            try:
                if hard:
                    # Cascade: flashcard deck → flashcard cards auto-deleted
                    obj.delete()
                    self.stdout.write(self.style.SUCCESS(
                        f'  🗑️  [{content_type}] Xoá vĩnh viễn: {title[:50]}'
                    ))
                else:
                    # Soft delete: set is_active/is_published = False
                    soft_field = self._get_soft_field(content_type, obj)
                    if soft_field:
                        setattr(obj, soft_field, False)
                        obj.save(update_fields=[soft_field])
                        self.stdout.write(self.style.WARNING(
                            f'  👁️  [{content_type}] Ẩn ({soft_field}=False): {title[:50]}'
                        ))
                    else:
                        # No soft delete field → hard delete
                        obj.delete()
                        self.stdout.write(self.style.SUCCESS(
                            f'  🗑️  [{content_type}] Xoá (no soft field): {title[:50]}'
                        ))
                deleted += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  ❌ [{content_type}] Lỗi xoá {title[:40]}: {e}'
                ))
        return deleted

    def _get_soft_field(self, content_type, obj):
        """Tìm field phù hợp cho soft delete."""
        soft_field_map = {
            'news': 'is_published',
            'knowledge': 'is_published',
            'resources': 'is_active',
            'tools': 'is_active',
            'videos': 'is_active',
            'stream-media': 'is_active',
            'flashcards': 'is_public',
        }
        field = soft_field_map.get(content_type)
        if field and hasattr(obj, field):
            return field
        # Categories, users, navigation → no soft field
        return None

"""
Menu Builder CLI — Quản lý menu framework dễ dàng từ command line.

Usage:
  python manage.py menu list                                    # Xem toàn bộ menu tree
  python manage.py menu list --location footer                  # Chỉ footer
  python manage.py menu add "Tên menu" /url --icon Home         # Thêm link navbar
  python manage.py menu add "Tên menu" /url --parent "Tin tức"  # Thêm submenu
  python manage.py menu add "Tên menu" /url --footer resources  # Thêm footer link
  python manage.py menu add "Facebook" https://fb.com --footer social --icon Facebook --newtab
  python manage.py menu remove "Tên menu"                       # Xoá menu
  python manage.py menu toggle "Tên menu"                       # Bật/tắt menu
  python manage.py menu move "Tên menu" --parent "Video"        # Đổi parent
  python manage.py menu move "Tên menu" --order 5               # Đổi thứ tự
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from core.models import NavigationLink


class Command(BaseCommand):
    help = 'Menu builder CLI — thêm, sửa, xoá, xem menu dễ dàng'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Hành động')

        # ── list ──
        list_cmd = subparsers.add_parser('list', help='Xem menu tree')
        list_cmd.add_argument('--location', choices=['navbar', 'footer', 'both'], help='Lọc vị trí')

        # ── add ──
        add_cmd = subparsers.add_parser('add', help='Thêm menu mới')
        add_cmd.add_argument('name', help='Tên hiển thị')
        add_cmd.add_argument('url', help='URL (nội bộ VD: /tin-tuc hoặc https://...)')
        add_cmd.add_argument('--icon', default='', help='Lucide icon name')
        add_cmd.add_argument('--parent', default='', help='Tên menu cha (tạo submenu)')
        add_cmd.add_argument('--footer', default='', help='Footer section: resources/company/legal/social/community')
        add_cmd.add_argument('--newtab', action='store_true', help='Mở tab mới')
        add_cmd.add_argument('--badge', default='', help='Badge text (VD: New, Hot)')
        add_cmd.add_argument('--vi', default='', help='Tên tiếng Việt')
        add_cmd.add_argument('--en', default='', help='Tên tiếng Anh')
        add_cmd.add_argument('--de', default='', help='Tên tiếng Đức')
        add_cmd.add_argument('--desc', default='', help='Mô tả ngắn')
        add_cmd.add_argument('--order', type=int, default=0, help='Thứ tự')

        # ── remove ──
        rm_cmd = subparsers.add_parser('remove', help='Xoá menu')
        rm_cmd.add_argument('name', help='Tên menu cần xoá')
        rm_cmd.add_argument('--force', action='store_true', help='Xoá không hỏi (kể cả có children)')

        # ── toggle ──
        tog_cmd = subparsers.add_parser('toggle', help='Bật/tắt menu')
        tog_cmd.add_argument('name', help='Tên menu')

        # ── move ──
        mv_cmd = subparsers.add_parser('move', help='Di chuyển/sắp xếp menu')
        mv_cmd.add_argument('name', help='Tên menu')
        mv_cmd.add_argument('--parent', default=None, help='Tên parent mới (hoặc "none" để thành root)')
        mv_cmd.add_argument('--order', type=int, default=None, help='Thứ tự mới')
        mv_cmd.add_argument('--location', choices=['navbar', 'footer', 'both'], default=None)

    def handle(self, *args, **options):
        action = options.get('action')
        if not action:
            self.stdout.write(self.style.ERROR('Cần chỉ định action: list, add, remove, toggle, move'))
            return

        handler = getattr(self, f'handle_{action}', None)
        if handler:
            handler(options)
        else:
            raise CommandError(f'Action không hợp lệ: {action}')

    def handle_list(self, options):
        """Hiển thị menu tree"""
        location = options.get('location')
        qs = NavigationLink.objects.filter(parent__isnull=True)
        if location:
            qs = qs.filter(location__in=[location, 'both'])
        qs = qs.prefetch_related('children').order_by('location', 'footer_section', 'order')

        if not qs.exists():
            self.stdout.write(self.style.WARNING('Không có menu nào.'))
            return

        current_location = None
        for parent in qs:
            # Section header
            loc = parent.get_location_display()
            if loc != current_location:
                current_location = loc
                self.stdout.write(f'\n{self.style.HTTP_INFO(f"═══ {loc.upper()} ═══")}')

            status = self.style.SUCCESS('●') if parent.is_active else self.style.ERROR('○')
            icon = f' [{parent.icon}]' if parent.icon else ''
            section = f' ({parent.footer_section})' if parent.footer_section else ''
            badge = f' 🏷️{parent.badge_text}' if parent.badge_text else ''
            self.stdout.write(f'  {status} {parent.name}{icon}{section}{badge}  →  {parent.url}  [order:{parent.order}]')

            children = parent.children.order_by('order')
            for child in children:
                c_status = self.style.SUCCESS('●') if child.is_active else self.style.ERROR('○')
                c_icon = f' [{child.icon}]' if child.icon else ''
                c_badge = f' 🏷️{child.badge_text}' if child.badge_text else ''
                soon = ' ⏳Soon' if child.is_coming_soon else ''
                self.stdout.write(f'    {c_status} └─ {child.name}{c_icon}{c_badge}{soon}  →  {child.url}')

        total = NavigationLink.objects.count()
        active = NavigationLink.objects.filter(is_active=True).count()
        self.stdout.write(f'\n📊 Tổng: {total} | Đang hiển thị: {active} | Đang ẩn: {total - active}')

    def handle_add(self, options):
        """Thêm menu mới"""
        name = options['name']
        url = options['url']

        # Determine location + parent
        parent_obj = None
        location = 'navbar'
        footer_section = ''

        if options['parent']:
            parent_obj = NavigationLink.objects.filter(name=options['parent'], parent__isnull=True).first()
            if not parent_obj:
                raise CommandError(f'Không tìm thấy menu cha: "{options["parent"]}"')
            location = parent_obj.location

        if options['footer']:
            location = 'footer'
            footer_section = options['footer']

        # Auto order: last position
        order = options['order']
        if order == 0:
            siblings = NavigationLink.objects.filter(parent=parent_obj, location=location)
            max_order = siblings.aggregate(m=models.Max('order'))['m'] or 0
            order = max_order + 1

        item = NavigationLink.objects.create(
            name=name,
            name_vi=options.get('vi') or name,
            name_en=options.get('en') or '',
            name_de=options.get('de') or '',
            url=url,
            description=options.get('desc') or '',
            icon=options.get('icon') or '',
            location=location,
            footer_section=footer_section,
            parent=parent_obj,
            open_in_new_tab=options.get('newtab', False),
            badge_text=options.get('badge') or '',
            order=order,
        )

        parent_info = f' (con của "{parent_obj.name}")' if parent_obj else ''
        self.stdout.write(self.style.SUCCESS(
            f'✅ Đã thêm: {item.name} → {item.url} [{location}]{parent_info} [order:{order}]'
        ))

    def handle_remove(self, options):
        """Xoá menu"""
        name = options['name']
        items = NavigationLink.objects.filter(name=name)
        if not items.exists():
            raise CommandError(f'Không tìm thấy: "{name}"')

        for item in items:
            children_count = item.children.count()
            if children_count > 0 and not options.get('force'):
                raise CommandError(
                    f'"{name}" có {children_count} mục con. Dùng --force để xoá cả children.'
                )
            item_str = f'{item.name} [{item.get_location_display()}]'
            item.delete()
            self.stdout.write(self.style.WARNING(f'🗑️ Đã xoá: {item_str}'))

    def handle_toggle(self, options):
        """Bật/tắt menu"""
        name = options['name']
        items = NavigationLink.objects.filter(name=name)
        if not items.exists():
            raise CommandError(f'Không tìm thấy: "{name}"')

        for item in items:
            item.is_active = not item.is_active
            item.save(update_fields=['is_active'])
            state = self.style.SUCCESS('BẬT') if item.is_active else self.style.ERROR('TẮT')
            self.stdout.write(f'🔄 {item.name}: {state}')

    def handle_move(self, options):
        """Di chuyển/sắp xếp menu"""
        name = options['name']
        item = NavigationLink.objects.filter(name=name).first()
        if not item:
            raise CommandError(f'Không tìm thấy: "{name}"')

        changed = []

        if options.get('parent') is not None:
            parent_name = options['parent']
            if parent_name.lower() == 'none':
                item.parent = None
                changed.append('parent → root')
            else:
                parent_obj = NavigationLink.objects.filter(name=parent_name, parent__isnull=True).first()
                if not parent_obj:
                    raise CommandError(f'Không tìm thấy parent: "{parent_name}"')
                item.parent = parent_obj
                changed.append(f'parent → {parent_name}')

        if options.get('order') is not None:
            item.order = options['order']
            changed.append(f'order → {options["order"]}')

        if options.get('location'):
            item.location = options['location']
            changed.append(f'location → {options["location"]}')

        if changed:
            item.save()
            self.stdout.write(self.style.SUCCESS(f'✅ {item.name}: {", ".join(changed)}'))
        else:
            self.stdout.write(self.style.WARNING('Không có gì thay đổi. Dùng --parent, --order, --location'))

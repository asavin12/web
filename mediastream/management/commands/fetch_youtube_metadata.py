"""
Management command để lấy metadata cho YouTube + Google Drive videos thiếu thông tin.
Usage: python manage.py fetch_youtube_metadata
"""
from django.core.management.base import BaseCommand
from mediastream.models import StreamMedia


class Command(BaseCommand):
    help = 'Fetch metadata (duration, tags, views) cho YouTube + Google Drive videos thiếu thông tin'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-fetch cho tất cả videos')
        parser.add_argument('--force', action='store_true', help='Ghi đè cả fields đã có')

    def handle(self, *args, **options):
        from core.config import invalidate_cache
        invalidate_cache()

        self._fetch_youtube(options)
        self._fetch_gdrive(options)

    def _fetch_youtube(self, options):
        from core.youtube import fetch_youtube_info_batch
        from django.db.models import Q

        qs = StreamMedia.objects.filter(storage_type='youtube').exclude(youtube_id='')
        self.stdout.write(f'\n=== YouTube videos: {qs.count()} tổng ===')

        if not options['all']:
            qs = qs.filter(Q(duration__isnull=True) | Q(duration=0) | Q(duration__lt=1))

        media_list = list(qs)
        total = len(media_list)
        if not total:
            self.stdout.write(self.style.SUCCESS('YouTube: tất cả đã có metadata.'))
            return

        self.stdout.write(f'Đang xử lý {total} YouTube videos...')
        video_ids = [m.youtube_id for m in media_list]
        all_info = fetch_youtube_info_batch(video_ids)
        self.stdout.write(f'Nhận được info cho {len(all_info)}/{len(video_ids)} videos')

        updated = 0
        failed = 0
        force = options.get('force', False)

        for media in media_list:
            self.stdout.write(f'  [{media.id}] {media.youtube_id} — {media.title[:50] if media.title else "(no title)"}')
            info = all_info.get(media.youtube_id)
            if not info:
                self.stdout.write(self.style.WARNING(f'    ❌ Không có info'))
                failed += 1
                continue

            try:
                changed = False

                if force or not media.title:
                    title = info.get('title', '')[:255]
                    if title:
                        media.title = title
                        changed = True

                if force or not media.description:
                    desc = info.get('description', '')
                    if desc:
                        media.description = desc
                        changed = True

                dur = info.get('duration_seconds')
                if dur and (force or not media.duration):
                    media.duration = int(dur)
                    changed = True

                tags = info.get('tags', [])
                if tags and (force or not media.tags):
                    media.tags = ', '.join(tags[:10])
                    changed = True

                views = info.get('view_count', 0)
                if views and (force or not media.view_count):
                    media.view_count = views
                    changed = True

                if changed:
                    media.save()
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✅ duration={media.duration}s, views={media.view_count}'
                    ))
                else:
                    self.stdout.write(f'    — Không có gì mới')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Error: {e}'))
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            f'YouTube: {updated} updated, {failed} failed, {total - updated - failed} skipped'
        ))

    def _fetch_gdrive(self, options):
        from mediastream import gdrive_oauth
        from django.db.models import Q

        qs = StreamMedia.objects.filter(storage_type='gdrive').exclude(gdrive_file_id='')
        self.stdout.write(f'\n=== Google Drive videos: {qs.count()} tổng ===')

        if not options['all']:
            qs = qs.filter(Q(duration__isnull=True) | Q(duration=0) | Q(duration__lt=1))

        media_list = list(qs)
        total = len(media_list)
        if not total:
            self.stdout.write(self.style.SUCCESS('GDrive: tất cả đã có metadata.'))
            return

        self.stdout.write(f'Đang xử lý {total} GDrive videos...')
        file_ids = [m.gdrive_file_id for m in media_list]
        all_info = gdrive_oauth.fetch_gdrive_metadata_batch(file_ids)
        self.stdout.write(f'Nhận được info cho {len(all_info)}/{len(file_ids)} files')

        updated = 0
        failed = 0
        force = options.get('force', False)

        for media in media_list:
            self.stdout.write(f'  [{media.id}] {media.gdrive_file_id[:20]} — {media.title[:50] if media.title else "(no title)"}')
            info = all_info.get(media.gdrive_file_id)
            if not info:
                self.stdout.write(self.style.WARNING(f'    ❌ Không có info'))
                failed += 1
                continue

            try:
                changed = False

                if info.get('size') and (force or not media.file_size):
                    media.file_size = info['size']
                    changed = True

                dur = info.get('duration_seconds')
                if dur and (force or not media.duration):
                    media.duration = dur
                    changed = True

                if info.get('mime_type') and (force or not media.mime_type):
                    media.mime_type = info['mime_type']
                    changed = True

                if info.get('width') and (force or not media.width):
                    media.width = info['width']
                    changed = True

                if info.get('height') and (force or not media.height):
                    media.height = info['height']
                    changed = True

                if changed:
                    media.save()
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'    ✅ duration={media.duration}s, size={media.file_size}, {media.width}x{media.height}'
                    ))
                else:
                    self.stdout.write(f'    — Không có gì mới')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Error: {e}'))
                failed += 1

        self.stdout.write(self.style.SUCCESS(
            f'GDrive: {updated} updated, {failed} failed, {total - updated - failed} skipped'
        ))

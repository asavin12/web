"""
Management command để lấy metadata cho tất cả YouTube videos thiếu thông tin.
Usage: python manage.py fetch_youtube_metadata
"""
from django.core.management.base import BaseCommand
from mediastream.models import StreamMedia


class Command(BaseCommand):
    help = 'Fetch YouTube metadata (duration, tags, views) cho các video thiếu thông tin'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-fetch cho tất cả YouTube videos')
        parser.add_argument('--force', action='store_true', help='Ghi đè cả fields đã có')

    def handle(self, *args, **options):
        from core.youtube import fetch_youtube_info_batch
        from django.db.models import Q

        # Reload config to get fresh API key
        from core.config import invalidate_cache
        invalidate_cache()

        qs = StreamMedia.objects.filter(storage_type='youtube').exclude(youtube_id='')
        self.stdout.write(f'Tổng YouTube videos: {qs.count()}')
        
        if not options['all']:
            qs = qs.filter(Q(duration__isnull=True) | Q(duration=0) | Q(duration__lt=1))

        media_list = list(qs)
        total = len(media_list)
        if not total:
            self.stdout.write(self.style.SUCCESS('Tất cả YouTube videos đã có metadata đầy đủ.'))
            return

        self.stdout.write(f'Đang xử lý {total} YouTube videos...')
        
        # Batch fetch: 1 API call cho tất cả
        video_ids = [m.youtube_id for m in media_list]
        self.stdout.write(f'Fetching batch: {", ".join(video_ids)}')
        all_info = fetch_youtube_info_batch(video_ids)
        self.stdout.write(f'Nhận được info cho {len(all_info)}/{len(video_ids)} videos')
        
        updated = 0
        failed = 0
        force = options.get('force', False)

        for media in media_list:
            self.stdout.write(f'  [{media.id}] {media.youtube_id} — {media.title[:50] if media.title else "(no title)"}')
            info = all_info.get(media.youtube_id)
            if not info:
                self.stdout.write(self.style.WARNING(f'    ❌ Không có info trong batch result'))
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
            f'\nHoàn tất: {updated} updated, {failed} failed, {total - updated - failed} skipped'
        ))

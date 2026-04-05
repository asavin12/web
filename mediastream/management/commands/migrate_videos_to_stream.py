"""
Migrate core.Video (YouTube) → mediastream.StreamMedia
Chuyển tất cả video YouTube cũ vào hệ thống Stream thống nhất.

Usage:
    python manage.py migrate_videos_to_stream
    python manage.py migrate_videos_to_stream --dry-run
"""

from django.core.management.base import BaseCommand
from core.models import Video
from mediastream.models import StreamMedia, MediaCategory


class Command(BaseCommand):
    help = 'Migrate YouTube videos from core.Video to StreamMedia'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        videos = Video.objects.filter(is_active=True)
        
        if not videos.exists():
            self.stdout.write(self.style.WARNING('No active videos found to migrate.'))
            return
        
        self.stdout.write(f'Found {videos.count()} videos to migrate...\n')
        
        # Get or create "YouTube" category
        youtube_cat, created = MediaCategory.objects.get_or_create(
            slug='youtube',
            defaults={
                'name': 'YouTube',
                'description': 'Video YouTube nhúng',
                'icon': 'youtube',
                'order': 10,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created category: YouTube'))
        
        migrated = 0
        skipped = 0
        
        for video in videos:
            # Skip if already migrated (check by youtube_id)
            if StreamMedia.objects.filter(youtube_id=video.youtube_id).exists():
                self.stdout.write(f'  SKIP (exists): {video.title}')
                skipped += 1
                continue
            
            self.stdout.write(f'  MIGRATE: {video.title} (yt:{video.youtube_id})')
            
            if not dry_run:
                # Map language: core.Video uses en/de/all, StreamMedia uses vi/en/de/all
                lang = video.language if video.language in ('en', 'de', 'all') else 'all'
                
                # Parse duration string "12:30" → seconds
                duration_seconds = None
                if video.duration:
                    try:
                        parts = video.duration.split(':')
                        if len(parts) == 2:
                            duration_seconds = int(parts[0]) * 60 + int(parts[1])
                        elif len(parts) == 3:
                            duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    except (ValueError, IndexError):
                        pass
                
                StreamMedia.objects.create(
                    title=video.title,
                    slug=video.slug,
                    description=video.description,
                    youtube_id=video.youtube_id,
                    storage_type='youtube',
                    media_type='video',
                    mime_type='video/youtube',
                    language=lang,
                    level=video.level if video.level else 'all',
                    category=youtube_cat,
                    duration=duration_seconds,
                    view_count=video.view_count,
                    is_public=True,
                    is_active=True,
                )
                migrated += 1
        
        self.stdout.write(f'\n  Migrated: {migrated}, Skipped: {skipped}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes made.'))
        else:
            self.stdout.write(self.style.SUCCESS('Migration complete!'))

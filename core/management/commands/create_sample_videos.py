from django.core.management.base import BaseCommand
from core.models import Video


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu Video'

    def handle(self, *args, **options):
        # Xóa dữ liệu cũ
        Video.objects.all().delete()
        self.stdout.write('Đã xóa video cũ')

        # Tạo video mẫu với YouTube ID thật
        videos_data = [
            {
                'title': 'Learn English in 30 Minutes - ALL the English Basics',
                'youtube_id': 'juKd26qkNAw',
                'duration': '30:25',
                'language': 'en',
                'level': 'A1',
                'is_featured': True,
                'order': 1,
            },
            {
                'title': '1000 English Conversation Practice',
                'youtube_id': 'kLCHFP0Y-rE',
                'duration': '3:02:25',
                'language': 'en',
                'level': 'A2',
                'is_featured': True,
                'order': 2,
            },
            {
                'title': 'German for Beginners A1 - Complete Course',
                'youtube_id': 'RuGmc662HDg',
                'duration': '4:15:30',
                'language': 'de',
                'level': 'A1',
                'is_featured': True,
                'order': 3,
            },
            {
                'title': 'Learn Vietnamese in 20 Minutes',
                'youtube_id': 'DfWxWX2xzFE',
                'duration': '20:15',
                'language': 'vi',
                'level': 'A1',
                'is_featured': True,
                'order': 4,
            },
            {
                'title': 'English Listening Practice Level 1',
                'youtube_id': 'ZpRVQZ3v3cQ',
                'duration': '45:12',
                'language': 'en',
                'level': 'A1',
                'order': 5,
            },
            {
                'title': 'IELTS Speaking Band 7+ Tips',
                'youtube_id': 'rZFI6_qLF5w',
                'duration': '18:45',
                'language': 'en',
                'level': 'B2',
                'order': 6,
            },
            {
                'title': 'German Pronunciation - Complete Guide',
                'youtube_id': 'Y7P0JBe8oD4',
                'duration': '25:18',
                'language': 'de',
                'level': 'A1',
                'order': 7,
            },
            {
                'title': 'German B1 Listening Practice',
                'youtube_id': 'uhEDWW9yDCk',
                'duration': '52:30',
                'language': 'de',
                'level': 'B1',
                'order': 8,
            },
        ]

        for data in videos_data:
            video = Video.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f'✅ {video.title}'))

        self.stdout.write(self.style.SUCCESS(f'\n🎬 Tổng cộng: {Video.objects.count()} video'))

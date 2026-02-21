"""
Management command để cập nhật lại slugs cho các bài viết
sử dụng vietnamese_slugify thay vì slugify mặc định
"""

from django.core.management.base import BaseCommand
from core.utils import vietnamese_slugify
from news.models import Article, Category as NewsCategory
from knowledge.models import KnowledgeArticle, Category as KnowledgeCategory


class Command(BaseCommand):
    help = 'Cập nhật lại slugs cho bài viết sử dụng vietnamese_slugify (không dấu)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị thay đổi, không lưu vào database',
        )
        parser.add_argument(
            '--news',
            action='store_true',
            help='Chỉ cập nhật News articles',
        )
        parser.add_argument(
            '--knowledge',
            action='store_true',
            help='Chỉ cập nhật Knowledge articles',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update_news = options['news'] or not (options['news'] or options['knowledge'])
        update_knowledge = options['knowledge'] or not (options['news'] or options['knowledge'])

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Không lưu thay đổi\n'))

        # Update News Categories
        if update_news:
            self.stdout.write(self.style.MIGRATE_HEADING('=== News Categories ==='))
            for cat in NewsCategory.objects.all():
                new_slug = vietnamese_slugify(cat.name)
                if cat.slug != new_slug:
                    self.stdout.write(f'  {cat.name}:')
                    self.stdout.write(f'    OLD: {cat.slug}')
                    self.stdout.write(f'    NEW: {new_slug}')
                    if not dry_run:
                        cat.slug = new_slug
                        cat.save(update_fields=['slug'])

            # Update News Articles
            self.stdout.write(self.style.MIGRATE_HEADING('\n=== News Articles ==='))
            for article in Article.objects.all():
                new_slug = vietnamese_slugify(article.title)
                # Ensure unique
                counter = 1
                original_slug = new_slug
                while Article.objects.filter(slug=new_slug).exclude(pk=article.pk).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                
                if article.slug != new_slug:
                    self.stdout.write(f'  {article.title[:50]}...:')
                    self.stdout.write(f'    OLD: {article.slug}')
                    self.stdout.write(f'    NEW: {new_slug}')
                    if not dry_run:
                        article.slug = new_slug
                        article.save(update_fields=['slug'])

        # Update Knowledge Categories
        if update_knowledge:
            self.stdout.write(self.style.MIGRATE_HEADING('\n=== Knowledge Categories ==='))
            for cat in KnowledgeCategory.objects.all():
                new_slug = vietnamese_slugify(cat.name)
                if cat.slug != new_slug:
                    self.stdout.write(f'  {cat.name}:')
                    self.stdout.write(f'    OLD: {cat.slug}')
                    self.stdout.write(f'    NEW: {new_slug}')
                    if not dry_run:
                        cat.slug = new_slug
                        cat.save(update_fields=['slug'])

            # Update Knowledge Articles
            self.stdout.write(self.style.MIGRATE_HEADING('\n=== Knowledge Articles ==='))
            for article in KnowledgeArticle.objects.all():
                new_slug = vietnamese_slugify(article.title)
                # Ensure unique
                counter = 1
                original_slug = new_slug
                while KnowledgeArticle.objects.filter(slug=new_slug).exclude(pk=article.pk).exists():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                
                if article.slug != new_slug:
                    self.stdout.write(f'  {article.title[:50]}...:')
                    self.stdout.write(f'    OLD: {article.slug}')
                    self.stdout.write(f'    NEW: {new_slug}')
                    if not dry_run:
                        article.slug = new_slug
                        article.save(update_fields=['slug'])

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN hoàn tất. Chạy lại không có --dry-run để lưu thay đổi.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nĐã cập nhật xong tất cả slugs!'))

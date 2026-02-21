"""
Unit tests cho News app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Article

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests cho Category model"""
    
    def test_create_category(self):
        category = Category.objects.create(name='Công nghệ')
        self.assertEqual(category.slug, 'cong-nghe')
        self.assertEqual(str(category), 'Công nghệ')
    
    def test_auto_slug_generation(self):
        category = Category.objects.create(name='Tin tức mới')
        self.assertEqual(category.slug, 'tin-tuc-moi')


class ArticleModelTest(TestCase):
    """Tests cho Article model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category')
    
    def test_create_article(self):
        article = Article.objects.create(
            title='Bài viết test',
            content='Nội dung bài viết',
            category=self.category,
            author=self.user
        )
        self.assertEqual(article.slug, 'bai-viet-test')
    
    def test_auto_seo_fields(self):
        article = Article.objects.create(
            title='Tiêu đề dài hơn bảy mươi ký tự để test tự động cắt ngắn meta title',
            excerpt='Đoạn tóm tắt ngắn',
            content='Nội dung',
            category=self.category,
            author=self.user
        )
        # meta_title tự động từ title
        self.assertLessEqual(len(article.meta_title), 70)
    
    def test_reading_time(self):
        # 400 từ ~ 2 phút
        content = ' '.join(['word'] * 400)
        article = Article.objects.create(
            title='Test',
            content=content,
            category=self.category,
            author=self.user
        )
        self.assertEqual(article.reading_time, 2)
    
    def test_increment_views(self):
        article = Article.objects.create(
            title='Test Views',
            content='Content',
            category=self.category,
            author=self.user
        )
        self.assertEqual(article.view_count, 0)
        article.increment_views()
        article.refresh_from_db()
        self.assertEqual(article.view_count, 1)


class NewsAPITest(APITestCase):
    """Tests cho News API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Tech', is_active=True)
        self.article = Article.objects.create(
            title='Published Article',
            slug='published-article',
            content='Content here',
            excerpt='Short excerpt',
            category=self.category,
            author=self.user,
            is_published=True
        )
        self.draft = Article.objects.create(
            title='Draft Article',
            content='Draft content',
            category=self.category,
            author=self.user,
            is_published=False
        )
    
    def test_list_categories(self):
        response = self.client.get('/api/v1/news/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_published_articles(self):
        response = self.client.get('/api/v1/news/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Chỉ hiển thị bài đã published
        self.assertEqual(len(response.data['results']), 1)
    
    def test_article_detail(self):
        response = self.client.get(f'/api/v1/news/articles/{self.article.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Published Article')
    
    def test_draft_not_accessible(self):
        response = self.client.get(f'/api/v1/news/articles/{self.draft.slug}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_featured_articles(self):
        self.article.is_featured = True
        self.article.save()
        response = self.client.get('/api/v1/news/articles/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_articles(self):
        response = self.client.get('/api/v1/news/articles/?search=Published')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

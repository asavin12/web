"""
Unit tests cho Knowledge app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, KnowledgeArticle

User = get_user_model()


class CategoryModelTest(TestCase):
    def test_create_category(self):
        category = Category.objects.create(name='Ngữ pháp')
        self.assertEqual(category.slug, 'ngu-phap')


class KnowledgeArticleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Grammar')
    
    def test_create_article(self):
        article = KnowledgeArticle.objects.create(
            title='Học ngữ pháp A1',
            content='Nội dung',
            category=self.category,
            author=self.user,
            language='de',
            level='A1'
        )
        self.assertEqual(article.slug, 'hoc-ngu-phap-a1')
        self.assertEqual(article.language, 'de')
        self.assertEqual(article.level, 'A1')
    
    def test_language_level_display(self):
        article = KnowledgeArticle.objects.create(
            title='Test',
            content='Content',
            category=self.category,
            author=self.user,
            language='en',
            level='B2'
        )
        self.assertEqual(article.get_language_display_vi(), 'Tiếng Anh')
        self.assertEqual(article.get_level_display_vi(), 'B2 - Trung cao')


class KnowledgeAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Grammar', is_active=True)
        self.article = KnowledgeArticle.objects.create(
            title='English Grammar Basics',
            slug='english-grammar-basics',
            content='Content',
            excerpt='Learn grammar',
            category=self.category,
            author=self.user,
            language='en',
            level='A1',
            is_published=True
        )
        self.german_article = KnowledgeArticle.objects.create(
            title='Deutsche Grammatik',
            content='Inhalt',
            category=self.category,
            author=self.user,
            language='de',
            level='B1',
            is_published=True
        )
    
    def test_list_articles(self):
        response = self.client.get('/api/v1/knowledge/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_language(self):
        response = self.client.get('/api/v1/knowledge/articles/?language=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_level(self):
        response = self.client.get('/api/v1/knowledge/articles/?level=A1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_article_detail(self):
        response = self.client.get(f'/api/v1/knowledge/articles/{self.article.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('schema_type', response.data)
    
    def test_by_language_action(self):
        response = self.client.get('/api/v1/knowledge/articles/by_language/?lang=de')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_by_level_action(self):
        response = self.client.get('/api/v1/knowledge/articles/by_level/?level=B1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

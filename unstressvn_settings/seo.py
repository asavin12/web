"""
SEO Module cho UnstressVN
Bao gồm Sitemaps và Robots.txt generator
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.http import HttpResponse
from core.models import Video
from resources.models import Resource
from news.models import Article as NewsArticle
from knowledge.models import KnowledgeArticle


class StaticViewSitemap(Sitemap):
    """Sitemap cho các trang tĩnh"""
    priority = 0.8
    changefreq = 'weekly'
    
    def items(self):
        return ['home', 'videos', 'resources', 'news', 'knowledge', 'about', 'contact']
    
    def location(self, item):
        urls = {
            'home': '/',
            'videos': '/videos',
            'resources': '/resources',
            'news': '/tin-tuc',
            'knowledge': '/kien-thuc',
            'about': '/about',
            'contact': '/contact',
        }
        return urls.get(item, '/')


class VideoSitemap(Sitemap):
    """Sitemap cho Videos"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Video.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/videos/{obj.slug}'


class ResourceSitemap(Sitemap):
    """Sitemap cho Resources"""
    changefreq = 'weekly'
    priority = 0.6
    
    def items(self):
        return Resource.objects.filter(is_approved=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/resources/{obj.slug}'


class NewsSitemap(Sitemap):
    """Sitemap cho News Articles"""
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return NewsArticle.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/tin-tuc/{obj.slug}'


class KnowledgeSitemap(Sitemap):
    """Sitemap cho Knowledge Articles"""
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return KnowledgeArticle.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return f'/kien-thuc/{obj.slug}'


# Tất cả sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'videos': VideoSitemap,
    'resources': ResourceSitemap,
    'news': NewsSitemap,
    'knowledge': KnowledgeSitemap,
}


def robots_txt(request):
    """Generate robots.txt dynamically"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# Disallow admin and API",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /accounts/",
        "",
        "# Allow specific API for SEO",
        "Allow: /api/v1/navigation/",
        "",
        "# Sitemap",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

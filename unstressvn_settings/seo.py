"""
SEO Module cho UnstressVN
Bao gồm Sitemaps và Robots.txt generator

URL mapping (khớp với React Router):
  /                              → Trang chủ
  /tin-tuc                       → Danh sách tin tức
  /tin-tuc/{categorySlug}/{slug} → Chi tiết bài viết
  /kien-thuc                     → Danh sách kiến thức
  /kien-thuc/{categorySlug}/{slug} → Chi tiết bài kiến thức
  /cong-cu                       → Danh sách công cụ
  /cong-cu/{categorySlug}/{slug} → Chi tiết công cụ
  /tai-lieu                      → Danh sách tài liệu
  /tai-lieu/{slug}               → Chi tiết tài liệu (không có category trong URL)
  /video                         → Danh sách video
  /video/{slug}                  → Chi tiết video
  /tim-kiem                      → Tìm kiếm
  /gioi-thieu                    → Giới thiệu
  /lien-he                       → Liên hệ
  /dieu-khoan                    → Điều khoản
  /chinh-sach-bao-mat            → Chính sách bảo mật
"""

from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from core.models import Video
from resources.models import Resource
from news.models import Article as NewsArticle
from knowledge.models import KnowledgeArticle
from tools.models import Tool
from mediastream.models import StreamMedia


class StaticViewSitemap(Sitemap):
    """Sitemap cho các trang tĩnh"""
    changefreq = 'weekly'

    def items(self):
        return [
            ('/', 1.0),            # Trang chủ
            ('/tin-tuc', 0.9),
            ('/kien-thuc', 0.9),
            ('/cong-cu', 0.9),
            ('/tai-lieu', 0.8),
            ('/video', 0.8),
            ('/stream', 0.8),
            ('/tim-kiem', 0.5),
            ('/gioi-thieu', 0.6),
            ('/lien-he', 0.5),
            ('/dieu-khoan', 0.3),
            ('/chinh-sach-bao-mat', 0.3),
        ]

    def location(self, item):
        return item[0]

    def priority(self, item):
        return item[1]


class VideoSitemap(Sitemap):
    """Sitemap cho Videos"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Video.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/video/{obj.slug}'


class ResourceSitemap(Sitemap):
    """Sitemap cho Resources (Tài liệu)"""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Resource.objects.filter(is_active=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/tai-lieu/{obj.slug}'


class NewsSitemap(Sitemap):
    """Sitemap cho News Articles (Tin tức)"""
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return (
            NewsArticle.objects
            .filter(is_published=True)
            .select_related('category')
            .order_by('-updated_at')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        category_slug = obj.category.slug if obj.category else 'chung'
        return f'/tin-tuc/{category_slug}/{obj.slug}'


class KnowledgeSitemap(Sitemap):
    """Sitemap cho Knowledge Articles (Kiến thức)"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return (
            KnowledgeArticle.objects
            .filter(is_published=True)
            .select_related('category')
            .order_by('-updated_at')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        category_slug = obj.category.slug if obj.category else 'chung'
        return f'/kien-thuc/{category_slug}/{obj.slug}'


class ToolsSitemap(Sitemap):
    """Sitemap cho Tools (Công cụ học tập)"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return (
            Tool.objects
            .filter(is_published=True, is_active=True)
            .select_related('category')
            .order_by('-updated_at')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        category_slug = obj.category.slug if obj.category else 'chung'
        return f'/cong-cu/{category_slug}/{obj.slug}'


class StreamSitemap(Sitemap):
    """Sitemap cho Stream Media (Video/Audio streaming)"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return (
            StreamMedia.objects
            .filter(is_active=True, is_public=True)
            .order_by('-updated_at')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/stream/{obj.uid}'


# Tất cả sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'videos': VideoSitemap,
    'resources': ResourceSitemap,
    'news': NewsSitemap,
    'knowledge': KnowledgeSitemap,
    'tools': ToolsSitemap,
    'stream': StreamSitemap,
}


def robots_txt(request):
    """
    Generate robots.txt tối ưu cho SEO.

    Nguyên tắc:
    - Allow tất cả trang public (nội dung, media)
    - Block trang private (admin, auth, profile, API)
    - Chỉ rõ Sitemap location
    - Crawl-delay hợp lý để không gây tải server
    """
    lines = [
        "# ============================================",
        "# UnstressVN - robots.txt",
        "# Public educational content: allow crawl",
        "# Sensitive/system routes: disallow crawl",
        "# ============================================",
        "",
        "User-agent: *",
        "",
        "# === ALLOW: Public content pages ===",
        "Allow: /",
        "Allow: /tin-tuc/",
        "Allow: /kien-thuc/",
        "Allow: /cong-cu/",
        "Allow: /tai-lieu/",
        "Allow: /video/",
        "Allow: /stream/",
        "Allow: /gioi-thieu",
        "Allow: /lien-he",
        "Allow: /dieu-khoan",
        "Allow: /chinh-sach-bao-mat",
        "",
        "# === ALLOW: Static and media assets ===",
        "Allow: /static/",
        "Allow: /media/",
        "Allow: /favicon.ico",
        "",
        "# === ALLOW: Public read-only APIs (SPA render/index support) ===",
        "Allow: /api/v1/navigation/",
        "Allow: /api/v1/news/",
        "Allow: /api/v1/knowledge/",
        "Allow: /api/v1/resources/",
        "Allow: /api/v1/tools/",
        "Allow: /api/v1/choices/",
        "Allow: /api/v1/stats/",
        "Allow: /api/v1/schema/",
        "",
        "# === DISALLOW: Sensitive/system routes ===",
        "Disallow: /api/v1/",
        "Disallow: /admin/",
        "Disallow: /admin-gateway/",
        "Disallow: /api/v1/auth/",
        "Disallow: /api/v1/admin-access/",
        "Disallow: /api/v1/n8n/",
        "Disallow: /accounts/",
        "Disallow: /media-stream/",
        "Disallow: /media-stream/admin/",
        "",
        "# === DISALLOW: Non-content user/private pages ===",
        "Disallow: /dang-nhap",
        "Disallow: /dang-ky",
        "Disallow: /ho-so/",
        "Disallow: /cai-dat",
        "Disallow: /doi-mat-khau",
        "Disallow: /thong-bao",
        "Disallow: /tim-kiem",
        "",
        "# === Optional crawl pacing for non-Google bots ===",
        "Crawl-delay: 1",
        "",
        "# === Sitemaps ===",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

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


# Tất cả sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'videos': VideoSitemap,
    'resources': ResourceSitemap,
    'news': NewsSitemap,
    'knowledge': KnowledgeSitemap,
    'tools': ToolsSitemap,
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
        "# Học tiếng Đức & tiếng Anh miễn phí",
        "# ============================================",
        "",
        "User-agent: *",
        "",
        "# === ALLOW: Nội dung public ===",
        "Allow: /",
        "Allow: /tin-tuc/",
        "Allow: /kien-thuc/",
        "Allow: /cong-cu/",
        "Allow: /tai-lieu/",
        "Allow: /video/",
        "Allow: /gioi-thieu",
        "Allow: /lien-he",
        "Allow: /tim-kiem",
        "Allow: /dieu-khoan",
        "Allow: /chinh-sach-bao-mat",
        "",
        "# === ALLOW: Media files (ảnh bìa, logo) ===",
        "Allow: /media/",
        "",
        "# === DISALLOW: Admin & hệ thống ===",
        "Disallow: /admin/",
        "Disallow: /admin-gateway/",
        "",
        "# === DISALLOW: API (trừ navigation) ===",
        "Disallow: /api/",
        "Allow: /api/v1/navigation/",
        "",
        "# === DISALLOW: Auth & trang cá nhân ===",
        "Disallow: /dang-nhap",
        "Disallow: /dang-ky",
        "Disallow: /ho-so/",
        "Disallow: /cai-dat",
        "Disallow: /doi-mat-khau",
        "Disallow: /thong-bao",
        "Disallow: /accounts/",
        "",
        "# === DISALLOW: Media streaming (protected) ===",
        "Disallow: /media-stream/",
        "",
        "# === Crawl delay ===",
        "Crawl-delay: 1",
        "",
        "# === Sitemap ===",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

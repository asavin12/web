"""
Custom Middleware cho UnstressVN
"""
import os
import hmac
import hashlib
import time
from django.conf import settings
from django.utils import translation
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse


class PublicMediaMiddleware:
    """
    Strip security headers từ /media/ responses để media files public và SEO-friendly.
    
    Phải đặt ĐẦU TIÊN trong MIDDLEWARE list để xử lý response CUỐI CÙNG,
    sau khi tất cả middleware khác đã thêm headers.
    
    Giải quyết các vấn đề:
    - X-Frame-Options: DENY → chặn OG image / social media embed
    - Set-Cookie → Cloudflare không cache (cf-cache-status: BYPASS)
    - Cross-Origin-Opener-Policy → chặn cross-origin access
    - Vary: Accept-Language → cache fragmentation
    - Content-Language → không cần cho media files
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Chỉ xử lý cho /media/ path và response thành công
        if not request.path.startswith('/media/') or response.status_code != 200:
            return response

        # Xóa security headers không phù hợp cho public media
        headers_to_remove = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Content-Security-Policy',
            'Cross-Origin-Opener-Policy',
            'Cross-Origin-Embedder-Policy',
            'Cross-Origin-Resource-Policy',
            'Content-Disposition',
            'Content-Language',
            'Referrer-Policy',
            'Vary',
            'Set-Cookie',
        ]
        for header in headers_to_remove:
            if header in response:
                del response[header]

        # Xóa cookies (Django tự thêm Set-Cookie từ response.cookies)
        response.cookies.clear()

        # Thêm headers cho public caching và CDN
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
        response['Access-Control-Allow-Origin'] = '*'

        return response


class Custom404Middleware:
    """
    Middleware để hiển thị trang 404 custom cho toàn bộ website.
    Hoạt động cả khi DEBUG=True.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Nếu response là 404, render template 404.html
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        
        return response


class AdminVietnameseMiddleware:
    """
    Middleware để force tiếng Việt cho trang admin.
    Admin panel chỉ cần một ngôn ngữ duy nhất.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Force tiếng Việt cho admin
        if request.path.startswith('/admin'):
            translation.activate('vi')
            request.LANGUAGE_CODE = 'vi'
        
        return self.get_response(request)


class AdminAccessMiddleware:
    """
    Middleware bảo mật cao cho trang admin.
    
    Yêu cầu:
    1. User phải đăng nhập
    2. User phải có is_superuser=True (không chỉ is_staff)
    3. Phải có admin_verified session token hợp lệ
    4. Token phải chưa hết hạn (30 phút)
    
    Để truy cập admin, user phải:
    - Đăng nhập vào SPA với tài khoản superuser
    - Truy cập /admin-gateway/?key=<ADMIN_SECRET_KEY>
    - Sau đó mới được redirect vào /admin/
    """
    
    ADMIN_SESSION_KEY = 'admin_verified'
    ADMIN_SESSION_TIMESTAMP = 'admin_verified_at'
    ADMIN_SESSION_TIMEOUT = 30 * 60  # 30 phút
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Bỏ qua admin gateway path
        if request.path == '/admin-gateway/':
            return self.get_response(request)
        
        # ẨN HOÀN TOÀN trang admin login - không cần thiết vì xác thực qua gateway
        # Trả về 404 cho cả /admin/login/ và /admin/logout/
        if request.path in ['/admin/login/', '/admin/logout/']:
            return render(request, '404.html', status=404)
        
        # Trong DEBUG mode, chỉ yêu cầu is_staff (bỏ qua session verification)
        if settings.DEBUG:
            if request.path.startswith('/admin/'):
                # Các trang admin cần đăng nhập
                if not request.user.is_authenticated:
                    # Redirect về trang chủ SPA để đăng nhập
                    return redirect('/?admin_required=true')
                if not request.user.is_staff:
                    return render(request, '404.html', status=404)
            return self.get_response(request)
        
        # Production mode: yêu cầu bảo mật cao
        # Kiểm tra nếu đường dẫn bắt đầu với /admin/
        if request.path.startswith('/admin/'):
            # Điều kiện 1: User phải đăng nhập VÀ là superuser
            if not request.user.is_authenticated:
                return render(request, '404.html', status=404)
            
            if not request.user.is_superuser:
                return render(request, '404.html', status=404)
            
            # Điều kiện 2: Phải có session admin_verified
            admin_verified = request.session.get(self.ADMIN_SESSION_KEY)
            admin_timestamp = request.session.get(self.ADMIN_SESSION_TIMESTAMP, 0)
            
            if not admin_verified:
                return render(request, '404.html', status=404)
            
            # Điều kiện 3: Token chưa hết hạn
            current_time = time.time()
            if current_time - admin_timestamp > self.ADMIN_SESSION_TIMEOUT:
                # Xóa session đã hết hạn
                request.session.pop(self.ADMIN_SESSION_KEY, None)
                request.session.pop(self.ADMIN_SESSION_TIMESTAMP, None)
                return render(request, '404.html', status=404)
            
            # Điều kiện 4: Verify token integrity
            expected_token = self._generate_token(request.user)
            if not hmac.compare_digest(admin_verified, expected_token):
                # Token không hợp lệ - có thể bị giả mạo
                request.session.pop(self.ADMIN_SESSION_KEY, None)
                request.session.pop(self.ADMIN_SESSION_TIMESTAMP, None)
                return render(request, '404.html', status=404)
        
        return self.get_response(request)
    
    @staticmethod
    def _generate_token(user):
        """Tạo token dựa trên user info và secret key"""
        from core.models import APIKey
        try:
            # Lấy key từ database
            secret = APIKey.get_key('admin_secret_key')
            if not secret:
                return ''  # Return empty — token comparison will fail safely
            data = f"{user.id}:{user.username}:{user.is_superuser}"
            return hmac.new(
                secret.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
        except Exception:
            return ''  # DB error — fail closed (deny access)
    
    @classmethod
    def verify_and_set_session(cls, request, secret_key):
        """
        Verify secret key và set session cho admin access.
        Trả về True nếu thành công, False nếu thất bại.
        """
        from core.models import APIKey
        
        # Lấy expected key từ database
        expected_key = APIKey.get_key('admin_secret_key')
        
        if not expected_key:
            return False
        
        # Constant-time comparison để tránh timing attack
        if not hmac.compare_digest(secret_key, expected_key):
            return False
        
        # User phải là superuser
        if not request.user.is_authenticated or not request.user.is_superuser:
            return False
        
        # Set session
        request.session[cls.ADMIN_SESSION_KEY] = cls._generate_token(request.user)
        request.session[cls.ADMIN_SESSION_TIMESTAMP] = time.time()
        
        return True


class ForceDefaultLanguageMiddleware:
    """
    Middleware để tự động nhận diện ngôn ngữ từ trình duyệt
    Nếu ngôn ngữ không được hỗ trợ (vi, en, de) thì mặc định là tiếng Anh
    """
    
    SUPPORTED_LANGUAGES = ['vi', 'en', 'de']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Kiểm tra cookie language
        language_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        
        # Chỉ set cookie nếu chưa có
        if not language_cookie and '/i18n/setlang/' not in request.path:
            # Lấy ngôn ngữ từ header Accept-Language của trình duyệt
            browser_lang = self._get_browser_language(request)
            
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                browser_lang,
                max_age=365 * 24 * 60 * 60,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
        
        return response
    
    def _get_browser_language(self, request):
        """
        Phân tích header Accept-Language và trả về ngôn ngữ phù hợp
        Ví dụ: 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6'
        """
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        
        if not accept_language:
            return 'en'  # Mặc định tiếng Anh
        
        # Parse Accept-Language header
        languages = []
        for lang_part in accept_language.split(','):
            parts = lang_part.strip().split(';')
            lang_code = parts[0].split('-')[0].lower()  # Lấy 'vi' từ 'vi-VN'
            
            # Lấy quality value (mặc định là 1.0)
            q = 1.0
            if len(parts) > 1:
                try:
                    q = float(parts[1].split('=')[1])
                except (IndexError, ValueError):
                    q = 1.0
            
            languages.append((lang_code, q))
        
        # Sắp xếp theo priority (q value cao nhất trước)
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Tìm ngôn ngữ được hỗ trợ đầu tiên
        for lang_code, _ in languages:
            if lang_code in self.SUPPORTED_LANGUAGES:
                return lang_code
        
        # Không tìm thấy ngôn ngữ hỗ trợ -> mặc định tiếng Anh
        return 'en'

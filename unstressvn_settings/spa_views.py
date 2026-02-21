"""
Views để serve React SPA frontend
Hỗ trợ cả Development (Vite) và Production (built files)
"""

from pathlib import Path
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.http import require_GET
from django.contrib.auth import login
from rest_framework.authtoken.models import Token

from .middleware import AdminAccessMiddleware


@require_GET
def admin_gateway(request):
    """
    Admin Gateway - Cổng bảo mật vào admin panel.
    
    Để truy cập admin:
    1. Truy cập: /admin-gateway/?key=<ADMIN_SECRET_KEY>&token=<AUTH_TOKEN>
    2. Nếu key và token hợp lệ → login user vào Django session và redirect /admin/
    3. Nếu không → trả về 404
    
    ADMIN_SECRET_KEY được lưu trong database (APIKey model)
    Chỉ superuser mới có thể sử dụng gateway này.
    """
    from core.models import APIKey
    
    secret_key = request.GET.get('key', '')
    auth_token = request.GET.get('token', '')
    
    if not secret_key or not auth_token:
        return render(request, '404.html', status=404)
    
    # Verify secret key - lấy từ database
    expected_key = APIKey.get_key('admin_secret_key')
    if not expected_key or secret_key != expected_key:
        return render(request, '404.html', status=404)
    
    # Verify token và lấy user
    try:
        token_obj = Token.objects.select_related('user').get(key=auth_token)
        user = token_obj.user
    except Token.DoesNotExist:
        return render(request, '404.html', status=404)
    
    # Chỉ superuser mới được truy cập
    if not user.is_superuser:
        return render(request, '404.html', status=404)
    
    # Login user vào Django session
    login(request, user)
    
    # Set admin session token
    AdminAccessMiddleware.verify_and_set_session(request, secret_key)
    
    return redirect('/admin/')


def spa_view(request, path=''):
    """
    Serve React SPA.
    
    Development mode (DEBUG=True):
        - Render template với Vite dev server scripts
        
    Production mode (DEBUG=False):
        - Serve built static files từ frontend/dist
    """
    
    if settings.DEBUG:
        # Development: Render template với Vite dev server
        return render(request, 'spa.html', {'debug': True})
    
    # Production: Serve built files
    frontend_dir = getattr(settings, 'FRONTEND_DIR', None)
    
    if not frontend_dir:
        frontend_dir = Path(settings.BASE_DIR) / 'frontend' / 'dist'
    else:
        frontend_dir = Path(frontend_dir)
    
    # Nếu request là cho static asset (js, css, images)
    if path and '.' in path.split('/')[-1]:
        asset_path = frontend_dir / 'assets' / path.split('/')[-1]
        if not asset_path.exists():
            asset_path = frontend_dir / path
        
        if asset_path.exists():
            content_type = get_content_type(path)
            with open(asset_path, 'rb') as f:
                return HttpResponse(f.read(), content_type=content_type)
        return HttpResponseNotFound('Asset not found')
    
    # Serve index.html cho tất cả các routes (SPA routing)
    index_path = frontend_dir / 'index.html'
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    
    # Fallback to template
    return render(request, 'spa.html', {'debug': False})


def get_content_type(path: str) -> str:
    """Xác định content type dựa trên extension"""
    extension = path.split('.')[-1].lower()
    content_types = {
        'js': 'application/javascript',
        'mjs': 'application/javascript',
        'css': 'text/css',
        'html': 'text/html',
        'json': 'application/json',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'svg': 'image/svg+xml',
        'ico': 'image/x-icon',
        'woff': 'font/woff',
        'woff2': 'font/woff2',
        'ttf': 'font/ttf',
        'eot': 'application/vnd.ms-fontobject',
        'map': 'application/json',
    }
    return content_types.get(extension, 'application/octet-stream')

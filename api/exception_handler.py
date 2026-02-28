"""
Global DRF Exception Handler — trả JSON thay vì HTML 500 cho mọi lỗi.
Đặc biệt quan trọng cho n8n vì n8n không parse được HTML error pages.
"""
import logging
import traceback

from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('n8n_api')


def custom_exception_handler(exc, context):
    """
    Custom exception handler:
    1. Gọi DRF default handler trước (xử lý 400, 401, 403, 404, 405, etc.)
    2. Nếu DRF default trả None → exception chưa được xử lý → trả JSON 500
    """
    # DRF default handler (handles APIException subclasses)
    response = drf_default_handler(exc, context)
    
    if response is not None:
        # DRF đã xử lý — đảm bảo format thống nhất
        response.data = {
            'success': False,
            'error': response.data.get('detail', str(response.data)) if isinstance(response.data, dict) else str(response.data),
            'status_code': response.status_code,
        }
        return response
    
    # Unhandled exception — log and return JSON 500
    view = context.get('view', None)
    view_name = getattr(view, '__name__', str(view)) if view else 'unknown'
    request = context.get('request', None)
    path = getattr(request, 'path', 'unknown') if request else 'unknown'
    method = getattr(request, 'method', 'unknown') if request else 'unknown'
    
    logger.error(
        f'Unhandled exception in {method} {path} ({view_name}): '
        f'{type(exc).__name__}: {exc}',
        exc_info=True
    )
    
    return Response({
        'success': False,
        'error': f'{type(exc).__name__}: {str(exc)[:1000]}',
        'hint': 'Lỗi hệ thống không mong muốn. Kiểm tra dữ liệu gửi và thử lại.',
        'view': view_name,
        'path': path,
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

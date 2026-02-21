"""
Mã hoá dữ liệu nhạy cảm trong database.
Sử dụng Fernet (AES-128-CBC + HMAC-SHA256) với key derived từ SECRET_KEY.

Nếu database bị đánh cắp, kẻ tấn công KHÔNG thể đọc dữ liệu nhạy cảm
vì encryption key nằm trong file .secret_key (không ở trong database).
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)

# Salt cố định cho key derivation — KHÔNG THAY ĐỔI
_KEY_SALT = b'unstressvn-encrypted-field-v1'


def _get_fernet():
    """Tạo Fernet instance từ SECRET_KEY."""
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        settings.SECRET_KEY.encode('utf-8'),
        _KEY_SALT,
        iterations=100_000,
        dklen=32,
    )
    return Fernet(base64.urlsafe_b64encode(dk))


def encrypt_value(plaintext: str) -> str:
    """Mã hoá chuỗi → ciphertext base64."""
    if not plaintext:
        return ''
    return _get_fernet().encrypt(plaintext.encode('utf-8')).decode('ascii')


def decrypt_value(ciphertext: str) -> str:
    """Giải mã ciphertext → chuỗi gốc."""
    if not ciphertext:
        return ''
    try:
        return _get_fernet().decrypt(ciphertext.encode('ascii')).decode('utf-8')
    except (InvalidToken, Exception) as exc:
        logger.warning(
            'Không thể giải mã giá trị — SECRET_KEY có thể đã thay đổi: %s', exc
        )
        return ''

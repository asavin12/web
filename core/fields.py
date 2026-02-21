"""
Custom Django model fields với mã hoá tự động.
Dữ liệu được mã hoá Fernet trước khi lưu vào database,
tự động giải mã khi đọc. Admin thấy plaintext, DB chứa ciphertext.
"""

from django.db import models


class EncryptedTextField(models.TextField):
    """
    TextField lưu dữ liệu dạng mã hoá (Fernet) trong database.
    Tự động mã hoá khi lưu, giải mã khi đọc.

    Trong database: gAAAA...base64 ciphertext
    Trong Python/Admin: plaintext
    """

    def get_prep_value(self, value):
        """Mã hoá trước khi lưu vào DB."""
        from .encryption import encrypt_value

        value = super().get_prep_value(value)
        if value:
            return encrypt_value(str(value))
        return value

    def from_db_value(self, value, expression, connection):
        """Giải mã khi đọc từ DB."""
        from .encryption import decrypt_value

        if value:
            return decrypt_value(value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'core.fields.EncryptedTextField', args, kwargs

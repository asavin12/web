from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import signals để register
        import core.signals  # noqa: F401

        # Tải cấu hình từ database → áp dụng vào Django settings
        # Nếu bảng chưa tồn tại (chưa migrate), bỏ qua.
        try:
            from core.config import apply_dynamic_settings
            apply_dynamic_settings()
        except Exception:
            pass

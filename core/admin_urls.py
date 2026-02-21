"""
Custom Admin URLs cho UnstressVN
Bao gồm PostgreSQL Dashboard và các tools khác
"""

from django.urls import path
from core import postgres_admin

# KHÔNG dùng app_name để tránh conflict với Django admin
# Các URLs này sẽ được mount vào /admin/
urlpatterns = [
    # PostgreSQL Dashboard
    path('postgres/', postgres_admin.postgres_dashboard, name='postgres_dashboard'),
    path('postgres/tables/', postgres_admin.postgres_tables, name='postgres_tables'),
    path('postgres/tables/<str:table_name>/', postgres_admin.postgres_table_schema, name='postgres_table_schema'),
    path('postgres/export-schema/', postgres_admin.export_schema, name='postgres_export_schema'),
    path('postgres/test-connection/', postgres_admin.test_connection, name='postgres_test_connection'),
    path('postgres/generate-password/', postgres_admin.generate_password, name='postgres_generate_password'),
    path('postgres/backup/', postgres_admin.backup_database, name='postgres_backup'),
    path('postgres/backup/delete/', postgres_admin.delete_backup, name='postgres_delete_backup'),
    path('postgres/restore/', postgres_admin.restore_database, name='postgres_restore'),
]

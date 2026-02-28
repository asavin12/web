"""
URL patterns for File Manager
"""

from django.urls import path
from . import views

app_name = 'filemanager'

urlpatterns = [
    path('browse/', views.file_browser, name='file_browser'),
    path('upload/', views.upload_file, name='upload_file'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('delete/', views.delete_item, name='delete_item'),
    path('rename/', views.rename_item, name='rename_item'),
    path('disk-usage/', views.disk_usage, name='disk_usage'),
    path('unused-media/', views.unused_media, name='unused_media'),
]

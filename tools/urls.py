"""
URLs cho Tools App
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tools'

router = DefaultRouter()
router.register(r'categories', views.ToolCategoryViewSet, basename='tool-category')
router.register(r'tools', views.ToolViewSet, basename='tool')
router.register(r'flashcard-decks', views.FlashcardDeckViewSet, basename='flashcard-deck')

urlpatterns = [
    path('', include(router.urls)),
]

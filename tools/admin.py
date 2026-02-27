from django.contrib import admin
from .models import ToolCategory, Tool, FlashcardDeck, Flashcard  # Flashcard used by FlashcardInline


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'tool_type', 'language', 'is_featured', 'is_active', 'view_count']
    list_filter = ['category', 'tool_type', 'language', 'is_featured', 'is_active']
    list_editable = ['is_featured', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    ordering = ['-is_featured', 'order', '-created_at']


class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 1
    fields = ['front', 'back', 'example', 'pronunciation', 'order']


@admin.register(FlashcardDeck)
class FlashcardDeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'level', 'author', 'card_count', 'is_public', 'is_featured', 'view_count']
    list_filter = ['language', 'level', 'is_public', 'is_featured']
    list_editable = ['is_public', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    inlines = [FlashcardInline]
    
    def card_count(self, obj):
        return obj.card_count
    card_count.short_description = 'Số thẻ'

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, KnowledgeArticle


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'article_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'language', 'level', 'schema_type',
                    'is_published', 'is_featured', 'view_count')
    list_filter = ('category', 'language', 'level', 'schema_type', 'is_published', 'is_featured')
    search_fields = ('title', 'content', 'excerpt')
    list_editable = ('is_published', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('view_count', 'created_at', 'updated_at', 'cover_preview')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Phân loại học tập', {
            'fields': ('category', 'language', 'level', 'author')
        }),
        ('Hình ảnh', {
            'fields': ('cover_image', 'cover_preview', 'thumbnail')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url'),
            'classes': ('collapse',)
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image'),
            'classes': ('collapse',)
        }),
        ('Structured Data', {
            'fields': ('schema_type',),
            'description': '💡 Chọn loại schema phù hợp để cải thiện hiển thị trên Google'
        }),
        ('Trạng thái', {
            'fields': ('is_published', 'is_featured', 'published_at')
        }),
        ('Thống kê', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px; border-radius: 8px;" />',
                obj.cover_image.url
            )
        return '-'
    cover_preview.short_description = 'Xem trước ảnh bìa'
    
    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

"""
Admin cho ứng dụng Resources
Quản lý kho tài liệu trong Django Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.contrib import messages
from .models import Category, Resource, Tag, RESOURCE_TYPE_CHOICES


class BulkTagForm(forms.Form):
    """Form để thêm hàng loạt thẻ tag"""
    tags_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 15,
            'cols': 60,
            'placeholder': 'Nhập mỗi thẻ tag trên một dòng, ví dụ:\nNgữ pháp\nTừ vựng\nIELTS\nA1\nB2\nHeißt\nÜbung',
            'style': 'font-family: monospace; font-size: 14px;'
        }),
        label='Danh sách thẻ tag',
        help_text='Mỗi thẻ tag trên một dòng. Đường dẫn sẽ tự động được tạo.'
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Admin cho Thẻ tag
    """
    list_display = ('name', 'slug', 'resource_count')
    search_fields = ('name',)
    readonly_fields = ('slug',)
    change_list_template = 'admin/resources/tag/change_list.html'
    
    def resource_count(self, obj):
        """Đếm số tài liệu sử dụng tag này"""
        count = obj.resources.count()
        return count
    resource_count.short_description = 'Số tài liệu'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-add/', self.admin_site.admin_view(self.bulk_add_view), name='resources_tag_bulk_add'),
        ]
        return custom_urls + urls
    
    def bulk_add_view(self, request):
        """View để thêm hàng loạt thẻ tag"""
        if request.method == 'POST':
            form = BulkTagForm(request.POST)
            if form.is_valid():
                tags_text = form.cleaned_data['tags_text']
                lines = [line.strip() for line in tags_text.split('\n') if line.strip()]
                
                created_count = 0
                skipped_count = 0
                skipped_tags = []
                
                for tag_name in lines:
                    # Kiểm tra tag đã tồn tại chưa
                    if not Tag.objects.filter(name__iexact=tag_name).exists():
                        Tag.objects.create(name=tag_name)
                        created_count += 1
                    else:
                        skipped_count += 1
                        skipped_tags.append(tag_name)
                
                if created_count > 0:
                    messages.success(request, f'✅ Đã tạo thành công {created_count} thẻ tag mới!')
                if skipped_count > 0:
                    messages.warning(request, f'⚠️ Bỏ qua {skipped_count} thẻ đã tồn tại: {", ".join(skipped_tags)}')
                
                return redirect('admin:resources_tag_changelist')
        else:
            form = BulkTagForm()
        
        context = {
            'form': form,
            'title': 'Thêm hàng loạt thẻ tag',
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/resources/tag/bulk_add.html', context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin cho Danh mục ngôn ngữ
    """
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """
    Admin cho Tài liệu
    """
    list_display = ('title', 'cover_thumbnail', 'slug', 'category', 'resource_type', 'author', 
                    'is_active', 'is_featured', 'view_count', 'created_at')
    list_filter = ('category', 'resource_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'author', 'tags__name')
    readonly_fields = ('slug', 'cover_preview', 'view_count', 'download_count', 'created_at', 'updated_at')
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'description', 'author'),
            'description': 'Đường dẫn (slug) sẽ tự động tạo từ tên tài liệu'
        }),
        ('Phân loại', {
            'fields': ('category', 'resource_type', 'tags')
        }),
        ('Nội dung', {
            'fields': ('file', 'external_url', 'youtube_url'),
            'description': 'Chọn MỘT trong các cách: Tải file lên / Nhập link tài liệu / Nhập link YouTube'
        }),
        ('Ảnh bìa', {
            'fields': ('cover_image', 'cover_preview'),
        }),
        ('Hiển thị', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Thống kê', {
            'fields': ('view_count', 'download_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_thumbnail(self, obj):
        """Hiển thị ảnh thu nhỏ trong danh sách"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 65px; object-fit: cover; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);" />',
                obj.cover_image.url
            )
        return format_html(
            '<div style="width: 50px; height: 65px; background: #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">No img</div>'
        )
    cover_thumbnail.short_description = 'Ảnh'
    
    def cover_preview(self, obj):
        """Hiển thị ảnh xem trước trong form chỉnh sửa với JS live preview"""
        current_img = ''
        if obj and obj.cover_image:
            current_img = f'<img id="cover-preview-img" src="{obj.cover_image.url}" style="max-width: 200px; max-height: 280px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);" />'
        else:
            current_img = '<div id="cover-preview-img" style="width: 150px; height: 200px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; border: 2px dashed #ddd;">Chưa có ảnh</div>'
        
        # JavaScript để xem trước ảnh ngay khi chọn file
        js_script = '''
        <script>
        (function() {
            function setupPreview() {
                var fileInput = document.getElementById('id_cover_image');
                if (!fileInput) return;
                
                fileInput.addEventListener('change', function(e) {
                    var file = e.target.files[0];
                    if (file && file.type.startsWith('image/')) {
                        var reader = new FileReader();
                        reader.onload = function(event) {
                            var container = document.getElementById('cover-preview-img');
                            if (container) {
                                var parent = container.parentNode;
                                var newImg = document.createElement('img');
                                newImg.id = 'cover-preview-img';
                                newImg.src = event.target.result;
                                newImg.style.cssText = 'max-width: 200px; max-height: 280px; object-fit: cover; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);';
                                parent.replaceChild(newImg, container);
                            }
                        };
                        reader.readAsDataURL(file);
                    }
                });
            }
            
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupPreview);
            } else {
                setupPreview();
            }
        })();
        </script>
        '''
        
        return format_html(current_img + js_script)
    cover_preview.short_description = 'Xem trước ảnh bìa'
    
    def save_model(self, request, obj, form, change):
        # Có thể thêm logic xử lý khi lưu
        super().save_model(request, obj, form, change)

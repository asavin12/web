"""
Admin cho ứng dụng Accounts
Quản lý hồ sơ người dùng trong Django Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline để hiển thị UserProfile trong trang User
    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Hồ sơ'
    verbose_name_plural = 'Hồ sơ'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """
    Tùy chỉnh UserAdmin để thêm UserProfile
    """
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 
                    'get_language', 'get_level', 'is_active')
    list_filter = BaseUserAdmin.list_filter + ('profile__target_language', 'profile__level')
    
    def get_language(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_language_display_vi()
        return '-'
    get_language.short_description = 'Ngôn ngữ'
    
    def get_level(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.level
        return '-'
    get_level.short_description = 'Trình độ'


# Đăng ký lại UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin riêng cho UserProfile
    """
    list_display = ('user', 'target_language', 'level', 'skill_focus', 'is_public', 'created_at')
    list_filter = ('target_language', 'level', 'skill_focus', 'is_public')
    search_fields = ('user__username', 'user__email', 'bio')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'avatar', 'bio')
        }),
        ('Học tập', {
            'fields': ('target_language', 'level', 'skill_focus')
        }),
        ('Cài đặt', {
            'fields': ('is_public',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

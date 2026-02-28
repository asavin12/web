"""
Models cho ứng dụng Accounts
Quản lý hồ sơ người dùng mở rộng
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """
    Hồ sơ người dùng mở rộng
    Lưu trữ thông tin bổ sung cho việc học ngôn ngữ
    """
    
    # Lựa chọn ngôn ngữ mục tiêu
    LANGUAGE_CHOICES = [
        ('en', _('Tiếng Anh')),
        ('de', _('Tiếng Đức')),
    ]
    
    # Lựa chọn trình độ (CEFR)
    LEVEL_CHOICES = [
        ('A1', _('A1 - Sơ cấp')),
        ('A2', _('A2 - Sơ cấp')),
        ('B1', _('B1 - Trung cấp')),
        ('B2', _('B2 - Trung cấp')),
        ('C1', _('C1 - Cao cấp')),
        ('C2', _('C2 - Cao cấp')),
    ]
    
    # Lựa chọn kỹ năng tập trung
    SKILL_CHOICES = [
        ('speaking', _('Nói')),
        ('listening', _('Nghe')),
        ('reading', _('Đọc')),
        ('writing', _('Viết')),
        ('grammar', _('Ngữ pháp')),
        ('vocabulary', _('Từ vựng')),
        ('all', _('Tất cả')),
    ]
    
    # Liên kết với User
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name='Tài khoản'
    )
    
    # Ảnh đại diện
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Ảnh đại diện'
    )
    
    # Giới thiệu bản thân
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Giới thiệu'
    )
    
    # Ngôn ngữ mục tiêu
    target_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='en',
        blank=True,
        verbose_name='Ngôn ngữ mục tiêu'
    )
    
    # Trình độ hiện tại
    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default='A1',
        verbose_name='Trình độ'
    )
    
    # Kỹ năng tập trung
    skill_focus = models.CharField(
        max_length=20,
        choices=SKILL_CHOICES,
        default='all',
        verbose_name='Kỹ năng tập trung'
    )
    
    # Cho phép hiển thị trong tìm kiếm
    is_public = models.BooleanField(
        default=True,
        verbose_name='Hiển thị công khai'
    )
    
    # Cho phép nhắn tin
    allow_messages = models.BooleanField(
        default=True,
        verbose_name='Cho phép nhắn tin'
    )
    
    # Thời gian tạo và cập nhật
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        verbose_name = 'Hồ sơ người dùng'
        verbose_name_plural = 'Hồ sơ người dùng'
    
    def __str__(self):
        return f'Hồ sơ của {self.user.username}'
    
    def get_avatar_url(self):
        """Lấy URL ảnh đại diện hoặc ảnh mặc định"""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'
    
    def get_language_display_vi(self):
        """Lấy tên ngôn ngữ tiếng Việt"""
        return dict(self.LANGUAGE_CHOICES).get(self.target_language, '')
    
    def get_level_display_vi(self):
        """Lấy tên trình độ tiếng Việt"""
        return dict(self.LEVEL_CHOICES).get(self.level, '')
    
    def get_skill_display_vi(self):
        """Lấy tên kỹ năng tiếng Việt"""
        return dict(self.SKILL_CHOICES).get(self.skill_focus, '')


# Signal: Tự động tạo UserProfile khi tạo User mới
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Tạo hồ sơ người dùng khi tạo tài khoản mới"""
    if created:
        try:
            UserProfile.objects.get_or_create(user=instance)
        except Exception:
            pass  # Don't crash User save if profile creation fails


# NOTE: Đã xoá signal save_user_profile — gây duplicate save khi dùng
# UserProfile inline trong UserAdmin. Django admin tự save inline formset,
# không cần signal gọi profile.save() lại.


class Notification(models.Model):
    """
    Model thông báo cho người dùng
    """
    # Loại thông báo
    TYPE_CHOICES = [
        ('friend_request', 'Lời mời kết bạn'),
        ('friend_accepted', 'Chấp nhận kết bạn'),
        ('new_message', 'Tin nhắn mới'),
        ('post_reply', 'Trả lời bài viết'),
        ('post_mention', 'Nhắc đến trong bài viết'),
        ('resource_bookmark', 'Tài liệu được lưu'),
        ('system', 'Thông báo hệ thống'),
        ('welcome', 'Chào mừng'),
    ]
    
    # Người nhận thông báo
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Người nhận'
    )
    
    # Người gửi/tạo thông báo (có thể null cho system notifications)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        blank=True,
        null=True,
        verbose_name='Người gửi'
    )
    
    # Loại thông báo
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system',
        verbose_name='Loại thông báo'
    )
    
    # Tiêu đề thông báo
    title = models.CharField(
        max_length=200,
        verbose_name='Tiêu đề'
    )
    
    # Nội dung thông báo
    message = models.TextField(
        verbose_name='Nội dung'
    )
    
    # Link liên quan (optional)
    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Đường dẫn'
    )
    
    # Trạng thái đã đọc
    is_read = models.BooleanField(
        default=False,
        verbose_name='Đã đọc'
    )
    
    # Thời gian tạo
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian'
    )
    
    class Meta:
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} - {self.recipient.username}'
    
    def mark_as_read(self):
        """Đánh dấu đã đọc"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    def get_icon(self):
        """Lấy icon tương ứng với loại thông báo"""
        icons = {
            'friend_request': 'user-plus',
            'friend_accepted': 'user-check',
            'new_message': 'message-circle',
            'post_reply': 'message-square',
            'post_mention': 'at-sign',
            'resource_bookmark': 'bookmark',
            'system': 'bell',
            'welcome': 'sparkles',
        }
        return icons.get(self.notification_type, 'bell')
    
    def get_color(self):
        """Lấy màu tương ứng với loại thông báo"""
        colors = {
            'friend_request': 'text-blue-500',
            'friend_accepted': 'text-green-500',
            'new_message': 'text-purple-500',
            'post_reply': 'text-orange-500',
            'post_mention': 'text-pink-500',
            'resource_bookmark': 'text-yellow-500',
            'system': 'text-gray-500',
            'welcome': 'text-vintage-olive',
        }
        return colors.get(self.notification_type, 'text-gray-500')


# Helper function để tạo thông báo
def create_notification(recipient, notification_type, title, message, sender=None, link=''):
    """
    Hàm tiện ích để tạo thông báo mới
    """
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )


# Signal: Tạo thông báo chào mừng khi user mới đăng ký
@receiver(post_save, sender=User)
def create_welcome_notification(sender, instance, created, **kwargs):
    """Tạo thông báo chào mừng cho user mới"""
    if created:
        try:
            Notification.objects.create(
                recipient=instance,
                notification_type='welcome',
                title='Chào mừng đến với UnstressVN!',
                message=f'Xin chào {instance.username}! Cảm ơn bạn đã tham gia cộng đồng học ngoại ngữ của chúng tôi. Hãy khám phá thư viện tài liệu và tìm kiếm bạn học nhé!',
                link='/'
            )
        except Exception:
            pass  # Don't crash User save if notification creation fails

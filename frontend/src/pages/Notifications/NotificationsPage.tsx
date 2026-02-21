import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useNotifications } from '@/hooks';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingPage } from '@/components/ui/Spinner';
import { SEO } from '@/components/common';
import { 
  Bell, 
  BellOff, 
  Check, 
  CheckCheck,
  Heart,
  MessageSquare,
  UserPlus,
  ChevronLeft,
  Settings
} from 'lucide-react';

export default function NotificationsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { notifications, unreadCount, isLoading, markAsRead, markAllRead } = useNotifications();

  if (isLoading) {
    return <LoadingPage />;
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'friend_request':
        return <UserPlus className="h-5 w-5" />;
      case 'like':
        return <Heart className="h-5 w-5" />;
      case 'comment':
        return <MessageSquare className="h-5 w-5" />;
      default:
        return <Bell className="h-5 w-5" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'friend_request':
        return 'bg-vintage-blue/15 text-vintage-blue';
      case 'like':
        return 'bg-vintage-brown/15 text-vintage-brown';
      case 'comment':
        return 'bg-vintage-olive/15 text-vintage-olive';
      default:
        return 'bg-vintage-cream text-vintage-olive';
    }
  };

  const handleNotificationClick = (notif: typeof notifications[0]) => {
    if (!notif.is_read) {
      markAsRead(notif.id);
    }
    if (notif.url) {
      navigate(notif.url);
    }
  };

  return (
    <>
      <SEO 
        title={t('notifications.pageTitle', 'Thông báo') + ' - UnstressVN'}
        description={t('notifications.pageDescription', 'Xem tất cả thông báo của bạn')}
      />

      <div className="bg-vintage-light min-h-screen">
        <div className="container-responsive section-spacing">
          {/* Header */}
          <header className="mb-6 md:mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 md:gap-3 mb-2">
                  <Bell className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive" />
                  <h1 className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark">
                    {t('notifications.title', 'Thông báo')}
                  </h1>
                  {unreadCount > 0 && (
                    <Badge variant="default" className="ml-2">
                      {unreadCount} {t('notifications.unread', 'chưa đọc')}
                    </Badge>
                  )}
                </div>
                <p className="text-sm md:text-base text-vintage-dark/70 font-serif italic">
                  {t('notifications.subtitle', 'Cập nhật hoạt động mới nhất')}
                </p>
              </div>
              
              <div className="flex flex-wrap gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => navigate(-1)}
                  className="touch-target inline-flex items-center gap-1.5"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>{t('common.back', 'Quay lại')}</span>
                </Button>
                {unreadCount > 0 && (
                  <Button 
                    variant="secondary" 
                    size="sm" 
                    onClick={markAllRead}
                    className="touch-target inline-flex items-center gap-1.5"
                  >
                    <CheckCheck className="h-4 w-4" />
                    <span>{t('notifications.markAllRead', 'Đọc tất cả')}</span>
                  </Button>
                )}
                <Button 
                  asChild 
                  variant="outline" 
                  size="sm" 
                  className="touch-target"
                >
                  <Link to="/cai-dat" className="inline-flex items-center gap-1.5">
                    <Settings className="h-4 w-4" />
                    <span className="hidden sm:inline">{t('nav.settings', 'Cài đặt')}</span>
                  </Link>
                </Button>
              </div>
            </div>
          </header>

          {/* Stats Summary */}
          <div className="grid grid-cols-2 gap-4 mb-6 md:mb-8">
            <Card className="border-vintage-tan/30">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 rounded-full bg-vintage-olive/10">
                  <Bell className="h-5 w-5 text-vintage-olive" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-vintage-dark">{notifications.length}</div>
                  <div className="text-xs text-vintage-tan">{t('notifications.total', 'Tổng thông báo')}</div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-vintage-tan/30">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-3 rounded-full bg-vintage-brown/10">
                  <BellOff className="h-5 w-5 text-vintage-brown" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-vintage-dark">{unreadCount}</div>
                  <div className="text-xs text-vintage-tan">{t('notifications.unread', 'Chưa đọc')}</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Notifications List */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Bell className="h-5 w-5 text-vintage-olive" />
              <h2 className="text-lg md:text-xl font-serif font-bold text-vintage-dark">
                {t('notifications.allNotifications', 'Tất cả thông báo')}
              </h2>
            </div>

            {notifications.length > 0 ? (
              <div className="space-y-3">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    onClick={() => handleNotificationClick(notif)}
                    className="cursor-pointer"
                  >
                    <Card 
                      className={`border-vintage-tan/30 hover:shadow-md transition-all ${
                        !notif.is_read ? 'bg-vintage-olive/5 border-l-4 border-l-vintage-olive' : ''
                      }`}
                    >
                    <CardContent className="p-4 md:p-5">
                      <div className="flex items-start gap-4">
                        {/* Icon or Avatar */}
                        <div className="flex-shrink-0">
                          {notif.sender?.avatar ? (
                            <img 
                              src={notif.sender.avatar} 
                              className="w-12 h-12 rounded-full object-cover border-2 border-vintage-tan/30" 
                              alt={notif.sender.username} 
                            />
                          ) : notif.sender ? (
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-vintage-olive to-vintage-brown flex items-center justify-center text-white font-bold text-lg">
                              {notif.sender.username.charAt(0).toUpperCase()}
                            </div>
                          ) : (
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getNotificationColor(notif.notification_type)}`}>
                              {getNotificationIcon(notif.notification_type)}
                            </div>
                          )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <h3 className={`font-semibold text-vintage-dark ${!notif.is_read ? 'font-bold' : ''}`}>
                              {notif.title}
                            </h3>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              {!notif.is_read && (
                                <span className="w-2.5 h-2.5 rounded-full bg-vintage-olive" title={t('notifications.unread', 'Chưa đọc')} />
                              )}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (!notif.is_read) {
                                    markAsRead(notif.id);
                                  }
                                }}
                                className={`p-1.5 rounded-lg hover:bg-vintage-cream transition ${
                                  notif.is_read ? 'text-vintage-tan' : 'text-vintage-olive'
                                }`}
                                title={notif.is_read ? t('notifications.read', 'Đã đọc') : t('notifications.markAsRead', 'Đánh dấu đã đọc')}
                              >
                                <Check className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                          <p className="text-sm text-vintage-tan line-clamp-2 mb-2">
                            {notif.message}
                          </p>
                          <div className="flex items-center gap-3 text-xs text-vintage-tan/70">
                            <span>{notif.time_ago || notif.created_at}</span>
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                              {t(`notifications.type.${notif.notification_type}`, notif.notification_type)}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  </div>
                ))}
              </div>
            ) : (
              <Card className="border-vintage-tan/30">
                <CardContent className="p-8 md:p-12 text-center">
                  <BellOff className="h-16 w-16 mx-auto mb-4 text-vintage-tan/50" />
                  <h3 className="text-lg font-semibold text-vintage-dark mb-2">
                    {t('notifications.empty', 'Không có thông báo')}
                  </h3>
                  <p className="text-sm text-vintage-tan max-w-md mx-auto">
                    {t('notifications.emptyHint', 'Bạn sẽ nhận thông báo khi có hoạt động mới')}
                  </p>
                </CardContent>
              </Card>
            )}
          </section>
        </div>
      </div>
    </>
  );
}

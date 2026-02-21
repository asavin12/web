import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import Spinner, { LoadingPage } from '@/components/ui/Spinner';
import { 
  ArrowLeft,
  Globe,
  Bell,
  Shield,
  Key,
  LogOut,
  Trash2,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user, profile, logout, updateProfile, isLoading } = useAuth();
  
  const [settings, setSettings] = useState({
    // Privacy
    is_public: true,
    show_online_status: true,
    allow_messages: true,
    // Notifications
    email_notifications: true,
    push_notifications: true,
    friend_request_notifications: true,
    message_notifications: true,
    // Appearance
    theme: 'light',
    language: i18n.language,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (profile) {
      setSettings((prev) => ({
        ...prev,
        is_public: profile.is_public ?? true,
        show_online_status: profile.show_online_status ?? true,
        allow_messages: profile.allow_messages ?? true,
        email_notifications: profile.email_notifications ?? true,
        push_notifications: profile.push_notifications ?? true,
        friend_request_notifications: profile.friend_request_notifications ?? true,
        message_notifications: profile.message_notifications ?? true,
      }));
    }
  }, [profile]);

  const handleToggle = (name: string) => {
    setSettings((prev) => ({
      ...prev,
      [name]: !prev[name as keyof typeof prev],
    }));
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLang = e.target.value;
    setSettings((prev) => ({ ...prev, language: newLang }));
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  const handleThemeChange = (theme: string) => {
    setSettings((prev) => ({ ...prev, theme }));
    // TODO: Implement theme switching
    localStorage.setItem('theme', theme);
  };

  const handleSaveSettings = async () => {
    setIsSubmitting(true);
    try {
      const profileData = new FormData();
      profileData.append('is_public', String(settings.is_public));
      profileData.append('show_online_status', String(settings.show_online_status));
      profileData.append('allow_messages', String(settings.allow_messages));
      profileData.append('email_notifications', String(settings.email_notifications));
      profileData.append('push_notifications', String(settings.push_notifications));
      
      await updateProfile(profileData);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (isLoading) {
    return <LoadingPage />;
  }

  if (!user) {
    return null;
  }

  const languageOptions = [
    { value: 'vi', label: `🇻🇳 ${t('nativeLanguages.vi', 'Tiếng Việt')}` },
    { value: 'en', label: `🇬🇧 ${t('nativeLanguages.en', 'English')}` },
    { value: 'de', label: `🇩🇪 ${t('nativeLanguages.de', 'Deutsch')}` },
  ];

  return (
    <div className="bg-vintage-light min-h-screen">
      <div className="container-responsive section-spacing">
        {/* Header */}
        <div className="mb-8">
          <Link 
            to="/ho-so" 
            className="inline-flex items-center gap-2 text-vintage-brown hover:text-vintage-olive mb-4 font-medium"
          >
            <ArrowLeft className="h-4 w-4" />
            {t('settings.backToProfile')}
          </Link>
          <h1 className="text-3xl font-serif font-bold text-vintage-dark">
            {t('settings.title')}
          </h1>
          <p className="text-vintage-dark/60 mt-2 italic font-serif">
            {t('settings.subtitle')}
          </p>
        </div>
        
        <div className="space-y-6">
          {/* Language & Appearance */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-vintage-olive" />
                {t('settings.languageAndAppearance')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Language */}
              <div>
                <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-2">
                  {t('settings.language')}
                </label>
                <Select
                  value={settings.language}
                  onChange={handleLanguageChange}
                  options={languageOptions}
                />
              </div>
              
              {/* Theme */}
              <div>
                <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-3">
                  {t('settings.theme')}
                </label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => handleThemeChange('light')}
                    className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition ${
                      settings.theme === 'light'
                        ? 'border-vintage-olive bg-vintage-cream'
                        : 'border-vintage-tan/30 hover:border-vintage-tan'
                    }`}
                  >
                    <Sun className="h-5 w-5" />
                    <span className="font-medium">{t('settings.lightTheme')}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleThemeChange('dark')}
                    className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition ${
                      settings.theme === 'dark'
                        ? 'border-vintage-olive bg-vintage-cream'
                        : 'border-vintage-tan/30 hover:border-vintage-tan'
                    }`}
                  >
                    <Moon className="h-5 w-5" />
                    <span className="font-medium">{t('settings.darkTheme')}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleThemeChange('system')}
                    className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition ${
                      settings.theme === 'system'
                        ? 'border-vintage-olive bg-vintage-cream'
                        : 'border-vintage-tan/30 hover:border-vintage-tan'
                    }`}
                  >
                    <Monitor className="h-5 w-5" />
                    <span className="font-medium">{t('settings.systemTheme')}</span>
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Privacy Settings */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-vintage-olive" />
                {t('settings.privacy')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.publicProfile')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('profile.publicProfileDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('is_public')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.is_public ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.is_public ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
              
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.showOnlineStatus')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('profile.showOnlineStatusDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('show_online_status')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.show_online_status ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.show_online_status ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
              
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.allowMessages')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('profile.allowMessagesDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('allow_messages')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.allow_messages ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.allow_messages ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
            </CardContent>
          </Card>
          
          {/* Notifications */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-vintage-olive" />
                {t('settings.notifications')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('settings.emailNotifications')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('settings.emailNotificationsDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('email_notifications')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.email_notifications ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.email_notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
              
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('settings.friendRequestNotifications')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('settings.friendRequestNotificationsDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('friend_request_notifications')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.friend_request_notifications ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.friend_request_notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
              
              <label className="flex items-center justify-between cursor-pointer p-3 rounded-lg hover:bg-vintage-cream/50 transition">
                <div>
                  <span className="font-bold text-vintage-dark">{t('settings.messageNotifications')}</span>
                  <p className="text-sm text-vintage-dark/60">{t('settings.messageNotificationsDesc')}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleToggle('message_notifications')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.message_notifications ? 'bg-vintage-olive' : 'bg-vintage-tan/40'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                      settings.message_notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </label>
            </CardContent>
          </Card>
          
          {/* Account Actions */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5 text-vintage-olive" />
                {t('settings.account')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Link 
                to="/doi-mat-khau"
                className="flex items-center justify-between p-4 rounded-lg border border-vintage-tan/30 hover:border-vintage-brown hover:bg-vintage-cream/50 transition"
              >
                <div className="flex items-center gap-3">
                  <Key className="h-5 w-5 text-vintage-brown" />
                  <div>
                    <span className="font-bold text-vintage-dark">{t('settings.changePassword')}</span>
                    <p className="text-sm text-vintage-dark/60">{t('settings.changePasswordDesc')}</p>
                  </div>
                </div>
                <ArrowLeft className="h-5 w-5 text-vintage-tan rotate-180" />
              </Link>
              
              <button 
                type="button"
                onClick={handleLogout}
                className="w-full flex items-center justify-between p-4 rounded-lg border border-vintage-tan/30 hover:border-vintage-brown hover:bg-vintage-cream/50 transition"
              >
                <div className="flex items-center gap-3">
                  <LogOut className="h-5 w-5 text-vintage-brown" />
                  <div className="text-left">
                    <span className="font-bold text-vintage-dark">{t('settings.logout')}</span>
                    <p className="text-sm text-vintage-dark/60">{t('settings.logoutDesc')}</p>
                  </div>
                </div>
              </button>
              
              <button 
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full flex items-center justify-between p-4 rounded-lg border border-vintage-brown/30 hover:border-vintage-brown hover:bg-vintage-brown/10 transition"
              >
                <div className="flex items-center gap-3">
                  <Trash2 className="h-5 w-5 text-vintage-brown" />
                  <div className="text-left">
                    <span className="font-bold text-vintage-brown">{t('settings.deleteAccount')}</span>
                    <p className="text-sm text-vintage-brown/60">{t('settings.deleteAccountDesc')}</p>
                  </div>
                </div>
              </button>
            </CardContent>
          </Card>
          
          {/* Save Button */}
          <div className="flex justify-end">
            <Button 
              onClick={handleSaveSettings}
              disabled={isSubmitting}
              className="min-w-[200px]"
            >
              {isSubmitting && <Spinner size="sm" className="mr-2" />}
              {t('common.saveChanges')}
            </Button>
          </div>
        </div>
        
        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="max-w-md w-full">
              <CardHeader>
                <CardTitle className="text-vintage-brown flex items-center gap-2">
                  <Trash2 className="h-5 w-5" />
                  {t('settings.deleteAccountConfirm')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-vintage-dark/70">
                  {t('settings.deleteAccountWarning')}
                </p>
                <div className="flex gap-3 justify-end">
                  <Button 
                    variant="outline" 
                    onClick={() => setShowDeleteConfirm(false)}
                  >
                    {t('common.cancel')}
                  </Button>
                  <Button 
                    variant="destructive"
                    onClick={() => {
                      // TODO: Implement account deletion
                      setShowDeleteConfirm(false);
                    }}
                  >
                    {t('settings.confirmDelete')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

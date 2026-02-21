import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { utilsApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import Spinner, { LoadingPage } from '@/components/ui/Spinner';
import { 
  ArrowLeft, 
  User, 
  BookOpen, 
  Link as LinkIcon, 
  Shield,
  Camera
} from 'lucide-react';

interface LearningLanguage {
  language?: string;
  code?: string;
  level: string;
}

export default function ProfileEditPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, profile, updateProfile, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    bio: '',
    native_language: '',
    target_language: '',
    level: '',
    skill_focus: '',
    interests: '',
    location: '',
    website: '',
    is_public: true,
    show_online_status: true,
    allow_messages: true,
  });
  const [learningLanguages, setLearningLanguages] = useState<LearningLanguage[]>([]);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch language choices
  const { data: choices } = useQuery({
    queryKey: ['choices'],
    queryFn: utilsApi.getChoices,
  });

  // Initialize form with user data
  useEffect(() => {
    if (user && profile) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        bio: profile.bio || '',
        native_language: profile.native_language || '',
        target_language: profile.target_language || '',
        level: profile.level || '',
        skill_focus: profile.skill_focus || '',
        interests: profile.interests?.join(', ') || '',
        location: profile.location || '',
        website: profile.website || '',
        is_public: profile.is_public ?? true,
        show_online_status: profile.show_online_status ?? true,
        allow_messages: profile.allow_messages ?? true,
      });
      setLearningLanguages((profile.learning_languages as LearningLanguage[]) || []);
      if (profile.avatar) {
        setAvatarPreview(profile.avatar);
      }
    }
  }, [user, profile]);

  // Cleanup URL.createObjectURL to prevent memory leaks
  useEffect(() => {
    return () => {
      if (avatarPreview && avatarPreview.startsWith('blob:')) {
        URL.revokeObjectURL(avatarPreview);
      }
    };
  }, [avatarPreview]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      setFormData((prev) => ({
        ...prev,
        [name]: (e.target as HTMLInputElement).checked,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      setAvatarPreview(URL.createObjectURL(file));
    }
  };

  const addLearningLanguage = () => {
    setLearningLanguages((prev) => [...prev, { language: '', level: 'A1' }]);
  };

  const removeLearningLanguage = (index: number) => {
    setLearningLanguages((prev) => prev.filter((_, i) => i !== index));
  };

  const updateLearningLanguage = (index: number, field: 'language' | 'level', value: string) => {
    setLearningLanguages((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrors({});

    try {
      const profileData = new FormData();
      
      // User fields
      profileData.append('first_name', formData.first_name);
      profileData.append('last_name', formData.last_name);
      
      // Profile fields
      profileData.append('bio', formData.bio);
      profileData.append('native_language', formData.native_language);
      profileData.append('target_language', formData.target_language);
      profileData.append('level', formData.level);
      profileData.append('skill_focus', formData.skill_focus);
      profileData.append('interests', formData.interests);
      profileData.append('location', formData.location);
      profileData.append('website', formData.website);
      profileData.append('is_public', String(formData.is_public));
      profileData.append('show_online_status', String(formData.show_online_status));
      profileData.append('allow_messages', String(formData.allow_messages));
      profileData.append('learning_languages', JSON.stringify(learningLanguages));
      
      if (avatarFile) {
        profileData.append('avatar', avatarFile);
      }

      await updateProfile(profileData);
      navigate('/ho-so');
    } catch (err: unknown) {
      const error = err as { response?: { data?: Record<string, string[]> } };
      if (error.response?.data) {
        const apiErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([key, value]) => {
          apiErrors[key] = Array.isArray(value) ? value[0] : value as string;
        });
        setErrors(apiErrors);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <LoadingPage />;
  }

  const languageOptions = choices?.languages || [];

  const nativeLanguageOptions = [
    { value: 'vi', label: `🇻🇳 ${t('nativeLanguages.vi', 'Tiếng Việt')}` },
    { value: 'en', label: `🇺🇸 ${t('nativeLanguages.en', 'English')}` },
    { value: 'de', label: `🇩🇪 ${t('nativeLanguages.de', 'Deutsch')}` },
    { value: 'ja', label: `🇯🇵 ${t('nativeLanguages.ja', '日本語')}` },
    { value: 'ko', label: `🇰🇷 ${t('nativeLanguages.ko', '한국어')}` },
    { value: 'zh', label: `🇨🇳 ${t('nativeLanguages.zh', '中文')}` },
    { value: 'fr', label: `🇫🇷 ${t('nativeLanguages.fr', 'Français')}` },
  ];

  const targetLanguageOptions = [
    { value: 'en', label: `🇬🇧 ${t('languages.en')}` },
    { value: 'de', label: `🇩🇪 ${t('languages.de')}` },
  ];

  const levelOptions = [
    { value: 'A1', label: t('levels.A1') },
    { value: 'A2', label: t('levels.A2') },
    { value: 'B1', label: t('levels.B1') },
    { value: 'B2', label: t('levels.B2') },
    { value: 'C1', label: t('levels.C1') },
    { value: 'C2', label: t('levels.C2') },
  ];

  const skillOptions = [
    { value: 'listening', label: `🎧 ${t('skills.listening')}` },
    { value: 'speaking', label: `🗣️ ${t('skills.speaking')}` },
    { value: 'reading', label: `📖 ${t('skills.reading')}` },
    { value: 'writing', label: `✍️ ${t('skills.writing')}` },
    { value: 'grammar', label: `📚 ${t('skills.grammar')}` },
    { value: 'vocabulary', label: `📝 ${t('skills.vocabulary')}` },
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
            {t('profile.backToProfile')}
          </Link>
          <h1 className="text-3xl font-serif font-bold text-vintage-dark">
            {t('profile.editTitle')}
          </h1>
          <p className="text-vintage-dark/60 mt-2 italic font-serif">
            {t('profile.editSubtitle')}
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Avatar Section */}
          <Card className="border-2 border-vintage-tan/30 overflow-hidden">
            {/* Cover Gradient */}
            <div className="h-24 bg-gradient-to-br from-vintage-olive via-vintage-brown to-vintage-tan" />
            
            <CardContent className="pt-0 pb-6">
              <div className="flex items-center gap-6 -mt-12 relative z-10">
                <div className="relative group">
                  {avatarPreview ? (
                    <img 
                      src={avatarPreview}
                      alt="Avatar"
                      className="h-24 w-24 sm:h-32 sm:w-32 rounded-xl border-4 border-white shadow-lg object-cover"
                    />
                  ) : (
                    <div className="h-24 w-24 sm:h-32 sm:w-32 rounded-xl border-4 border-white shadow-lg bg-gradient-to-br from-vintage-olive to-vintage-brown flex items-center justify-center text-white text-3xl font-serif font-bold">
                      {user?.username?.slice(0, 1).toUpperCase() || '?'}
                    </div>
                  )}
                  
                  {/* Upload Overlay */}
                  <label className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl opacity-0 group-hover:opacity-100 transition cursor-pointer">
                    <input 
                      type="file" 
                      accept="image/*" 
                      className="hidden" 
                      onChange={handleAvatarChange}
                    />
                    <Camera className="h-6 w-6 text-white" />
                  </label>
                </div>
                
                <div className="pt-12 sm:pt-16">
                  <p className="text-sm text-vintage-tan italic">
                    {t('profile.avatarHint')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Basic Info */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-vintage-olive" />
                {t('profile.basicInfo')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <Input
                  label={t('profile.firstName')}
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  error={errors.first_name}
                />
                <Input
                  label={t('profile.lastName')}
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  error={errors.last_name}
                />
              </div>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-2">
                    {t('profile.username')}
                  </label>
                  <input 
                    type="text" 
                    value={user?.username || ''} 
                    className="w-full px-4 py-3 border border-vintage-tan/20 rounded-lg bg-vintage-cream text-vintage-tan cursor-not-allowed"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-2">
                    {t('profile.email')}
                  </label>
                  <input 
                    type="email" 
                    value={user?.email || ''} 
                    className="w-full px-4 py-3 border border-vintage-tan/20 rounded-lg bg-vintage-cream text-vintage-tan cursor-not-allowed"
                    readOnly
                  />
                </div>
              </div>
              
              <Input
                label={t('profile.location')}
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder={t('profile.locationPlaceholder')}
                error={errors.location}
              />
              
              <div>
                <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-2">
                  {t('profile.bio')}
                </label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-4 py-3 border border-vintage-tan/40 rounded-lg bg-vintage-light focus:bg-white focus:ring-1 focus:ring-vintage-brown focus:border-vintage-brown transition-all resize-none"
                  placeholder={t('profile.bioPlaceholder')}
                />
              </div>
            </CardContent>
          </Card>
          
          {/* Learning Settings */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-vintage-olive" />
                {t('profile.learningSettings')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <Select
                  label={t('profile.nativeLanguage')}
                  name="native_language"
                  value={formData.native_language}
                  onChange={handleChange}
                  options={nativeLanguageOptions}
                  placeholder={t('common.selectLanguage')}
                />
                <Select
                  label={t('profile.targetLanguage')}
                  name="target_language"
                  value={formData.target_language}
                  onChange={handleChange}
                  options={targetLanguageOptions}
                  placeholder={t('common.selectLanguage')}
                />
              </div>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <Select
                  label={t('profile.level')}
                  name="level"
                  value={formData.level}
                  onChange={handleChange}
                  options={levelOptions}
                  placeholder={t('auth.register.selectLevel')}
                />
                <Select
                  label={t('profile.skillFocus')}
                  name="skill_focus"
                  value={formData.skill_focus}
                  onChange={handleChange}
                  options={skillOptions}
                  placeholder={t('auth.register.selectSkill')}
                />
              </div>
              
              {/* Learning Languages */}
              <div>
                <label className="block text-sm font-bold text-vintage-dark uppercase tracking-wide mb-2">
                  {t('profile.learningLanguages')}
                </label>
                <div className="space-y-2">
                  {learningLanguages.map((lang, index) => (
                    <div key={index} className="flex gap-2">
                      <Select
                        value={lang.language || lang.code || ''}
                        onChange={(e) => updateLearningLanguage(index, 'language', e.target.value)}
                        options={languageOptions}
                        placeholder={t('common.selectLanguage')}
                        className="flex-1"
                      />
                      <Select
                        value={lang.level}
                        onChange={(e) => updateLearningLanguage(index, 'level', e.target.value)}
                        options={levelOptions}
                        className="w-40"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeLearningLanguage(index)}
                        className="text-red-500 hover:text-red-600"
                      >
                        ✕
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addLearningLanguage}
                  >
                    + {t('profile.addLanguage')}
                  </Button>
                </div>
              </div>
              
              <Input
                label={t('profile.interests')}
                name="interests"
                value={formData.interests}
                onChange={handleChange}
                placeholder={t('profile.interestsPlaceholder')}
                error={errors.interests}
              />
            </CardContent>
          </Card>
          
          {/* Social Links */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LinkIcon className="h-5 w-5 text-vintage-olive" />
                {t('profile.socialLinks')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Input
                label={t('profile.website')}
                name="website"
                type="url"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://yourwebsite.com"
                error={errors.website}
              />
            </CardContent>
          </Card>
          
          {/* Privacy Settings */}
          <Card className="border-2 border-vintage-tan/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-vintage-olive" />
                {t('profile.privacySettings')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  name="is_public"
                  checked={formData.is_public}
                  onChange={handleChange}
                  className="w-5 h-5 text-vintage-olive rounded focus:ring-vintage-brown border-vintage-tan"
                />
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.publicProfile')}</span>
                  <p className="text-sm text-vintage-dark/60 italic">{t('profile.publicProfileDesc')}</p>
                </div>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  name="show_online_status"
                  checked={formData.show_online_status}
                  onChange={handleChange}
                  className="w-5 h-5 text-vintage-olive rounded focus:ring-vintage-brown border-vintage-tan"
                />
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.showOnlineStatus')}</span>
                  <p className="text-sm text-vintage-dark/60 italic">{t('profile.showOnlineStatusDesc')}</p>
                </div>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox" 
                  name="allow_messages"
                  checked={formData.allow_messages}
                  onChange={handleChange}
                  className="w-5 h-5 text-vintage-olive rounded focus:ring-vintage-brown border-vintage-tan"
                />
                <div>
                  <span className="font-bold text-vintage-dark">{t('profile.allowMessages')}</span>
                  <p className="text-sm text-vintage-dark/60 italic">{t('profile.allowMessagesDesc')}</p>
                </div>
              </label>
            </CardContent>
          </Card>
          
          {/* Submit Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/ho-so')}
              className="order-2 sm:order-1"
            >
              {t('common.cancel')}
            </Button>
            <Button 
              type="submit" 
              disabled={isSubmitting}
              className="order-1 sm:order-2"
            >
              {isSubmitting && <Spinner size="sm" className="mr-2" />}
              {t('common.saveChanges')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

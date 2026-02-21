import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { resourcesApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingPage } from '@/components/ui/Spinner';
import { formatDate, getLanguageName } from '@/lib/utils';
import { 
  Edit2, 
  Calendar, 
  BookOpen, 
  BarChart2, 
  Activity,
  FileText,
  Users,
  MessageSquare,
  Bookmark,
  Settings,
  Globe,
  Target,
  Zap
} from 'lucide-react';

export default function ProfilePage() {
  const { t } = useTranslation();
  const { user, profile, isLoading, refreshUser } = useAuth();

  // Try to refresh user data if profile is missing
  useEffect(() => {
    if (user && !profile) {
      refreshUser();
    }
  }, [user, profile, refreshUser]);

  // Fetch user stats
  const { data: userResources } = useQuery({
    queryKey: ['user-resources', user?.id],
    queryFn: () => resourcesApi.getAll({ page: 1, page_size: 4 }),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return <LoadingPage />;
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-vintage-dark/70">{t('common.error')}</p>
            <Button asChild className="mt-4">
              <Link to="/dang-nhap">{t('nav.login')}</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const fullName = user.first_name && user.last_name 
    ? `${user.first_name} ${user.last_name}` 
    : user.username;

  // Stats data
  const stats = {
    resources: userResources?.count || 0,
    friends: 0, // TODO: Get from API
    posts: 0, // Forum removed
    bookmarks: 0, // TODO: Get from API
  };

  return (
    <div className="bg-vintage-light min-h-screen">
      <div className="container-responsive section-spacing">
        {/* Profile Header Card */}
        <div className="bg-white rounded-lg shadow-md border-2 border-vintage-tan/30 overflow-hidden mb-6">
          {/* Cover Image */}
          <div className="h-32 bg-gradient-to-br from-vintage-olive via-vintage-brown to-vintage-tan relative">
            {/* Cover image could be added here */}
          </div>
          
          {/* Avatar & Basic Info */}
          <div className="px-6 pb-6">
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between -mt-12 sm:-mt-16">
              <div className="flex items-end gap-4">
                {/* Avatar */}
                <div className="relative">
                  {profile?.avatar ? (
                    <img 
                      src={profile.avatar} 
                      alt={user.username}
                      className="h-24 w-24 sm:h-32 sm:w-32 rounded-xl border-4 border-white shadow-lg object-cover"
                    />
                  ) : (
                    <div className="h-24 w-24 sm:h-32 sm:w-32 rounded-xl border-4 border-white shadow-lg bg-gradient-to-br from-vintage-olive to-vintage-brown flex items-center justify-center text-white text-3xl sm:text-4xl font-serif font-bold">
                      {user.username.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                </div>
                
                {/* Name & Username */}
                <div className="pb-2">
                  <h1 className="text-2xl font-serif font-bold text-vintage-dark">
                    {fullName}
                  </h1>
                  <p className="text-vintage-tan">@{user.username}</p>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="mt-4 sm:mt-0 flex gap-2">
                <Button asChild variant="outline" size="sm">
                  <Link to="/cai-dat" className="gap-2">
                    <Settings className="h-4 w-4" />
                    {t('profile.settings')}
                  </Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/ho-so/cap-nhat" className="gap-2">
                    <Edit2 className="h-4 w-4" />
                    {t('profile.edit')}
                  </Link>
                </Button>
              </div>
            </div>
            
            {/* Bio */}
            {profile?.bio && (
              <div className="mt-4 relative">
                <span className="absolute -top-2 -left-2 text-3xl text-vintage-tan/30 font-serif">"</span>
                <p className="text-vintage-dark/80 italic font-serif pl-4">{profile?.bio}</p>
              </div>
            )}
            
            {/* Meta Info */}
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-vintage-tan font-medium">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {t('profile.memberSince')}: {formatDate(user.date_joined)}
              </span>
              {user.email && (
                <span className="flex items-center gap-1">
                  <Globe className="h-4 w-4" />
                  {user.email}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Info */}
          <div className="space-y-6">
            {/* Learning Info */}
            <Card className="border-2 border-vintage-tan/20">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BookOpen className="h-5 w-5 text-vintage-olive" />
                  {t('profile.learningInfo')}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Native Language */}
                <div className="flex justify-between items-center py-2 border-b border-vintage-tan/20">
                  <span className="text-vintage-dark/70">{t('profile.nativeLanguage')}</span>
                  <span className="font-bold text-vintage-dark">
                    {profile?.native_language ? (
                      getLanguageName(profile?.native_language)
                    ) : (
                      <span className="text-vintage-tan italic">{t('profile.notSet')}</span>
                    )}
                  </span>
                </div>
                
                {/* Target Language */}
                <div className="flex justify-between items-center py-2 border-b border-vintage-tan/20">
                  <span className="text-vintage-dark/70 flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    {t('profile.targetLanguage')}
                  </span>
                  <span className="font-bold text-vintage-dark">
                    {profile?.target_language ? (
                      getLanguageName(profile?.target_language)
                    ) : (
                      <span className="text-vintage-tan italic">{t('profile.notSet')}</span>
                    )}
                  </span>
                </div>
                
                {/* Level */}
                <div className="flex justify-between items-center py-2 border-b border-vintage-tan/20">
                  <span className="text-vintage-dark/70">{t('profile.level')}</span>
                  <span className="font-bold text-vintage-dark">
                    {profile?.level ? (
                      <Badge variant="secondary">{t(`levels.${profile?.level}`)}</Badge>
                    ) : (
                      <span className="text-vintage-tan italic">{t('profile.notSet')}</span>
                    )}
                  </span>
                </div>
                
                {/* Skill Focus */}
                <div className="flex justify-between items-center py-2">
                  <span className="text-vintage-dark/70 flex items-center gap-1">
                    <Zap className="h-4 w-4" />
                    {t('profile.skillFocus')}
                  </span>
                  <span className="font-bold text-vintage-dark">
                    {profile?.skill_focus ? (
                      t(`skills.${profile?.skill_focus}`)
                    ) : (
                      <span className="text-vintage-tan italic">{t('profile.notSet')}</span>
                    )}
                  </span>
                </div>
              </CardContent>
            </Card>
            
            {/* Learning Languages */}
            {profile?.learning_languages && profile?.learning_languages.length > 0 && (
              <Card className="border-2 border-vintage-tan/20">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Globe className="h-5 w-5 text-vintage-olive" />
                    {t('profile.learningLanguages')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {profile?.learning_languages.map((lang: { code?: string; language?: string; level: string }, index: number) => (
                      <div key={index} className="flex items-center justify-between py-2 border-b border-vintage-tan/20 last:border-0">
                        <Badge variant="outline">
                          {getLanguageName(lang.code || lang.language || '')}
                        </Badge>
                        <span className="text-sm text-vintage-tan">
                          {t(`levels.${lang.level}`)}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Stats */}
            <Card className="border-2 border-vintage-tan/20">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BarChart2 className="h-5 w-5 text-vintage-olive" />
                  {t('profile.stats')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-vintage-cream rounded-lg border border-vintage-tan/20">
                    <div className="text-2xl font-serif font-bold text-vintage-olive">{stats.resources}</div>
                    <div className="text-xs text-vintage-dark/60 uppercase tracking-wide flex items-center justify-center gap-1">
                      <FileText className="h-3 w-3" />
                      {t('profile.resources')}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-vintage-cream rounded-lg border border-vintage-tan/20">
                    <div className="text-2xl font-serif font-bold text-vintage-brown">{stats.friends}</div>
                    <div className="text-xs text-vintage-dark/60 uppercase tracking-wide flex items-center justify-center gap-1">
                      <Users className="h-3 w-3" />
                      {t('profile.friends')}
                    </div>
                  </div>
                  <div className="text-center p-3 bg-vintage-cream rounded-lg border border-vintage-tan/20">
                    <div className="text-2xl font-serif font-bold text-vintage-blue">{stats.posts}</div>
                    <div className="text-xs text-vintage-dark/60 uppercase tracking-wide flex items-center justify-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {t('profile.posts')}
                    </div>
                  </div>
                  <Link 
                    to="/da-luu" 
                    className="text-center p-3 bg-vintage-cream rounded-lg border border-vintage-tan/20 hover:bg-vintage-tan/20 transition"
                  >
                    <div className="text-2xl font-serif font-bold text-vintage-tan">{stats.bookmarks}</div>
                    <div className="text-xs text-vintage-dark/60 uppercase tracking-wide flex items-center justify-center gap-1">
                      <Bookmark className="h-3 w-3" />
                      {t('profile.bookmarks')}
                    </div>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Right Column - Activity & Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Interests */}
            {profile?.interests && profile?.interests.length > 0 && (
              <Card className="border-2 border-vintage-tan/20">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Activity className="h-5 w-5 text-vintage-olive" />
                    {t('profile.interests')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {profile?.interests.map((interest: string, index: number) => (
                      <Badge key={index} variant="secondary" className="px-3 py-1">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Account Info */}
            <Card className="border-2 border-vintage-tan/20">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Settings className="h-5 w-5 text-vintage-olive" />
                  {t('profile.accountInfo')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-vintage-cream/50 rounded-lg">
                    <dt className="text-sm text-vintage-tan uppercase tracking-wide">{t('profile.username')}</dt>
                    <dd className="font-medium text-vintage-dark mt-1">@{user.username}</dd>
                  </div>
                  <div className="p-3 bg-vintage-cream/50 rounded-lg">
                    <dt className="text-sm text-vintage-tan uppercase tracking-wide">{t('profile.email')}</dt>
                    <dd className="font-medium text-vintage-dark mt-1">{user.email}</dd>
                  </div>
                  <div className="p-3 bg-vintage-cream/50 rounded-lg">
                    <dt className="text-sm text-vintage-tan uppercase tracking-wide">{t('profile.memberSince')}</dt>
                    <dd className="font-medium text-vintage-dark mt-1">{formatDate(user.date_joined)}</dd>
                  </div>
                  <div className="p-3 bg-vintage-cream/50 rounded-lg">
                    <dt className="text-sm text-vintage-tan uppercase tracking-wide">{t('profile.lastLogin')}</dt>
                    <dd className="font-medium text-vintage-dark mt-1">
                      {user.last_login ? formatDate(user.last_login) : t('profile.never')}
                    </dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
            
            {/* Quick Actions */}
            <Card className="border-2 border-vintage-tan/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{t('profile.quickActions')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Link 
                    to="/tai-lieu"
                    className="flex flex-col items-center gap-2 p-4 rounded-lg bg-vintage-cream/50 hover:bg-vintage-cream transition border border-vintage-tan/20"
                  >
                    <FileText className="h-6 w-6 text-vintage-olive" />
                    <span className="text-sm font-medium text-vintage-dark">{t('nav.resources')}</span>
                  </Link>
                  <Link 
                    to="/video"
                    className="flex flex-col items-center gap-2 p-4 rounded-lg bg-vintage-cream/50 hover:bg-vintage-cream transition border border-vintage-tan/20"
                  >
                    <Users className="h-6 w-6 text-vintage-brown" />
                    <span className="text-sm font-medium text-vintage-dark">{t('nav.videos')}</span>
                  </Link>
                  <Link 
                    to="/kien-thuc"
                    className="flex flex-col items-center gap-2 p-4 rounded-lg bg-vintage-cream/50 hover:bg-vintage-cream transition border border-vintage-tan/20"
                  >
                    <MessageSquare className="h-6 w-6 text-vintage-blue" />
                    <span className="text-sm font-medium text-vintage-dark">{t('nav.knowledge')}</span>
                  </Link>
                  <Link 
                    to="/cong-cu"
                    className="flex flex-col items-center gap-2 p-4 rounded-lg bg-vintage-cream/50 hover:bg-vintage-cream transition border border-vintage-tan/20"
                  >
                    <MessageSquare className="h-6 w-6 text-vintage-tan" />
                    <span className="text-sm font-medium text-vintage-dark">{t('nav.tools')}</span>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourcesApi } from '@/api';
import type { Resource } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingPage } from '@/components/ui/Spinner';
import { SEO } from '@/components/common';
import { Breadcrumb } from '@/components/common/Breadcrumb';
import { useAuth } from '@/contexts/AuthContext';
import { formatDate } from '@/lib/utils';
import { 
  ChevronLeft,
  Download, 
  Eye, 
  BookOpen, 
  User,
  Calendar,
  Video,
  Headphones,
  Book,
  ArrowLeft,
  PlayCircle,
  UserPlus,
  Bookmark,
  Hash
} from 'lucide-react';

export default function ResourceDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const { data: resource, isLoading, error } = useQuery({
    queryKey: ['resource', slug],
    queryFn: () => resourcesApi.getBySlug(slug!),
    enabled: !!slug,
  });

  const downloadMutation = useMutation({
    mutationFn: () => resourcesApi.download(slug!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource', slug] });
    },
  });

  if (isLoading) {
    return <LoadingPage />;
  }

  if (error || !resource) {
    return (
      <div className="container-responsive section-spacing text-center">
        <div className="max-w-md mx-auto">
          <BookOpen className="h-16 w-16 text-vintage-tan mx-auto mb-4" />
          <h1 className="text-2xl font-serif font-bold text-vintage-dark mb-4">
            {t('resources.notFound', 'Resource not found')}
          </h1>
          <p className="text-vintage-dark/60 mb-6">
            {t('resources.notFoundDescription', 'The resource you are looking for might have been removed or does not exist.')}
          </p>
          <Button asChild className="touch-target">
            <Link to="/tai-lieu">
              <ChevronLeft className="h-4 w-4 mr-2" />
              {t('resources.backToList', 'Back to Resources')}
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  const handleDownload = async () => {
    try {
      await downloadMutation.mutateAsync();
      if (resource?.file) {
        window.open(resource.file, '_blank');
      } else if (resource?.external_url) {
        window.open(resource.external_url, '_blank');
      }
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const uploaderName = resource.uploaded_by?.first_name
    ? `${resource.uploaded_by.first_name} ${resource.uploaded_by.last_name}`
    : resource.uploaded_by?.username;

  // Get icon based on resource type
  const getTypeIcon = () => {
    const type = resource.resource_type || '';
    if (type.includes('video')) return <Video className="h-3 w-3 mr-1" />;
    if (type.includes('audio')) return <Headphones className="h-3 w-3 mr-1" />;
    return <Book className="h-3 w-3 mr-1" />;
  };

  const getCoverIcon = () => {
    const type = resource.resource_type || '';
    if (type.includes('video')) return <Video className="h-20 w-20 text-white/50" />;
    if (type.includes('audio')) return <Headphones className="h-20 w-20 text-white/50" />;
    return <BookOpen className="h-20 w-20 text-white/50" />;
  };

  return (
    <>
      {/* SEO */}
      <SEO 
        title={`${resource.title} - UnstressVN`}
        description={resource.description?.slice(0, 160) || ''}
        keywords={[resource.language_display || '', resource.level || '', resource.resource_type_display || '', 'tài liệu học tập', 'UnstressVN']}
        type="article"
        publishedTime={resource.created_at}
        author={uploaderName}
      />

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white py-8">
        <div className="container-responsive">
          {/* Breadcrumb */}
          <Breadcrumb items={[
            { label: t('resources.library', 'Thư viện'), href: '/tai-lieu' },
            { label: resource.title.length > 30 ? resource.title.slice(0, 30) + '...' : resource.title },
          ]} className="mb-8" />

          {/* Main Content - Two Column Layout matching template */}
          <div className="bg-white rounded-xl shadow-lg border-2 border-vintage-tan/30 overflow-hidden">
            <div className="flex flex-col lg:flex-row">
              {/* Left: Cover Image */}
              <div className="lg:w-1/3 bg-vintage-cream p-6 flex items-start justify-center">
                <div className="w-full max-w-xs">
                  {resource.cover_image ? (
                    <img 
                      src={resource.cover_image} 
                      alt={resource.title}
                      className="w-full rounded-lg shadow-xl border-4 border-white object-cover aspect-[3/4]"
                    />
                  ) : (
                    <div className="w-full rounded-lg shadow-xl border-4 border-white bg-gradient-to-br from-vintage-olive to-vintage-brown aspect-[3/4] flex items-center justify-center">
                      {getCoverIcon()}
                    </div>
                  )}
                  
                  {/* Quick Stats under cover */}
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <div className="bg-white rounded-lg p-3 text-center border border-vintage-tan/30">
                      <Eye className="h-5 w-5 mx-auto text-vintage-olive mb-1" />
                      <span className="block text-lg font-bold text-vintage-dark">{resource.view_count || 0}</span>
                      <span className="text-[10px] text-vintage-tan uppercase tracking-wide font-bold">
                        {t('resources.views', 'Lượt xem')}
                      </span>
                    </div>
                    <div className="bg-white rounded-lg p-3 text-center border border-vintage-tan/30">
                      <Download className="h-5 w-5 mx-auto text-vintage-olive mb-1" />
                      <span className="block text-lg font-bold text-vintage-dark">{resource.download_count || 0}</span>
                      <span className="text-[10px] text-vintage-tan uppercase tracking-wide font-bold">
                        {t('resources.downloads', 'Lượt tải')}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Right: Content */}
              <div className="lg:w-2/3 p-6 md:p-8">
                {/* Category Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {resource.language_display && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-olive/10 text-vintage-olive border border-vintage-olive/20">
                      {resource.language_display}
                    </span>
                  )}
                  {resource.resource_type_display && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-blue/10 text-vintage-blue border border-vintage-blue/20">
                      {getTypeIcon()}
                      {resource.resource_type_display}
                    </span>
                  )}
                  {resource.level && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-tan/20 text-vintage-brown border border-vintage-tan/30">
                      {resource.level}
                    </span>
                  )}
                </div>
                
                {/* Resource Tags */}
                {resource.tags && resource.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {resource.tags.map((tag) => (
                      <Link
                        key={tag.id}
                        to={`/tai-lieu?tag=${tag.slug}`}
                        className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-vintage-cream text-vintage-brown hover:bg-vintage-tan/30 border border-vintage-tan/20 transition-colors"
                      >
                        #{tag.name}
                      </Link>
                    ))}
                  </div>
                )}
                
                {/* Title */}
                <h1 className="text-2xl md:text-3xl font-serif font-bold text-vintage-dark mb-2">
                  {resource.title}
                </h1>
                
                {/* Author & Date */}
                <div className="flex flex-wrap items-center gap-4 text-sm text-vintage-tan mb-6">
                  {resource.uploaded_by && (
                    <Link to={`/ho-so/${resource.uploaded_by.username}`} className="flex items-center gap-1 hover:text-vintage-olive transition-colors">
                      <User className="h-4 w-4" />
                      {uploaderName}
                    </Link>
                  )}
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(resource.created_at)}
                  </span>
                </div>
                
                {/* Description */}
                <div className="prose max-w-none text-vintage-dark/80 mb-8 font-serif leading-relaxed">
                  {resource.description?.split('\n').map((paragraph, i) => (
                    <p key={i}>{paragraph}</p>
                  ))}
                </div>
                
                {/* Actions */}
                <div className="flex flex-wrap gap-3 pt-6 border-t border-vintage-tan/30">
                  {resource.file || resource.external_url ? (
                    isAuthenticated ? (
                      <Button
                        onClick={handleDownload}
                        disabled={downloadMutation.isPending}
                        className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-bold uppercase tracking-wide rounded-lg text-white bg-vintage-brown hover:bg-vintage-olive shadow-lg transition-all hover:shadow-xl"
                      >
                        <Download className="h-5 w-5 mr-2" />
                        {downloadMutation.isPending ? t('common.loading', 'Đang tải...') : t('resources.download', 'Tải xuống')}
                      </Button>
                    ) : (
                      <Link
                        to="/dang-ky"
                        className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-bold uppercase tracking-wide rounded-lg text-white bg-vintage-olive hover:bg-vintage-brown shadow-lg transition-all hover:shadow-xl"
                      >
                        <UserPlus className="h-5 w-5 mr-2" />
                        {t('resources.registerToDownload', 'Đăng ký để tải')}
                      </Link>
                    )
                  ) : null}
                  
                  {resource.external_url && (
                    <a 
                      href={resource.external_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center px-6 py-3 border-2 border-vintage-blue text-sm font-bold uppercase tracking-wide rounded-lg text-vintage-blue bg-white hover:bg-vintage-blue/10 shadow-sm transition-all"
                    >
                      <PlayCircle className="h-5 w-5 mr-2" />
                      {t('resources.visitLink', 'Xem liên kết')}
                    </a>
                  )}
                  
                  <Link
                    to="/tai-lieu"
                    className="inline-flex items-center justify-center px-6 py-3 border border-vintage-tan text-sm font-bold uppercase tracking-wide rounded-lg text-vintage-dark bg-white hover:bg-vintage-cream shadow-sm transition-colors"
                  >
                    <ArrowLeft className="h-5 w-5 mr-2" />
                    {t('resources.backToList', 'Quay lại')}
                  </Link>
                  
                  {/* Bookmark Button */}
                  <button
                    className="inline-flex items-center justify-center px-6 py-3 border-2 border-vintage-tan text-sm font-bold uppercase tracking-wide rounded-lg text-vintage-tan bg-white hover:bg-vintage-cream hover:border-vintage-brown hover:text-vintage-brown shadow-sm transition-all"
                  >
                    <Bookmark className="h-5 w-5 mr-2" />
                    {t('resources.save', 'Lưu lại')}
                  </button>
                </div>
                
                {/* Category Tag */}
                {resource.category_name && (
                  <div className="mt-8 pt-6 border-t border-vintage-tan/30">
                    <h3 className="text-sm font-bold text-vintage-dark uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Hash className="h-4 w-4 text-vintage-olive" />
                      {t('resources.category', 'Danh mục')}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      <Link
                        to={`/tai-lieu?category=${resource.category?.id || ''}`}
                        className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-vintage-cream text-vintage-brown border border-vintage-tan/40 hover:bg-vintage-tan/20 hover:border-vintage-brown transition-all"
                      >
                        <Hash className="h-3 w-3 mr-1" />
                        {resource.category_name}
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Related Resources */}
          {resource.related_resources && resource.related_resources.length > 0 && (
            <div className="mt-10">
              <h2 className="text-2xl font-serif font-bold text-vintage-dark mb-6 flex items-center gap-2">
                <BookOpen className="h-6 w-6 text-vintage-olive" />
                {t('resources.related', 'Tài liệu liên quan')}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {resource.related_resources.map((item: Resource) => (
                  <Link
                    key={item.id}
                    to={`/tai-lieu/${item.slug}`}
                    className="bg-white rounded-lg border border-vintage-tan/40 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group"
                  >
                    <div className="h-32 w-full bg-vintage-cream relative">
                      {item.cover_image ? (
                        <img 
                          src={item.cover_image} 
                          alt={item.title}
                          className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-vintage-olive/20 to-vintage-brown/20">
                          <Book className="h-10 w-10 text-vintage-tan" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-serif font-bold text-vintage-dark line-clamp-2 group-hover:text-vintage-brown transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-xs text-vintage-tan mt-1">
                        {item.level || t('resources.unknownLevel', 'Không rõ cấp độ')}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

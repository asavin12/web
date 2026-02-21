import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { utilsApi } from '@/api';
import type { Video } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { LoadingInline } from '@/components/ui/Spinner';
import { Pagination } from '@/components/ui/Pagination';
import { SEO } from '@/components/common';
import { 
  Video as VideoIcon, 
  Search, 
  Filter, 
  Play, 
  Eye, 
  Star,
  X
} from 'lucide-react';

export default function VideoListPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  
  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    language: searchParams.get('language') || '',
    level: searchParams.get('level') || '',
  });
  
  const page = parseInt(searchParams.get('page') || '1');

  // Fetch videos
  const { data, isLoading, error } = useQuery({
    queryKey: ['videos', filters, page],
    queryFn: () => utilsApi.getVideos({ ...filters, page }),
  });

  const videos = data?.results || [];
  const totalVideos = data?.count || 0;
  const totalPages = data?.total_pages || 1;
  const languageChoices = data?.language_choices || [];
  const levelChoices = data?.level_choices || [];

  const handleFilterChange = (name: string, value: string) => {
    setFilters(prev => ({ ...prev, [name]: value }));
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(name, value);
    } else {
      newParams.delete(name);
    }
    newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setFilters({ q: '', language: '', level: '' });
    setSearchParams({});
  };

  const hasActiveFilters = filters.language || filters.level || filters.q;

  // Convert choices to Select options format
  const languageOptions = languageChoices.map(([value, label]: [string, string]) => ({ value, label }));
  const levelOptions = levelChoices.map(([value, label]: [string, string]) => ({ value, label }));

  return (
    <>
      <SEO 
        title={t('videos.seo.title', 'Video học tập - UnstressVN')}
        description={t('videos.seo.description', 'Bộ sưu tập video bài giảng giúp nâng cao kỹ năng ngôn ngữ của bạn.')}
        keywords={['video học tiếng Đức', 'video học tiếng Anh', 'bài giảng ngôn ngữ', 'UnstressVN']}
        type="website"
      />

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        <div className="container-responsive py-8">
        {/* Header */}
        <header className="mb-6 md:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 md:gap-3 mb-2">
                <VideoIcon className="h-6 w-6 md:h-8 md:w-8 text-vintage-blue" />
                <h1 className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark">
                  {t('videos.pageTitle')}
                </h1>
              </div>
              <p className="text-sm md:text-base text-vintage-dark/70 font-serif italic">
                {t('videos.subtitle')}
              </p>
            </div>
            
            {/* Filter Toggle - Mobile */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`md:hidden touch-target inline-flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                  showFilters ? 'bg-vintage-blue text-white border-vintage-blue' : 'border-vintage-tan text-vintage-dark'
                }`}
              >
                <Filter className="h-4 w-4" />
                <span className="text-sm font-medium">{t('common.filters')}</span>
                {hasActiveFilters && (
                  <span className="w-2 h-2 rounded-full bg-vintage-brown"></span>
                )}
              </button>
            </div>
          </div>
        </header>

        {/* Filters - Responsive Inline */}
        <div className={`${showFilters ? 'block' : 'hidden'} md:block mb-6 md:mb-8`}>
          <Card>
            <CardContent className="p-4 md:pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
                {/* Search */}
                <div className="sm:col-span-2 lg:col-span-2 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-vintage-tan" />
                  <Input
                    className="pl-9"
                    placeholder={t('videos.searchPlaceholder')}
                    value={filters.q}
                    onChange={(e) => handleFilterChange('q', e.target.value)}
                  />
                </div>
                
                <Select
                  value={filters.language}
                  onChange={(e) => handleFilterChange('language', e.target.value)}
                  options={languageOptions}
                  placeholder={t('videos.allLanguages')}
                />
                <Select
                  value={filters.level}
                  onChange={(e) => handleFilterChange('level', e.target.value)}
                  options={levelOptions}
                  placeholder={t('videos.allLevels')}
                />
                
                {hasActiveFilters && (
                  <Button variant="outline" onClick={clearFilters} size="sm" className="h-10">
                    <X className="h-4 w-4 mr-1" />
                    {t('common.clearFilters', 'Xóa lọc')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Count */}
        {totalVideos > 0 && (
          <p className="text-sm md:text-base text-vintage-dark/60 mb-4 md:mb-6 font-serif">
            {totalVideos} {t('videos.videosCount', 'video')}
          </p>
        )}

        {/* Results */}
        {isLoading ? (
          <div className="py-12">
            <LoadingInline text={t('common.loading', 'Đang tải...')} />
          </div>
        ) : error ? (
          <Card className="border-vintage-brown/30 bg-vintage-brown/10">
            <CardContent className="py-12 text-center">
              <VideoIcon className="h-16 w-16 text-vintage-brown/40 mx-auto mb-4" />
              <h3 className="text-xl font-serif font-bold text-vintage-brown mb-2">
                {t('videos.error', 'Không thể tải video')}
              </h3>
              <p className="text-vintage-brown/70 mb-6">
                {t('videos.errorDescription', 'Vui lòng kiểm tra kết nối và thử lại.')}
              </p>
              <Button onClick={() => window.location.reload()} variant="outline" className="border-vintage-brown/30 text-vintage-brown">
                {t('common.retry', 'Thử Lại')}
              </Button>
            </CardContent>
          </Card>
        ) : videos.length > 0 ? (
          <>
            {/* Video Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
              {videos.map((video: Video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 md:mt-10">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        ) : (
          <Card className="border-vintage-tan/30">
            <CardContent className="py-16 text-center">
              <VideoIcon className="h-16 w-16 text-vintage-tan/50 mx-auto mb-4" />
              <h3 className="text-xl font-serif font-bold text-vintage-dark mb-2">
                {t('videos.noVideos', 'Không tìm thấy video')}
              </h3>
              <p className="text-vintage-tan mb-6">
                {hasActiveFilters 
                  ? t('videos.noResultsFiltered', 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm.')
                  : t('videos.noVideosDescription', 'Hãy quay lại sau để xem các video mới!')}
              </p>
              {hasActiveFilters && (
                <Button onClick={clearFilters} variant="outline" size="sm">
                  <X className="h-4 w-4 mr-1" />
                  {t('common.clearFilters', 'Xóa lọc')}
                </Button>
              )}
            </CardContent>
          </Card>
        )}
        </div>
      </div>
    </>
  );
}

// Video Card Component
interface VideoCardProps {
  video: Video;
}

function VideoCard({ video }: VideoCardProps) {
  return (
    <Link 
      to={`/video/${video.slug}`}
      className="group relative bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-vintage-tan/30"
    >
      {/* Thumbnail */}
      <div className="relative">
        <img 
          src={video.thumbnail} 
          alt={video.title}
          className="w-full h-40 sm:h-44 object-cover transform group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-vintage-dark/20 group-hover:bg-vintage-brown/40 transition-colors duration-300 flex items-center justify-center">
          <Play className="h-12 w-12 text-white drop-shadow-lg transform group-hover:scale-110 transition-transform duration-300" />
        </div>
        
        {/* Duration badge */}
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-black/70 text-white text-[10px] px-2 py-1 rounded font-mono">
            {video.duration}
          </div>
        )}
        
        {/* Language badge */}
        <div className="absolute top-2 left-2 bg-vintage-olive/90 text-white text-[10px] px-2 py-1 rounded font-bold uppercase">
          {video.language_display}
        </div>
        
        {/* Featured badge */}
        {video.is_featured && (
          <div className="absolute top-2 right-2 bg-vintage-brown/90 text-white text-[10px] px-2 py-1 rounded font-bold uppercase flex items-center gap-1">
            <Star className="h-3 w-3" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3 sm:p-4 bg-vintage-cream/20">
        <h3 className="text-sm sm:text-base font-serif font-bold text-vintage-dark line-clamp-2 mb-1.5 group-hover:text-vintage-blue transition-colors leading-tight">
          {video.title}
        </h3>
        <p className="text-[10px] sm:text-[11px] font-bold text-vintage-tan uppercase tracking-wide mb-2">
          {video.level_display}
        </p>
        <div className="flex items-center justify-between border-t border-vintage-tan/20 pt-2 text-[10px] sm:text-[11px] text-vintage-dark/60 font-medium">
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {video.view_count}
          </span>
          <span>{video.created_at}</span>
        </div>
      </div>
    </Link>
  );
}

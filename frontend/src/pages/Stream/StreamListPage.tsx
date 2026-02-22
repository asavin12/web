/**
 * StreamListPage - Danh sách video/audio stream
 * 
 * Features:
 * - Grid hiển thị media items
 * - Filter theo ngôn ngữ, trình độ, loại media
 * - Tìm kiếm
 * - Phân trang
 */
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { mediaStreamApi, type StreamMedia, type StreamMediaFilters } from '@/api/mediastream';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingInline } from '@/components/ui/Spinner';
import { SEO } from '@/components/common';
import {
  Play,
  Music,
  Search,
  Filter,
  Eye,
  Clock,
  Globe,
  BarChart2,
  X,
  Film,
} from 'lucide-react';

// Filter options
const MEDIA_TYPES = [
  { value: '', label: 'Tất cả' },
  { value: 'video', label: '🎬 Video' },
  { value: 'audio', label: '🎵 Audio' },
];

const LANGUAGES = [
  { value: '', label: 'Tất cả ngôn ngữ' },
  { value: 'vi', label: '🇻🇳 Tiếng Việt' },
  { value: 'en', label: '🇬🇧 English' },
  { value: 'de', label: '🇩🇪 Deutsch' },
];

const LEVELS = [
  { value: '', label: 'Tất cả trình độ' },
  { value: 'A1', label: 'A1 - Sơ cấp' },
  { value: 'A2', label: 'A2 - Cơ bản' },
  { value: 'B1', label: 'B1 - Trung cấp' },
  { value: 'B2', label: 'B2 - Trung cao' },
  { value: 'C1', label: 'C1 - Cao cấp' },
  { value: 'C2', label: 'C2 - Thành thạo' },
];

function StreamMediaCard({ media }: { media: StreamMedia }) {
  const isVideo = media.media_type === 'video';

  return (
    <Link to={`/stream/${media.uid}`} className="block group">
      <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 border-2 border-vintage-tan/20 hover:border-vintage-olive/40 h-full">
        {/* Thumbnail / Icon */}
        <div className="relative aspect-video bg-vintage-dark/5 overflow-hidden">
          {media.thumbnail_url ? (
            <img
              src={media.thumbnail_url}
              alt={media.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-vintage-olive/10 to-vintage-blue/10">
              {isVideo ? (
                <Film className="h-12 w-12 text-vintage-olive/40" />
              ) : (
                <Music className="h-12 w-12 text-vintage-blue/40" />
              )}
            </div>
          )}

          {/* Play overlay */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center">
            <div className="bg-white/90 rounded-full p-3 opacity-0 group-hover:opacity-100 transform scale-75 group-hover:scale-100 transition-all duration-300 shadow-lg">
              <Play className="h-6 w-6 text-vintage-olive fill-vintage-olive" />
            </div>
          </div>

          {/* Duration badge */}
          {media.duration_formatted && (
            <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-0.5 rounded font-mono">
              {media.duration_formatted}
            </div>
          )}

          {/* Media type badge */}
          <div className="absolute top-2 left-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              isVideo
                ? 'bg-vintage-olive/90 text-white'
                : 'bg-vintage-blue/90 text-white'
            }`}>
              {isVideo ? 'VIDEO' : 'AUDIO'}
            </span>
          </div>
        </div>

        {/* Info */}
        <CardContent className="p-4">
          <h3 className="font-serif font-bold text-vintage-dark text-base leading-tight line-clamp-2 group-hover:text-vintage-olive transition-colors mb-2">
            {media.title}
          </h3>

          {media.description && (
            <p className="text-sm text-vintage-dark/60 line-clamp-2 mb-3">
              {media.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 text-xs text-vintage-tan">
            {media.language && media.language !== 'all' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-vintage-olive/10 text-vintage-olive rounded-full">
                <Globe className="h-3 w-3" />
                {media.language === 'vi' ? 'VN' : media.language === 'en' ? 'EN' : media.language === 'de' ? 'DE' : media.language.toUpperCase()}
              </span>
            )}
            {media.level && media.level !== 'all' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-vintage-blue/10 text-vintage-blue rounded-full">
                <BarChart2 className="h-3 w-3" />
                {media.level}
              </span>
            )}
            <span className="inline-flex items-center gap-1 ml-auto">
              <Eye className="h-3 w-3" />
              {media.view_count}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export default function StreamListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState<StreamMediaFilters>({
    search: searchParams.get('q') || '',
    media_type: searchParams.get('type') || '',
    language: searchParams.get('language') || '',
    level: searchParams.get('level') || '',
  });

  const page = parseInt(searchParams.get('page') || '1');

  // Fetch media list
  const { data, isLoading } = useQuery({
    queryKey: ['stream-media-list', filters, page],
    queryFn: () => mediaStreamApi.getAll({ ...filters, page, page_size: 12 }),
  });

  const mediaItems = data?.results || [];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / 12);

  const handleFilterChange = (name: string, value: string) => {
    setFilters(prev => ({ ...prev, [name]: value }));
    const newParams = new URLSearchParams(searchParams);
    const paramName = name === 'search' ? 'q' : name === 'media_type' ? 'type' : name;
    if (value) {
      newParams.set(paramName, value);
    } else {
      newParams.delete(paramName);
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
    setFilters({ search: '', media_type: '', language: '', level: '' });
    setSearchParams({});
  };

  const hasActiveFilters = filters.language || filters.level || filters.media_type || filters.search;

  return (
    <>
      <SEO
        title="Stream Media - UnstressVN"
        description="Thư viện video và audio học ngoại ngữ với phụ đề và dịch realtime."
        keywords={['stream video', 'học tiếng Đức', 'học tiếng Anh', 'phụ đề', 'UnstressVN']}
        type="website"
      />

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        <div className="container-responsive py-8">

          {/* Header */}
          <header className="mb-6 md:mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 md:gap-3 mb-2">
                  <Film className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive" />
                  <h1 className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark">
                    Stream Media
                  </h1>
                </div>
                <p className="text-sm md:text-base text-vintage-dark/70 font-serif italic">
                  Video và audio học ngoại ngữ với phụ đề song ngữ
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  onClick={() => setShowFilters(!showFilters)}
                  variant="outline"
                  size="sm"
                  className={`border-vintage-tan ${showFilters ? 'bg-vintage-cream' : ''}`}
                >
                  <Filter className="h-4 w-4 mr-1.5" />
                  Bộ lọc
                  {hasActiveFilters && (
                    <span className="ml-1.5 bg-vintage-olive text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      !
                    </span>
                  )}
                </Button>
              </div>
            </div>
          </header>

          {/* Filters */}
          {showFilters && (
            <div className="bg-white rounded-xl border-2 border-vintage-tan/30 p-4 md:p-6 mb-6 shadow-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Search */}
                <div>
                  <label className="text-xs font-bold text-vintage-dark/60 uppercase tracking-wide mb-1 block">
                    Tìm kiếm
                  </label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-vintage-tan" />
                    <Input
                      type="text"
                      placeholder="Tìm video, audio..."
                      value={filters.search || ''}
                      onChange={(e) => handleFilterChange('search', e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                {/* Media Type */}
                <div>
                  <label className="text-xs font-bold text-vintage-dark/60 uppercase tracking-wide mb-1 block">
                    Loại
                  </label>
                  <Select
                    value={filters.media_type || ''}
                    onChange={(e) => handleFilterChange('media_type', e.target.value)}
                    options={MEDIA_TYPES}
                  />
                </div>

                {/* Language */}
                <div>
                  <label className="text-xs font-bold text-vintage-dark/60 uppercase tracking-wide mb-1 block">
                    Ngôn ngữ
                  </label>
                  <Select
                    value={filters.language || ''}
                    onChange={(e) => handleFilterChange('language', e.target.value)}
                    options={LANGUAGES}
                  />
                </div>

                {/* Level */}
                <div>
                  <label className="text-xs font-bold text-vintage-dark/60 uppercase tracking-wide mb-1 block">
                    Trình độ
                  </label>
                  <Select
                    value={filters.level || ''}
                    onChange={(e) => handleFilterChange('level', e.target.value)}
                    options={LEVELS}
                  />
                </div>
              </div>

              {hasActiveFilters && (
                <div className="mt-4 pt-3 border-t border-vintage-tan/20 flex justify-end">
                  <Button onClick={clearFilters} variant="outline" size="sm" className="text-vintage-tan border-vintage-tan/30">
                    <X className="h-3.5 w-3.5 mr-1" />
                    Xoá bộ lọc
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Results Count */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-vintage-dark/60">
              {isLoading ? (
                <LoadingInline />
              ) : (
                <>{totalCount} kết quả</>
              )}
            </p>
          </div>

          {/* Media Grid */}
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse">
                  <div className="aspect-video bg-vintage-tan/20 rounded-xl mb-3" />
                  <div className="h-4 bg-vintage-tan/20 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-vintage-tan/10 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : mediaItems.length === 0 ? (
            <div className="text-center py-16">
              <Film className="h-16 w-16 text-vintage-tan/30 mx-auto mb-4" />
              <h2 className="text-xl font-serif font-bold text-vintage-dark/60 mb-2">
                Chưa có nội dung
              </h2>
              <p className="text-vintage-tan">
                {hasActiveFilters
                  ? 'Không tìm thấy media phù hợp với bộ lọc.'
                  : 'Nội dung stream sẽ được thêm sớm.'}
              </p>
              {hasActiveFilters && (
                <Button onClick={clearFilters} variant="outline" className="mt-4">
                  <X className="h-4 w-4 mr-1" />
                  Xoá bộ lọc
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {mediaItems.map((item) => (
                <StreamMediaCard key={item.uid} media={item} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex justify-center">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

import { useTranslation } from 'react-i18next';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { utilsApi } from '@/api';
import type { Video } from '@/types';
import { Button } from '@/components/ui/Button';
import Spinner from '@/components/ui/Spinner';
import { SEO } from '@/components/common';
import { useAuth } from '@/contexts/AuthContext';
import { 
  Video as VideoIcon, 
  Eye, 
  Calendar,
  Clock,
  Globe,
  BarChart2,
  Star,
  ExternalLink,
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Play
} from 'lucide-react';

export default function VideoDetailPage() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Fetch video detail
  const { data: video, isLoading, error } = useQuery({
    queryKey: ['video', slug],
    queryFn: () => utilsApi.getVideoDetail(slug!),
    enabled: !!slug,
  });

  // Fetch related videos
  const { data: relatedData } = useQuery({
    queryKey: ['videos', { language: video?.language, page_size: 5 }],
    queryFn: () => utilsApi.getVideos({ language: video?.language, page_size: 5 }),
    enabled: !!video?.language,
  });

  const relatedVideos = relatedData?.results?.filter(v => v.id !== video?.id).slice(0, 4) || [];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <VideoIcon className="h-16 w-16 text-vintage-tan/50 mx-auto mb-4" />
          <h2 className="text-xl font-serif font-bold text-vintage-dark mb-2">
            {t('videos.notFound', 'Video không tồn tại')}
          </h2>
          <Button onClick={() => navigate('/video')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('common.back', 'Quay lại')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      <SEO 
        title={`${video.title} - UnstressVN`}
        description={video.description?.slice(0, 160) || video.title}
        type="website"
      />

      <div className="min-h-screen bg-vintage-light py-6">
        <div className="container-responsive">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Main Video Section */}
            <div className="lg:w-2/3">
              {/* Video Player */}
              <div className="bg-black rounded-xl overflow-hidden shadow-2xl">
                <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
                  <iframe 
                    src={`https://www.youtube.com/embed/${video.youtube_id}?rel=0&modestbranding=1`}
                    className="absolute top-0 left-0 w-full h-full border-0"
                    title={video.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    referrerPolicy="strict-origin-when-cross-origin"
                    allowFullScreen
                  />
                </div>
              </div>
              
              {/* Fallback link */}
              <p className="text-center text-sm text-vintage-tan mt-2">
                {t('videos.notDisplaying', 'Video không hiển thị?')}{' '}
                <a 
                  href={video.youtube_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-vintage-brown hover:underline font-semibold"
                >
                  {t('videos.watchOnYouTube', 'Xem trực tiếp trên YouTube')}
                </a>
              </p>
              
              {/* Video Info */}
              <div className="mt-4 bg-white rounded-xl border-2 border-vintage-tan/30 p-6">
                {/* Title */}
                <h1 className="text-2xl font-serif font-bold text-vintage-dark mb-3">
                  {video.title}
                </h1>
                
                {/* Meta Info */}
                <div className="flex flex-wrap items-center gap-4 text-sm text-vintage-tan mb-4 pb-4 border-b border-vintage-tan/20">
                  <span className="flex items-center gap-1">
                    <Eye className="h-4 w-4" />
                    {video.view_count} {t('videos.views', 'lượt xem')}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {video.created_at}
                  </span>
                  {video.duration && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {video.duration}
                    </span>
                  )}
                </div>
                
                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-olive/10 text-vintage-olive border border-vintage-olive/20">
                    <Globe className="h-3 w-3 mr-1" />
                    {video.language_display}
                  </span>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-blue/10 text-vintage-blue border border-vintage-blue/20">
                    <BarChart2 className="h-3 w-3 mr-1" />
                    {video.level_display}
                  </span>
                  {video.is_featured && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-tan/20 text-vintage-dark border border-vintage-tan/30">
                      <Star className="h-3 w-3 mr-1" />
                      {t('common.featured', 'Nổi bật')}
                    </span>
                  )}
                </div>
                
                {/* Description */}
                {video.description && (
                  <div className="prose max-w-none text-vintage-dark/80 font-serif leading-relaxed whitespace-pre-wrap">
                    {video.description}
                  </div>
                )}
                
                {/* Actions */}
                <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-vintage-tan/20">
                  <a 
                    href={video.youtube_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-4 py-2 bg-vintage-olive hover:bg-vintage-brown text-white rounded-lg font-bold text-sm transition"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    {t('videos.watchOnYouTube', 'Xem trên YouTube')}
                  </a>
                  <Button 
                    onClick={() => navigate('/video')}
                    variant="outline"
                    className="border-vintage-tan text-vintage-dark hover:bg-vintage-cream"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    {t('common.back', 'Quay lại')}
                  </Button>
                  
                  {/* Bookmark Button */}
                  {user ? (
                    <Button
                      variant="outline"
                      className={`border-2 ${video.is_bookmarked 
                        ? 'border-vintage-olive bg-vintage-olive/10 text-vintage-olive hover:bg-vintage-olive/20' 
                        : 'border-vintage-tan text-vintage-tan hover:bg-vintage-cream hover:border-vintage-brown hover:text-vintage-brown'
                      }`}
                    >
                      {video.is_bookmarked ? (
                        <>
                          <BookmarkCheck className="h-4 w-4 mr-2" />
                          {t('videos.saved', 'Đã lưu')}
                        </>
                      ) : (
                        <>
                          <Bookmark className="h-4 w-4 mr-2" />
                          {t('videos.save', 'Lưu video')}
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      asChild
                      variant="outline"
                      className="border-2 border-vintage-tan text-vintage-tan hover:bg-vintage-cream"
                    >
                      <Link to={`/dang-nhap?next=/video/${video.slug}`}>
                        <Bookmark className="h-4 w-4 mr-2" />
                        {t('videos.loginToSave', 'Đăng nhập để lưu')}
                      </Link>
                    </Button>
                  )}
                </div>
              </div>
            </div>
            
            {/* Sidebar - Related Videos */}
            <aside className="lg:w-1/3">
              <div className="bg-white rounded-xl border-2 border-vintage-tan/30 p-4">
                <h2 className="text-lg font-serif font-bold text-vintage-dark mb-4 flex items-center gap-2">
                  <VideoIcon className="h-5 w-5 text-vintage-olive" />
                  {t('videos.related', 'Video liên quan')}
                </h2>
                
                {relatedVideos.length > 0 ? (
                  <div className="space-y-4">
                    {relatedVideos.map((related: Video) => (
                      <Link 
                        key={related.id}
                        to={`/video/${related.slug}`}
                        className="flex gap-3 group hover:bg-vintage-cream/50 p-2 rounded-lg transition"
                      >
                        {/* Thumbnail */}
                        <div className="relative flex-shrink-0 w-40">
                          <img 
                            src={related.thumbnail} 
                            alt={related.title}
                            className="w-full aspect-video object-cover rounded-lg"
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 rounded-lg transition">
                            <Play className="h-8 w-8 text-white opacity-80 group-hover:opacity-100 transition" />
                          </div>
                          {related.duration && (
                            <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                              {related.duration}
                            </span>
                          )}
                        </div>
                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-vintage-dark text-sm line-clamp-2 group-hover:text-vintage-brown transition">
                            {related.title}
                          </h3>
                          <p className="text-xs text-vintage-tan mt-1">
                            {related.view_count} {t('videos.views', 'lượt xem')}
                          </p>
                          <p className="text-xs text-vintage-tan/70 mt-0.5">
                            {related.level_display}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-vintage-tan text-center py-4">
                    {t('videos.noRelated', 'Không có video liên quan')}
                  </p>
                )}
                
                {/* View all link */}
                <Link 
                  to="/video" 
                  className="block mt-4 text-center text-sm font-bold text-vintage-brown hover:text-vintage-olive transition"
                >
                  {t('videos.viewAll', 'Xem tất cả video')} →
                </Link>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </>
  );
}

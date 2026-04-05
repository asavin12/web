import { Link } from 'react-router-dom';
import type { StreamMedia } from '@/api/mediastream';
import { Card, CardContent } from '@/components/ui/Card';
import { Play, Music, Eye, Globe, BarChart2, Film } from 'lucide-react';

export default function StreamMediaCard({ media }: { media: StreamMedia }) {
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
              media.storage_type === 'youtube'
                ? 'bg-red-600/90 text-white'
                : isVideo
                  ? 'bg-vintage-olive/90 text-white'
                  : 'bg-vintage-blue/90 text-white'
            }`}>
              {media.storage_type === 'youtube' ? 'YOUTUBE' : isVideo ? 'VIDEO' : 'AUDIO'}
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

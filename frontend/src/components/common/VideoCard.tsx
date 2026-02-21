import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PlayCircle, Eye, Clock, Globe, BarChart2, Star } from 'lucide-react';
import type { Video } from '@/types';

interface VideoCardProps {
  video: Video;
}

const VideoCard: React.FC<VideoCardProps> = ({ video }) => {
  const { t } = useTranslation();

  return (
    <Link 
      to={`/video/${video.slug}`}
      className="group relative bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-vintage-tan/30"
    >
      <div className="relative">
        <img
          src={video.thumbnail || `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`}
          alt={video.title}
          className="w-full h-48 object-cover transform group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-vintage-dark/20 group-hover:bg-vintage-brown/40 transition-colors duration-300 flex items-center justify-center">
          <PlayCircle className="h-14 w-14 text-white drop-shadow-lg transform group-hover:scale-110 transition-transform duration-300" />
        </div>
        
        {/* Duration badge */}
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-vintage-dark/80 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {video.duration}
          </div>
        )}
        
        {/* Featured badge */}
        {video.is_featured && (
          <div className="absolute top-2 left-2 bg-vintage-accent text-white text-xs px-2 py-1 rounded flex items-center gap-1">
            <Star className="h-3 w-3" />
            {t('media.featured')}
          </div>
        )}
      </div>
      
      <div className="p-4 bg-vintage-cream/20">
        <h3 className="text-lg font-serif font-bold text-vintage-dark line-clamp-2 mb-2 group-hover:text-vintage-blue transition-colors leading-tight">
          {video.title}
        </h3>
        
        <div className="flex items-center flex-wrap gap-2 mb-3">
          {video.language_display && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-vintage-cream text-vintage-dark rounded-full">
              <Globe className="h-3 w-3" />
              {video.language_display}
            </span>
          )}
          {video.level_display && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-vintage-blue/10 text-vintage-blue rounded-full">
              <BarChart2 className="h-3 w-3" />
              {video.level_display}
            </span>
          )}
        </div>
        
        <div className="flex items-center justify-between border-t border-vintage-tan/20 pt-3 text-xs text-vintage-dark/60 font-medium">
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {video.view_count.toLocaleString()} {t('media.views')}
          </span>
        </div>
      </div>
    </Link>
  );
};

export default VideoCard;

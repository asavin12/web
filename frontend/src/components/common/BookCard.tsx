import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Resource } from '@/types';

interface BookCardProps {
  resource: Resource;
  compact?: boolean;
}

const BookCard: React.FC<BookCardProps> = ({ resource, compact = false }) => {
  const { t } = useTranslation();
  const thumbnail = resource.cover_image || resource.cover_url || 'https://picsum.photos/seed/' + resource.id + '/200/280';
  const author = resource.uploaded_by?.username || t('common.unknown', 'Unknown');
  
  return (
    <Link to={`/tai-lieu/${resource.slug || resource.id}`} className="group flex flex-col items-center cursor-pointer">
      {/* Book Container with 3D Effect */}
      <div className={`relative ${compact ? 'w-24 h-32 md:w-28 md:h-40' : 'w-28 h-40 md:w-32 md:h-44 lg:w-36 lg:h-52'} perspective-1000`}>
        {/* Book wrapper for 3D tilt */}
        <div className="relative w-full h-full transform-gpu group-hover:-translate-y-1 group-hover:rotate-y-2 transition-all duration-500 ease-out preserve-3d">
          
          {/* Book Spine - Left side 3D effect */}
          <div className="absolute left-0 top-1 bottom-1 w-2.5 md:w-3 bg-gradient-to-r from-vintage-brown/90 via-vintage-brown/70 to-vintage-brown/50 rounded-l-sm z-10 shadow-inner">
            {/* Spine highlight */}
            <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent rounded-l-sm"></div>
            {/* Spine lines */}
            <div className="absolute left-0.5 top-2 bottom-2 w-px bg-black/20"></div>
            <div className="absolute right-0.5 top-0 bottom-0 w-px bg-black/30"></div>
          </div>
          
          {/* Book Cover */}
          <div className="absolute left-2 md:left-2.5 right-0 top-0 bottom-0 rounded-r-sm overflow-hidden shadow-[2px_2px_8px_rgba(0,0,0,0.15),4px_4px_16px_rgba(0,0,0,0.1)] group-hover:shadow-[4px_4px_12px_rgba(0,0,0,0.2),8px_8px_24px_rgba(0,0,0,0.15)] transition-shadow duration-500">
            {/* Cover Image */}
            <img 
              src={thumbnail} 
              alt={resource.title} 
              className="w-full h-full object-cover transform scale-100 group-hover:scale-105 transition-transform duration-700" 
            />
            
            {/* Paper texture overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-black/10 pointer-events-none"></div>
            
            {/* Top/Bottom page effect */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-b from-vintage-cream/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-t from-vintage-tan/40 to-transparent"></div>
            
            {/* Right edge (pages) */}
            <div className="absolute right-0 top-1 bottom-1 w-1 bg-gradient-to-l from-vintage-cream/80 via-vintage-cream/60 to-transparent">
              <div className="absolute inset-y-0 right-0 w-px bg-vintage-tan/50"></div>
            </div>
            
            {/* Hover glow */}
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
            
            {/* Language badge - smaller */}
            {resource.language && (
              <div className="absolute top-1 right-1 bg-vintage-cream/95 text-vintage-olive text-[8px] md:text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm uppercase tracking-wide">
                {resource.language}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Book Info */}
      <div className={`mt-2 md:mt-3 space-y-1 text-center ${compact ? 'max-w-24 md:max-w-28' : 'max-w-28 md:max-w-32 lg:max-w-36'}`}>
        <h3 className={`${compact ? 'text-xs md:text-sm' : 'text-sm md:text-base'} font-serif font-semibold text-vintage-dark leading-tight group-hover:text-vintage-brown transition-colors line-clamp-2`}>
          {resource.title}
        </h3>
        <p className={`${compact ? 'text-[9px] md:text-[10px]' : 'text-[10px] md:text-xs'} text-vintage-olive/80 truncate`}>{author}</p>
      </div>
    </Link>
  );
};

export default BookCard;

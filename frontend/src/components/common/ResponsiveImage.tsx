/**
 * ResponsiveImage component
 * 
 * Renders images with srcset for automatic device detection and optimal loading.
 * Supports WebP images with responsive breakpoints (480w, 768w, 1200w, 1920w).
 * Falls back to single src if no srcset data is available.
 * 
 * Usage:
 *   <ResponsiveImage
 *     src={article.featured_image}
 *     srcset={article.cover_image_srcset}
 *     alt={article.title}
 *     loading="lazy"
 *     className="w-full h-full object-cover"
 *   />
 */

import React from 'react';

// Responsive breakpoint widths matching backend RESPONSIVE_SIZES
const RESPONSIVE_WIDTHS: Record<string, number> = {
  sm: 480,
  md: 768,
  lg: 1200,
  xl: 1920,
};

interface ResponsiveImageProps {
  /** Primary image URL (fallback) */
  src: string | null | undefined;
  /** Responsive image URLs from cover_image_srcset */
  srcset?: Record<string, string> | null;
  /** Alt text for accessibility */
  alt: string;
  /** CSS class names */
  className?: string;
  /** Loading strategy */
  loading?: 'lazy' | 'eager';
  /** Sizes attribute for responsive rendering */
  sizes?: string;
  /** Whether this is a hero/featured image (uses larger default sizes) */
  isHero?: boolean;
  /** Schema.org itemProp */
  itemProp?: string;
  /** Additional HTML attributes */
  style?: React.CSSProperties;
  /** Click handler */
  onClick?: () => void;
}

/**
 * Build srcset string from responsive image data.
 * Format: "url 480w, url 768w, url 1200w, url 1920w"
 */
function buildSrcSet(srcset: Record<string, string> | null | undefined): string | undefined {
  if (!srcset || Object.keys(srcset).length === 0) return undefined;

  const entries: string[] = [];
  for (const [size, url] of Object.entries(srcset)) {
    const width = RESPONSIVE_WIDTHS[size];
    if (width && url) {
      entries.push(`${url} ${width}w`);
    }
  }

  return entries.length > 0 ? entries.join(', ') : undefined;
}

/**
 * Get default sizes attribute based on usage context.
 * - Hero: full width up to 1200px, then capped
 * - Card: smaller columns on desktop
 */
function getDefaultSizes(isHero: boolean): string {
  if (isHero) {
    return '(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px';
  }
  return '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw';
}

const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  srcset,
  alt,
  className = '',
  loading = 'lazy',
  sizes,
  isHero = false,
  itemProp,
  style,
  onClick,
}) => {
  if (!src) return null;

  const srcSetStr = buildSrcSet(srcset);
  const sizesStr = sizes || (srcSetStr ? getDefaultSizes(isHero) : undefined);

  return (
    <img
      src={src}
      srcSet={srcSetStr}
      sizes={sizesStr}
      alt={alt}
      className={className}
      loading={loading}
      decoding={loading === 'lazy' ? 'async' : 'auto'}
      itemProp={itemProp}
      style={style}
      onClick={onClick}
    />
  );
};

export default ResponsiveImage;

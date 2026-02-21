/**
 * Unified Article Detail Page
 * Shared detail page component for News, Knowledge, and Tools articles
 * SEO-optimized with consistent layout
 */

import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import DOMPurify from 'dompurify';
import { 
  Newspaper, BookOpen, Wrench, Calendar, Eye, User, ChevronLeft, 
  Share2, BookmarkPlus, Clock, GraduationCap, Languages, Tag, CheckCircle
} from 'lucide-react';
import { getNewsArticleBySlug, getRelatedNews, NewsArticle } from '@/api/news';
import { getKnowledgeArticleBySlug, getKnowledgeArticles, KnowledgeArticle } from '@/api/knowledge';
import { getToolBySlug, getTools, Tool } from '@/api/tools';
import { Breadcrumb } from '@/components/common/Breadcrumb';
import ResponsiveImage from '@/components/common/ResponsiveImage';

// Content type definitions
export type ContentType = 'news' | 'knowledge' | 'tools';

interface ArticleDetailPageProps {
  contentType: ContentType;
}

// Unified article type - includes Tool now
type UnifiedArticle = NewsArticle | KnowledgeArticle | Tool;

// Content type configurations
const contentConfig = {
  news: {
    icon: Newspaper,
    basePath: '/tin-tuc',
    titleKey: 'news.title',
    defaultTitle: 'Tin tức',
    notFoundKey: 'news.notFound',
    defaultNotFound: 'Bài viết không tồn tại',
    backKey: 'news.backToList',
    defaultBack: 'Quay lại danh sách tin tức',
    iconColor: 'text-vintage-olive',
  },
  knowledge: {
    icon: BookOpen,
    basePath: '/kien-thuc',
    titleKey: 'knowledge.title',
    defaultTitle: 'Kiến thức',
    notFoundKey: 'knowledge.notFound',
    defaultNotFound: 'Bài viết không tồn tại',
    backKey: 'knowledge.backToList',
    defaultBack: 'Quay lại danh sách kiến thức',
    iconColor: 'text-vintage-brown',
  },
  tools: {
    icon: Wrench,
    basePath: '/cong-cu',
    titleKey: 'tools.title',
    defaultTitle: 'Công cụ',
    notFoundKey: 'tools.notFound',
    defaultNotFound: 'Công cụ không tồn tại',
    backKey: 'tools.backToList',
    defaultBack: 'Quay lại danh sách công cụ',
    iconColor: 'text-vintage-blue',
  },
};

// Calculate reading time (avg 200 words/min)
const calculateReadingTime = (content: string) => {
  const text = content.replace(/<[^>]*>/g, '');
  const words = text.split(/\s+/).length;
  return Math.max(1, Math.ceil(words / 200));
};

export default function ArticleDetailPage({ contentType }: ArticleDetailPageProps) {
  const { t, i18n } = useTranslation();
  const { categorySlug, slug } = useParams<{ categorySlug: string; slug: string }>();

  const config = contentConfig[contentType];
  const Icon = config.icon;

  // Memoize dateLocale to prevent unnecessary re-renders
  const dateLocale = i18n.language === 'de' ? 'de-DE' : i18n.language === 'en' ? 'en-US' : 'vi-VN';

  // Fetch article with useQuery
  const { data: article = null, isLoading: loading, error: queryError } = useQuery({
    queryKey: ['article', contentType, slug],
    queryFn: async () => {
      if (!slug) return null;
      if (contentType === 'news') return getNewsArticleBySlug(slug);
      if (contentType === 'knowledge') return getKnowledgeArticleBySlug(slug);
      if (contentType === 'tools') return getToolBySlug(slug);
      return null;
    },
    enabled: !!slug,
    retry: 1,
  });

  // Fetch related articles
  const { data: relatedArticles = [] } = useQuery({
    queryKey: ['relatedArticles', contentType, slug, article?.id],
    queryFn: async (): Promise<UnifiedArticle[]> => {
      if (!article || !slug) return [];
      try {
        if (contentType === 'news') {
          const related = await getRelatedNews(slug, 4);
          return Array.isArray(related) ? related : [];
        }
        if (contentType === 'knowledge') {
          const knowledgeArticle = article as KnowledgeArticle;
          if (knowledgeArticle.language || knowledgeArticle.level) {
            const related = await getKnowledgeArticles({
              language: knowledgeArticle.language || undefined,
              level: knowledgeArticle.level || undefined,
              page_size: 5
            });
            return related.results.filter(a => a.id !== article.id).slice(0, 4);
          }
          return [];
        }
        if (contentType === 'tools') {
          const toolData = article as Tool;
          const related = await getTools({
            category: toolData.category?.slug,
            page_size: 5
          });
          return related.results.filter(t => t.id !== article.id).slice(0, 4) as unknown as UnifiedArticle[];
        }
        return [];
      } catch {
        return [];
      }
    },
    enabled: !!article && !!slug,
    staleTime: 5 * 60 * 1000,
  });

  // Derive error state
  const error = queryError 
    ? ((queryError as { response?: { status?: number } }).response?.status === 404 ? 'notFound' : 'serverError')
    : null;

  const handleShare = async () => {
    const url = window.location.href;
    // Get title based on article type (Tool uses 'name', others use 'title')
    const shareTitle = article ? ('title' in article ? article.title : (article as Tool).name) : '';
    const shareText = article ? ('excerpt' in article ? article.excerpt : (article as Tool).description) : '';
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareTitle,
          text: shareText,
          url
        });
      } catch {
        // User cancelled
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        alert(t('common.linkCopied', 'Đã sao chép liên kết!'));
      } catch {
        // Clipboard not available
      }
    }
  };

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="animate-pulse space-y-6">
            <div className="h-6 bg-vintage-tan/20 rounded w-1/4"></div>
            <div className="h-10 bg-vintage-tan/20 rounded w-3/4"></div>
            <div className="flex gap-4">
              <div className="h-4 bg-vintage-tan/20 rounded w-20"></div>
              <div className="h-4 bg-vintage-tan/20 rounded w-24"></div>
              <div className="h-4 bg-vintage-tan/20 rounded w-16"></div>
            </div>
            <div className="h-80 bg-vintage-tan/20 rounded-2xl"></div>
            <div className="space-y-3">
              <div className="h-4 bg-vintage-tan/20 rounded"></div>
              <div className="h-4 bg-vintage-tan/20 rounded w-5/6"></div>
              <div className="h-4 bg-vintage-tan/20 rounded w-4/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Helper to get unified article properties (Tool uses 'name', others use 'title')
  const isTool = contentType === 'tools';
  const toolArticle = isTool ? article as Tool : null;
  
  const getArticleTitle = () => {
    if (isTool && toolArticle) return toolArticle.name;
    return (article as NewsArticle | KnowledgeArticle).title;
  };
  
  const getArticleExcerpt = () => {
    if (isTool && toolArticle) return toolArticle.excerpt || toolArticle.description;
    return (article as NewsArticle | KnowledgeArticle).excerpt;
  };
  
  const getArticleContent = () => {
    if (isTool && toolArticle) return toolArticle.content || toolArticle.description;
    return (article as NewsArticle | KnowledgeArticle).content;
  };
  
  const getArticleFeaturedImage = () => {
    if (isTool && toolArticle) return toolArticle.featured_image || toolArticle.cover_image;
    return (article as NewsArticle | KnowledgeArticle).featured_image;
  };
  
  const getArticleSrcset = (): Record<string, string> | null | undefined => {
    if (isTool && toolArticle) return toolArticle.cover_image_srcset;
    return (article as NewsArticle | KnowledgeArticle).cover_image_srcset;
  };
  
  const getAuthorInfo = () => {
    if (isTool && toolArticle) {
      return toolArticle.author_name ? {
        username: toolArticle.author_name,
        avatar: toolArticle.author_avatar || null
      } : null;
    }
    return (article as NewsArticle | KnowledgeArticle).author;
  };
  
  const articleTitle = getArticleTitle();
  const articleExcerpt = getArticleExcerpt();
  const articleContent = getArticleContent() || '';
  const articleFeaturedImage = getArticleFeaturedImage();
  const articleSrcset = getArticleSrcset();
  const authorInfo = getAuthorInfo();
  // Error State
  if (error || !article) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white flex items-center justify-center">
        <div className="text-center px-4">
          <Icon className={`h-20 w-20 mx-auto ${config.iconColor} opacity-50 mb-6`} />
          <h1 className="text-3xl font-serif font-bold text-vintage-dark mb-4">
            {error === 'notFound' 
              ? t(config.notFoundKey, config.defaultNotFound)
              : t('common.serverError', 'Đã xảy ra lỗi')
            }
          </h1>
          <p className="text-vintage-tan mb-8">
            {error === 'notFound'
              ? t('common.notFoundHint', 'Nội dung này có thể đã bị xóa hoặc URL không đúng')
              : t('common.tryAgainLater', 'Vui lòng thử lại sau')
            }
          </p>
          <Link
            to={config.basePath}
            className="inline-flex items-center gap-2 px-6 py-3 bg-vintage-olive text-white rounded-xl hover:bg-vintage-brown transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
            {t(config.backKey, config.defaultBack)}
          </Link>
        </div>
      </div>
    );
  }

  const readingTime = calculateReadingTime(articleContent);
  const isKnowledge = contentType === 'knowledge';
  const knowledgeArticle = isKnowledge ? article as KnowledgeArticle : null;

  // Build JSON-LD schema for SEO
  const schemaData = {
    "@context": "https://schema.org",
    "@type": (isKnowledge && knowledgeArticle?.schema_type) || "Article",
    "headline": articleTitle,
    "description": ('meta_description' in article && article.meta_description) || articleExcerpt,
    "image": ('og_image' in article && article.og_image) || articleFeaturedImage,
    ...(authorInfo && {
      "author": {
        "@type": "Person",
        "name": authorInfo.username
      }
    }),
    "publisher": {
      "@type": "Organization",
      "name": "UnstressVN",
      "logo": {
        "@type": "ImageObject",
        "url": `${window.location.origin}/logo.png`
      }
    },
    "datePublished": article.published_at,
    "dateModified": article.updated_at,
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": window.location.href
    }
  };

  // BreadcrumbList schema
  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": t('nav.home', 'Trang chủ'),
        "item": window.location.origin
      },
      {
        "@type": "ListItem",
        "position": 2,
        "name": t(config.titleKey, config.defaultTitle),
        "item": `${window.location.origin}${config.basePath}`
      },
      {
        "@type": "ListItem",
        "position": 3,
        "name": articleTitle,
        "item": window.location.href
      }
    ]
  };

  return (
    <>
      <Helmet>
        <title>{('meta_title' in article && article.meta_title) || articleTitle} | UnstressVN</title>
        <meta name="description" content={('meta_description' in article && article.meta_description) || articleExcerpt} />
        
        {/* Open Graph */}
        <meta property="og:type" content="article" />
        <meta property="og:title" content={articleTitle} />
        <meta property="og:description" content={('meta_description' in article && article.meta_description) || articleExcerpt} />
        <meta property="og:url" content={window.location.href} />
        {(('og_image' in article && article.og_image) || articleFeaturedImage) && (
          <meta property="og:image" content={('og_image' in article && article.og_image) || articleFeaturedImage || ''} />
        )}
        <meta property="article:published_time" content={article.published_at} />
        <meta property="article:modified_time" content={article.updated_at} />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={articleTitle} />
        <meta name="twitter:description" content={('meta_description' in article && article.meta_description) || articleExcerpt} />
        
        {/* Canonical */}
        {'canonical_url' in article && article.canonical_url && <link rel="canonical" href={article.canonical_url} />}
        
        {/* Schema.org */}
        <script type="application/ld+json">
          {JSON.stringify(schemaData)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify(breadcrumbSchema)}
        </script>
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        {/* Breadcrumb Navigation */}
        <div className="bg-white border-b border-vintage-tan/20">
          <div className="container-responsive py-4">
            <Breadcrumb items={[
              { label: t(config.titleKey, config.defaultTitle), href: config.basePath },
              ...(article.category ? [{ label: article.category.name, href: `${config.basePath}/${article.category.slug}` }] : []),
              { label: articleTitle },
            ]} />
          </div>
        </div>

        {/* Main Article Content */}
        <article className="container-responsive py-8" itemScope itemType="https://schema.org/Article">
          <div className="bg-white rounded-2xl shadow-lg border-2 border-vintage-tan/30 overflow-hidden">
            <div className="p-6 md:p-8 lg:p-10">
          {/* Article Header */}
          <header className="mb-8">
            {/* Tags/Badges */}
            <div className="flex flex-wrap items-center gap-3 mb-5">
              {/* Knowledge-specific badges */}
              {isKnowledge && knowledgeArticle && (
                <>
                  {knowledgeArticle.level_display && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-vintage-olive text-white rounded-full text-sm font-medium">
                      <GraduationCap className="h-4 w-4" />
                      {knowledgeArticle.level_display}
                    </span>
                  )}
                  {knowledgeArticle.language_display && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-vintage-brown text-white rounded-full text-sm font-medium">
                      <Languages className="h-4 w-4" />
                      {knowledgeArticle.language_display}
                    </span>
                  )}
                </>
              )}
              
              {/* Category badge */}
              {article.category && (
                <Link
                  to={`${config.basePath}/${article.category.slug}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-vintage-tan/20 text-vintage-dark rounded-full text-sm font-medium hover:bg-vintage-tan/30 transition-colors"
                >
                  <Tag className="h-4 w-4" />
                  {article.category.name}
                </Link>
              )}
              
              {/* Featured badge */}
              {article.is_featured && (
                <span className="px-3 py-1.5 bg-vintage-brown text-white rounded-full text-sm font-medium">
                  {t('common.featured', 'Nổi bật')}
                </span>
              )}
            </div>

            {/* Title */}
            <h1 
              className="text-3xl md:text-4xl lg:text-5xl font-serif font-bold text-vintage-dark mb-6 leading-tight"
              itemProp="headline"
            >
              {articleTitle}
            </h1>

            {/* Excerpt/Summary */}
            {articleExcerpt && (
              <p className="text-lg text-vintage-dark/70 mb-6 leading-relaxed" itemProp="description">
                {articleExcerpt}
              </p>
            )}

            {/* Meta Information */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-vintage-tan border-b border-vintage-tan/20 pb-6">
              {authorInfo && (
                <div className="flex items-center gap-2" itemProp="author" itemScope itemType="https://schema.org/Person">
                  <div className="w-8 h-8 rounded-full bg-vintage-olive/10 flex items-center justify-center overflow-hidden">
                    {authorInfo.avatar ? (
                      <img 
                        src={authorInfo.avatar} 
                        alt={authorInfo.username}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User className="h-4 w-4 text-vintage-olive" />
                    )}
                  </div>
                  <span itemProp="name" className="font-medium text-vintage-dark">{authorInfo.username}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <time dateTime={article.published_at} itemProp="datePublished">
                  {new Date(article.published_at || article.created_at).toLocaleDateString(dateLocale, {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </time>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>{readingTime} {t('common.minRead', 'phút đọc')}</span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                <span>{article.view_count.toLocaleString()} {t('common.views', 'lượt xem')}</span>
              </div>
            </div>
          </header>

          {/* Featured Image */}
          {articleFeaturedImage && (
            <figure className="mb-10">
              <div className="relative rounded-2xl overflow-hidden shadow-xl">
                <ResponsiveImage
                  src={articleFeaturedImage}
                  srcset={articleSrcset}
                  alt={articleTitle}
                  className="w-full h-auto max-h-[500px] object-cover"
                  itemProp="image"
                  loading="eager"
                  isHero
                />
              </div>
            </figure>
          )}

          {/* Article Content — SEO-optimized body */}
          <section className="article-body mb-12">
            <div 
              className="prose prose-lg max-w-none
                prose-headings:font-serif prose-headings:text-vintage-dark prose-headings:font-bold prose-headings:scroll-mt-20
                prose-h2:text-2xl prose-h2:md:text-3xl prose-h2:mt-12 prose-h2:mb-5 prose-h2:border-b prose-h2:border-vintage-tan/20 prose-h2:pb-3 prose-h2:relative
                prose-h3:text-xl prose-h3:md:text-2xl prose-h3:mt-10 prose-h3:mb-4
                prose-h4:text-lg prose-h4:md:text-xl prose-h4:mt-8 prose-h4:mb-3 prose-h4:text-vintage-dark/90
                prose-p:text-base prose-p:md:text-lg prose-p:text-vintage-dark/85 prose-p:leading-[1.8] prose-p:mb-5 prose-p:tracking-wide
                prose-a:text-vintage-olive prose-a:font-medium prose-a:underline prose-a:underline-offset-4 prose-a:decoration-vintage-olive/30 hover:prose-a:decoration-vintage-olive hover:prose-a:text-vintage-brown prose-a:transition-colors
                prose-strong:text-vintage-dark prose-strong:font-semibold
                prose-em:text-vintage-dark/75
                prose-ul:my-5 prose-ul:space-y-2 prose-ol:my-5 prose-ol:space-y-2
                prose-li:text-vintage-dark/85 prose-li:leading-[1.8] prose-li:marker:text-vintage-olive
                prose-img:rounded-2xl prose-img:shadow-xl prose-img:my-10 prose-img:w-full
                prose-figure:my-10
                prose-figcaption:text-center prose-figcaption:text-sm prose-figcaption:text-vintage-tan prose-figcaption:mt-3 prose-figcaption:italic
                prose-blockquote:border-l-4 prose-blockquote:border-vintage-olive prose-blockquote:bg-gradient-to-r prose-blockquote:from-vintage-cream/80 prose-blockquote:to-transparent prose-blockquote:py-4 prose-blockquote:px-6 prose-blockquote:rounded-r-xl prose-blockquote:italic prose-blockquote:my-8 prose-blockquote:shadow-sm prose-blockquote:text-vintage-dark/80
                prose-code:text-vintage-olive prose-code:bg-vintage-tan/10 prose-code:px-2 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-code:font-mono
                prose-pre:bg-vintage-dark prose-pre:rounded-xl prose-pre:shadow-lg prose-pre:my-8
                prose-table:my-8 prose-table:w-full prose-table:rounded-xl prose-table:overflow-hidden prose-table:shadow-sm
                prose-thead:bg-vintage-olive/10
                prose-th:text-vintage-dark prose-th:font-semibold prose-th:px-4 prose-th:py-3 prose-th:text-left
                prose-td:px-4 prose-td:py-3 prose-td:border-b prose-td:border-vintage-tan/10 prose-td:text-vintage-dark/80
                prose-hr:border-vintage-tan/20 prose-hr:my-10
                prose-video:rounded-2xl prose-video:shadow-xl prose-video:my-10"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(articleContent, { ADD_TAGS: ['iframe', 'nav'], ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'scrolling', 'target', 'itemProp'] }) }}
              itemProp="articleBody"
            />
          </section>

          {/* Level Progress Navigation (Knowledge only) */}
          {isKnowledge && knowledgeArticle && (
            <div className="bg-gradient-to-r from-vintage-olive/10 to-vintage-brown/10 rounded-2xl p-6 mb-8">
              <h3 className="font-semibold text-vintage-dark mb-4 flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-vintage-olive" />
                {t('knowledge.levelProgress', 'Lộ trình học theo cấp độ')}
              </h3>
              <div className="flex gap-2 flex-wrap">
                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((level) => (
                  <Link
                    key={level}
                    to={`/kien-thuc?level=${level}`}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      level === knowledgeArticle.level
                        ? 'bg-vintage-olive text-white shadow-md'
                        : 'bg-white text-vintage-dark hover:bg-vintage-tan/20 hover:shadow-sm'
                    }`}
                  >
                    {level === knowledgeArticle.level && <CheckCircle className="h-4 w-4 inline mr-1" />}
                    {level}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between py-6 border-t border-b border-vintage-tan/20">
            <div className="flex items-center gap-3">
              <button
                onClick={handleShare}
                className="flex items-center gap-2 px-4 py-2.5 bg-vintage-olive text-white rounded-xl hover:bg-vintage-olive/90 transition-colors shadow-sm"
              >
                <Share2 className="h-5 w-5" />
                {t('common.share', 'Chia sẻ')}
              </button>
              <button className="flex items-center gap-2 px-4 py-2.5 bg-vintage-tan/20 text-vintage-dark rounded-xl hover:bg-vintage-tan/30 transition-colors">
                <BookmarkPlus className="h-5 w-5" />
                {t('common.save', 'Lưu lại')}
              </button>
            </div>
            <Link
              to={config.basePath}
              className="flex items-center gap-2 text-vintage-olive hover:text-vintage-brown transition-colors font-medium"
            >
              <ChevronLeft className="h-5 w-5" />
              {t(config.backKey, config.defaultBack)}
            </Link>
          </div>


            </div>
          </div>
        </article>

        {/* Related Articles */}
        {Array.isArray(relatedArticles) && relatedArticles.length > 0 && (
          <section className="bg-white py-12 border-t border-vintage-tan/10">
            <div className="container-responsive">
              <h2 className="text-2xl font-serif font-bold text-vintage-dark mb-8 flex items-center gap-3">
                <Icon className={`h-6 w-6 ${config.iconColor}`} />
                {t('common.relatedArticles', 'Bài viết liên quan')}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {relatedArticles.map((related) => {
                  // Handle both NewsArticle/KnowledgeArticle (title) and Tool (name)
                  const relatedTitle = 'title' in related ? related.title : (related as unknown as Tool).name;
                  const relatedImage = 'featured_image' in related ? related.featured_image : 
                    ((related as unknown as Tool).featured_image || (related as unknown as Tool).cover_image);
                  const relatedSrcset = 'cover_image_srcset' in related ? 
                    (related as NewsArticle | KnowledgeArticle).cover_image_srcset : 
                    (related as unknown as Tool).cover_image_srcset;
                  const relatedDate = related.published_at || related.created_at;
                  
                  return (
                    <Link
                      key={related.id}
                      to={`${config.basePath}/${related.category?.slug || categorySlug || 'bai-viet'}/${related.slug}`}
                      className="group bg-vintage-cream rounded-xl overflow-hidden hover:shadow-xl transition-all duration-300 border border-transparent hover:border-vintage-olive/20"
                    >
                      <div className="relative h-36 overflow-hidden">
                        {relatedImage ? (
                          <ResponsiveImage
                            src={relatedImage}
                            srcset={relatedSrcset}
                            alt={relatedTitle}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full bg-vintage-olive/10 flex items-center justify-center">
                            <Icon className={`h-10 w-10 ${config.iconColor} opacity-40`} />
                          </div>
                        )}
                        {isKnowledge && 'level' in related && (
                          <div className="absolute top-2 left-2 flex gap-1.5">
                            <span className="px-2 py-0.5 bg-vintage-olive text-white text-xs font-medium rounded">
                              {related.level}
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="p-4">
                        <h3 className="font-medium text-vintage-dark line-clamp-2 group-hover:text-vintage-olive transition-colors leading-snug">
                          {relatedTitle}
                        </h3>
                        <div className="flex items-center gap-3 text-xs text-vintage-tan mt-3">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(relatedDate).toLocaleDateString(dateLocale)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye className="h-3 w-3" />
                            {related.view_count}
                          </span>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </section>
        )}
      </div>
    </>
  );
}

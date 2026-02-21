/**
 * Unified Articles Page
 * Shared page component for News, Knowledge, and Tools articles
 * Supports different content types with same layout
 */

import { Link, useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Helmet } from 'react-helmet-async';
import { useQuery } from '@tanstack/react-query';
import { 
  Newspaper, BookOpen, Wrench, Calendar, Eye, 
  Search, GraduationCap, Languages, X 
} from 'lucide-react';
import { getNewsArticles, getNewsCategories, getNewsByCategory, NewsArticle, NewsCategory } from '@/api/news';
import ResponsiveImage from '@/components/common/ResponsiveImage';
import { 
  getKnowledgeArticles, getKnowledgeCategories, getKnowledgeByCategory,
  KnowledgeArticle, KnowledgeCategory, getLanguageChoices, getLevelChoices 
} from '@/api/knowledge';
import { getToolCategories, getTools, ToolCategory, Tool } from '@/api/tools';
import { Breadcrumb } from '@/components/common/Breadcrumb';

// Content type definitions
export type ContentType = 'news' | 'knowledge' | 'tools';

interface ArticlesPageProps {
  contentType: ContentType;
}

// Unified article type
type UnifiedArticle = NewsArticle | KnowledgeArticle;
type UnifiedCategory = NewsCategory | KnowledgeCategory;

// Content type configurations
const contentConfig = {
  news: {
    icon: Newspaper,
    basePath: '/tin-tuc',
    titleKey: 'news.title',
    defaultTitle: 'Tin tức',
    descKey: 'news.description',
    defaultDesc: 'Tin tức và bài viết mới nhất về học ngoại ngữ',
    allKey: 'news.all',
    defaultAll: 'Tất cả',
    iconColor: 'text-vintage-olive',
  },
  knowledge: {
    icon: BookOpen,
    basePath: '/kien-thuc',
    titleKey: 'knowledge.title',
    defaultTitle: 'Kiến thức',
    descKey: 'knowledge.description',
    defaultDesc: 'Kiến thức học ngoại ngữ từ cơ bản đến nâng cao',
    allKey: 'knowledge.all',
    defaultAll: 'Tất cả',
    iconColor: 'text-vintage-brown',
  },
  tools: {
    icon: Wrench,
    basePath: '/cong-cu',
    titleKey: 'tools.title',
    defaultTitle: 'Công cụ',
    descKey: 'tools.description',
    defaultDesc: 'Bộ sưu tập công cụ hỗ trợ học ngôn ngữ',
    allKey: 'tools.all',
    defaultAll: 'Tất cả',
    iconColor: 'text-vintage-blue',
  },
};

export default function ArticlesPage({ contentType }: ArticlesPageProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { categorySlug } = useParams<{ categorySlug?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const config = contentConfig[contentType];
  const Icon = config.icon;

  const currentPage = parseInt(searchParams.get('page') || '1');
  const currentLanguage = searchParams.get('language') || '';
  const currentLevel = searchParams.get('level') || '';
  const searchTerm = searchParams.get('q') || '';
  const pageSize = 12;

  // Date locale
  const dateLocale = i18n.language === 'de' ? 'de-DE' : i18n.language === 'en' ? 'en-US' : 'vi-VN';

  // Fetch categories
  const { data: newsCategories = [] } = useQuery({
    queryKey: ['newsCategories'],
    queryFn: getNewsCategories,
    enabled: contentType === 'news',
    staleTime: 5 * 60 * 1000,
  });

  const { data: knowledgeCategories = [] } = useQuery({
    queryKey: ['knowledgeCategories'],
    queryFn: getKnowledgeCategories,
    enabled: contentType === 'knowledge',
    staleTime: 5 * 60 * 1000,
  });

  const { data: toolCategoriesData = [] } = useQuery({
    queryKey: ['toolCategories'],
    queryFn: getToolCategories,
    enabled: contentType === 'tools',
    staleTime: 5 * 60 * 1000,
  });

  // Fetch articles/tools data
  const { data: newsData, isLoading: newsLoading } = useQuery({
    queryKey: ['newsArticles', categorySlug, currentPage, pageSize, searchTerm],
    queryFn: () => {
      if (categorySlug) {
        const catInfo = newsCategories.find((c: NewsCategory) => c.slug === categorySlug);
        if (catInfo) return getNewsByCategory(categorySlug, currentPage, pageSize);
      }
      return getNewsArticles({ page: currentPage, page_size: pageSize, search: searchTerm || undefined });
    },
    enabled: contentType === 'news',
  });

  const { data: knowledgeData, isLoading: knowledgeLoading } = useQuery({
    queryKey: ['knowledgeArticles', categorySlug, currentPage, pageSize, currentLanguage, currentLevel, searchTerm],
    queryFn: () => {
      if (categorySlug) {
        const catInfo = knowledgeCategories.find((c: KnowledgeCategory) => c.slug === categorySlug);
        if (catInfo) return getKnowledgeByCategory(categorySlug, currentPage, pageSize);
      }
      return getKnowledgeArticles({
        page: currentPage,
        page_size: pageSize,
        language: currentLanguage || undefined,
        level: currentLevel || undefined,
        search: searchTerm || undefined
      });
    },
    enabled: contentType === 'knowledge',
  });

  const { data: toolsData, isLoading: toolsLoading } = useQuery({
    queryKey: ['tools', categorySlug, currentLanguage, searchTerm],
    queryFn: () => getTools({
      category: categorySlug || undefined,
      language: currentLanguage || undefined,
      search: searchTerm || undefined
    }),
    enabled: contentType === 'tools',
  });

  // Derive state from queries
  const categories: (NewsCategory | KnowledgeCategory)[] = contentType === 'news' ? newsCategories : knowledgeCategories;
  const toolCategories: ToolCategory[] = toolCategoriesData;
  const displayCategories = contentType === 'tools' ? toolCategories : categories;
  
  const articles: (NewsArticle | KnowledgeArticle)[] = contentType === 'news' 
    ? (newsData?.results || []) 
    : (knowledgeData?.results || []);
  const tools: Tool[] = toolsData?.results || [];
  const totalCount = contentType === 'news' 
    ? (newsData?.count || 0) 
    : contentType === 'knowledge' 
      ? (knowledgeData?.count || 0) 
      : (toolsData?.count || 0);
  const loading = contentType === 'news' ? newsLoading : contentType === 'knowledge' ? knowledgeLoading : toolsLoading;

  const currentCategoryInfo = categorySlug
    ? displayCategories.find((c) => c.slug === categorySlug) || null
    : null;

  // Handlers
  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    params.set('page', '1');
    setSearchParams(params);
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get('search') as string;
    updateFilter('q', query);
  };

  const handleCategoryClick = (slug: string) => {
    if (slug) {
      navigate(`${config.basePath}/${slug}`);
    } else {
      navigate(config.basePath);
    }
  };

  const clearFilters = () => {
    setSearchParams({});
    navigate(config.basePath);
  };

  const totalPages = Math.ceil(totalCount / pageSize);
  const hasActiveFilters = searchTerm || categorySlug || currentLanguage || currentLevel;

  // Page title and description
  const pageTitle = currentCategoryInfo 
    ? currentCategoryInfo.name
    : t(config.titleKey, config.defaultTitle);
  
  const pageDescription = currentCategoryInfo && 'description' in currentCategoryInfo
    ? currentCategoryInfo.description || `${config.defaultDesc}`
    : t(config.descKey, config.defaultDesc);

  // Get categories to display - already computed above

  // Build breadcrumb items
  const breadcrumbItems = currentCategoryInfo
    ? [
        { label: t(config.titleKey, config.defaultTitle), href: config.basePath },
        { label: currentCategoryInfo.name },
      ]
    : [
        { label: t(config.titleKey, config.defaultTitle) },
      ];

  return (
    <>
      <Helmet>
        <title>{pageTitle} | UnstressVN</title>
        <meta name="description" content={pageDescription} />
        <meta property="og:title" content={`${pageTitle} | UnstressVN`} />
        <meta property="og:description" content={pageDescription} />
        <meta property="og:type" content="website" />
        <link rel="canonical" href={`https://unstressvn.com${config.basePath}${categorySlug ? '/' + categorySlug : ''}`} />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        <div className="container-responsive py-8">
          {/* Header with Breadcrumb */}
          <header className="mb-8">
            {/* Breadcrumb */}
            <Breadcrumb items={breadcrumbItems} className="mb-4" />
            
            {/* Title */}
            <div className="flex items-center gap-3 mb-3">
              <Icon className={`h-8 w-8 ${config.iconColor}`} />
              <h1 className="text-3xl md:text-4xl font-serif font-bold text-vintage-dark">
                {pageTitle}
              </h1>
            </div>
            <p className="text-vintage-dark/70 font-serif italic max-w-2xl">
              {pageDescription}
            </p>
          </header>

          {/* Category Pills */}
          {displayCategories.length > 0 && (
            <div className="mb-6 overflow-x-auto pb-2 scrollbar-hide">
              <div className="flex gap-2 min-w-max">
                <button
                  onClick={() => handleCategoryClick('')}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                    !categorySlug
                      ? 'bg-vintage-olive text-white shadow-md'
                      : 'bg-white text-vintage-dark hover:bg-vintage-tan/20 border border-vintage-tan/30'
                  }`}
                >
                  {t(config.allKey, config.defaultAll)}
                </button>
                {displayCategories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => handleCategoryClick(cat.slug)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                      categorySlug === cat.slug
                        ? 'bg-vintage-olive text-white shadow-md'
                        : 'bg-white text-vintage-dark hover:bg-vintage-tan/20 border border-vintage-tan/30'
                    }`}
                  >
                    {cat.name} {'article_count' in cat ? `(${cat.article_count})` : 'tools_count' in cat ? `(${cat.tools_count})` : ''}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filters Row */}
          <div className="flex flex-col md:flex-row gap-4 mb-8">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-vintage-tan" />
                <input
                  type="text"
                  name="search"
                  defaultValue={searchTerm}
                  placeholder={t('common.searchPlaceholder', 'Tìm kiếm...')}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-vintage-tan/30 rounded-xl focus:ring-2 focus:ring-vintage-olive/30 focus:border-vintage-olive transition-all"
                />
              </div>
            </form>

            {/* Knowledge-specific filters */}
            {contentType === 'knowledge' && (
              <div className="flex gap-2">
                <select
                  value={currentLanguage}
                  onChange={(e) => updateFilter('language', e.target.value)}
                  className="px-4 py-3 bg-white border border-vintage-tan/30 rounded-xl focus:ring-2 focus:ring-vintage-olive/30 focus:border-vintage-olive transition-all text-sm"
                >
                  <option value="">{t('knowledge.allLanguages', 'Tất cả ngôn ngữ')}</option>
                  {getLanguageChoices().map((lang) => (
                    <option key={lang.value} value={lang.value}>{lang.label}</option>
                  ))}
                </select>
                <select
                  value={currentLevel}
                  onChange={(e) => updateFilter('level', e.target.value)}
                  className="px-4 py-3 bg-white border border-vintage-tan/30 rounded-xl focus:ring-2 focus:ring-vintage-olive/30 focus:border-vintage-olive transition-all text-sm"
                >
                  <option value="">{t('knowledge.allLevels', 'Tất cả cấp độ')}</option>
                  {getLevelChoices().map((level) => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Clear filters */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-2 px-4 py-2 text-vintage-tan hover:text-vintage-dark transition-colors"
              >
                <X className="h-4 w-4" />
                {t('common.clearFilters', 'Xóa bộ lọc')}
              </button>
            )}
          </div>

          {/* Results count */}
          <div className="mb-6 text-sm text-vintage-tan">
            {t('common.resultsCount', '{{count}} kết quả', { count: totalCount })}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white rounded-2xl overflow-hidden shadow-sm animate-pulse">
                  <div className="h-44 bg-vintage-tan/20"></div>
                  <div className="p-5 space-y-3">
                    <div className="h-4 bg-vintage-tan/20 rounded w-3/4"></div>
                    <div className="h-4 bg-vintage-tan/20 rounded w-1/2"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Articles Grid (News & Knowledge) */}
          {!loading && contentType !== 'tools' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {articles.map((article) => (
                <Link
                  key={article.id}
                  to={`${config.basePath}/${article.category?.slug || 'bai-viet'}/${article.slug}`}
                  className="block cursor-pointer group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-vintage-olive/20"
                >
                  {/* Image */}
                  <div className="relative h-44 overflow-hidden bg-vintage-cream">
                    {article.featured_image ? (
                      <ResponsiveImage
                        src={article.featured_image}
                        srcset={article.cover_image_srcset}
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Icon className={`h-12 w-12 ${config.iconColor} opacity-30`} />
                      </div>
                    )}
                    
                    {/* Badges */}
                    <div className="absolute top-3 left-3 flex gap-2">
                      {article.is_featured && (
                        <span className="px-2 py-1 bg-vintage-brown text-white text-xs font-medium rounded-full">
                          {t('common.featured', 'Nổi bật')}
                        </span>
                      )}
                      {'level' in article && article.level && (
                        <span className="px-2 py-1 bg-vintage-olive text-white text-xs font-medium rounded-full flex items-center gap-1">
                          <GraduationCap className="h-3 w-3" />
                          {article.level}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-5">
                    {/* Category */}
                    {article.category && (
                      <span className="text-xs font-medium text-vintage-olive mb-2 block">
                        {article.category.name}
                      </span>
                    )}
                    
                    {/* Title */}
                    <h3 className="font-semibold text-vintage-dark line-clamp-2 group-hover:text-vintage-olive transition-colors mb-3 leading-snug">
                      {article.title}
                    </h3>
                    
                    {/* Excerpt */}
                    <p className="text-sm text-vintage-dark/60 line-clamp-2 mb-4">
                      {article.excerpt}
                    </p>
                    
                    {/* Meta */}
                    <div className="flex items-center justify-between text-xs text-vintage-tan">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{new Date(article.published_at || article.created_at).toLocaleDateString(dateLocale)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="h-3.5 w-3.5" />
                        <span>{article.view_count}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {/* Tools Grid - Now displayed as articles */}
          {!loading && contentType === 'tools' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {tools.map((tool) => (
                <Link
                  key={tool.id}
                  to={`${config.basePath}/${tool.category?.slug || 'cong-cu'}/${tool.slug}`}
                  className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-transparent hover:border-vintage-olive/20"
                >
                  {/* Image */}
                  <div className="relative h-44 overflow-hidden bg-vintage-cream">
                    {(tool.featured_image || tool.cover_image) ? (
                      <ResponsiveImage
                        src={tool.featured_image || tool.cover_image}
                        srcset={tool.cover_image_srcset}
                        alt={tool.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Wrench className="h-12 w-12 text-vintage-blue opacity-30" />
                      </div>
                    )}
                    
                    {/* Badges */}
                    <div className="absolute top-3 left-3 flex gap-2">
                      {tool.is_featured && (
                        <span className="px-2 py-1 bg-vintage-brown text-white text-xs font-medium rounded-full">
                          {t('common.featured', 'Nổi bật')}
                        </span>
                      )}
                      {tool.language && tool.language !== 'all' && (
                        <span className={`px-2 py-1 text-xs font-medium rounded-full flex items-center gap-1 ${
                          tool.language === 'de' ? 'bg-vintage-tan/20 text-vintage-dark' :
                          tool.language === 'en' ? 'bg-vintage-blue/15 text-vintage-blue' :
                          'bg-vintage-cream text-vintage-dark/70'
                        }`}>
                          <Languages className="h-3 w-3" />
                          {tool.language === 'de' ? 'DE' : tool.language === 'en' ? 'EN' : String(tool.language).toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-5">
                    {/* Category */}
                    {tool.category && (
                      <span className="text-xs font-medium text-vintage-olive mb-2 block">
                        {tool.category.name}
                      </span>
                    )}
                    
                    {/* Title */}
                    <h3 className="font-semibold text-vintage-dark line-clamp-2 group-hover:text-vintage-olive transition-colors mb-3 leading-snug">
                      {tool.name}
                    </h3>
                    
                    {/* Excerpt/Description */}
                    <p className="text-sm text-vintage-dark/60 line-clamp-2 mb-4">
                      {tool.excerpt || tool.description}
                    </p>
                    
                    {/* Meta */}
                    <div className="flex items-center justify-between text-xs text-vintage-tan">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{new Date(tool.published_at || tool.created_at).toLocaleDateString(dateLocale)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="h-3.5 w-3.5" />
                        <span>{tool.view_count}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && (contentType === 'tools' ? tools.length === 0 : articles.length === 0) && (
            <div className="text-center py-16">
              <Icon className={`h-16 w-16 mx-auto ${config.iconColor} opacity-30 mb-4`} />
              <h3 className="text-xl font-semibold text-vintage-dark mb-2">
                {t('common.noResults', 'Không tìm thấy kết quả')}
              </h3>
              <p className="text-vintage-tan mb-6">
                {t('common.tryDifferentFilter', 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm')}
              </p>
              <button
                onClick={clearFilters}
                className="px-6 py-3 bg-vintage-olive text-white rounded-xl hover:bg-vintage-olive/90 transition-colors"
              >
                {t('common.clearFilters', 'Xóa bộ lọc')}
              </button>
            </div>
          )}

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <div className="mt-12 flex justify-center">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateFilter('page', String(Math.max(1, currentPage - 1)))}
                  disabled={currentPage <= 1}
                  className="px-4 py-2 rounded-lg border border-vintage-tan/30 hover:bg-vintage-cream disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {t('common.previous', 'Trước')}
                </button>
                
                <div className="flex items-center gap-1">
                  {[...Array(Math.min(5, totalPages))].map((_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => updateFilter('page', String(pageNum))}
                        className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                          currentPage === pageNum
                            ? 'bg-vintage-olive text-white'
                            : 'hover:bg-vintage-cream'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <button
                  onClick={() => updateFilter('page', String(Math.min(totalPages, currentPage + 1)))}
                  disabled={currentPage >= totalPages}
                  className="px-4 py-2 rounded-lg border border-vintage-tan/30 hover:bg-vintage-cream disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {t('common.next', 'Sau')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

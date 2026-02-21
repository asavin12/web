import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { resourcesApi, utilsApi } from '@/api';
import type { Resource } from '@/types';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingInline } from '@/components/ui/Spinner';
import { SEO, BookCard } from '@/components/common';
import { BookOpen, Filter, X, Search, Grid3X3, List } from 'lucide-react';

// 3 rows x 6 columns (desktop) = 18 items per page
const ITEMS_PER_PAGE = 18;

export default function ResourceListPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  const [filters, setFilters] = useState({
    search: searchParams.get('q') || '',
    language: searchParams.get('language') || '',
    level: searchParams.get('level') || '',
    resource_type: searchParams.get('type') || '',
  });
  
  const page = parseInt(searchParams.get('page') || '1');

  // Fetch choices
  const { data: choices } = useQuery({
    queryKey: ['choices'],
    queryFn: utilsApi.getChoices,
  });

  // Fetch resources with page_size for 3 rows
  const { data: resources, isLoading } = useQuery({
    queryKey: ['resources', filters, page, ITEMS_PER_PAGE],
    queryFn: () => resourcesApi.getAll({
      ...filters,
      page,
      page_size: ITEMS_PER_PAGE,
    }),
  });

  const handleFilterChange = (name: string, value: string) => {
    setFilters((prev) => ({ ...prev, [name]: value }));
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(name === 'search' ? 'q' : name, value);
    } else {
      newParams.delete(name === 'search' ? 'q' : name);
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
    setFilters({
      search: '',
      language: '',
      level: '',
      resource_type: '',
    });
    setSearchParams({});
  };

  const hasActiveFilters = filters.search || filters.language || filters.level || filters.resource_type;

  const languageOptions = choices?.languages || [];

  const levelOptions = [
    { value: 'A1', label: t('levels.A1', 'A1 - Beginner') },
    { value: 'A2', label: t('levels.A2', 'A2 - Elementary') },
    { value: 'B1', label: t('levels.B1', 'B1 - Intermediate') },
    { value: 'B2', label: t('levels.B2', 'B2 - Upper Intermediate') },
    { value: 'C1', label: t('levels.C1', 'C1 - Advanced') },
    { value: 'C2', label: t('levels.C2', 'C2 - Proficiency') },
  ];

  const typeOptions = choices?.resource_types || [
    { value: 'book', label: t('resources.types.book', 'Book') },
    { value: 'audio', label: t('resources.types.audio', 'Audio') },
    { value: 'video', label: t('resources.types.video', 'Video') },
    { value: 'article', label: t('resources.types.article', 'Article') },
    { value: 'other', label: t('resources.types.other', 'Other') },
  ];

  return (
    <>
      {/* SEO */}
      <SEO 
        title={t('resources.seo.title', 'Thư viện tài liệu - UnstressVN')}
        description={t('resources.seo.description', 'Duyệt qua thư viện tài liệu học ngôn ngữ phong phú bao gồm sách, audio, video và bài viết cho mọi trình độ.')}
        keywords={['tài liệu học ngoại ngữ', 'sách học tiếng Đức', 'video học tiếng Anh', 'tài liệu miễn phí', 'UnstressVN']}
        type="website"
      />

      <div className="min-h-screen bg-gradient-to-b from-vintage-cream to-white">
        <div className="container-responsive py-8">
        {/* Header */}
        <header className="mb-6 md:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 md:gap-3 mb-2">
                <BookOpen className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive" />
                <h1 className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark">
                  {t('resources.title', 'Thư viện tài liệu')}
                </h1>
              </div>
              <p className="text-sm md:text-base text-vintage-dark/70 font-serif italic">
                {t('resources.subtitle', 'Tài liệu học tập cho mọi trình độ')}
              </p>
            </div>
            
            {/* View Mode & Filter Toggle - Desktop */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`md:hidden touch-target inline-flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                  showFilters ? 'bg-vintage-olive text-white border-vintage-olive' : 'border-vintage-tan text-vintage-dark'
                }`}
              >
                <Filter className="h-4 w-4" />
                <span className="text-sm font-medium">{t('common.filters', 'Filters')}</span>
                {hasActiveFilters && (
                  <span className="w-2 h-2 rounded-full bg-vintage-brown"></span>
                )}
              </button>
              
              <div className="hidden md:flex items-center gap-1 bg-vintage-tan/10 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-vintage-olive text-white' : 'text-vintage-dark hover:bg-vintage-tan/20'}`}
                  aria-label={t('resources.gridView', 'Grid view')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-colors ${viewMode === 'list' ? 'bg-vintage-olive text-white' : 'text-vintage-dark hover:bg-vintage-tan/20'}`}
                  aria-label={t('resources.listView', 'List view')}
                >
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Filters - Responsive */}
        <div className={`${showFilters ? 'block' : 'hidden'} md:block mb-6 md:mb-8`}>
          <Card>
            <CardContent className="p-4 md:pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
                {/* Search */}
                <div className="sm:col-span-2 lg:col-span-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-vintage-tan" />
                  <Input
                    className="pl-9"
                    placeholder={t('resources.searchPlaceholder', 'Search resources...')}
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                  />
                </div>
                
                <Select
                  value={filters.language}
                  onChange={(e) => handleFilterChange('language', e.target.value)}
                  options={languageOptions}
                  placeholder={t('resources.allLanguages', 'All Languages')}
                />
                <Select
                  value={filters.level}
                  onChange={(e) => handleFilterChange('level', e.target.value)}
                  options={levelOptions}
                  placeholder={t('resources.allLevels', 'All Levels')}
                />
                <Select
                  value={filters.resource_type}
                  onChange={(e) => handleFilterChange('resource_type', e.target.value)}
                  options={typeOptions}
                  placeholder={t('resources.allTypes', 'All Types')}
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

        {/* Results Count & Top Pagination */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 md:mb-6">
          {resources?.count !== undefined && (
            <p className="text-sm md:text-base text-vintage-dark/60 font-serif">
              {t('resources.resultsCount', { count: resources.count })} {t('resources.resultUnit', { count: resources.count })}
            </p>
          )}
          
          {/* Top-right pagination */}
          {resources?.count && resources.count > ITEMS_PER_PAGE && (
            <Pagination
              currentPage={page}
              totalPages={Math.ceil(resources.count / ITEMS_PER_PAGE)}
              onPageChange={handlePageChange}
              className="self-end"
            />
          )}
        </div>

        {/* Results */}
        {isLoading ? (
          <div className="py-12">
            <LoadingInline text={t('common.loading', 'Loading...')} />
          </div>
        ) : resources?.results && resources.results.length > 0 ? (
          <>
            {/* Grid View - 3 rows x 4 columns on desktop */}
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3 md:gap-4 lg:gap-6">
                {resources.results.map((resource: Resource) => (
                  <BookCard key={resource.id} resource={resource} />
                ))}
              </div>
            ) : (
              /* List View */
              <div className="space-y-4">
                {resources.results.map((resource: Resource) => (
                  <Card key={resource.id} className="hover:shadow-lg transition-shadow overflow-hidden card-interactive">
                    <Link to={`/tai-lieu/${resource.slug}`} className="flex flex-col sm:flex-row">
                      {resource.cover_image && (
                        <div className="sm:w-32 md:w-40 lg:w-48 flex-shrink-0">
                          <img
                            src={resource.cover_image}
                            alt={resource.title}
                            className="w-full h-32 sm:h-full object-cover"
                          />
                        </div>
                      )}
                      <div className="flex-1 p-4 md:p-6">
                        <h3 className="text-lg md:text-xl font-serif font-bold text-vintage-dark line-clamp-2 mb-2">
                          {resource.title}
                        </h3>
                        <p className="text-sm md:text-base text-vintage-dark/70 line-clamp-2 mb-4">
                          {resource.description}
                        </p>
                        <div className="flex flex-wrap gap-2 mb-4">
                          <Badge variant="secondary">{resource.language_display}</Badge>
                          <Badge variant="outline">{resource.level}</Badge>
                          <Badge variant="outline">{resource.resource_type_display}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-vintage-dark/60">
                          <span className="flex items-center gap-1">👁 {resource.view_count}</span>
                          <span className="flex items-center gap-1">⬇ {resource.download_count}</span>
                        </div>
                      </div>
                    </Link>
                  </Card>
                ))}
              </div>
            )}

            {/* Bottom Pagination */}
            {resources.count > ITEMS_PER_PAGE && (
              <div className="mt-8 md:mt-12">
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(resources.count / ITEMS_PER_PAGE)}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        ) : (
          <Card>
            <CardContent className="py-12 md:py-16 text-center">
              <BookOpen className="h-12 w-12 md:h-16 md:w-16 text-vintage-tan mx-auto mb-4" />
              <p className="text-lg md:text-xl font-serif text-vintage-dark/60">
                {t('resources.noResults', 'No resources found')}
              </p>
              <p className="text-sm text-vintage-tan mt-2">
                {t('resources.tryDifferent', 'Try adjusting your filters')}
              </p>
            </CardContent>
          </Card>
        )}
        </div>
      </div>
    </>
  );
}

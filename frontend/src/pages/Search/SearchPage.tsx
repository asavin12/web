import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { utilsApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { LoadingInline } from '@/components/ui/Spinner';
import { HighlightText } from '@/components/common';

// Chỉ tìm kiếm resources - không tìm users/posts để bảo vệ thông tin
type SearchTab = 'all' | 'resources';

export default function SearchPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const query = searchParams.get('q') || '';
  const [searchInput, setSearchInput] = useState(query);
  const [activeTab, setActiveTab] = useState<SearchTab>('all');

  // Search query
  const { data: results, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: () => utilsApi.search(query),
    enabled: query.length >= 2,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ q: searchInput.trim() });
    }
  };

  const tabs: { key: SearchTab; label: string; count: number }[] = [
    { key: 'all', label: t('search.all'), count: results?.resources?.length || 0 },
    { key: 'resources', label: t('search.resources'), count: results?.resources?.length || 0 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">{t('search.title')}</h1>

      {/* Search Form */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-2">
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder={t('search.placeholder')}
            className="flex-1"
          />
          <Button type="submit">{t('search.search')}</Button>
        </div>
      </form>

      {query && (
        <>
          {/* Tabs */}
          <div className="flex gap-2 border-b pb-2">
            {tabs.map((tab) => (
              <Button
                key={tab.key}
                variant={activeTab === tab.key ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label} ({tab.count})
              </Button>
            ))}
          </div>

          {/* Results */}
          {isLoading ? (
            <LoadingInline text={t('search.searching')} />
          ) : (
            <div className="space-y-8">
              {/* Resources */}
              {results?.resources && results.resources.length > 0 && (
                <section>
                  <h2 className="text-xl font-semibold mb-4">{t('search.resources')}</h2>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {results.resources.map((resource) => (
                      <Card key={resource.id} className="hover:shadow-lg transition-shadow">
                        <Link to={`/tai-lieu/${resource.slug}`}>
                          {resource.cover_image && (
                            <img
                              src={resource.cover_image}
                              alt={resource.title}
                              className="w-full h-32 object-cover rounded-t-lg"
                            />
                          )}
                          <CardHeader className="py-3">
                            <CardTitle className="text-base line-clamp-2">
                              <HighlightText text={resource.title} highlight={query} />
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="pt-0">
                            <div className="flex gap-2">
                              <Badge variant="secondary">{resource.language_display}</Badge>
                              <Badge variant="outline">{resource.level}</Badge>
                            </div>
                          </CardContent>
                        </Link>
                      </Card>
                    ))}
                  </div>
                </section>
              )}

              {/* No results */}
              {!isLoading && results && !results.resources?.length && (
                <Card>
                  <CardContent className="py-12 text-center">
                    <p className="text-muted-foreground">
                      {t('search.noResults', { query })}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {!query && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">{t('search.enterQuery')}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

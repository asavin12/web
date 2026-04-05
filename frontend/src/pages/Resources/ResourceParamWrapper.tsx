/**
 * Discriminator wrapper for /tai-lieu/:slug routes
 * Checks if slug matches a resource category → show filtered list
 * Otherwise → show resource detail page
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { resourcesApi } from '@/api/resources';
import { lazy, Suspense } from 'react';
import { LoadingPage } from '@/components/ui/Spinner';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

const ResourceListPage = lazy(() => import('./ResourceListPage'));
const ResourceDetailPage = lazy(() => import('./ResourceDetailPage'));

export default function ResourceParamWrapper() {
  const { slug } = useParams<{ slug: string }>();
  
  const { data: categories, isLoading } = useQuery({
    queryKey: ['resource-categories'],
    queryFn: resourcesApi.getCategories,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <LoadingPage />;

  const isCategory = categories?.some(c => c.slug === slug);

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingPage />}>
        {isCategory ? <ResourceListPage /> : <ResourceDetailPage />}
      </Suspense>
    </ErrorBoundary>
  );
}

import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

export default function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center">
      <h1 className="text-9xl font-bold text-primary/20">404</h1>
      <h2 className="text-2xl font-semibold mt-4">{t('errors.notFound.title')}</h2>
      <p className="text-muted-foreground mt-2 max-w-md">
        {t('errors.notFound.description')}
      </p>
      <div className="flex gap-4 mt-8">
        <Button asChild>
          <Link to="/">{t('errors.notFound.goHome')}</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/tim-kiem">{t('errors.notFound.search')}</Link>
        </Button>
      </div>
    </div>
  );
}

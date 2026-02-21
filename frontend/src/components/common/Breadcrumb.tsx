import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items?: BreadcrumbItem[];
  className?: string;
}

// Route to breadcrumb mapping
const routeLabels: Record<string, string> = {
  'tai-lieu': 'resources.title',
  'ho-so': 'nav.profile',
  'cap-nhat': 'profile.edit',
  'doi-mat-khau': 'auth.changePassword',
  'tim-kiem': 'nav.search',
  'dang-nhap': 'auth.login',
  'dang-ky': 'auth.register',
  'video': 'nav.videos',
  'tin-tuc': 'nav.news',
  'kien-thuc': 'nav.knowledge',
  'cong-cu': 'nav.tools',
  'gioi-thieu': 'nav.about',
  'lien-he': 'nav.contact',
};

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  const { t } = useTranslation();
  const location = useLocation();
  
  // Auto-generate breadcrumbs from URL if items not provided
  const breadcrumbs: BreadcrumbItem[] = items || (() => {
    const pathParts = location.pathname.split('/').filter(Boolean);
    const result: BreadcrumbItem[] = [];
    
    let currentPath = '';
    pathParts.forEach((part, index) => {
      currentPath += `/${part}`;
      const labelKey = routeLabels[part];
      
      // Skip dynamic segments (slugs, ids, usernames)
      if (labelKey) {
        result.push({
          label: t(labelKey),
          href: index < pathParts.length - 1 ? currentPath : undefined,
        });
      } else if (!Object.keys(routeLabels).includes(part)) {
        // This might be a slug or username, show it as-is
        result.push({
          label: decodeURIComponent(part),
          href: undefined,
        });
      }
    });
    
    return result;
  })();

  if (breadcrumbs.length === 0) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center text-sm text-vintage-tan mb-4', className)}
    >
      <ol className="flex items-center gap-1 flex-wrap">
        <li>
          <Link
            to="/"
            className="flex items-center gap-1 text-vintage-olive hover:text-vintage-brown transition-colors"
          >
            <Home className="h-4 w-4" />
            <span className="sr-only">{t('nav.home')}</span>
          </Link>
        </li>
        
        {breadcrumbs.map((item, index) => (
          <li key={index} className="flex items-center gap-1">
            <ChevronRight className="h-4 w-4 text-vintage-tan/50" />
            {item.href ? (
              <Link
                to={item.href}
                className="text-vintage-olive hover:text-vintage-brown transition-colors"
              >
                {item.label}
              </Link>
            ) : (
              <span className="text-vintage-dark font-medium">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default Breadcrumb;

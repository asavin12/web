import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { MainLayout } from '@/layouts';
import { LoadingPage } from '@/components/ui/Spinner';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import ProtectedRoute from './ProtectedRoute';

// Lazy load pages for code splitting
const HomePage = lazy(() => import('@/pages/Home/HomePage'));
const LoginPage = lazy(() => import('@/pages/Auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/Auth/RegisterPage'));
const ProfilePage = lazy(() => import('@/pages/Auth/ProfilePage'));
const ProfileEditPage = lazy(() => import('@/pages/Auth/ProfileEditPage'));
const PasswordChangePage = lazy(() => import('@/pages/Auth/PasswordChangePage'));
const SettingsPage = lazy(() => import('@/pages/Auth/SettingsPage'));
const ResourceListPage = lazy(() => import('@/pages/Resources/ResourceListPage'));
const ResourceDetailPage = lazy(() => import('@/pages/Resources/ResourceDetailPage'));
const VideoListPage = lazy(() => import('@/pages/Videos/VideoListPage'));
const VideoDetailPage = lazy(() => import('@/pages/Videos/VideoDetailPage'));
const SearchPage = lazy(() => import('@/pages/Search/SearchPage'));
const NotificationsPage = lazy(() => import('@/pages/Notifications/NotificationsPage'));
const AboutPage = lazy(() => import('@/pages/Static/AboutPage'));
const ContactPage = lazy(() => import('@/pages/Static/ContactPage'));
const TermsPage = lazy(() => import('@/pages/Static/TermsPage'));
const PrivacyPage = lazy(() => import('@/pages/Static/PrivacyPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

// Unified Articles pages (News, Knowledge, Tools share same layout)
const ArticlesPage = lazy(() => import('@/pages/articles/ArticlesPage'));
const ArticleDetailPage = lazy(() => import('@/pages/articles/ArticleDetailPage'));

// Wrapper for lazy-loaded pages
function LazyPage({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingPage />}>{children}</Suspense>
    </ErrorBoundary>
  );
}

// Wrapper components for different content types
function NewsListWrapper() {
  return <LazyPage><ArticlesPage contentType="news" /></LazyPage>;
}

function NewsDetailWrapper() {
  return <LazyPage><ArticleDetailPage contentType="news" /></LazyPage>;
}

function KnowledgeListWrapper() {
  return <LazyPage><ArticlesPage contentType="knowledge" /></LazyPage>;
}

function KnowledgeDetailWrapper() {
  return <LazyPage><ArticleDetailPage contentType="knowledge" /></LazyPage>;
}

function ToolsListWrapper() {
  return <LazyPage><ArticlesPage contentType="tools" /></LazyPage>;
}

function ToolsDetailWrapper() {
  return <LazyPage><ArticleDetailPage contentType="tools" /></LazyPage>;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      // Public routes
      {
        index: true,
        element: <LazyPage><HomePage /></LazyPage>,
      },
      {
        path: 'dang-nhap',
        element: <LazyPage><LoginPage /></LazyPage>,
      },
      {
        path: 'dang-ky',
        element: <LazyPage><RegisterPage /></LazyPage>,
      },
      
      // Resources (public)
      {
        path: 'tai-lieu',
        element: <LazyPage><ResourceListPage /></LazyPage>,
      },
      {
        path: 'tai-lieu/:slug',
        element: <LazyPage><ResourceDetailPage /></LazyPage>,
      },
      
      // Videos (public)
      {
        path: 'video',
        element: <LazyPage><VideoListPage /></LazyPage>,
      },
      {
        path: 'video/:slug',
        element: <LazyPage><VideoDetailPage /></LazyPage>,
      },
      
      // News (using unified ArticlesPage)
      {
        path: 'tin-tuc/:categorySlug/:slug',
        element: <NewsDetailWrapper />,
      },
      {
        path: 'tin-tuc/:categorySlug',
        element: <NewsListWrapper />,
      },
      {
        path: 'tin-tuc',
        element: <NewsListWrapper />,
      },
      
      // Knowledge (using unified ArticlesPage)
      {
        path: 'kien-thuc/:categorySlug/:slug',
        element: <KnowledgeDetailWrapper />,
      },
      {
        path: 'kien-thuc/:categorySlug',
        element: <KnowledgeListWrapper />,
      },
      {
        path: 'kien-thuc',
        element: <KnowledgeListWrapper />,
      },
      
      // Tools (using unified ArticlesPage)
      {
        path: 'cong-cu/:categorySlug/:slug',
        element: <ToolsDetailWrapper />,
      },
      {
        path: 'cong-cu/:categorySlug',
        element: <ToolsListWrapper />,
      },
      {
        path: 'cong-cu',
        element: <ToolsListWrapper />,
      },
      
      // Profile (protected)
      {
        path: 'ho-so',
        element: (
          <ProtectedRoute>
            <LazyPage><ProfilePage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      {
        path: 'ho-so/cap-nhat',
        element: (
          <ProtectedRoute>
            <LazyPage><ProfileEditPage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      {
        path: 'ho-so/doi-mat-khau',
        element: (
          <ProtectedRoute>
            <LazyPage><PasswordChangePage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      
      // Settings (protected)
      {
        path: 'cai-dat',
        element: (
          <ProtectedRoute>
            <LazyPage><SettingsPage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      {
        path: 'doi-mat-khau',
        element: (
          <ProtectedRoute>
            <LazyPage><PasswordChangePage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      
      // Search
      {
        path: 'tim-kiem',
        element: <LazyPage><SearchPage /></LazyPage>,
      },
      
      // Notifications (protected)
      {
        path: 'thong-bao',
        element: (
          <ProtectedRoute>
            <LazyPage><NotificationsPage /></LazyPage>
          </ProtectedRoute>
        ),
      },
      
      // Static pages
      {
        path: 'gioi-thieu',
        element: <LazyPage><AboutPage /></LazyPage>,
      },
      {
        path: 'lien-he',
        element: <LazyPage><ContactPage /></LazyPage>,
      },
      {
        path: 'dieu-khoan',
        element: <LazyPage><TermsPage /></LazyPage>,
      },
      {
        path: 'chinh-sach-bao-mat',
        element: <LazyPage><PrivacyPage /></LazyPage>,
      },
      
      // 404
      {
        path: '*',
        element: <LazyPage><NotFoundPage /></LazyPage>,
      },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}

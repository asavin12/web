import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import i18n from '@/i18n';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const t = i18n.t.bind(i18n);

      return (
        <div className="min-h-[50vh] flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-vintage-brown/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="h-8 w-8 text-vintage-brown" />
            </div>
            <h2 className="text-2xl font-serif font-bold text-vintage-dark mb-3">
              {t('errorBoundary.title')}
            </h2>
            <p className="text-vintage-dark/60 mb-6">
              {t('errorBoundary.description')}
            </p>
            {this.state.error && (
              <details className="mb-6 text-left">
                <summary className="text-sm text-vintage-tan cursor-pointer hover:text-vintage-dark">
                  {t('errorBoundary.errorDetails')}
                </summary>
                <pre className="mt-2 p-3 bg-vintage-cream rounded-lg text-xs text-vintage-dark/70 overflow-auto max-h-32">
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-vintage-olive text-white rounded-xl hover:bg-vintage-brown transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                {t('errorBoundary.retry')}
              </button>
              <a
                href="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-vintage-tan/20 text-vintage-dark rounded-xl hover:bg-vintage-tan/30 transition-colors"
              >
                <Home className="h-4 w-4" />
                {t('errorBoundary.home')}
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

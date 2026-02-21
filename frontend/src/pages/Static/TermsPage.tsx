import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { SEO } from '@/components/common';
import { Breadcrumb } from '@/components/common/Breadcrumb';
import { FileText, Scale, Shield, Users, AlertTriangle, Ban, MessageSquare } from 'lucide-react';

export default function TermsPage() {
  const { t } = useTranslation();

  return (
    <>
      <SEO 
        title={t('terms.seo.title')}
        description={t('terms.seo.description')}
        keywords={['terms of service', 'user agreement', 'legal terms', 'usage policy']}
        type="website"
      />

      <div className="bg-vintage-light min-h-screen">
        <div className="container-responsive section-spacing">
          {/* Breadcrumb */}
          <Breadcrumb items={[{ label: t('terms.title') }]} className="mb-8" />

          {/* Header */}
          <header className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-vintage-olive/10 rounded-2xl mb-6">
              <FileText className="h-8 w-8 text-vintage-olive" />
            </div>
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif font-bold text-vintage-dark mb-4">
              {t('terms.title')}
            </h1>
            <p className="text-vintage-dark/60 font-serif italic">
              {t('terms.lastUpdated')}: 21/12/2025
            </p>
          </header>

          {/* Content */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-vintage-tan/30 overflow-hidden">
            <div className="p-6 md:p-8 lg:p-10 space-y-8">
              
              {/* Section 1 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center">
                    <Scale className="h-5 w-5 text-vintage-olive" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    1. {t('terms.acceptance.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p>
                    {t('terms.acceptance.content')}
                  </p>
                </div>
              </section>

              {/* Section 2 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-blue/10 rounded-lg flex items-center justify-center">
                    <Users className="h-5 w-5 text-vintage-blue" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    2. {t('terms.account.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('terms.account.item1')}</li>
                    <li>{t('terms.account.item2')}</li>
                    <li>{t('terms.account.item3')}</li>
                    <li>{t('terms.account.item4')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 3 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-brown/10 rounded-lg flex items-center justify-center">
                    <MessageSquare className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    3. {t('terms.content.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('terms.content.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('terms.content.item1')}</li>
                    <li>{t('terms.content.item2')}</li>
                    <li>{t('terms.content.item3')}</li>
                    <li>{t('terms.content.item4')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 4 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-brown/10 rounded-lg flex items-center justify-center">
                    <Ban className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    4. {t('terms.prohibited.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('terms.prohibited.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('terms.prohibited.item1')}</li>
                    <li>{t('terms.prohibited.item2')}</li>
                    <li>{t('terms.prohibited.item3')}</li>
                    <li>{t('terms.prohibited.item4')}</li>
                    <li>{t('terms.prohibited.item5')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 5 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center">
                    <Shield className="h-5 w-5 text-vintage-olive" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    5. {t('terms.intellectual.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p>
                    {t('terms.intellectual.content')}
                  </p>
                </div>
              </section>

              {/* Section 6 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-tan/20 rounded-lg flex items-center justify-center">
                    <AlertTriangle className="h-5 w-5 text-vintage-tan" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    6. {t('terms.disclaimer.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('terms.disclaimer.item1')}</li>
                    <li>{t('terms.disclaimer.item2')}</li>
                    <li>{t('terms.disclaimer.item3')}</li>
                    <li>{t('terms.disclaimer.item4')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 7 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-tan/30 rounded-lg flex items-center justify-center">
                    <FileText className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    7. {t('terms.changes.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p>
                    {t('terms.changes.content')}
                  </p>
                </div>
              </section>

              {/* Contact */}
              <section className="bg-vintage-cream rounded-xl p-6 mt-8">
                <h3 className="text-lg font-serif font-bold text-vintage-dark mb-3">
                  {t('terms.contact.title')}
                </h3>
                <p className="text-vintage-dark/70">
                  {t('terms.contact.content')}{' '}
                  <Link to="/lien-he" className="text-vintage-olive hover:text-vintage-brown font-bold">
                    {t('nav.contact')}
                  </Link>.
                </p>
              </section>

            </div>
          </div>
        </div>
      </div>
    </>
  );
}

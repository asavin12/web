import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { SEO } from '@/components/common';
import { Breadcrumb } from '@/components/common/Breadcrumb';
import { Shield, Database, Eye, Lock, Share2, Bell, Cookie, UserCheck } from 'lucide-react';

export default function PrivacyPage() {
  const { t } = useTranslation();

  return (
    <>
      <SEO 
        title={t('privacy.seo.title')}
        description={t('privacy.seo.description')}
        keywords={['privacy policy', 'data protection', 'personal information', 'GDPR', 'user privacy']}
        type="website"
      />

      <div className="bg-vintage-light min-h-screen">
        <div className="container-responsive section-spacing">
          {/* Breadcrumb */}
          <Breadcrumb items={[{ label: t('privacy.title') }]} className="mb-8" />

          {/* Header */}
          <header className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-vintage-blue/10 rounded-2xl mb-6">
              <Shield className="h-8 w-8 text-vintage-blue" />
            </div>
            <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif font-bold text-vintage-dark mb-4">
              {t('privacy.title')}
            </h1>
            <p className="text-vintage-dark/60 font-serif italic">
              {t('privacy.lastUpdated')}: 21/12/2025
            </p>
          </header>

          {/* Content */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-vintage-tan/30 overflow-hidden">
            <div className="p-6 md:p-8 lg:p-10 space-y-8">
              
              {/* Intro */}
              <section className="bg-vintage-cream rounded-xl p-6">
                <p className="text-vintage-dark/80 font-serif italic">
                  {t('privacy.intro')}
                </p>
              </section>

              {/* Section 1 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center">
                    <Database className="h-5 w-5 text-vintage-olive" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    1. {t('privacy.collection.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <h3 className="text-lg font-bold text-vintage-dark mb-2">
                    {t('privacy.collection.provided')}
                  </h3>
                  <ul className="list-disc pl-6 space-y-2 mb-4">
                    <li>{t('privacy.collection.item1')}</li>
                    <li>{t('privacy.collection.item2')}</li>
                    <li>{t('privacy.collection.item3')}</li>
                  </ul>
                  <h3 className="text-lg font-bold text-vintage-dark mb-2">
                    {t('privacy.collection.automatic')}
                  </h3>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('privacy.collection.item4')}</li>
                    <li>{t('privacy.collection.item5')}</li>
                    <li>{t('privacy.collection.item6')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 2 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-blue/10 rounded-lg flex items-center justify-center">
                    <Eye className="h-5 w-5 text-vintage-blue" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    2. {t('privacy.usage.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('privacy.usage.item1')}</li>
                    <li>{t('privacy.usage.item2')}</li>
                    <li>{t('privacy.usage.item3')}</li>
                    <li>{t('privacy.usage.item4')}</li>
                    <li>{t('privacy.usage.item5')}</li>
                    <li>{t('privacy.usage.item6')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 3 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-brown/10 rounded-lg flex items-center justify-center">
                    <Share2 className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    3. {t('privacy.sharing.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('privacy.sharing.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('privacy.sharing.item1')}</li>
                    <li>{t('privacy.sharing.item2')}</li>
                    <li>{t('privacy.sharing.item3')}</li>
                    <li>{t('privacy.sharing.item4')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 4 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center">
                    <Lock className="h-5 w-5 text-vintage-olive" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    4. {t('privacy.security.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('privacy.security.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('privacy.security.item1')}</li>
                    <li>{t('privacy.security.item2')}</li>
                    <li>{t('privacy.security.item3')}</li>
                    <li>{t('privacy.security.item4')}</li>
                    <li>{t('privacy.security.item5')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 5 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-tan/20 rounded-lg flex items-center justify-center">
                    <Cookie className="h-5 w-5 text-yellow-600" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    5. {t('privacy.cookies.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('privacy.cookies.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li>{t('privacy.cookies.item1')}</li>
                    <li>{t('privacy.cookies.item2')}</li>
                    <li>{t('privacy.cookies.item3')}</li>
                  </ul>
                  <p className="mt-4">
                    {t('privacy.cookies.control')}
                  </p>
                </div>
              </section>

              {/* Section 6 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-blue/10 rounded-lg flex items-center justify-center">
                    <UserCheck className="h-5 w-5 text-vintage-blue" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    6. {t('privacy.rights.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p className="mb-4">
                    {t('privacy.rights.intro')}
                  </p>
                  <ul className="list-disc pl-6 space-y-2">
                    <li><strong>{t('privacy.rights.access')}</strong> {t('privacy.rights.accessDesc')}</li>
                    <li><strong>{t('privacy.rights.rectify')}</strong> {t('privacy.rights.rectifyDesc')}</li>
                    <li><strong>{t('privacy.rights.delete')}</strong> {t('privacy.rights.deleteDesc')}</li>
                    <li><strong>{t('privacy.rights.export')}</strong> {t('privacy.rights.exportDesc')}</li>
                    <li><strong>{t('privacy.rights.optout')}</strong> {t('privacy.rights.optoutDesc')}</li>
                  </ul>
                </div>
              </section>

              {/* Section 7 */}
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-vintage-tan/30 rounded-lg flex items-center justify-center">
                    <Bell className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark">
                    7. {t('privacy.changes.title')}
                  </h2>
                </div>
                <div className="prose prose-vintage max-w-none text-vintage-dark/80 pl-13">
                  <p>
                    {t('privacy.changes.content')}
                  </p>
                </div>
              </section>

              {/* Contact */}
              <section className="bg-vintage-cream rounded-xl p-6 mt-8">
                <h3 className="text-lg font-serif font-bold text-vintage-dark mb-3">
                  {t('privacy.contact.title')}
                </h3>
                <p className="text-vintage-dark/70 mb-4">
                  {t('privacy.contact.content')}
                </p>
                <ul className="text-vintage-dark/70 space-y-1">
                  <li><strong>Email:</strong> unstressvn@gmail.com</li>
                  <li><strong>{t('privacy.contact.page')}</strong>{' '}
                    <Link to="/lien-he" className="text-vintage-olive hover:text-vintage-brown font-bold">
                      {t('nav.contact')}
                    </Link>
                  </li>
                </ul>
              </section>

            </div>
          </div>
        </div>
      </div>
    </>
  );
}

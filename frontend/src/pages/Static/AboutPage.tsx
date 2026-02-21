import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/common';
import { BookOpen, Users, Globe, Heart, GraduationCap, MessageSquare } from 'lucide-react';

export default function AboutPage() {
  const { t } = useTranslation();

  return (
    <>
      <SEO 
        title={t('about.seo.title')}
        description={t('about.seo.description')}
        keywords={['về UnstressVN', 'nền tảng học ngoại ngữ', 'cộng đồng học tiếng Đức', 'học tiếng Anh']}
        type="website"
      />

      <div className="container-responsive section-spacing">
        {/* Hero Section */}
        <section className="text-center mb-12 md:mb-16">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif font-bold text-vintage-dark mb-4 md:mb-6">
            {t('about.title')}
          </h1>
          <p className="max-w-2xl mx-auto text-base md:text-lg text-vintage-dark/70 font-serif italic">
            {t('about.subtitle')}
          </p>
          <div className="mt-6 w-24 h-1 bg-vintage-brown mx-auto rounded-full opacity-50"></div>
        </section>

        {/* Mission */}
        <section className="mb-12 md:mb-16">
          <div className="bg-vintage-cream rounded-2xl p-6 md:p-10 border border-vintage-tan/30">
            <div className="flex flex-col md:flex-row items-center gap-6 md:gap-10">
              <div className="w-16 h-16 md:w-20 md:h-20 bg-vintage-olive rounded-2xl flex items-center justify-center flex-shrink-0">
                <GraduationCap className="h-8 w-8 md:h-10 md:w-10 text-white" />
              </div>
              <div>
                <h2 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark mb-3 text-center md:text-left">
                  {t('about.mission.title')}
                </h2>
                <p className="text-vintage-dark/70 leading-relaxed text-sm md:text-base">
                  {t('about.mission.description')}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="mb-12 md:mb-16">
          <h2 className="text-2xl md:text-3xl font-serif font-bold text-vintage-dark mb-8 text-center">
            {t('about.features.title')}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            <div className="bg-white rounded-2xl p-6 border border-vintage-tan/30 shadow-sm text-center card-interactive">
              <div className="w-14 h-14 bg-vintage-olive/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-7 w-7 text-vintage-olive" />
              </div>
              <h3 className="text-lg font-serif font-bold text-vintage-dark mb-2">
                {t('about.features.resources.title')}
              </h3>
              <p className="text-vintage-dark/70 text-sm">
                {t('about.features.resources.description')}
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-vintage-tan/30 shadow-sm text-center card-interactive">
              <div className="w-14 h-14 bg-vintage-blue/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Users className="h-7 w-7 text-vintage-blue" />
              </div>
              <h3 className="text-lg font-serif font-bold text-vintage-dark mb-2">
                {t('about.features.partners.title')}
              </h3>
              <p className="text-vintage-dark/70 text-sm">
                {t('about.features.partners.description')}
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-vintage-tan/30 shadow-sm text-center card-interactive">
              <div className="w-14 h-14 bg-vintage-brown/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="h-7 w-7 text-vintage-brown" />
              </div>
              <h3 className="text-lg font-serif font-bold text-vintage-dark mb-2">
                {t('about.features.community.title')}
              </h3>
              <p className="text-vintage-dark/70 text-sm">
                {t('about.features.community.description')}
              </p>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="mb-12 md:mb-16">
          <div className="bg-gradient-to-r from-vintage-olive to-vintage-brown rounded-2xl p-6 md:p-10 text-white">
            <h2 className="text-xl md:text-2xl font-serif font-bold mb-8 text-center">
              {t('about.stats.title')}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-serif font-bold">10K+</p>
                <p className="text-white/70 text-sm mt-1">{t('about.stats.members')}</p>
              </div>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-serif font-bold">500+</p>
                <p className="text-white/70 text-sm mt-1">{t('about.stats.resources')}</p>
              </div>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-serif font-bold">20+</p>
                <p className="text-white/70 text-sm mt-1">{t('about.stats.languages')}</p>
              </div>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-serif font-bold">50K+</p>
                <p className="text-white/70 text-sm mt-1">{t('about.stats.connections')}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Values */}
        <section>
          <h2 className="text-2xl md:text-3xl font-serif font-bold text-vintage-dark mb-8 text-center">
            {t('about.values.title')}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex gap-4 p-4 md:p-6 bg-vintage-cream/50 rounded-xl">
              <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Globe className="h-5 w-5 text-vintage-olive" />
              </div>
              <div>
                <h3 className="font-serif font-bold text-vintage-dark mb-1">
                  {t('about.values.inclusivity.title')}
                </h3>
                <p className="text-vintage-dark/70 text-sm">
                  {t('about.values.inclusivity.description')}
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-4 md:p-6 bg-vintage-cream/50 rounded-xl">
              <div className="w-10 h-10 bg-vintage-blue/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Heart className="h-5 w-5 text-vintage-blue" />
              </div>
              <div>
                <h3 className="font-serif font-bold text-vintage-dark mb-1">
                  {t('about.values.community.title')}
                </h3>
                <p className="text-vintage-dark/70 text-sm">
                  {t('about.values.community.description')}
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-4 md:p-6 bg-vintage-cream/50 rounded-xl">
              <div className="w-10 h-10 bg-vintage-brown/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <BookOpen className="h-5 w-5 text-vintage-brown" />
              </div>
              <div>
                <h3 className="font-serif font-bold text-vintage-dark mb-1">
                  {t('about.values.quality.title')}
                </h3>
                <p className="text-vintage-dark/70 text-sm">
                  {t('about.values.quality.description')}
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-4 md:p-6 bg-vintage-cream/50 rounded-xl">
              <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <GraduationCap className="h-5 w-5 text-vintage-olive" />
              </div>
              <div>
                <h3 className="font-serif font-bold text-vintage-dark mb-1">
                  {t('about.values.growth.title')}
                </h3>
                <p className="text-vintage-dark/70 text-sm">
                  {t('about.values.growth.description')}
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

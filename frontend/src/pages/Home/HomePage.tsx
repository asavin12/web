import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { resourcesApi, knowledgeApi, utilsApi } from '@/api';
import type { Resource, Video } from '@/types';
import type { KnowledgeArticle } from '@/api/knowledge';
import { ArrowRight, BookOpen, Video as VideoIcon, Play, Eye, FileText, Users, GraduationCap, Clock, Flame, Star, History } from 'lucide-react';
import { VideoCard, BookCard, SEO } from '@/components/common';

export default function HomePage() {
  const { t } = useTranslation();
  const { isAuthenticated, user } = useAuth();
  const [articleSort, setArticleSort] = useState<'most_viewed' | 'newest' | 'oldest' | 'most_featured'>('most_viewed');

  // Fetch top articles
  const { data: topArticles, isLoading: loadingArticles } = useQuery({
    queryKey: ['topArticles', articleSort],
    queryFn: () => knowledgeApi.getTopArticles(articleSort, 5),
  });

  // Fetch latest resources (books)
  const { data: resourcesData, isLoading: loadingResources } = useQuery({
    queryKey: ['resources', 'latest'],
    queryFn: () => resourcesApi.getAll({ page: 1 }),
  });

  // Fetch videos
  const { data: videosData, isLoading: loadingVideos } = useQuery({
    queryKey: ['videos'],
    queryFn: () => utilsApi.getVideos({ is_featured: true, page_size: 4 }),
  });

  const resources = resourcesData?.results || resourcesData || [];
  const videos = videosData?.results || [];

  return (
    <>
      {/* SEO Meta Tags */}
      <SEO 
        title={t('home.seo.title', 'UnstressVN - Học Ngoại Ngữ Dễ Dàng')}
        description={t('home.seo.description', 'Cộng đồng học ngoại ngữ UnstressVN - Tài liệu, video, tin tức và kiến thức học tiếng Đức, tiếng Anh miễn phí.')}
        keywords={['học tiếng đức', 'học tiếng anh', 'tài liệu học', 'video học', 'unstressvn', 'học ngoại ngữ']}
        type="website"
      />

      <div className="pb-12 md:pb-16 lg:pb-20">

        {/* TOP ARTICLES SECTION - Forum Style */}
        <section className="section-spacing container-responsive" aria-label={t('home.topArticles.label', 'Top bài viết')}>
          <header className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-6 border-b-2 border-vintage-tan/30 pb-4">
            <div className="mb-4 sm:mb-0">
              <span className="text-[10px] md:text-xs font-bold text-vintage-olive uppercase tracking-widest mb-1 block">
                {t('home.topArticles.badge', 'Top Bài Viết')}
              </span>
              <h2 className="text-2xl md:text-3xl font-serif font-bold text-vintage-dark flex items-center gap-2">
                <FileText className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive" />
                {t('home.topArticles.title', 'Bài viết nổi bật')}
              </h2>
            </div>
            <Link to="/kien-thuc" className="hidden sm:flex text-sm font-bold text-vintage-olive hover:text-vintage-brown items-center gap-2 transition-colors uppercase tracking-wide">
              {t('home.topArticles.viewAll', 'Xem tất cả')} <ArrowRight className="h-4 w-4" />
            </Link>
          </header>

          {/* Sort Buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            <button
              onClick={() => setArticleSort('most_viewed')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                articleSort === 'most_viewed' 
                  ? 'bg-vintage-olive text-white' 
                  : 'bg-vintage-cream text-vintage-dark hover:bg-vintage-tan/30'
              }`}
            >
              <Flame className="h-4 w-4" />
              {t('home.topArticles.mostViewed', 'Xem nhiều nhất')}
            </button>
            <button
              onClick={() => setArticleSort('newest')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                articleSort === 'newest' 
                  ? 'bg-vintage-olive text-white' 
                  : 'bg-vintage-cream text-vintage-dark hover:bg-vintage-tan/30'
              }`}
            >
              <Clock className="h-4 w-4" />
              {t('home.topArticles.newest', 'Mới nhất')}
            </button>
            <button
              onClick={() => setArticleSort('most_featured')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                articleSort === 'most_featured' 
                  ? 'bg-vintage-olive text-white' 
                  : 'bg-vintage-cream text-vintage-dark hover:bg-vintage-tan/30'
              }`}
            >
              <Star className="h-4 w-4" />
              {t('home.topArticles.featured', 'Nổi bật')}
            </button>
            <button
              onClick={() => setArticleSort('oldest')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                articleSort === 'oldest' 
                  ? 'bg-vintage-olive text-white' 
                  : 'bg-vintage-cream text-vintage-dark hover:bg-vintage-tan/30'
              }`}
            >
              <History className="h-4 w-4" />
              {t('home.topArticles.oldest', 'Cũ nhất')}
            </button>
          </div>

          {/* Articles Table - Forum Style */}
          <div className="bg-white rounded-xl border border-vintage-tan/30 overflow-hidden shadow-sm">
            {/* Table Header */}
            <div className="hidden md:grid grid-cols-12 bg-vintage-cream px-4 py-3 text-xs font-bold text-vintage-dark uppercase tracking-wide border-b border-vintage-tan/30">
              <div className="col-span-1 text-center">#</div>
              <div className="col-span-6">{t('home.topArticles.columnTitle', 'Tiêu đề')}</div>
              <div className="col-span-2">{t('home.topArticles.columnCategory', 'Danh mục')}</div>
              <div className="col-span-2">{t('home.topArticles.columnLevel', 'Trình độ')}</div>
              <div className="col-span-1 text-right">{t('home.topArticles.columnViews', 'Lượt xem')}</div>
            </div>

            {/* Table Body */}
            {loadingArticles ? (
              <div className="divide-y divide-vintage-tan/20">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="grid grid-cols-1 md:grid-cols-12 px-4 py-3 animate-pulse">
                    <div className="col-span-1 flex justify-center"><div className="h-6 w-6 bg-vintage-tan/20 rounded-full"></div></div>
                    <div className="col-span-6"><div className="h-4 bg-vintage-tan/20 rounded w-3/4"></div></div>
                    <div className="col-span-2"><div className="h-4 bg-vintage-tan/20 rounded w-1/2"></div></div>
                    <div className="col-span-2"><div className="h-4 bg-vintage-tan/20 rounded w-1/3"></div></div>
                    <div className="col-span-1"><div className="h-4 bg-vintage-tan/20 rounded w-1/2 ml-auto"></div></div>
                  </div>
                ))}
              </div>
            ) : topArticles && topArticles.length > 0 ? (
              <div className="divide-y divide-vintage-tan/20">
                {topArticles.map((article: KnowledgeArticle, index: number) => (
                  <Link
                    key={article.id}
                    to={`/kien-thuc/${article.category?.slug || 'bai-viet'}/${article.slug}`}
                    className="grid grid-cols-1 md:grid-cols-12 px-4 py-3 hover:bg-vintage-cream/50 transition-colors group"
                  >
                    {/* Rank */}
                    <div className="hidden md:flex col-span-1 items-center justify-center">
                      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                        index === 0 ? 'bg-vintage-tan text-vintage-dark' :
                        index === 1 ? 'bg-vintage-cream text-vintage-dark/70' :
                        index === 2 ? 'bg-vintage-brown/30 text-vintage-brown' :
                        'bg-vintage-tan/30 text-vintage-dark'
                      }`}>
                        {index + 1}
                      </span>
                    </div>

                    {/* Title & Excerpt (Mobile shows all info) */}
                    <div className="col-span-1 md:col-span-6">
                      <div className="flex items-start gap-2">
                        <span className="md:hidden w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold bg-vintage-olive text-white">
                          {index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-serif font-bold text-vintage-dark group-hover:text-vintage-olive transition-colors line-clamp-1">
                            {article.is_featured && <Star className="inline h-4 w-4 text-yellow-500 mr-1" />}
                            {article.title}
                          </h3>
                          <p className="text-xs text-vintage-dark/60 line-clamp-1 mt-0.5">
                            {article.excerpt}
                          </p>
                          {/* Mobile: Show category & level inline */}
                          <div className="md:hidden flex flex-wrap gap-2 mt-1.5">
                            {article.category && (
                              <span className="text-xs px-2 py-0.5 bg-vintage-tan/20 text-vintage-dark rounded-full">
                                {article.category.name}
                              </span>
                            )}
                            {article.level_display && (
                              <span className="text-xs px-2 py-0.5 bg-vintage-olive/10 text-vintage-olive rounded-full">
                                {article.level_display}
                              </span>
                            )}
                            <span className="text-xs text-vintage-dark/50 flex items-center gap-1">
                              <Eye className="h-3 w-3" /> {article.view_count}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Category (Desktop) */}
                    <div className="hidden md:flex col-span-2 items-center">
                      {article.category && (
                        <span className="text-sm text-vintage-dark/70 px-2 py-1 bg-vintage-tan/20 rounded-lg truncate">
                          {article.category.name}
                        </span>
                      )}
                    </div>

                    {/* Level (Desktop) */}
                    <div className="hidden md:flex col-span-2 items-center">
                      {article.level_display && (
                        <span className="text-sm px-2 py-1 bg-vintage-olive/10 text-vintage-olive rounded-lg">
                          {article.level_display}
                        </span>
                      )}
                    </div>

                    {/* View Count (Desktop) */}
                    <div className="hidden md:flex col-span-1 items-center justify-end">
                      <span className="flex items-center gap-1 text-sm text-vintage-dark/60">
                        <Eye className="h-4 w-4" />
                        {article.view_count}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-vintage-dark/50">
                <FileText className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p>{t('home.topArticles.noArticles', 'Chưa có bài viết nào')}</p>
              </div>
            )}
          </div>

          <div className="mt-4 text-center sm:hidden">
            <Link to="/kien-thuc" className="touch-target inline-flex items-center gap-2 text-sm font-bold text-vintage-olive uppercase">
              {t('home.topArticles.viewAll', 'Xem tất cả bài viết')} <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

        <div className="space-y-16 md:space-y-20 lg:space-y-24 container-responsive">
          {/* BOOKS SECTION */}
          {Array.isArray(resources) && resources.length > 0 && (
            <section aria-labelledby="books-heading" className="relative">
              <header className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-6 md:mb-10 border-b-2 border-vintage-tan/30 pb-4">
                <div className="mb-4 sm:mb-0">
                  <span className="text-[10px] md:text-xs font-bold text-vintage-brown uppercase tracking-widest mb-1 block">
                    {t('home.books.badge', 'New Arrivals')}
                  </span>
                  <h2 id="books-heading" className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark flex items-center gap-2 md:gap-3">
                    <BookOpen className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive" />
                    {t('home.features.resources.title', 'Recommended Reading')}
                  </h2>
                </div>
                <Link to="/tai-lieu" className="hidden sm:flex text-sm font-bold text-vintage-olive hover:text-vintage-brown items-center gap-2 transition-colors uppercase tracking-wide">
                  {t('home.books.viewAll', 'Browse Stacks')} <ArrowRight className="h-4 w-4" />
                </Link>
              </header>
              
              {/* Book grid - 3 rows x 6 columns = 18 books max */}
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 md:gap-4 lg:gap-6">
                {resources.slice(0, 12).map((resource: Resource) => (
                  <BookCard key={resource.id} resource={resource} />
                ))}
              </div>
              
              <div className="mt-6 md:mt-10 text-center sm:hidden">
                <Link to="/tai-lieu" className="touch-target inline-flex items-center gap-2 text-sm font-bold text-vintage-brown uppercase">
                  {t('home.books.viewAll', 'View All Books')} <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </section>
          )}

          {/* VIDEOS SECTION */}
          {Array.isArray(videos) && videos.length > 0 && (
            <section aria-labelledby="videos-heading" className="relative">
              <div className="hidden md:block absolute inset-0 bg-vintage-cream/50 -mx-4 lg:-mx-8 rounded-2xl lg:rounded-[3rem] -z-10 transform -skew-y-1 border border-vintage-tan/20" />
              
              <div className="py-6 md:py-12">
                <header className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-6 md:mb-10">
                  <div className="mb-4 sm:mb-0">
                    <span className="text-[10px] md:text-xs font-bold text-vintage-blue uppercase tracking-widest mb-1 block">
                      {t('home.videos.badge', 'Media Archive')}
                    </span>
                    <h2 id="videos-heading" className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark flex items-center gap-2 md:gap-3">
                      <VideoIcon className="h-6 w-6 md:h-8 md:w-8 text-vintage-blue" />
                      {t('home.videos.title', 'Curated Video Lessons')}
                    </h2>
                  </div>
                  <Link to="/video" className="hidden sm:flex text-sm font-bold text-vintage-blue hover:text-vintage-brown items-center gap-2 transition-colors uppercase tracking-wide">
                    {t('home.videos.viewAll', 'Watch All')} <ArrowRight className="h-4 w-4" />
                  </Link>
                </header>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 lg:gap-8">
                  {videos.slice(0, 8).map((video: Video) => (
                    <VideoCard key={video.id} video={video} />
                  ))}
                </div>
                
                <div className="mt-6 text-center sm:hidden">
                  <Link to="/video" className="touch-target inline-flex items-center gap-2 text-sm font-bold text-vintage-blue uppercase">
                    {t('home.videos.viewAll', 'Watch All Videos')} <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </section>
          )}

          {/* FEATURES SECTION */}
          <section aria-labelledby="features-heading" className="relative section-spacing">
            <header className="text-center mb-8 md:mb-12">
              <h2 id="features-heading" className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark mb-4">
                {t('home.features.title', 'Why UnstressVN?')}
              </h2>
              <div className="w-16 md:w-24 h-1 bg-vintage-brown mx-auto rounded-full opacity-50"></div>
            </header>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
              <article className="bg-white rounded-2xl p-6 md:p-8 border border-vintage-tan/30 shadow-lg hover:shadow-xl transition-all group card-interactive">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-olive/10 rounded-xl md:rounded-2xl flex items-center justify-center mb-4 md:mb-6 group-hover:bg-vintage-olive transition-colors">
                  <BookOpen className="h-6 w-6 md:h-8 md:w-8 text-vintage-olive group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark mb-2 md:mb-3">
                  {t('home.features.resources.title', 'Thư viện phong phú')}
                </h3>
                <p className="text-vintage-dark/70 mb-4 md:mb-6 font-serif italic text-sm md:text-base line-clamp-3">
                  {t('home.features.resources.description', 'Tài liệu học tiếng Đức, tiếng Anh được tuyển chọn kỹ lưỡng.')}
                </p>
                <Link to="/tai-lieu" className="touch-target inline-flex items-center gap-2 text-vintage-olive font-bold uppercase tracking-wide hover:text-vintage-brown transition-colors text-sm">
                  {t('home.features.resources.cta', 'Xem tài liệu')} <ArrowRight className="h-4 w-4" />
                </Link>
              </article>

              <article className="bg-white rounded-2xl p-6 md:p-8 border border-vintage-tan/30 shadow-lg hover:shadow-xl transition-all group card-interactive">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-blue/10 rounded-xl md:rounded-2xl flex items-center justify-center mb-4 md:mb-6 group-hover:bg-vintage-blue transition-colors">
                  <Users className="h-6 w-6 md:h-8 md:w-8 text-vintage-blue group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark mb-2 md:mb-3">
                  {t('home.features.news.title', 'Tin tức & Kiến thức')}
                </h3>
                <p className="text-vintage-dark/70 mb-4 md:mb-6 font-serif italic text-sm md:text-base line-clamp-3">
                  {t('home.features.news.description', 'Cập nhật tin tức du học, cuộc sống và kiến thức ngôn ngữ.')}
                </p>
                <Link to="/tin-tuc" className="touch-target inline-flex items-center gap-2 text-vintage-blue font-bold uppercase tracking-wide hover:text-vintage-brown transition-colors text-sm">
                  {t('home.features.news.cta', 'Đọc tin tức')} <ArrowRight className="h-4 w-4" />
                </Link>
              </article>

              <article className="bg-white rounded-2xl p-6 md:p-8 border border-vintage-tan/30 shadow-lg hover:shadow-xl transition-all group card-interactive">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-brown/10 rounded-xl md:rounded-2xl flex items-center justify-center mb-4 md:mb-6 group-hover:bg-vintage-brown transition-colors">
                  <Play className="h-6 w-6 md:h-8 md:w-8 text-vintage-brown group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl md:text-2xl font-serif font-bold text-vintage-dark mb-2 md:mb-3">
                  {t('home.features.videos.title', 'Video học tập')}
                </h3>
                <p className="text-vintage-dark/70 mb-4 md:mb-6 font-serif italic text-sm md:text-base line-clamp-3">
                  {t('home.features.videos.description', 'Video bài giảng, phim ngắn và nội dung học tập đa dạng.')}
                </p>
                <Link to="/video" className="touch-target inline-flex items-center gap-2 text-vintage-brown font-bold uppercase tracking-wide hover:text-vintage-olive transition-colors text-sm">
                  {t('home.features.videos.cta', 'Xem video')} <ArrowRight className="h-4 w-4" />
                </Link>
              </article>
            </div>
          </section>

          {/* HOW IT WORKS */}
          <section aria-labelledby="how-it-works" className="relative">
            <header className="text-center mb-8 md:mb-12">
              <span className="text-[10px] md:text-xs font-bold text-vintage-blue uppercase tracking-widest mb-2 block">
                {t('home.howItWorks.badge', 'Bắt đầu')}
              </span>
              <h2 id="how-it-works" className="text-2xl md:text-3xl lg:text-4xl font-serif font-bold text-vintage-dark mb-4">
                {t('home.howItWorks.title', 'Cách sử dụng UnstressVN')}
              </h2>
              <p className="max-w-2xl mx-auto text-vintage-dark/70 font-serif italic text-sm md:text-base">
                {t('home.howItWorks.subtitle', 'Bắt đầu hành trình học ngoại ngữ chỉ với 3 bước đơn giản')}
              </p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
              <div className="hidden md:block absolute top-16 left-1/6 right-1/6 h-0.5 bg-vintage-tan/30" />
              
              <div className="text-center relative">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-olive text-white rounded-full flex items-center justify-center mx-auto mb-4 font-serif font-bold text-xl md:text-2xl shadow-lg relative z-10">
                  1
                </div>
                <h3 className="text-lg md:text-xl font-serif font-bold text-vintage-dark mb-2">
                  {t('home.howItWorks.step1.title', 'Đọc bài viết')}
                </h3>
                <p className="text-vintage-dark/70 text-sm md:text-base">
                  {t('home.howItWorks.step1.description', 'Khám phá kho kiến thức với các bài viết về ngữ pháp, từ vựng và kinh nghiệm học tập.')}
                </p>
              </div>

              <div className="text-center relative">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-blue text-white rounded-full flex items-center justify-center mx-auto mb-4 font-serif font-bold text-xl md:text-2xl shadow-lg relative z-10">
                  2
                </div>
                <h3 className="text-lg md:text-xl font-serif font-bold text-vintage-dark mb-2">
                  {t('home.howItWorks.step2.title', 'Tải tài liệu')}
                </h3>
                <p className="text-vintage-dark/70 text-sm md:text-base">
                  {t('home.howItWorks.step2.description', 'Tải sách, giáo trình và tài liệu học tiếng Đức, tiếng Anh miễn phí.')}
                </p>
              </div>

              <div className="text-center relative">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-vintage-brown text-white rounded-full flex items-center justify-center mx-auto mb-4 font-serif font-bold text-xl md:text-2xl shadow-lg relative z-10">
                  3
                </div>
                <h3 className="text-lg md:text-xl font-serif font-bold text-vintage-dark mb-2">
                  {t('home.howItWorks.step3.title', 'Sử dụng công cụ')}
                </h3>
                <p className="text-vintage-dark/70 text-sm md:text-base">
                  {t('home.howItWorks.step3.description', 'Học flashcard, luyện phát âm và tra cứu từ điển với các công cụ tiện ích.')}
                </p>
              </div>
            </div>
          </section>

          {/* CTA BANNER */}
          {!isAuthenticated && (
            <section className="bg-gradient-to-r from-vintage-olive to-vintage-brown rounded-2xl p-6 md:p-10 lg:p-12 text-center text-white">
              <GraduationCap className="h-10 w-10 md:h-12 md:w-12 mx-auto mb-4 opacity-80" />
              <h2 className="text-xl md:text-2xl lg:text-3xl font-serif font-bold mb-3 md:mb-4">
                {t('home.cta.title', 'Sẵn sàng bắt đầu hành trình học tập?')}
              </h2>
              <p className="text-white/80 mb-6 md:mb-8 max-w-xl mx-auto text-sm md:text-base">
                {t('home.cta.description', 'Tham gia cùng hàng nghìn người học ngoại ngữ. Truy cập tài liệu miễn phí và kết nối với cộng đồng.')}
              </p>
              <div className="flex flex-col sm:flex-row gap-3 md:gap-4 justify-center">
                <Link 
                  to="/dang-ky" 
                  className="touch-target inline-flex items-center justify-center gap-2 px-6 md:px-8 py-3 bg-white text-vintage-olive font-bold uppercase tracking-wide rounded-lg hover:bg-vintage-cream transition-colors shadow-md text-sm md:text-base"
                >
                  {t('home.cta.signup', 'Đăng ký miễn phí')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link 
                  to="/gioi-thieu" 
                  className="touch-target inline-flex items-center justify-center gap-2 px-6 md:px-8 py-3 bg-transparent text-white font-bold uppercase tracking-wide rounded-lg border-2 border-white/50 hover:bg-white/10 transition-colors text-sm md:text-base"
                >
                  {t('home.cta.learn', 'Tìm hiểu thêm')}
                </Link>
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

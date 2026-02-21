import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, Facebook, Twitter, Instagram, Youtube } from 'lucide-react';

export default function Footer() {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-vintage-dark text-vintage-cream mt-auto safe-area-bottom">
      {/* Decorative border */}
      <div className="h-1 md:h-2 bg-gradient-to-r from-vintage-olive via-vintage-brown to-vintage-olive"></div>
      
      <div className="container-responsive py-8 md:py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
          {/* Logo & Description - Full width on mobile */}
          <div className="col-span-2 md:col-span-2">
            <Link to="/" className="flex items-center gap-2 md:gap-3 mb-3 md:mb-4 group">
              <img 
                src="/static/logos/unstressvn-logo-footer.webp" 
                alt="UnstressVN" 
                className="h-10 md:h-12 w-auto object-contain group-hover:opacity-90 transition-opacity"
              />
              <div className="flex flex-col">
                <span className="text-lg md:text-xl font-serif font-bold text-vintage-cream group-hover:text-vintage-tan transition-colors">
                  UnstressVN
                </span>
                <span className="text-[10px] md:text-xs text-vintage-tan/70 uppercase tracking-wider">
                  {t('app.tagline', 'Học ngoại ngữ dễ dàng')}
                </span>
              </div>
            </Link>
            <p className="text-vintage-tan/80 font-serif italic leading-relaxed max-w-md text-sm md:text-base hidden sm:block">
              {t('home.hero.subtitle')}
            </p>
            
            {/* Social Links */}
            <div className="mt-4 md:mt-6 flex items-center gap-3">
              <a href="https://facebook.com/unstressvn" target="_blank" rel="noopener noreferrer" className="p-2 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive transition-colors" aria-label="Facebook">
                <Facebook className="h-4 w-4" />
              </a>
              <a href="https://twitter.com/unstressvn" target="_blank" rel="noopener noreferrer" className="p-2 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive transition-colors" aria-label="Twitter">
                <Twitter className="h-4 w-4" />
              </a>
              <a href="https://instagram.com/unstressvn" target="_blank" rel="noopener noreferrer" className="p-2 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive transition-colors" aria-label="Instagram">
                <Instagram className="h-4 w-4" />
              </a>
              <a href="https://youtube.com/@unstressvn" target="_blank" rel="noopener noreferrer" className="p-2 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive transition-colors" aria-label="Youtube">
                <Youtube className="h-4 w-4" />
              </a>
            </div>
            
            {/* Contact Info - Desktop only */}
            <div className="hidden md:block mt-6 space-y-2 text-sm text-vintage-tan/70">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                <span>unstressvn@gmail.com</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                <span>{t('contact.location.address', 'Hanoi, Vietnam')}</span>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-serif font-bold text-base md:text-lg mb-3 md:mb-4 text-vintage-cream">
              {t('footer.explore')}
            </h4>
            <ul className="space-y-2 md:space-y-3">
              <li>
                <Link to="/kien-thuc" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.knowledge')}
                </Link>
              </li>
              <li>
                <Link to="/tai-lieu" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.resources')}
                </Link>
              </li>
              <li>
                <Link to="/cong-cu" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.tools')}
                </Link>
              </li>
              <li>
                <Link to="/tin-tuc" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.news')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="font-serif font-bold text-base md:text-lg mb-3 md:mb-4 text-vintage-cream">
              {t('footer.support')}
            </h4>
            <ul className="space-y-2 md:space-y-3">
              <li>
                <Link to="/gioi-thieu" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.about')}
                </Link>
              </li>
              <li>
                <Link to="/lien-he" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.contact')}
                </Link>
              </li>
              <li>
                <Link to="/dieu-khoan" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.terms')}
                </Link>
              </li>
              <li>
                <Link to="/chinh-sach-bao-mat" className="text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium">
                  {t('footer.privacy')}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-vintage-tan/20 mt-6 md:mt-10 pt-6 md:pt-8 text-center">
          <p className="text-vintage-tan/60 text-xs md:text-sm font-medium">
            © {currentYear} UnstressVN. {t('footer.allRightsReserved')}
          </p>
          <p className="text-vintage-tan/40 text-[10px] md:text-xs mt-1 md:mt-2 uppercase tracking-widest">
            {t('footer.craftedWith')}
          </p>
        </div>
      </div>
    </footer>
  );
}

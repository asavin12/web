import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin } from 'lucide-react';
import { useNavigation, getIcon, getLocalizedName, type NavLink } from '@/hooks/useNavigation';

// Section labels — mapped from DB footer_section values
const SECTION_LABELS: Record<string, Record<string, string>> = {
  resources: { vi: 'Khám phá', en: 'Explore', de: 'Entdecken' },
  company: { vi: 'Hỗ trợ', en: 'Support', de: 'Unterstützung' },
  legal: { vi: 'Pháp lý', en: 'Legal', de: 'Rechtliches' },
  community: { vi: 'Cộng đồng', en: 'Community', de: 'Gemeinschaft' },
};

// Display order for footer sections
const SECTION_ORDER = ['resources', 'company', 'legal', 'community'];

function FooterLink({ item, lang }: { item: NavLink; lang: string }) {
  const label = getLocalizedName(item, lang);
  const cls = "text-vintage-tan/80 hover:text-vintage-cream transition-colors text-xs md:text-sm uppercase tracking-wide font-medium";

  if (item.is_external || item.open_in_new_tab) {
    return (
      <a href={item.url} target="_blank" rel="noopener noreferrer" className={cls}>
        {label}
      </a>
    );
  }
  return <Link to={item.url} className={cls}>{label}</Link>;
}

function SocialLink({ item }: { item: NavLink }) {
  const IconComp = getIcon(item.icon);
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="p-2 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive transition-colors"
      aria-label={item.name}
    >
      {IconComp ? <IconComp className="h-4 w-4" /> : <span className="text-xs">{item.name}</span>}
    </a>
  );
}

export default function Footer() {
  const { t, i18n } = useTranslation();
  const { footer } = useNavigation();
  const currentYear = new Date().getFullYear();
  const lang = i18n.language || 'vi';

  const socialLinks = footer.social || [];
  const sections = SECTION_ORDER
    .filter(key => footer[key] && footer[key].length > 0)
    .map(key => ({ key, label: SECTION_LABELS[key]?.[lang] || SECTION_LABELS[key]?.vi || key, items: footer[key] }));

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
            
            {/* Social Links — dynamic from DB */}
            {socialLinks.length > 0 && (
              <div className="mt-4 md:mt-6 flex items-center gap-3">
                {socialLinks.map((link: NavLink) => (
                  <SocialLink key={link.id} item={link} />
                ))}
              </div>
            )}
            
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

          {/* Dynamic footer sections from DB */}
          {sections.map(({ key, label, items }) => (
            <div key={key}>
              <h4 className="font-serif font-bold text-base md:text-lg mb-3 md:mb-4 text-vintage-cream">
                {label}
              </h4>
              <ul className="space-y-2 md:space-y-3">
                {items.map((item: NavLink) => (
                  <li key={item.id}>
                    <FooterLink item={item} lang={lang} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
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

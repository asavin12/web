import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, MapPin, Phone, Heart } from 'lucide-react';
import { useNavigation, getIcon, getLocalizedName, type NavLink } from '@/hooks/useNavigation';

// Section labels — mapped from DB footer_section values
const SECTION_LABELS: Record<string, Record<string, string>> = {
  resources: { vi: 'Học tập', en: 'Learning', de: 'Lernen' },
  company: { vi: 'Về chúng tôi', en: 'About Us', de: 'Über uns' },
  legal: { vi: 'Pháp lý', en: 'Legal', de: 'Rechtliches' },
  community: { vi: 'Cộng đồng', en: 'Community', de: 'Gemeinschaft' },
};

// Display order for non-social footer sections
const SECTION_ORDER = ['resources', 'company', 'community', 'legal'];

function FooterLink({ item, lang }: { item: NavLink; lang: string }) {
  const label = getLocalizedName(item, lang);

  if (item.is_external || item.open_in_new_tab) {
    return (
      <a href={item.url} target="_blank" rel="noopener noreferrer"
        className="text-vintage-tan/70 hover:text-vintage-cream transition-colors text-sm leading-relaxed">
        {label}
      </a>
    );
  }
  return (
    <Link to={item.url}
      className="text-vintage-tan/70 hover:text-vintage-cream transition-colors text-sm leading-relaxed">
      {label}
    </Link>
  );
}

function SocialLink({ item }: { item: NavLink }) {
  const IconComp = getIcon(item.icon);
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="p-2.5 rounded-full bg-vintage-tan/10 hover:bg-vintage-olive/80 transition-all duration-200 hover:scale-110"
      aria-label={item.name}
      title={item.name}
    >
      {IconComp ? <IconComp className="h-4 w-4" /> : <span className="text-xs font-bold">{item.name.slice(0, 2)}</span>}
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
    <footer className="bg-vintage-dark text-vintage-cream mt-auto safe-area-bottom" role="contentinfo"
      itemScope itemType="https://schema.org/WPFooter">
      {/* Decorative top border */}
      <div className="h-1 bg-gradient-to-r from-vintage-olive via-vintage-brown to-vintage-olive"></div>

      <div className="container-responsive py-10 md:py-14">
        {/* ═══ Main Grid: Brand + Nav Sections ═══ */}
        <div className="grid grid-cols-2 md:grid-cols-12 gap-8 md:gap-6">

          {/* ── Brand Column (wider) ── */}
          <div className="col-span-2 md:col-span-4 lg:col-span-4">
            <Link to="/" className="flex items-center gap-3 mb-4 group">
              <img
                src="/static/logos/unstressvn-logo-footer.webp"
                alt="UnstressVN - Dự án giáo dục phi lợi nhuận"
                className="h-11 w-auto object-contain group-hover:opacity-90 transition-opacity"
                width="44" height="44"
              />
              <div className="flex flex-col">
                <span className="text-xl font-serif font-bold text-vintage-cream group-hover:text-vintage-tan transition-colors">
                  UnstressVN
                </span>
                <span className="text-[10px] text-vintage-tan/60 uppercase tracking-widest">
                  {t('footer.orgType', 'Dự án giáo dục phi lợi nhuận')}
                </span>
              </div>
            </Link>

            <p className="text-vintage-tan/70 text-sm leading-relaxed max-w-sm mb-5">
              {t('footer.description', 'Cung cấp công cụ học ngoại ngữ ứng dụng AI hoàn toàn miễn phí. Xoá bỏ áp lực, tối ưu hoá lộ trình tự học với phương pháp Comprehensible Input & Shadowing.')}
            </p>

            {/* Social Links */}
            {socialLinks.length > 0 && (
              <div className="flex items-center gap-2 mb-6">
                {socialLinks.map((link: NavLink) => (
                  <SocialLink key={link.id} item={link} />
                ))}
              </div>
            )}

            {/* Contact Info — visible on all sizes for SEO */}
            <address className="not-italic space-y-2 text-sm text-vintage-tan/60"
              itemScope itemType="https://schema.org/PostalAddress">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 mt-0.5 shrink-0" />
                <span itemProp="streetAddress">Tầng 11, Chung cư CT1, Khu đô thị Văn Khê, Phường La Khê, Quận Hà Đông, Hà Nội</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 shrink-0" />
                <a href="mailto:unstressvn@gmail.com" className="hover:text-vintage-cream transition-colors"
                  itemProp="email">unstressvn@gmail.com</a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 shrink-0" />
                <a href="tel:+84123456789" className="hover:text-vintage-cream transition-colors"
                  itemProp="telephone">+84 (0) 123 456 789</a>
              </div>
            </address>
          </div>

          {/* ── Navigation Sections (evenly spaced) ── */}
          {sections.map(({ key, label, items }) => (
            <div key={key} className="col-span-1 md:col-span-2 lg:col-span-2">
              <h3 className="font-serif font-bold text-sm md:text-base mb-3 text-vintage-cream uppercase tracking-wide">
                {label}
              </h3>
              <nav aria-label={label}>
                <ul className="space-y-2">
                  {items.map((item: NavLink) => (
                    <li key={item.id}>
                      <FooterLink item={item} lang={lang} />
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          ))}
        </div>

        {/* ═══ Bottom Bar: Copyright + Badges ═══ */}
        <div className="border-t border-vintage-tan/15 mt-10 pt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-vintage-tan/50 text-xs">
            <p>
              © {currentYear} UnstressVN. {t('footer.allRightsReserved')}
            </p>
            <p className="flex items-center gap-1.5 uppercase tracking-widest">
              {t('footer.craftedWith', 'Được tạo ra với')} <Heart className="h-3 w-3 text-red-400 fill-red-400" /> {t('footer.craftedFor', 'cho người học ngoại ngữ')}
            </p>
          </div>
        </div>
      </div>

      {/* ═══ JSON-LD Organization Schema (SEO) ═══ */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'EducationalOrganization',
        name: 'UnstressVN',
        alternateName: 'UnStress VN',
        url: 'https://unstressvn.com',
        logo: 'https://unstressvn.com/static/logos/unstressvn-logo-full.webp',
        description: 'Dự án giáo dục phi lợi nhuận cung cấp công cụ học ngoại ngữ ứng dụng AI hoàn toàn miễn phí hoặc chi phí thấp. Phương pháp Comprehensible Input & Shadowing.',
        foundingDate: '2024',
        address: {
          '@type': 'PostalAddress',
          streetAddress: 'Tầng 11, Chung cư CT1, Khu đô thị Văn Khê, Phường La Khê',
          addressLocality: 'Hà Nội',
          addressRegion: 'Hà Nội',
          addressCountry: 'VN',
        },
        contactPoint: {
          '@type': 'ContactPoint',
          email: 'unstressvn@gmail.com',
          contactType: 'customer service',
          availableLanguage: ['Vietnamese', 'English', 'German'],
        },
        sameAs: [
          'https://facebook.com/unstressvn',
          'https://youtube.com/@unstressvn',
          'https://tiktok.com/@unstressvn',
          'https://t.me/unstressvn',
          'https://discord.gg/unstressvn',
        ],
        nonprofitStatus: 'Nonprofit',
      }) }} />
    </footer>
  );
}

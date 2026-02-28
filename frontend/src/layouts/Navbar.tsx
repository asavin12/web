import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { useClickOutside, useNotifications, useNavigation, getIcon, getLocalizedName } from '@/hooks';
import type { NavLink as NavLinkType, NavChild } from '@/hooks';
import { changeLanguage, languages } from '@/i18n';
import { Menu, X, Search, Bell, User, Settings, LogOut, Globe, Shield, ExternalLink, BellOff, Heart, MessageSquare, ChevronDown, Newspaper, BookOpen, FileText, GraduationCap, Languages, Users, Wrench } from 'lucide-react';
import api from '@/api/client';
import { useToast } from '@/components/ui/Toast';

export default function Navbar() {
  const { t, i18n } = useTranslation();
  const { user, profile, isAuthenticated, logout } = useAuth();
  const { notifications, unreadCount: notificationUnreadCount, markAsRead, markAllRead, isLoading: notificationsLoading } = useNotifications();
  const { navbar } = useNavigation();
  const { error: showError } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const lang = i18n.language;
  
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  // Dynamic dropdown states — keyed by NavLink id
  const [openDropdownId, setOpenDropdownId] = useState<number | null>(null);
  const [isLoadingAdmin, setIsLoadingAdmin] = useState(false);
  
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const langRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationRef = useRef<HTMLDivElement>(null);
  // Dynamic dropdown refs — one per dropdown
  const dropdownRefs = useRef<Record<number, HTMLDivElement | null>>({});
  // Hover delay timer for dropdowns (desktop only)
  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Click outside handlers
  const closeSearch = useCallback(() => setIsSearchOpen(false), []);
  const closeLang = useCallback(() => setIsLangMenuOpen(false), []);
  const closeUserMenu = useCallback(() => setIsUserMenuOpen(false), []);
  const closeNotification = useCallback(() => setIsNotificationOpen(false), []);

  useClickOutside(searchRef, closeSearch, isSearchOpen);
  useClickOutside(langRef, closeLang, isLangMenuOpen);
  useClickOutside(userMenuRef, closeUserMenu, isUserMenuOpen);
  useClickOutside(notificationRef, closeNotification, isNotificationOpen);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (openDropdownId === null) return;
    const handler = (e: MouseEvent) => {
      const ref = dropdownRefs.current[openDropdownId];
      if (ref && !ref.contains(e.target as Node)) {
        setOpenDropdownId(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [openDropdownId]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleAdminAccess = async () => {
    setIsUserMenuOpen(false);
    setIsLoadingAdmin(true);
    
    try {
      const response = await api.get('/admin-access/');
      const { admin_url } = response.data;
      
      // Redirect to admin gateway with secret key
      window.location.href = admin_url;
    } catch (error: unknown) {
      const err = error as { response?: { status?: number } };
      if (err.response?.status === 403) {
        showError(t('errors.noPermission', 'Không có quyền truy cập'));
      } else {
        showError(t('errors.serverError', 'Lỗi server'));
      }
    } finally {
      setIsLoadingAdmin(false);
    }
  };

  const navLinks = navbar.directLinks.map(link => ({
    to: link.url,
    label: getLocalizedName(link, lang),
  }));

  // Fallback if API hasn't loaded yet
  const fallbackNavLinks = [
    { to: '/', label: t('nav.home', 'Trang chủ') },
    { to: '/video', label: t('nav.videos', 'Video') },
    { to: '/tai-lieu', label: t('nav.resources', 'Thư viện') },
    { to: '/tin-tuc', label: t('nav.news', 'Tin tức') },
    { to: '/kien-thuc', label: t('nav.knowledge', 'Kiến thức') },
    { to: '/cong-cu', label: t('nav.tools', 'Công cụ') },
    { to: '/stream', label: t('nav.stream', 'Xem phim') },
  ];

  const displayNavLinks = navLinks.length > 0 ? navLinks : fallbackNavLinks;
  const displayDropdowns = navbar.dropdowns;

  // ── Render helper: dropdown child item ──
  const renderChildItem = (child: NavChild, onClose: () => void) => {
    const IconComp = getIcon(child.icon);
    const label = getLocalizedName(child, lang);
    const isFirstChild = child.order === 1; // "All" item = parent-style

    if (child.is_coming_soon) {
      return (
        <div
          key={child.id}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-vintage-dark/50 cursor-not-allowed"
        >
          {IconComp && <IconComp className="h-4 w-4 text-vintage-olive/50" />}
          {label}
          <span className="ml-auto text-[10px] bg-vintage-tan/30 text-vintage-olive px-1.5 py-0.5 rounded-full">
            {child.badge_text || t('common.soon', 'Soon')}
          </span>
        </div>
      );
    }

    if (child.is_external || child.open_in_new_tab) {
      return (
        <a
          key={child.id}
          href={child.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClose}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-vintage-dark hover:bg-vintage-tan/20 transition-colors"
        >
          {IconComp && <IconComp className="h-4 w-4 text-vintage-olive" />}
          {label}
          <ExternalLink className="h-3 w-3 ml-auto text-vintage-tan" />
        </a>
      );
    }

    return (
      <Link
        key={child.id}
        to={child.url}
        onClick={onClose}
        className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
          isFirstChild
            ? 'text-vintage-olive font-semibold hover:bg-vintage-olive/10'
            : 'text-vintage-dark hover:bg-vintage-tan/20 pl-6'
        }`}
      >
        {IconComp && <IconComp className={`h-4 w-4 ${isFirstChild ? 'text-vintage-olive' : 'text-vintage-tan'}`} />}
        {label}
      </Link>
    );
  };

  // ── Hover handlers for desktop dropdowns (open on hover, close with small delay) ──
  const handleDropdownEnter = useCallback((id: number) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
      hoverTimeoutRef.current = null;
    }
    setOpenDropdownId(id);
  }, []);

  const handleDropdownLeave = useCallback(() => {
    hoverTimeoutRef.current = setTimeout(() => {
      setOpenDropdownId(null);
    }, 150); // 150ms grace period to move cursor into panel
  }, []);

  // Clean up hover timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    };
  }, []);

  // ── Render helper: desktop dropdown (hover to open) ──
  const renderDesktopDropdown = (dropdown: NavLinkType) => {
    const isOpen = openDropdownId === dropdown.id;
    const label = getLocalizedName(dropdown, lang);
    const isActiveRoute = location.pathname.startsWith(dropdown.url);

    return (
      <div
        key={dropdown.id}
        className="relative"
        ref={el => { dropdownRefs.current[dropdown.id] = el; }}
        onMouseEnter={() => handleDropdownEnter(dropdown.id)}
        onMouseLeave={handleDropdownLeave}
      >
        <button
          onClick={() => setOpenDropdownId(isOpen ? null : dropdown.id)}
          className={`${
            isActiveRoute
              ? 'text-vintage-brown border-vintage-brown'
              : 'text-vintage-dark/60 border-transparent hover:text-vintage-olive hover:border-vintage-tan'
          } inline-flex items-center gap-1 px-1 pt-1 border-b-2 text-sm font-semibold tracking-wide transition-all duration-200 uppercase`}
        >
          {label}
          <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute left-0 top-full mt-1 w-64 bg-vintage-cream rounded-xl shadow-xl py-2 z-50 border border-vintage-tan animate-in fade-in slide-in-from-top-2 duration-150">
            {dropdown.children.map((child, idx) => (
              <div key={child.id}>
                {idx === 1 && <div className="my-1 border-t border-vintage-tan/30" />}
                {renderChildItem(child, () => setOpenDropdownId(null))}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // ── Render helper: mobile dropdown section ──
  const renderMobileDropdownSection = (dropdown: NavLinkType) => {
    const label = getLocalizedName(dropdown, lang);
    return (
      <div key={dropdown.id} className="pt-2">
        <p className="px-4 py-2 text-xs font-bold text-vintage-tan uppercase tracking-wide">{label}</p>
        {dropdown.children.map(child => renderMobileChildItem(child))}
      </div>
    );
  };

  const renderMobileChildItem = (child: NavChild) => {
    const IconComp = getIcon(child.icon);
    const label = getLocalizedName(child, lang);
    const isFirstChild = child.order === 1;

    if (child.is_coming_soon) {
      return (
        <div
          key={child.id}
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-vintage-dark/50 cursor-not-allowed"
        >
          {IconComp && <IconComp className="h-4 w-4 text-vintage-olive/50" />}
          {label}
          <span className="ml-auto text-[10px] bg-vintage-tan/30 text-vintage-olive px-1.5 py-0.5 rounded-full">
            {child.badge_text || t('common.soon', 'Soon')}
          </span>
        </div>
      );
    }

    if (child.is_external || child.open_in_new_tab) {
      return (
        <a
          key={child.id}
          href={child.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => setIsMobileMenuOpen(false)}
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-vintage-dark hover:bg-vintage-tan/20"
        >
          {IconComp && <IconComp className="h-4 w-4 text-vintage-olive" />}
          {label}
          <ExternalLink className="h-3 w-3 ml-auto text-vintage-tan" />
        </a>
      );
    }

    return (
      <Link
        key={child.id}
        to={child.url}
        onClick={() => setIsMobileMenuOpen(false)}
        className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm ${
          isFirstChild
            ? 'text-vintage-olive font-semibold hover:bg-vintage-olive/10'
            : 'text-vintage-dark hover:bg-vintage-tan/20 pl-8'
        }`}
      >
        {IconComp && <IconComp className={`h-4 w-4 ${isFirstChild ? 'text-vintage-olive' : 'text-vintage-tan'}`} />}
        {label}
      </Link>
    );
  };

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };
  
  // Focus input when search opens
  useEffect(() => {
    if (isSearchOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isSearchOpen]);

  const handleSearchChange = useMemo(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      const term = e.target.value;
      clearTimeout(timeoutId);
      if (term) {
        timeoutId = setTimeout(() => {
          navigate(`/tim-kiem?q=${encodeURIComponent(term)}`);
        }, 400);
      }
    };
  }, [navigate]);

  const avatar = profile?.avatar || profile?.avatar_url || `https://picsum.photos/seed/${user?.username}/200/200`;

  return (
    <nav className="sticky top-0 z-50 bg-vintage-cream/95 backdrop-blur-sm border-b border-vintage-tan/50 shadow-sm transition-all duration-300">
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          {/* Logo Area */}
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center gap-3 group">
              <img 
                src="/static/logos/unstressvn-logo-header.webp" 
                alt="UnstressVN" 
                className="h-10 w-auto object-contain group-hover:opacity-90 transition-opacity duration-300"
                loading="eager"
              />
              <div className="flex flex-col">
                <span className="font-serif font-bold text-xl md:text-2xl text-vintage-olive leading-none tracking-tight group-hover:text-vintage-brown transition-colors">
                  UnstressVN
                </span>
                <span className="text-[9px] md:text-[10px] uppercase tracking-widest text-vintage-tan font-bold hidden sm:block">
                  {t('app.tagline', 'Học Ngoại Ngữ Dễ Dàng')}
                </span>
              </div>
            </Link>
            
            {/* Desktop Nav Links */}
            <div className="hidden sm:ml-12 sm:flex sm:items-center sm:space-x-6">
              {displayNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`${
                    isActive(link.to)
                      ? 'text-vintage-brown border-vintage-brown'
                      : 'text-vintage-dark/60 border-transparent hover:text-vintage-olive hover:border-vintage-tan'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-semibold tracking-wide transition-all duration-200 uppercase`}
                >
                  {link.label}
                </Link>
              ))}

              {/* Dynamic Dropdowns — rendered from NavigationLink API */}
              {displayDropdowns.map(dropdown => renderDesktopDropdown(dropdown))}
            </div>
          </div>
          
          {/* Right Side Actions */}
          <div className="hidden sm:ml-6 sm:flex sm:items-center gap-3">
            {/* Search Popover */}
            <div className="relative" ref={searchRef}>
              <button 
                onClick={() => setIsSearchOpen(!isSearchOpen)}
                aria-label={t('nav.search', 'Tìm kiếm')}
                className={`p-2.5 rounded-full transition-all duration-200 ${
                  isSearchOpen 
                    ? 'bg-vintage-brown text-white shadow-inner' 
                    : 'text-vintage-olive hover:text-vintage-brown hover:bg-vintage-tan/10'
                }`}
              >
                <Search className="h-5 w-5" />
              </button>

              {isSearchOpen && (
                <div className="absolute right-0 top-full mt-4 w-96 bg-vintage-cream rounded-xl shadow-xl border-2 border-vintage-tan p-4 z-50">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 h-5 w-5 text-vintage-olive" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      className="block w-full pl-10 pr-4 py-2.5 border border-vintage-tan rounded-lg text-sm bg-white text-vintage-dark placeholder-vintage-tan/70 focus:outline-none focus:ring-2 focus:ring-vintage-olive focus:bg-white transition-all font-serif"
                      placeholder={t('common.search') + '...'}
                      onChange={handleSearchChange}
                    />
                    <div className="mt-3 flex justify-between px-2 text-[10px] text-vintage-olive/70 uppercase tracking-widest font-bold">
                      <span>{t('search.books', 'Books')}</span>
                      <span>{t('search.videos', 'Videos')}</span>
                      <span>{t('search.discussions', 'Discussions')}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="h-6 w-px bg-vintage-tan/40 mx-1"></div>

            {/* Language Switcher */}
            <div className="relative" ref={langRef}>
              <button
                onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                aria-label={t('nav.language', 'Chuyển ngôn ngữ')}
                className="flex items-center gap-1 p-2.5 text-vintage-olive hover:text-vintage-brown rounded-full hover:bg-vintage-tan/10 transition-colors"
              >
                <Globe className="h-5 w-5" />
              </button>

              {isLangMenuOpen && (
                <div className="absolute right-0 mt-2 w-40 bg-vintage-cream rounded-xl shadow-xl py-2 z-50 border border-vintage-tan">
                  {languages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={async () => {
                        await changeLanguage(lang.code);
                        setIsLangMenuOpen(false);
                      }}
                      className={`w-full px-4 py-2 text-left flex items-center gap-2 hover:bg-vintage-tan/20 transition-colors ${
                        i18n.language === lang.code ? 'bg-vintage-tan/10 text-vintage-brown font-bold' : 'text-vintage-dark'
                      }`}
                    >
                      <span>{lang.flag}</span>
                      <span className="text-sm">{lang.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {isAuthenticated ? (
              <>
                {/* Notification Icon with Popup */}
                <div className="relative" ref={notificationRef}>
                  <button 
                    onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                    aria-label={t('notifications.title', 'Thông báo')}
                    className={`p-2.5 relative transition-all duration-200 rounded-full ${
                      isNotificationOpen
                        ? 'bg-vintage-olive text-white'
                        : 'text-vintage-olive hover:text-vintage-brown hover:bg-vintage-tan/10'
                    }`}
                  >
                    <Bell className="h-5 w-5" />
                    {notificationUnreadCount > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full ring-2 ring-vintage-cream">
                        {notificationUnreadCount > 9 ? '9+' : notificationUnreadCount}
                      </span>
                    )}
                  </button>

                  {/* Notifications Popup */}
                  {isNotificationOpen && (
                    <div className="absolute right-0 top-full mt-3 w-80 sm:w-96 bg-white rounded-xl shadow-2xl border border-vintage-tan/30 overflow-hidden z-50">
                      {/* Header */}
                      <div className="p-4 bg-gradient-to-r from-vintage-olive to-vintage-brown text-white flex items-center justify-between">
                        <h3 className="font-bold flex items-center gap-2">
                          <Bell className="h-5 w-5" />
                          {t('notifications.title', 'Thông báo')}
                          {notificationUnreadCount > 0 && (
                            <span className="text-sm opacity-80">({notificationUnreadCount})</span>
                          )}
                        </h3>
                        <div className="flex items-center gap-2">
                          {notificationUnreadCount > 0 && (
                            <button 
                              onClick={markAllRead}
                              className="p-1.5 rounded-lg hover:bg-white/20 transition text-xs font-medium"
                            >
                              {t('notifications.markAllRead', 'Đọc tất cả')}
                            </button>
                          )}
                          <button onClick={() => setIsNotificationOpen(false)} className="p-1.5 rounded-lg hover:bg-white/20 transition">
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* Notifications List */}
                      <div className="max-h-96 overflow-y-auto">
                        {notificationsLoading ? (
                          <div className="p-8 text-center">
                            <div className="animate-spin h-6 w-6 mx-auto border-2 border-vintage-olive border-t-transparent rounded-full"></div>
                          </div>
                        ) : notifications.length > 0 ? (
                          notifications.slice(0, 10).map((notif) => (
                            <div
                              key={notif.id}
                              onClick={() => {
                                if (!notif.is_read) {
                                  markAsRead(notif.id);
                                }
                                if (notif.url) {
                                  navigate(notif.url);
                                  setIsNotificationOpen(false);
                                }
                              }}
                              className={`block p-4 hover:bg-vintage-cream/50 transition border-b border-vintage-tan/10 cursor-pointer ${
                                !notif.is_read ? 'bg-vintage-olive/5' : ''
                              }`}
                            >
                              <div className="flex gap-3">
                                {/* Icon or Avatar */}
                                <div className="flex-shrink-0">
                                  {notif.sender?.avatar ? (
                                    <img src={notif.sender.avatar} className="w-10 h-10 rounded-full object-cover" alt="" />
                                  ) : notif.sender ? (
                                    <div className="w-10 h-10 rounded-full bg-vintage-olive/20 flex items-center justify-center text-vintage-olive font-bold">
                                      {notif.sender.username.charAt(0).toUpperCase()}
                                    </div>
                                  ) : (
                                    <div className="w-10 h-10 rounded-full bg-vintage-cream flex items-center justify-center text-vintage-olive">
                                      {notif.notification_type === 'like' ? (
                                        <Heart className="h-5 w-5" />
                                      ) : notif.notification_type === 'comment' ? (
                                        <MessageSquare className="h-5 w-5" />
                                      ) : (
                                        <Bell className="h-5 w-5" />
                                      )}
                                    </div>
                                  )}
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-semibold text-vintage-dark">{notif.title}</p>
                                  <p className="text-xs text-vintage-tan line-clamp-2 mt-0.5">{notif.message}</p>
                                  <p className="text-[10px] text-vintage-tan/70 mt-1">{notif.time_ago || notif.created_at}</p>
                                </div>

                                {/* Unread indicator */}
                                {!notif.is_read && (
                                  <div className="flex-shrink-0">
                                    <span className="w-2 h-2 rounded-full bg-vintage-olive block"></span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="p-8 text-center text-vintage-tan">
                            <BellOff className="h-12 w-12 mx-auto mb-3 opacity-50" />
                            <p className="font-medium">{t('notifications.empty', 'Không có thông báo')}</p>
                            <p className="text-sm mt-1">{t('notifications.emptyHint', 'Bạn sẽ nhận thông báo khi có hoạt động mới')}</p>
                          </div>
                        )}
                      </div>

                      {/* Footer */}
                      <div className="p-3 bg-vintage-cream/50 border-t border-vintage-tan/20">
                        <Link 
                          to="/thong-bao"
                          onClick={() => setIsNotificationOpen(false)}
                          className="block text-center text-sm font-medium text-vintage-olive hover:text-vintage-brown transition"
                        >
                          {t('notifications.viewAll', 'Xem tất cả thông báo')} →
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Profile Dropdown */}
                <div className="ml-2 relative" ref={userMenuRef}>
                  <button
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    className="flex text-sm border-2 border-vintage-tan/50 rounded-full focus:outline-none focus:border-vintage-brown transition-all hover:ring-2 hover:ring-vintage-tan/30 hover:ring-offset-1"
                  >
                    <img
                      className="h-9 w-9 rounded-full object-cover shadow-sm"
                      src={avatar}
                      alt={user?.username}
                    />
                  </button>
                  
                  {isUserMenuOpen && (
                    <div className="origin-top-right absolute right-0 mt-3 w-64 rounded-xl shadow-xl py-1 bg-vintage-light ring-1 ring-black ring-opacity-5 z-50 border border-vintage-tan">
                      <div className="px-4 py-4 border-b border-vintage-tan/20 bg-vintage-cream/30">
                        <p className="text-sm font-bold text-vintage-dark font-serif">{user?.username}</p>
                        <p className="text-xs text-vintage-olive font-medium tracking-wide">
                          {user?.is_superuser ? t('user.role.admin', 'Quản trị viên') : user?.is_staff ? t('user.role.staff', 'Nhân viên') : t('user.role.member', 'Thành viên')}
                        </p>
                      </div>
                      <div className="py-2">
                        <Link
                          to="/ho-so"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="block px-4 py-2.5 text-sm text-vintage-dark hover:bg-vintage-cream hover:text-vintage-brown flex items-center gap-3 transition-colors"
                        >
                          <User className="h-4 w-4" />
                          {t('nav.profile')}
                        </Link>
                        <Link
                          to="/ho-so/cap-nhat"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="block px-4 py-2.5 text-sm text-vintage-dark hover:bg-vintage-cream hover:text-vintage-brown flex items-center gap-3 transition-colors"
                        >
                          <Settings className="h-4 w-4" />
                          {t('nav.settings')}
                        </Link>
                        {(user?.is_superuser || user?.is_staff) && (
                          <button
                            onClick={handleAdminAccess}
                            disabled={isLoadingAdmin}
                            className="w-full px-4 py-2.5 text-sm text-vintage-dark hover:bg-vintage-cream hover:text-vintage-brown flex items-center gap-3 transition-colors disabled:opacity-50"
                          >
                            <Shield className="h-4 w-4" />
                            {isLoadingAdmin ? t('common.loading', 'Đang tải...') : t('nav.adminPanel', 'Quản trị website')}
                          </button>
                        )}
                      </div>
                      <div className="border-t border-vintage-tan/20 py-2">
                        <button
                          onClick={() => {
                            setIsUserMenuOpen(false);
                            handleLogout();
                          }}
                          className="w-full px-4 py-2.5 text-sm text-vintage-brown hover:bg-vintage-brown/10 flex items-center gap-3 transition-colors"
                        >
                          <LogOut className="h-4 w-4" />
                          {t('nav.logout')}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/dang-nhap"
                  className="text-sm font-semibold text-vintage-olive hover:text-vintage-brown transition-colors uppercase tracking-wide"
                >
                  {t('nav.login')}
                </Link>
                <Link
                  to="/dang-ky"
                  className="btn btn-primary text-sm px-4 py-2"
                >
                  {t('nav.register')}
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="sm:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label={t('nav.menu', 'Menu')}
              className="p-2 rounded-md text-vintage-olive hover:text-vintage-brown hover:bg-vintage-tan/10 transition-colors"
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu - Improved */}
      {isMobileMenuOpen && (
        <div className="sm:hidden bg-vintage-cream border-t border-vintage-tan/30 safe-area-bottom">
          {/* Mobile Search */}
          <div className="px-4 pt-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-vintage-olive" />
              <input
                type="text"
                className="block w-full pl-10 pr-4 py-3 border border-vintage-tan rounded-lg text-base bg-white text-vintage-dark placeholder-vintage-tan/70 focus:outline-none focus:ring-2 focus:ring-vintage-olive"
                placeholder={t('common.search') + '...'}
                onChange={handleSearchChange}
              />
            </div>
          </div>

          <div className="px-4 pt-4 pb-3 space-y-1">
            {displayNavLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`block px-4 py-3 rounded-lg text-base font-medium transition-colors touch-target ${
                  isActive(link.to)
                    ? 'bg-vintage-olive text-white'
                    : 'text-vintage-dark hover:bg-vintage-tan/20 active:bg-vintage-tan/30'
                }`}
              >
                {link.label}
              </Link>
            ))}
            
            {/* Dynamic Dropdown Sections — rendered from NavigationLink API */}
            {displayDropdowns.map(dropdown => renderMobileDropdownSection(dropdown))}
          </div>

          {/* Language Switcher - Mobile */}
          <div className="px-4 py-3 border-t border-vintage-tan/20">
            <p className="px-4 py-2 text-xs font-bold text-vintage-tan uppercase tracking-wide">{t('common.language', 'Language')}</p>
            <div className="flex gap-2 px-4">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={async () => {
                    await changeLanguage(lang.code);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`flex-1 py-2 px-3 rounded-lg text-center text-sm touch-target ${
                    i18n.language === lang.code 
                      ? 'bg-vintage-olive text-white font-bold' 
                      : 'bg-vintage-tan/10 text-vintage-dark'
                  }`}
                >
                  <span className="mr-1">{lang.flag}</span> {lang.name}
                </button>
              ))}
            </div>
          </div>
          
          <div className="border-t border-vintage-tan/30 px-4 py-4">
            {isAuthenticated ? (
              <div className="space-y-2">
                {/* User Info */}
                <Link
                  to="/ho-so"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 text-vintage-dark hover:bg-vintage-tan/20 rounded-lg touch-target"
                >
                  <img src={avatar} alt="" className="h-10 w-10 rounded-full object-cover border-2 border-vintage-tan" />
                  <div>
                    <span className="font-bold text-base block">{user?.username}</span>
                    <span className="text-xs text-vintage-tan">{t('user.memberLevel', 'Scholar Member')}</span>
                  </div>
                </Link>
                
                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-2 py-2">
                  <Link
                    to="/ho-so/cap-nhat"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex flex-col items-center gap-1 p-3 rounded-lg bg-vintage-tan/10 hover:bg-vintage-tan/20"
                  >
                    <Settings className="h-5 w-5 text-vintage-olive" />
                    <span className="text-[10px] font-bold uppercase text-vintage-dark">{t('nav.settings', 'Settings')}</span>
                  </Link>
                  <Link
                    to="/thong-bao"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex flex-col items-center gap-1 p-3 rounded-lg bg-vintage-tan/10 hover:bg-vintage-tan/20"
                  >
                    <Bell className="h-5 w-5 text-vintage-brown" />
                    <span className="text-[10px] font-bold uppercase text-vintage-dark">{t('nav.notifications', 'Notifications')}</span>
                  </Link>
                </div>

                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="w-full text-left px-4 py-3 text-vintage-brown hover:bg-vintage-brown/10 rounded-lg font-medium touch-target flex items-center gap-3"
                >
                  <LogOut className="h-5 w-5" />
                  {t('nav.logout')}
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <Link
                  to="/dang-ky"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="text-center px-6 py-3 btn btn-primary text-base font-bold touch-target"
                >
                  {t('nav.register')}
                </Link>
                <Link
                  to="/dang-nhap"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="text-center px-6 py-3 border-2 border-vintage-tan text-vintage-brown hover:text-vintage-brown rounded-lg font-bold touch-target"
                >
                  {t('nav.login')}
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

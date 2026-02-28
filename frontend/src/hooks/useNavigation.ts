/**
 * useNavigation — Fetch & cache navigation data from backend API.
 *
 * Returns navbar links (with children for dropdowns) and footer links (grouped by section).
 * Includes built-in caching, error handling, and icon mapping.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '@/api/client';
import {
  Newspaper, BookOpen, FileText, GraduationCap, Languages,
  Users, Wrench, MessageSquare, Music, Facebook, Twitter,
  Instagram, Youtube, ExternalLink, Home, Library, Video,
  Radio, Globe, Heart, Star, Bookmark, Compass, Mail, MapPin,
  Search, Info, Phone, Settings, Link, Play, HelpCircle,
  Lock, Shield, Calendar, Bell, Clipboard, Pen, Download,
  Upload, Image, Camera, Mic, Headphones, Code, Database,
  Trophy, Map,
  type LucideIcon,
} from 'lucide-react';

// ── Icon mapping (Lucide names) ──
const ICON_MAP: Record<string, LucideIcon> = {
  Newspaper, BookOpen, FileText, GraduationCap, Languages,
  Users, Wrench, MessageSquare, Music, Facebook, Twitter,
  Instagram, Youtube, ExternalLink, Home, Library, Video,
  Radio, Globe, Heart, Star, Bookmark, Compass, Mail, MapPin,
  Search, Info, Phone, Settings, Link, Play, HelpCircle,
  Lock, Shield, Calendar, Bell, Clipboard, Pen, Download,
  Upload, Image, Camera, Mic, Headphones, Code, Database,
  Trophy, Map,
};

// ── FontAwesome → Lucide fallback (for legacy DB data) ──
const FA_FALLBACK: Record<string, string> = {
  FaHome: 'Home', FaVideo: 'Video', FaBook: 'BookOpen',
  FaNewspaper: 'Newspaper', FaLightbulb: 'BookOpen', FaTools: 'Wrench',
  FaUsers: 'Users', FaFacebook: 'Facebook', FaYoutube: 'Youtube',
  FaTiktok: 'Music', FaDiscord: 'Users', FaInstagram: 'Instagram',
  FaTwitter: 'Twitter', FaGlobe: 'Globe', FaFile: 'FileText',
  FaFileAlt: 'FileText', FaGraduationCap: 'GraduationCap',
  FaLanguage: 'Languages', FaWrench: 'Wrench', FaHeart: 'Heart',
  FaStar: 'Star', FaBookmark: 'Bookmark', FaCompass: 'Compass',
  FaEnvelope: 'Mail', FaMapMarker: 'MapPin', FaMusic: 'Music',
  FaRadio: 'Radio', FaExternalLink: 'ExternalLink',
  FaComment: 'MessageSquare', FaSearch: 'Search', FaInfo: 'Info',
  FaPhone: 'Phone', FaCog: 'Settings', FaLink: 'Link', FaPlay: 'Play',
  FaQuestion: 'HelpCircle', FaLock: 'Lock', FaShield: 'Shield',
  FaCalendar: 'Calendar', FaBell: 'Bell', FaClipboard: 'Clipboard',
  FaPen: 'Pen', FaDownload: 'Download', FaUpload: 'Upload',
  FaImage: 'Image', FaCamera: 'Camera', FaMicrophone: 'Mic',
  FaHeadphones: 'Headphones', FaCode: 'Code', FaDatabase: 'Database',
  FaTrophy: 'Trophy', FaMap: 'Map', FaFilePdf: 'FileText',
};

export function getIcon(name: string): LucideIcon | undefined {
  // Direct Lucide name match
  if (ICON_MAP[name]) return ICON_MAP[name];
  // FontAwesome fallback
  const mapped = FA_FALLBACK[name];
  return mapped ? ICON_MAP[mapped] : undefined;
}

// ── Types ──
export interface NavChild {
  id: number;
  name: string;
  name_vi: string;
  name_en: string;
  name_de: string;
  url: string;
  icon: string;
  open_in_new_tab: boolean;
  is_external: boolean;
  is_coming_soon: boolean;
  badge_text: string;
  order: number;
}

export interface NavLink {
  id: number;
  name: string;
  name_vi: string;
  name_en: string;
  name_de: string;
  url: string;
  icon: string;
  location: 'navbar' | 'footer' | 'both';
  footer_section: string;
  open_in_new_tab: boolean;
  is_external: boolean;
  is_coming_soon: boolean;
  badge_text: string;
  has_children: boolean;
  order: number;
  children: NavChild[];
}

export interface NavigationData {
  navbar: NavLink[];
  footer: Record<string, NavLink[]>;
}

// ── Cache ──
let _cache: NavigationData | null = null;
let _cacheTimestamp = 0;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function invalidateNavigationCache() {
  _cache = null;
  _cacheTimestamp = 0;
}

// ── Hook ──
export function useNavigation() {
  const [data, setData] = useState<NavigationData | null>(_cache);
  const [isLoading, setIsLoading] = useState(!_cache);
  const [error, setError] = useState<string | null>(null);

  const fetchNavigation = useCallback(async () => {
    // Use cache if still fresh
    if (_cache && Date.now() - _cacheTimestamp < CACHE_TTL) {
      setData(_cache);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await api.get<NavigationData>('/navigation/');
      _cache = response.data;
      _cacheTimestamp = Date.now();
      setData(response.data);
      setError(null);
    } catch (err) {
      console.error('[useNavigation] Failed to fetch:', err);
      setError('Failed to load navigation');
      // Keep stale cache data if available
      if (_cache) setData(_cache);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNavigation();
  }, [fetchNavigation]);

  // ── Derived data ──
  const navbar = useMemo(() => {
    if (!data) return { directLinks: [], dropdowns: [] };

    const directLinks: NavLink[] = [];
    const dropdowns: NavLink[] = [];

    for (const link of data.navbar) {
      if (link.has_children || (link.children && link.children.length > 0)) {
        dropdowns.push(link);
      } else {
        directLinks.push(link);
      }
    }

    return { directLinks, dropdowns };
  }, [data]);

  const footer = useMemo(() => data?.footer ?? {}, [data]);

  return {
    data,
    navbar,
    footer,
    isLoading,
    error,
    refetch: fetchNavigation,
  };
}

/**
 * Helper: get localized name from a NavLink/NavChild based on language code
 */
export function getLocalizedName(
  item: NavLink | NavChild,
  lang: string
): string {
  const key = `name_${lang}` as keyof typeof item;
  return (item[key] as string) || item.name;
}

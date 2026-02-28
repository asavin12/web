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
  type LucideIcon,
} from 'lucide-react';

// ── Icon mapping ──
const ICON_MAP: Record<string, LucideIcon> = {
  Newspaper, BookOpen, FileText, GraduationCap, Languages,
  Users, Wrench, MessageSquare, Music, Facebook, Twitter,
  Instagram, Youtube, ExternalLink, Home, Library, Video,
  Radio, Globe, Heart, Star, Bookmark, Compass, Mail, MapPin,
};

export function getIcon(name: string): LucideIcon | undefined {
  return ICON_MAP[name];
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

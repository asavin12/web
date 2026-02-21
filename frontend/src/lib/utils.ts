import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import i18n from '@/i18n';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, locale = 'vi-VN'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function getLanguageName(code: string): string {
  const languageKeys: Record<string, string> = {
    vi: 'languages.vi',
    en: 'languages.en',
    de: 'languages.de',
  };
  const nativeNames: Record<string, string> = {
    fr: 'Français',
    es: 'Español',
    ja: '日本語',
    ko: '한국어',
    zh: '中文',
  };
  const key = languageKeys[code];
  if (key) return i18n.t(key);
  return nativeNames[code] || code;
}

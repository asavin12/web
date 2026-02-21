import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import vi from './locales/vi.json';
import en from './locales/en.json';
import de from './locales/de.json';

const resources = {
  vi: { translation: vi },
  en: { translation: en },
  de: { translation: de },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'vi',
    supportedLngs: ['vi', 'en', 'de'],
    
    detection: {
      order: ['localStorage', 'cookie', 'navigator', 'htmlTag'],
      caches: ['localStorage', 'cookie'],
      lookupLocalStorage: 'language',
      lookupCookie: 'django_language', // Match Django's cookie name
    },

    interpolation: {
      escapeValue: false, // React already escapes
    },

    react: {
      useSuspense: true,
    },
  });

export default i18n;

// Helper to change language - force reload to apply all changes
export const changeLanguage = async (lang: string) => {
  // Update localStorage first
  localStorage.setItem('language', lang);
  localStorage.setItem('i18nextLng', lang);
  
  // Set cookie for Django compatibility
  document.cookie = `django_language=${lang};path=/;max-age=31536000`;
  
  // Change i18n language
  await i18n.changeLanguage(lang);
  
  // Update HTML lang attribute
  document.documentElement.lang = lang;
};

// Available languages
export const languages = [
  { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
];

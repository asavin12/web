/**
 * Knowledge API module
 * API calls for knowledge articles and categories
 */

import api from './client';
import i18n from '@/i18n';

// ============================================
// Types
// ============================================

export interface KnowledgeCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  article_count: number;
}

export interface KnowledgeArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  featured_image: string | null;
  cover_image_srcset: Record<string, string> | null;
  category: KnowledgeCategory;
  author: {
    id: number;
    username: string;
    avatar: string | null;
  };
  language: string;
  language_display: string;
  level: string;
  level_display: string;
  is_featured: boolean;
  is_published: boolean;
  view_count: number;
  published_at: string;
  created_at: string;
  updated_at: string;
  // SEO fields
  meta_title?: string;
  meta_description?: string;
  og_image?: string;
  schema_type?: string;
  canonical_url?: string;
}

export interface KnowledgeListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: KnowledgeArticle[];
}

// Language and level choices - use functions to support i18n

export const getLanguageChoices = () => [
  { value: 'de', label: i18n.t('languages.de') },
  { value: 'en', label: i18n.t('languages.en') },
  { value: 'vi', label: i18n.t('languages.vi') }
];

export const getLevelChoices = () => [
  { value: 'A1', label: i18n.t('levels.A1') },
  { value: 'A2', label: i18n.t('levels.A2') },
  { value: 'B1', label: i18n.t('levels.B1') },
  { value: 'B2', label: i18n.t('levels.B2') },
  { value: 'C1', label: i18n.t('levels.C1') },
  { value: 'C2', label: i18n.t('levels.C2') }
];

// ============================================
// API Functions
// ============================================

/**
 * Get list of knowledge categories
 */
export const getKnowledgeCategories = async (): Promise<KnowledgeCategory[]> => {
  const response = await api.get('/knowledge/categories/');
  return response.data;
};

/**
 * Get knowledge articles by category slug
 */
export const getKnowledgeByCategory = async (
  categorySlug: string,
  page: number = 1,
  pageSize: number = 12
): Promise<KnowledgeListResponse> => {
  const response = await api.get('/knowledge/articles/', {
    params: {
      category__slug: categorySlug,
      page,
      page_size: pageSize
    }
  });
  return response.data;
};

/**
 * Get list of knowledge articles with optional filters
 */
export const getKnowledgeArticles = async (params?: {
  page?: number;
  page_size?: number;
  category?: string;
  language?: string;
  level?: string;
  search?: string;
  is_featured?: boolean;
}): Promise<KnowledgeListResponse> => {
  const response = await api.get('/knowledge/articles/', { params });
  return response.data;
};

/**
 * Get single knowledge article by slug
 */
export const getKnowledgeArticleBySlug = async (slug: string): Promise<KnowledgeArticle> => {
  const response = await api.get(`/knowledge/articles/${slug}/`);
  return response.data;
};

/**
 * Get top knowledge articles by criteria
 * @param sort - 'most_viewed' | 'newest' | 'oldest' | 'most_featured'
 * @param limit - number of articles to return (default: 5)
 */
export const getTopArticles = async (
  sort: 'most_viewed' | 'newest' | 'oldest' | 'most_featured' = 'most_viewed',
  limit: number = 5
): Promise<KnowledgeArticle[]> => {
  const response = await api.get('/knowledge/articles/top/', {
    params: { sort, limit }
  });
  return response.data;
};

export default {
  getKnowledgeCategories,
  getKnowledgeByCategory,
  getKnowledgeArticles,
  getKnowledgeArticleBySlug,
  getTopArticles
};

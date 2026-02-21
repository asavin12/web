/**
 * News API module
 * API calls for news articles and categories
 */

import api from './client';

// ============================================
// Types
// ============================================

export interface NewsCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  article_count: number;
}

export interface NewsArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  featured_image: string | null;
  cover_image_srcset: Record<string, string> | null;
  category: NewsCategory;
  author: {
    id: number;
    username: string;
    avatar: string | null;
  };
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
  canonical_url?: string;
}

export interface NewsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: NewsArticle[];
}

// ============================================
// API Functions
// ============================================

/**
 * Get list of news categories
 */
export const getNewsCategories = async (): Promise<NewsCategory[]> => {
  const response = await api.get('/news/categories/');
  return response.data;
};

/**
 * Get news articles by category slug
 */
export const getNewsByCategory = async (
  categorySlug: string,
  page: number = 1,
  pageSize: number = 12
): Promise<NewsListResponse> => {
  const response = await api.get('/news/articles/', {
    params: {
      category__slug: categorySlug,
      page,
      page_size: pageSize
    }
  });
  return response.data;
};

/**
 * Get list of news articles with optional filters
 */
export const getNewsArticles = async (params?: {
  page?: number;
  page_size?: number;
  category?: string;
  search?: string;
  is_featured?: boolean;
}): Promise<NewsListResponse> => {
  const response = await api.get('/news/articles/', { params });
  return response.data;
};

/**
 * Get single news article by slug
 */
export const getNewsArticleBySlug = async (slug: string): Promise<NewsArticle> => {
  const response = await api.get(`/news/articles/${slug}/`);
  return response.data;
};

/**
 * Get related news articles
 */
export const getRelatedNews = async (articleSlug: string, limit: number = 4): Promise<NewsArticle[]> => {
  const response = await api.get(`/news/articles/${articleSlug}/related/`, {
    params: { limit }
  });
  return response.data;
};

export default {
  getNewsCategories,
  getNewsByCategory,
  getNewsArticles,
  getNewsArticleBySlug,
  getRelatedNews
};

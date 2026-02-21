/**
 * Tools API module
 * API calls for learning tools and tool categories
 */

import api from './client';

// ============================================
// Types
// ============================================

export interface ToolCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  tool_count: number;
  is_active: boolean;
}

export interface Tool {
  id: number;
  name: string;
  slug: string;
  description: string;
  content?: string;
  excerpt?: string;
  category: ToolCategory | null;
  author?: number | null;
  author_name?: string | null;
  author_avatar?: string | null;
  tool_type: 'internal' | 'external' | 'embed' | 'article';
  url: string;
  embed_code?: string;
  icon: string;
  cover_image: string | null;
  featured_image?: string | null;
  cover_image_srcset?: Record<string, string> | null;
  language: 'en' | 'de' | 'all';
  language_display?: string;
  is_featured: boolean;
  is_published: boolean;
  is_active: boolean;
  view_count: number;
  meta_title?: string;
  meta_description?: string;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ToolListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Tool[];
}

// ============================================
// API Functions
// ============================================

/**
 * Get list of tool categories
 */
export const getToolCategories = async (): Promise<ToolCategory[]> => {
  const response = await api.get('/tools/categories/');
  return response.data;
};

/**
 * Get list of tools with optional filters
 */
export const getTools = async (params?: {
  page?: number;
  page_size?: number;
  category?: string;
  language?: string;
  is_featured?: boolean;
  search?: string;
}): Promise<ToolListResponse> => {
  const response = await api.get('/tools/tools/', { params });
  return response.data;
};

/**
 * Get single tool by slug
 */
export const getToolBySlug = async (slug: string): Promise<Tool> => {
  const response = await api.get(`/tools/tools/${slug}/`);
  return response.data;
};

export default {
  getToolCategories,
  getTools,
  getToolBySlug
};

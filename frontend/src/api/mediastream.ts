/**
 * MediaStream API client
 * Giao tiếp với backend mediastream endpoints
 */
import axios from 'axios';

// Separate axios instance for mediastream (different base path)
const streamApi = axios.create({
  baseURL: '/media-stream',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// ============================================================================
// Types
// ============================================================================

export interface MediaSubtitle {
  id: number;
  language: string;
  label: string;
  subtitle_url: string;
  is_default?: boolean;
}

export interface StreamMedia {
  id: number;
  uid: string;
  title: string;
  slug: string;
  description: string;
  media_type: 'video' | 'audio';
  language: string;
  level: string;
  category: number | null;
  category_name: string | null;
  thumbnail_url: string | null;
  duration: number | null;
  duration_formatted: string | null;
  stream_url: string;
  subtitles: MediaSubtitle[];
  view_count: number;
  created_at: string;
  // Detail fields
  embed_code?: string;
  tags?: string;
  transcript?: string;
  mime_type?: string;
  file_size?: number;
  width?: number;
  height?: number;
}

export interface MediaCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  media_count: number;
}

export interface StreamMediaListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StreamMedia[];
}

export interface TranslateRequest {
  subtitle_id?: number;
  vtt_content?: string;
  source_lang?: string;
  target_lang: string;
  gemini_api_key?: string;
}

export interface TranslateResponse {
  translated_vtt: string;
  source_lang: string;
  target_lang: string;
  cached: boolean;
  segment_count?: number;
}

export interface StreamMediaFilters {
  media_type?: string;
  language?: string;
  level?: string;
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// API Functions
// ============================================================================

export const mediaStreamApi = {
  /**
   * Get paginated list of stream media
   */
  getAll: async (filters: StreamMediaFilters = {}): Promise<StreamMediaListResponse> => {
    const params = new URLSearchParams();
    if (filters.media_type) params.append('media_type', filters.media_type);
    if (filters.language) params.append('language', filters.language);
    if (filters.level) params.append('level', filters.level);
    if (filters.category) params.append('category', filters.category);
    if (filters.search) params.append('search', filters.search);
    if (filters.page) params.append('page', String(filters.page));
    if (filters.page_size) params.append('page_size', String(filters.page_size));
    
    const response = await streamApi.get<StreamMediaListResponse>(
      `/api/media/?${params}`
    );
    return response.data;
  },

  /**
   * Get single media item by UID
   */
  getByUid: async (uid: string): Promise<StreamMedia> => {
    const response = await streamApi.get<StreamMedia>(
      `/api/media/${uid}/`
    );
    return response.data;
  },

  /**
   * Get categories
   */
  getCategories: async (): Promise<MediaCategory[]> => {
    const response = await streamApi.get<{ results: MediaCategory[] }>(
      '/api/categories/'
    );
    return response.data.results;
  },

  /**
   * Translate subtitle using Gemini API
   */
  translateSubtitle: async (data: TranslateRequest): Promise<TranslateResponse> => {
    const response = await streamApi.post<TranslateResponse>(
      '/translate/',
      data
    );
    return response.data;
  },

  /**
   * Get subtitle file content as text
   */
  getSubtitleContent: async (subtitleUrl: string): Promise<string> => {
    const response = await streamApi.get(subtitleUrl, {
      baseURL: '/',
      responseType: 'text',
      transformResponse: [(data: string) => data],
    });
    return response.data;
  },
};

export default mediaStreamApi;

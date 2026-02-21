import api from './client';
import type { Resource, Choices, Video, VideoListResponse } from '@/types';

// Search chỉ trả về resources - không tìm kiếm users để bảo vệ thông tin
export interface SearchResults {
  resources: Resource[];
}

export interface VideoFilters {
  language?: string;
  level?: string;
  q?: string;
  page?: number;
  page_size?: number;
  is_featured?: boolean;
}

export const utilsApi = {
  // Global search - chỉ resources
  search: async (query: string): Promise<SearchResults> => {
    const response = await api.get<SearchResults>(`/search/?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Get choices (languages, levels, skills, etc.)
  getChoices: async (): Promise<Choices> => {
    const response = await api.get<Choices>('/choices/');
    return response.data;
  },

  // Get videos from core.Video model
  getVideos: async (filters?: VideoFilters): Promise<VideoListResponse> => {
    const params = new URLSearchParams();
    if (filters?.language) params.append('language', filters.language);
    if (filters?.level) params.append('level', filters.level);
    if (filters?.q) params.append('q', filters.q);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());
    
    const queryString = params.toString();
    const url = queryString ? `/videos/?${queryString}` : '/videos/';
    const response = await api.get<VideoListResponse>(url);
    return response.data;
  },

  // Get video detail
  getVideoDetail: async (slug: string): Promise<Video> => {
    const response = await api.get<Video>(`/videos/${slug}/`);
    return response.data;
  },
};

export default utilsApi;

import api from './client';
import type { Resource, PaginatedResponse } from '@/types';

export interface ResourceFilters {
  category?: string;
  language?: string;
  level?: string;
  resource_type?: string;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const resourcesApi = {
  getAll: async (filters: ResourceFilters = {}): Promise<PaginatedResponse<Resource>> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, String(value));
    });
    const response = await api.get<PaginatedResponse<Resource>>(`/resources/?${params}`);
    return response.data;
  },

  getBySlug: async (slug: string): Promise<Resource> => {
    const response = await api.get<Resource>(`/resources/${slug}/`);
    return response.data;
  },

  download: async (slug: string): Promise<void> => {
    const response = await api.post(`/resources/${slug}/download/`);
    return response.data;
  },
};

export default resourcesApi;

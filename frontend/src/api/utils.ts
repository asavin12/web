import api from './client';
import type { Resource, Choices } from '@/types';

// Search chỉ trả về resources - không tìm kiếm users để bảo vệ thông tin
export interface SearchResults {
  resources: Resource[];
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
};

export default utilsApi;

import api from './client';
import type {
  User,
  UserProfile,
  AuthResponse,
  LoginCredentials,
  RegisterData,
} from '@/types';

// Auth API
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login/', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout/');
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register/', data);
    return response.data;
  },

  getMe: async (): Promise<{ user: User; profile: UserProfile }> => {
    const response = await api.get('/me/');
    return response.data;
  },

  updateProfile: async (data: Partial<UserProfile> | FormData): Promise<UserProfile> => {
    const isFormData = data instanceof FormData;
    const response = await api.patch<UserProfile>('/my-profile/', data, isFormData ? {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    } : undefined);
    return response.data;
  },

  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await api.post('/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};

export default authApi;

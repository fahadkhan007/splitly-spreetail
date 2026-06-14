import { apiClient, setAccessToken, clearAccessToken } from './client';
import type { User, TokenPair } from './types';

export const auth = {
  register: async (email: string, password: string, display_name: string) => {
    const { data } = await apiClient.post<User>('/auth/register', {
      email,
      password,
      display_name,
    });
    return data;
  },

  verifyEmail: async (token: string) => {
    const { data } = await apiClient.get<{ message: string; user: User }>(
      `/auth/verify-email?token=${token}`
    );
    return data;
  },

  login: async (email: string, password: string) => {
    // Send JSON because backend expects LoginRequest model
    const { data } = await apiClient.post<TokenPair>('/auth/login', {
      email,
      password,
    });
    
    // Store access token immediately
    setAccessToken(data.access_token);
    return data;
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      // Always clear local token even if network fails
      clearAccessToken();
    }
  },

  getMe: async () => {
    const { data } = await apiClient.get<User>('/users/me');
    return data;
  },
};

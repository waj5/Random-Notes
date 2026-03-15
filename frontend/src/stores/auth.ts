import { defineStore } from 'pinia'
import apiClient from '@/api/client'

interface User {
  id: number;
  username: string;
  nickname: string;
  email?: string;
  avatar_url?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token'),
    refreshToken: localStorage.getItem('refreshToken'),
    isAuthenticated: !!localStorage.getItem('token'),
  }),
  actions: {
    async login(credentials: any) {
      try {
        const response = await apiClient.post('/auth/login', credentials);
        const { access_token, refresh_token } = response.data.data;
        
        this.token = access_token;
        this.refreshToken = refresh_token;
        this.isAuthenticated = true;
        
        localStorage.setItem('token', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        await this.fetchUser();
      } catch (error) {
        console.error('Login failed:', error);
        throw error;
      }
    },
    async register(data: any) {
      try {
        await apiClient.post('/auth/register', data);
      } catch (error) {
        console.error('Registration failed:', error);
        throw error;
      }
    },
    async fetchUser() {
      try {
        const response = await apiClient.get('/auth/me');
        this.user = response.data.data;
        localStorage.setItem('user', JSON.stringify(this.user));
      } catch (error) {
        console.error('Fetch user failed:', error);
        this.logout();
      }
    },
    async refreshUserToken() {
      try {
        const response = await apiClient.post('/auth/refresh', {
          refresh_token: this.refreshToken
        });
        const { access_token, refresh_token } = response.data;
        
        this.token = access_token;
        this.refreshToken = refresh_token;
        
        localStorage.setItem('token', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        return access_token;
      } catch (error) {
        console.error('Refresh token failed:', error);
        this.logout();
        throw error;
      }
    },
    logout() {
      this.user = null;
      this.token = null;
      this.refreshToken = null;
      this.isAuthenticated = false;
      
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      
      // Optional: Call logout API
      apiClient.post('/auth/logout').catch(() => {});
    }
  }
})

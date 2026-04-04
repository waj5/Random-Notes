import { defineStore } from 'pinia'
import apiClient from '../api/client'

interface User {
  id: number;
  username: string;
  phone?: string;
  nickname: string;
  email?: string;
  avatar_url?: string;
  profile_background_url?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  followingIds: number[];
  initialized: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: sessionStorage.getItem('token'),
    isAuthenticated: false,
    followingIds: JSON.parse(localStorage.getItem('followingIds') || '[]'),
    initialized: false,
  }),
  actions: {
    async initialize() {
      if (this.initialized) return
      try {
        await this.fetchUser()
        if (this.user) {
          this.isAuthenticated = true
          await this.fetchFollowingIds()
        }
      } catch {
        try {
          await this.refreshUserToken()
          await this.fetchUser()
          if (this.user) {
            this.isAuthenticated = true
            await this.fetchFollowingIds()
          }
        } catch {
          this.clearAuthState()
        }
      } finally {
        this.initialized = true
      }
    },
    async login(credentials: any) {
      try {
        const response = await apiClient.post('/auth/login', credentials);
        const { access_token } = response.data.data;
        
        this.token = access_token;
        this.isAuthenticated = true;
        this.initialized = true;
        
        sessionStorage.setItem('token', access_token);
        
        await this.fetchUser();
        await this.fetchFollowingIds();
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
    async sendSmsCode(data: { phone: string; purpose: 'register' | 'login' }) {
      try {
        const response = await apiClient.post('/auth/sms-code', data)
        return response.data.data
      } catch (error) {
        console.error('Send sms code failed:', error)
        throw error
      }
    },
    async fetchUser() {
      try {
        const response = await apiClient.get('/auth/me');
        this.user = response.data.data;
        this.isAuthenticated = true;
        localStorage.setItem('user', JSON.stringify(this.user));
      } catch (error) {
        console.error('Fetch user failed:', error);
        this.clearAuthState();
        throw error;
      }
    },
    async updateProfile(data: {
      nickname?: string;
      phone?: string;
      email?: string;
      avatar_url?: string;
      profile_background_url?: string;
      current_password?: string;
      new_password?: string;
    }) {
      const response = await apiClient.put('/auth/me', data)
      this.user = response.data.data
      localStorage.setItem('user', JSON.stringify(this.user))
      return this.user
    },
    async fetchFollowingIds() {
      try {
        const response = await apiClient.get('/follows/');
        this.followingIds = response.data.data.following_ids || [];
        localStorage.setItem('followingIds', JSON.stringify(this.followingIds));
      } catch (error) {
        console.error('Fetch following failed:', error);
        this.followingIds = [];
        localStorage.setItem('followingIds', '[]');
      }
    },
    async followUser(targetUserId: number) {
      await apiClient.post(`/follows/${targetUserId}`);
      if (!this.followingIds.includes(targetUserId)) {
        this.followingIds.push(targetUserId);
        localStorage.setItem('followingIds', JSON.stringify(this.followingIds));
      }
    },
    async unfollowUser(targetUserId: number) {
      await apiClient.delete(`/follows/${targetUserId}`);
      this.followingIds = this.followingIds.filter(id => id !== targetUserId);
      localStorage.setItem('followingIds', JSON.stringify(this.followingIds));
    },
    async refreshUserToken() {
      try {
        const response = await apiClient.post('/auth/refresh', {});
        const { access_token } = response.data;
        
        this.token = access_token;
        this.isAuthenticated = true;
        
        sessionStorage.setItem('token', access_token);
        
        return access_token;
      } catch (error) {
        console.error('Refresh token failed:', error);
        this.clearAuthState();
        throw error;
      }
    },
    clearAuthState() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      
      localStorage.removeItem('user');
      localStorage.removeItem('followingIds');
      sessionStorage.removeItem('token');
      this.followingIds = [];
    },
    async logout(callApi = true) {
      const accessToken = this.token
      this.clearAuthState();
      
      if (!callApi || !accessToken) {
        return
      }

      apiClient.post('/auth/logout', {}, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }).catch(() => {})
    }
  }
})

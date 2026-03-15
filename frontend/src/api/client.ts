import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const authStore = useAuthStore();
    
    // Handle 401 Unauthorized
    if (error.response && error.response.status === 401) {
      // If we have a refresh token and haven't retried yet
      if (authStore.refreshToken && !error.config._retry) {
        error.config._retry = true;
        try {
          // Try to refresh the token
          await authStore.refreshUserToken();
          // Retry the original request
          return apiClient(error.config);
        } catch (refreshError) {
          // If refresh fails, logout
          authStore.logout();
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token or already retried, logout
        authStore.logout();
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

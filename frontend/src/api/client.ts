import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const appBase = import.meta.env.BASE_URL.endsWith('/')
  ? import.meta.env.BASE_URL
  : `${import.meta.env.BASE_URL}/`

const apiClient = axios.create({
  baseURL: `${appBase}api`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    if (config.url?.startsWith('/')) {
      config.url = config.url.slice(1)
    }
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
    const requestUrl = error.config?.url || '';
    const isLoginRequest = requestUrl.includes('/auth/login');
    const isRefreshRequest = requestUrl.includes('/auth/refresh');
    const isLogoutRequest = requestUrl.includes('/auth/logout');
    
    // Handle 401 Unauthorized
    if (error.response && error.response.status === 401 && !isLoginRequest && !isLogoutRequest) {
      // If we have a refresh token and haven't retried yet
      if (!isRefreshRequest && !error.config._retry) {
        error.config._retry = true;
        try {
          // Try to refresh the token
          await authStore.refreshUserToken();
          // Retry the original request
          return apiClient(error.config);
        } catch (refreshError) {
          // If refresh fails, clear local auth only
          authStore.clearAuthState();
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token or already retried
        authStore.clearAuthState();
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

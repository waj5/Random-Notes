import axios from 'axios';
import { useAuthStore } from '../stores/auth';

/** 并发 401 时只发起一次 refresh，避免对 /auth/refresh 风暴请求 */
let refreshFlight: Promise<void> | null = null;

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
          if (!refreshFlight) {
            refreshFlight = authStore.refreshUserToken().finally(() => {
              refreshFlight = null;
            });
          }
          await refreshFlight;
          return apiClient(error.config);
        } catch (refreshError) {
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

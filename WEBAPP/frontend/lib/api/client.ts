// ============================================
// API Client with Axios
// Centralized HTTP client with interceptors
// ============================================

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { API_BASE_URL, REQUEST_TIMEOUT, ERROR_MESSAGES } from '@/utils/constants';
import { tokenStorage } from '@/utils/storage';
import type { APIError, TokenRefresh } from './types';

// ============================================
// CREATE AXIOS INSTANCE
// ============================================

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ============================================
// REQUEST INTERCEPTOR
// Attach access token to all requests
// ============================================

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.getAccessToken();
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// ============================================
// RESPONSE INTERCEPTOR
// Handle errors and token refresh
// ============================================

let isRefreshing = false;
let hasRedirected = false; // Prevent multiple redirects
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Success response - return data
    return response;
  },
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Network error
    if (!error.response) {
      return Promise.reject({
        message: ERROR_MESSAGES.NETWORK_ERROR,
        status: 0,
      });
    }

    const status = error.response.status;

    // Handle 401 Unauthorized - Token expired
    if (status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Add failed request to queue
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenStorage.getRefreshToken();

      if (!refreshToken) {
        // No refresh token - logout (only redirect once)
        tokenStorage.clearTokens();
        if (typeof window !== 'undefined' && !hasRedirected) {
          hasRedirected = true;
          // Don't do a hard redirect, just reject the promise
          // The AuthContext will handle the logout state
        }
        return Promise.reject(error);
      }

      try {
        // Try to refresh the token
        const response = await axios.post<TokenRefresh>(
          `${API_BASE_URL}/api/auth/refresh/`,
          { refresh: refreshToken }
        );

        const { access, refresh } = response.data;
        
        // Save new tokens
        tokenStorage.setAccessToken(access);
        if (refresh) {
          tokenStorage.setRefreshToken(refresh);
        }

        // Update original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        // Process queued requests
        processQueue(null, access);

        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - logout (only redirect once)
        processQueue(refreshError as AxiosError, null);
        tokenStorage.clearTokens();
        
        if (typeof window !== 'undefined' && !hasRedirected) {
          hasRedirected = true;
          // Don't do a hard redirect, just reject the promise
          // The AuthContext will handle the logout state
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle other errors
    const apiError: APIError = {
      status,
      detail: error.response.data?.detail,
      message: error.response.data?.message,
      errors: error.response.data?.errors,
    };

    // Map status codes to user-friendly messages
    if (status === 403) {
      apiError.message = ERROR_MESSAGES.FORBIDDEN;
    } else if (status === 404) {
      apiError.message = ERROR_MESSAGES.NOT_FOUND;
    } else if (status >= 500) {
      apiError.message = ERROR_MESSAGES.SERVER_ERROR;
    } else if (status === 400) {
      apiError.message = apiError.message || ERROR_MESSAGES.VALIDATION_ERROR;
    }

    return Promise.reject(apiError);
  }
);

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Extract error message from API error
 */
export const getErrorMessage = (error: any): string => {
  if (typeof error === 'string') {
    return error;
  }

  if (error?.message) {
    return error.message;
  }

  if (error?.detail) {
    return error.detail;
  }

  if (error?.errors) {
    // Extract first error from errors object
    const firstKey = Object.keys(error.errors)[0];
    if (firstKey && error.errors[firstKey]?.[0]) {
      return error.errors[firstKey][0];
    }
  }

  return ERROR_MESSAGES.UNKNOWN_ERROR;
};

/**
 * Check if error is network error
 */
export const isNetworkError = (error: any): boolean => {
  return error?.status === 0 || !error?.status;
};

/**
 * Check if error is authentication error
 */
export const isAuthError = (error: any): boolean => {
  return error?.status === 401;
};

export default apiClient;

// ============================================
// Authentication Service
// All authentication-related API calls
// ============================================

import apiClient from './client';
import { API_ENDPOINTS } from '@/utils/constants';
import { tokenStorage, userStorage } from '@/utils/storage';
import type {
  LoginResponse,
  RegisterResponse,
  UserRegistrationRequest,
  UserLoginRequest,
  EmailVerificationRequest,
  PasswordResetRequestRequest,
  PasswordResetConfirmRequest,
  ChangePasswordRequest,
  TokenRefresh,
  TokenRefreshRequest,
  MessageResponse,
} from './types';

// ============================================
// AUTHENTICATION METHODS
// ============================================

export const authService = {
  /**
   * Register a new user
   * POST /api/auth/register/
   */
  register: async (data: UserRegistrationRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>(
      API_ENDPOINTS.AUTH.REGISTER,
      data
    );
    
    // Registration doesn't return tokens - user needs to verify email first
    // Just return the response, don't save tokens
    return response.data;
  },

  /**
   * Login with email and password
   * POST /api/auth/login/
   */
  login: async (data: UserLoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      data
    );
    
    // Backend returns: { message, tokens: { access, refresh }, user }
    const { user, tokens } = response.data;
    
    // Save tokens and user data
    tokenStorage.setTokens(tokens.access, tokens.refresh);
    userStorage.setUser(user);
    
    return response.data;
  },

  /**
   * Logout current user
   * POST /api/auth/logout/
   */
  logout: async (): Promise<MessageResponse> => {
    try {
      const response = await apiClient.post<MessageResponse>(
        API_ENDPOINTS.AUTH.LOGOUT
      );
      return response.data;
    } finally {
      // Always clear local storage, even if API call fails
      tokenStorage.clearTokens();
      userStorage.clearUser();
    }
  },

  /**
   * Refresh access token
   * POST /api/auth/refresh/
   */
  refreshToken: async (refreshToken?: string): Promise<TokenRefresh> => {
    const token = refreshToken || tokenStorage.getRefreshToken();
    
    if (!token) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<TokenRefresh>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refresh: token } as TokenRefreshRequest
    );
    
    // Save new access token
    const { access, refresh } = response.data;
    tokenStorage.setAccessToken(access);
    
    // Update refresh token if provided
    if (refresh) {
      tokenStorage.setRefreshToken(refresh);
    }
    
    return response.data;
  },

  /**
   * Verify email address
   * POST /api/auth/verify-email/
   */
  verifyEmail: async (data: EmailVerificationRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(
      API_ENDPOINTS.AUTH.VERIFY_EMAIL,
      data
    );
    
    return response.data;
  },

  /**
   * Request password reset
   * POST /api/auth/forgot-password/
   */
  forgotPassword: async (data: PasswordResetRequestRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(
      API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
      data
    );
    
    return response.data;
  },

  /**
   * Reset password with token
   * POST /api/auth/reset-password/
   */
  resetPassword: async (data: PasswordResetConfirmRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD,
      data
    );
    
    return response.data;
  },

  /**
   * Change password (authenticated user)
   * POST /api/auth/change-password/
   */
  changePassword: async (data: ChangePasswordRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(
      API_ENDPOINTS.AUTH.CHANGE_PASSWORD,
      data
    );
    
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return tokenStorage.hasAccessToken();
  },

  /**
   * Get current access token
   */
  getAccessToken: (): string | null => {
    return tokenStorage.getAccessToken();
  },

  /**
   * Get current refresh token
   */
  getRefreshToken: (): string | null => {
    return tokenStorage.getRefreshToken();
  },

  /**
   * Clear all auth data (local logout)
   */
  clearAuth: (): void => {
    tokenStorage.clearTokens();
    userStorage.clearUser();
  },
};

export default authService;

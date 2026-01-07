// ============================================
// User Service
// User profile and session management
// ============================================

import apiClient from './client';
import { API_ENDPOINTS } from '@/utils/constants';
import { userStorage } from '@/utils/storage';
import type {
  CustomUser,
  CustomUserRequest,
  UserProfile,
  UserProfileRequest,
  PaginatedUserSessionList,
  MessageResponse,
  UserSettings,
  UserSettingsRequest,
} from './types';

// ============================================
// USER METHODS
// ============================================

export const userService = {
  /**
   * Get current user details
   * GET /api/users/me/
   */
  getCurrentUser: async (): Promise<CustomUser> => {
    const response = await apiClient.get<CustomUser>(
      API_ENDPOINTS.USERS.ME
    );
    
    // Cache user data
    userStorage.setUser(response.data);
    
    return response.data;
  },

  /**
   * Update current user
   * PUT /api/users/me/
   */
  updateCurrentUser: async (data: CustomUserRequest): Promise<CustomUser> => {
    const response = await apiClient.put<CustomUser>(
      API_ENDPOINTS.USERS.ME,
      data
    );
    
    // Update cached user data
    userStorage.setUser(response.data);
    
    return response.data;
  },

  /**
   * Partially update current user
   * PATCH /api/users/me/
   */
  partialUpdateCurrentUser: async (data: Partial<CustomUserRequest>): Promise<CustomUser> => {
    const response = await apiClient.patch<CustomUser>(
      API_ENDPOINTS.USERS.ME,
      data
    );
    
    // Update cached user data
    userStorage.setUser(response.data);
    
    return response.data;
  },

  /**
   * Get user profile
   * GET /api/users/me/profile/
   */
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>(
      API_ENDPOINTS.USERS.PROFILE
    );
    
    // Cache profile data
    userStorage.setProfile(response.data);
    
    return response.data;
  },

  /**
   * Update user profile
   * PUT /api/users/me/profile/
   */
  updateProfile: async (data: UserProfileRequest): Promise<UserProfile> => {
    const response = await apiClient.put<UserProfile>(
      API_ENDPOINTS.USERS.PROFILE,
      data
    );
    
    // Update cached profile data
    userStorage.setProfile(response.data);
    
    return response.data;
  },

  /**
   * Partially update user profile
   * PATCH /api/users/me/profile/
   */
  partialUpdateProfile: async (data: Partial<UserProfileRequest>): Promise<UserProfile> => {
    const response = await apiClient.patch<UserProfile>(
      API_ENDPOINTS.USERS.PROFILE,
      data
    );
    
    // Update cached profile data
    userStorage.setProfile(response.data);
    
    return response.data;
  },

  /**
   * List active sessions
   * GET /api/users/sessions/
   */
  listSessions: async (page?: number): Promise<PaginatedUserSessionList> => {
    const params = page ? { page } : {};
    
    const response = await apiClient.get<PaginatedUserSessionList>(
      API_ENDPOINTS.USERS.SESSIONS,
      { params }
    );
    
    return response.data;
  },

  /**
   * Revoke a session (logout from specific device)
   * DELETE /api/users/sessions/{session_id}/
   */
  revokeSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(
      API_ENDPOINTS.USERS.SESSION_BY_ID(sessionId)
    );
  },

  /**
   * Get cached user data
   */
  getCachedUser: (): CustomUser | null => {
    return userStorage.getUser();
  },

  /**
   * Get cached profile data
   */
  getCachedProfile: (): UserProfile | null => {
    return userStorage.getProfile();
  },

  /**
   * Clear cached user data
   */
  clearCache: (): void => {
    userStorage.clearUser();
  },

  // ============================================
  // USER SETTINGS METHODS
  // ============================================

  /**
   * Get user settings
   * GET /api/users/me/settings/
   */
  getSettings: async (): Promise<UserSettings> => {
    const response = await apiClient.get<UserSettings>(
      API_ENDPOINTS.USERS.SETTINGS
    );
    
    return response.data;
  },

  /**
   * Update user settings (full update)
   * PUT /api/users/me/settings/
   */
  updateSettings: async (data: UserSettingsRequest): Promise<UserSettings> => {
    const response = await apiClient.put<UserSettings>(
      API_ENDPOINTS.USERS.SETTINGS,
      data
    );
    
    return response.data;
  },

  /**
   * Partially update user settings
   * PATCH /api/users/me/settings/
   */
  partialUpdateSettings: async (data: Partial<UserSettingsRequest>): Promise<UserSettings> => {
    const response = await apiClient.patch<UserSettings>(
      API_ENDPOINTS.USERS.SETTINGS,
      data
    );
    
    return response.data;
  },
};

export default userService;

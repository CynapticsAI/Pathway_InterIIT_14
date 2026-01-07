// ============================================
// Notification API Service
// Handles notification-related API calls
// ============================================

import apiClient from './client';
import { requestCache } from '../requestCache';
import type { 
  Notification, 
  NotificationPreference, 
  NotificationListResponse,
  NotificationUnreadCount,
  NotificationRecentResponse,
  NotificationMarkResponse
} from './types';

// ============================================
// NOTIFICATION ENDPOINTS
// ============================================

export const notificationService = {
  /**
   * List notifications with optional filters
   */
  list: async (params?: {
    status?: 'UNREAD' | 'READ' | 'ARCHIVED';
    type?: 'NEWS' | 'VOLUME_SPIKE';
    symbol?: string;
    priority?: 'LOW' | 'MEDIUM' | 'HIGH';
    page?: number;
    page_size?: number;
  }): Promise<NotificationListResponse> => {
    const cacheKey = `notifications:list:${JSON.stringify(params || {})}`;
    
    return requestCache.get(
      cacheKey,
      async () => {
        const response = await apiClient.get<NotificationListResponse>('/api/notifications/', { 
          params 
        });
        return response.data;
      },
      3000 // Cache for 3 seconds
    );
  },

  /**
   * Get single notification by ID
   */
  get: async (id: number): Promise<Notification> => {
    const response = await apiClient.get<Notification>(`/api/notifications/${id}/`);
    return response.data;
  },

  /**
   * Get unread notification count
   */
  getUnreadCount: async (): Promise<number> => {
    const cacheKey = 'notifications:unread_count';
    
    return requestCache.get(
      cacheKey,
      async () => {
        const response = await apiClient.get<NotificationUnreadCount>(
          '/api/notifications/unread_count/'
        );
        return response.data.unread_count;
      },
      5000 // Cache for 5 seconds
    );
  },

  /**
   * Get recent notifications (last 10 unread)
   */
  getRecent: async (): Promise<NotificationRecentResponse> => {
    const response = await apiClient.get<NotificationRecentResponse>(
      '/api/notifications/recent/'
    );
    return response.data;
  },

  /**
   * Mark notification as read
   */
  markAsRead: async (id: number): Promise<NotificationMarkResponse> => {
    const response = await apiClient.post<NotificationMarkResponse>(
      `/api/notifications/${id}/mark_read/`
    );
    
    // Invalidate caches after marking as read
    requestCache.invalidatePattern(/^notifications:/);
    
    return response.data;
  },

  /**
   * Mark notification as unread
   */
  markAsUnread: async (id: number): Promise<NotificationMarkResponse> => {
    const response = await apiClient.post<NotificationMarkResponse>(
      `/api/notifications/${id}/mark_unread/`
    );
    
    // Invalidate caches
    requestCache.invalidatePattern(/^notifications:/);
    
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async (notificationIds?: number[]): Promise<{ message: string; count: number }> => {
    const response = await apiClient.post<{ message: string; count: number }>(
      '/api/notifications/mark_all_read/',
      { notification_ids: notificationIds }
    );
    
    // Invalidate caches
    requestCache.invalidatePattern(/^notifications:/);
    
    return response.data;
  },

  /**
   * Archive (delete) notification
   */
  archive: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/notifications/${id}/`);
    
    // Invalidate caches
    requestCache.invalidatePattern(/^notifications:/);
  },

  /**
   * Get user notification preferences
   */
  getPreferences: async (): Promise<NotificationPreference> => {
    const response = await apiClient.get<NotificationPreference>(
      '/api/notification-preferences/me/'
    );
    return response.data;
  },

  /**
   * Update notification preferences
   */
  updatePreferences: async (
    id: number, 
    preferences: Partial<NotificationPreference>
  ): Promise<NotificationPreference> => {
    const response = await apiClient.patch<NotificationPreference>(
      `/api/notification-preferences/${id}/`,
      preferences
    );
    return response.data;
  },
};

// Export for convenience
export default notificationService;

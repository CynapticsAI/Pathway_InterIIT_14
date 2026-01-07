'use client';

// ============================================
// Notification Context
// Global notification state management
// ============================================

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { notificationWS, NotificationMessage } from '@/lib/notificationWebSocket';
import { notificationService } from '@/lib/api';
import type { 
  Notification, 
  NotificationPreference 
} from '@/lib/api/types';
import { useAuth } from '@/hooks/useAuth';
import { showToast } from '@/utils/toast';

// ============================================
// TYPES
// ============================================

interface NotificationContextType {
  // State
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  preferences: NotificationPreference | null;
  isConnected: boolean;

  // Actions
  fetchNotifications: (filters?: FetchFilters) => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  archiveNotification: (id: number) => Promise<void>;
  updatePreferences: (prefs: Partial<NotificationPreference>) => Promise<void>;
  playNotificationSound: () => void;
}

interface FetchFilters {
  status?: 'UNREAD' | 'READ' | 'ARCHIVED';
  type?: 'NEWS' | 'VOLUME_SPIKE';
  symbol?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
  page?: number;
  page_size?: number;
}

// ============================================
// CONTEXT
// ============================================

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// ============================================
// PROVIDER
// ============================================

interface NotificationProviderProps {
  children: React.ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // ============================================
  // WEBSOCKET MESSAGE HANDLER
  // ============================================

  const handleWebSocketMessage = useCallback((message: NotificationMessage) => {
    console.log('📨 Received notification message:', message);

    switch (message.type) {
      case 'notification':
        if (message.notification) {
          handleNewNotification(message.notification);
        }
        break;
      
      case 'unread_count':
        if (message.count !== undefined) {
          setUnreadCount(message.count);
        }
        break;
      
      case 'connection_established':
        setIsConnected(true);
        console.log('✅ Notification WebSocket connection established');
        break;

      case 'notification_marked_read':
        if (message.unread_count !== undefined) {
          setUnreadCount(message.unread_count);
        }
        break;
    }
  }, [preferences]);

  // ============================================
  // HANDLE NEW NOTIFICATION
  // ============================================

  const handleNewNotification = useCallback((notificationData: any) => {
    // Convert to Notification type
    const notification: Notification = {
      id: notificationData.id,
      notification_type: notificationData.type,
      status: 'UNREAD',
      symbol: notificationData.symbol,
      title: notificationData.title,
      message: notificationData.message,
      data: notificationData.data || {},
      timestamp: notificationData.timestamp,
      created_at: notificationData.created_at || new Date().toISOString(),
      priority: notificationData.priority,
      time_ago: 'just now',
    };

    // Add to notifications list
    setNotifications(prev => [notification, ...prev]);
    
    // Increment unread count
    setUnreadCount(prev => prev + 1);
    
    // Show toast notification
    const icon = notification.notification_type === 'NEWS' ? '📰' : '📊';
    showToast.custom(`${icon} ${notification.title}: ${notification.message}`);
    
    // Play sound if enabled
    if (preferences?.web_notifications_enabled) {
      playNotificationSound();
    }
  }, [preferences]);

  // ============================================
  // API METHODS
  // ============================================

  const fetchNotifications = useCallback(async (filters?: FetchFilters) => {
    setIsLoading(true);
    try {
      const response = await notificationService.list(filters);
      setNotifications(response.results);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      showToast.error('Failed to load notifications');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  }, []);

  const markAsRead = useCallback(async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, status: 'READ' as const } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read:', error);
      showToast.error('Failed to mark notification as read');
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications(prev =>
        prev.map(n => ({ ...n, status: 'READ' as const }))
      );
      setUnreadCount(0);
      showToast.success('All notifications marked as read');
    } catch (error) {
      console.error('Failed to mark all as read:', error);
      showToast.error('Failed to mark all notifications as read');
    }
  }, []);

  const archiveNotification = useCallback(async (id: number) => {
    try {
      await notificationService.archive(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      showToast.success('Notification archived');
    } catch (error) {
      console.error('Failed to archive notification:', error);
      showToast.error('Failed to archive notification');
    }
  }, []);

  const updatePreferences = useCallback(async (prefs: Partial<NotificationPreference>) => {
    if (!preferences) return;
    
    try {
      const updated = await notificationService.updatePreferences(preferences.id, prefs);
      setPreferences(updated);
      showToast.success('Preferences updated successfully');
    } catch (error) {
      console.error('Failed to update preferences:', error);
      showToast.error('Failed to update preferences');
    }
  }, [preferences]);

  const playNotificationSound = useCallback(() => {
    if (typeof window === 'undefined') return;
    
    try {
      const audio = new Audio('/sounds/notification.mp3');
      audio.volume = 0.5;
      audio.play().catch(e => console.log('Could not play notification sound:', e));
    } catch (error) {
      console.log('Notification sound not available');
    }
  }, []);

  // ============================================
  // WEBSOCKET INITIALIZATION
  // ============================================

  useEffect(() => {
    if (!isAuthenticated) {
      // Disconnect if not authenticated
      notificationWS.disconnect();
      setIsConnected(false);
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    // Connect to WebSocket
    notificationWS.connect();

    // Subscribe to messages
    const unsubscribeMessage = notificationWS.onMessage(handleWebSocketMessage);
    const unsubscribeConnect = notificationWS.onConnect(() => setIsConnected(true));
    const unsubscribeDisconnect = notificationWS.onDisconnect(() => setIsConnected(false));

    // Fetch initial data only once
    const loadInitialData = async () => {
      try {
        // Fetch notifications and count
        const [notifResponse, unreadCountResponse, prefsResponse] = await Promise.all([
          notificationService.list({ status: 'UNREAD', page_size: 20 }),
          notificationService.getUnreadCount(),
          notificationService.getPreferences().catch(() => null),
        ]);
        
        setNotifications(notifResponse.results);
        setUnreadCount(unreadCountResponse);
        if (prefsResponse) {
          setPreferences(prefsResponse);
        }
      } catch (error) {
        console.error('Failed to load initial notification data:', error);
      }
    };
    
    loadInitialData();

    // Ping interval to keep connection alive
    const pingInterval = setInterval(() => {
      if (notificationWS.isConnected()) {
        notificationWS.sendPing();
      }
    }, 30000); // Ping every 30 seconds

    // Cleanup
    return () => {
      unsubscribeMessage();
      unsubscribeConnect();
      unsubscribeDisconnect();
      clearInterval(pingInterval);
      notificationWS.disconnect();
    };
    // Only re-run when authentication changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  // ============================================
  // CONTEXT VALUE
  // ============================================

  const value: NotificationContextType = {
    notifications,
    unreadCount,
    isLoading,
    preferences,
    isConnected,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    archiveNotification,
    updatePreferences,
    playNotificationSound,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

// ============================================
// HOOK
// ============================================

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

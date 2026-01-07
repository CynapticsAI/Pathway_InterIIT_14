'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useNotifications } from '@/contexts/NotificationContext';
import { NotificationItem } from './NotificationItem';
import { CheckCheck, Settings, Loader2 } from 'lucide-react';

interface NotificationDropdownProps {
  onClose?: () => void;
}

export function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const router = useRouter();
  const {
    notifications,
    isLoading,
    unreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  // Load recent notifications when dropdown opens (only once)
  useEffect(() => {
    fetchNotifications({ page_size: 10 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run on mount

  const recentNotifications = notifications.slice(0, 10);

  const handleViewAll = () => {
    router.push('/notifications');
    onClose?.();
  };

  const handleSettings = () => {
    router.push('/settings/notifications');
    onClose?.();
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Notifications
          </h3>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title="Mark all as read"
            >
              <CheckCheck className="h-4 w-4 text-gray-600 dark:text-gray-400" />
            </button>
          )}
          <button
            onClick={handleSettings}
            className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Notification settings"
          >
            <Settings className="h-4 w-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="max-h-[500px] overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : recentNotifications.length === 0 ? (
          <div className="py-12 text-center text-gray-500 dark:text-gray-400">
            <p className="text-sm">No notifications yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {recentNotifications.map((notification) => (
              <div key={notification.id} className="px-2 py-2">
                <NotificationItem
                  notification={notification}
                  onMarkAsRead={markAsRead}
                  onClick={onClose}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {recentNotifications.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleViewAll}
            className="w-full text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
          >
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
}

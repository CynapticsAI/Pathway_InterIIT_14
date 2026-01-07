'use client';

import React from 'react';
import { Notification } from '@/lib/api/types';
import { Bell, TrendingUp, Clock, CheckCircle } from 'lucide-react';

// Simple time formatting utility
const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `${weeks}w ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  const years = Math.floor(days / 365);
  return `${years}y ago`;
};

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead?: (id: number) => void;
  onArchive?: (id: number) => void;
  onClick?: () => void;
}

export function NotificationItem({
  notification,
  onMarkAsRead,
  onArchive,
  onClick,
}: NotificationItemProps) {
  const isUnread = notification.status === 'UNREAD';

  const getIcon = () => {
    switch (notification.notification_type) {
      case 'NEWS':
        return <Bell className="h-5 w-5 text-blue-500" />;
      case 'VOLUME_SPIKE':
        return <TrendingUp className="h-5 w-5 text-orange-500" />;
      default:
        return <Bell className="h-5 w-5 text-gray-500" />;
    }
  };

  const getPriorityColor = () => {
    switch (notification.priority) {
      case 'HIGH':
        return 'border-l-red-500';
      case 'MEDIUM':
        return 'border-l-yellow-500';
      case 'LOW':
        return 'border-l-blue-500';
      default:
        return 'border-l-gray-300';
    }
  };

  const handleClick = () => {
    if (isUnread && onMarkAsRead) {
      onMarkAsRead(notification.id);
    }
    onClick?.();
  };

  return (
    <div
      className={`
        relative border-l-4 ${getPriorityColor()}
        bg-white dark:bg-gray-800 
        rounded-lg shadow-sm hover:shadow-md 
        transition-all duration-200
        ${isUnread ? 'bg-blue-50 dark:bg-blue-900/10' : ''}
        cursor-pointer
      `}
      onClick={handleClick}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="flex-shrink-0 mt-1">
            {getIcon()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title and Symbol */}
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                {notification.title}
              </h4>
              {notification.symbol && (
                <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                  {notification.symbol}
                </span>
              )}
            </div>

            {/* Message */}
            <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
              {notification.message}
            </p>

            {/* Metadata */}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatTimeAgo(notification.created_at)}
              </span>
              {notification.status === 'READ' && (
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  Read
                </span>
              )}
            </div>
          </div>

          {/* Unread Indicator */}
          {isUnread && (
            <div className="flex-shrink-0">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>
          )}
        </div>

        {/* Actions */}
        {(onMarkAsRead || onArchive) && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            {isUnread && onMarkAsRead && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMarkAsRead(notification.id);
                }}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Mark as read
              </button>
            )}
            {onArchive && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onArchive(notification.id);
                }}
                className="text-xs text-gray-600 dark:text-gray-400 hover:underline"
              >
                Archive
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

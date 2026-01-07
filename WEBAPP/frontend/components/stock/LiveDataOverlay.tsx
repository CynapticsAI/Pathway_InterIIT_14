'use client';

import { useEffect, useState } from 'react';
import { useStockData } from '@/contexts/StockDataContext';
import { NewsItem } from '@/types/news';
import { VolumeVolatilityItem } from '@/types/volumeVolatility';

interface Notification {
  id: string;
  type: 'news' | 'volume';
  data: NewsItem | VolumeVolatilityItem;
  timestamp: number;
}

export function LiveDataOverlay() {
  const { latestNews, latestVolumeSpike } = useStockData();
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Add new news notification
  useEffect(() => {
    if (latestNews) {
      const notification: Notification = {
        id: `news-${latestNews.time}`,
        type: 'news',
        data: latestNews,
        timestamp: Date.now(),
      };
      
      setNotifications(prev => [notification, ...prev].slice(0, 5));
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id));
      }, 5000);
    }
  }, [latestNews]);

  // Add new volume spike notification
  useEffect(() => {
    if (latestVolumeSpike) {
      const notification: Notification = {
        id: `volume-${latestVolumeSpike.time}`,
        type: 'volume',
        data: latestVolumeSpike,
        timestamp: Date.now(),
      };
      
      setNotifications(prev => [notification, ...prev].slice(0, 5));
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== notification.id));
      }, 5000);
    }
  }, [latestVolumeSpike]);

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return 'border-red-500 bg-red-500/20';
      case 'HIGH':
        return 'border-orange-500 bg-orange-500/20';
      case 'MEDIUM':
        return 'border-yellow-500 bg-yellow-500/20';
      case 'LOW':
        return 'border-green-500 bg-green-500/20';
      default:
        return 'border-gray-500 bg-gray-500/20';
    }
  };

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`animate-slide-in-right backdrop-blur-lg rounded-lg border-2 shadow-2xl overflow-hidden ${
            notification.type === 'news'
              ? 'border-blue-500 bg-blue-500/20'
              : getRiskColor((notification.data as VolumeVolatilityItem).riskLevel)
          }`}
        >
          <div className="p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">
                  {notification.type === 'news' ? '📰' : '📊'}
                </span>
                <span className="font-bold text-white">
                  {notification.type === 'news' ? 'Breaking News' : 'Volume Spike Alert'}
                </span>
              </div>
              <button
                onClick={() => dismissNotification(notification.id)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            {notification.type === 'news' ? (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-1 bg-blue-500/40 text-blue-200 rounded text-xs font-bold">
                    {(notification.data as NewsItem).ticker}
                  </span>
                  <span className="text-xs text-gray-300">
                    {(notification.data as NewsItem).source}
                  </span>
                </div>
                <p className="text-white text-sm line-clamp-2 mb-2">
                  {(notification.data as NewsItem).title}
                </p>
                <a
                  href={(notification.data as NewsItem).url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-300 hover:text-blue-200 text-xs flex items-center gap-1"
                >
                  Read more →
                </a>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-1 bg-white/20 text-white rounded text-xs font-bold">
                    {(notification.data as VolumeVolatilityItem).symbol}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    (notification.data as VolumeVolatilityItem).riskLevel === 'CRITICAL' ? 'bg-red-500 text-white' :
                    (notification.data as VolumeVolatilityItem).riskLevel === 'HIGH' ? 'bg-orange-500 text-white' :
                    (notification.data as VolumeVolatilityItem).riskLevel === 'MEDIUM' ? 'bg-yellow-500 text-black' :
                    'bg-green-500 text-white'
                  }`}>
                    {(notification.data as VolumeVolatilityItem).riskLevel}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-400">Price:</span>
                    <span className="text-white ml-1 font-bold">
                      ${(notification.data as VolumeVolatilityItem).currentClose.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Volume:</span>
                    <span className="text-white ml-1 font-bold">
                      {(notification.data as VolumeVolatilityItem).currentVolume.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Vol Z-Score:</span>
                    <span className="text-white ml-1 font-bold">
                      {(notification.data as VolumeVolatilityItem).volumeZScore.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Volatility Z:</span>
                    <span className="text-white ml-1 font-bold">
                      {(notification.data as VolumeVolatilityItem).volatilityZScore.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          <div className="h-1 bg-gray-700">
            <div className="h-full bg-white animate-shrink-width" style={{ animationDuration: '5s' }}></div>
          </div>
        </div>
      ))}
    </div>
  );
}

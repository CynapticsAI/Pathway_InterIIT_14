'use client';

import React, { useState, useEffect } from 'react';
import { useNotifications } from '@/contexts/NotificationContext';
import { Settings, Bell, TrendingUp, Volume2, Save, Loader2 } from 'lucide-react';
import { showToast } from '@/utils/toast';

export default function NotificationSettingsPage() {
  const { preferences, updatePreferences } = useNotifications();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    web_notifications_enabled: true,
    news_alerts_enabled: true,
    volume_spike_alerts_enabled: true,
    min_volume_spike_threshold: 2.0,
  });

  // Load preferences when available
  useEffect(() => {
    if (preferences) {
      setFormData({
        web_notifications_enabled: preferences.web_notifications_enabled,
        news_alerts_enabled: preferences.news_alerts_enabled,
        volume_spike_alerts_enabled: preferences.volume_spike_alerts_enabled,
        min_volume_spike_threshold: preferences.min_volume_spike_threshold,
      });
    }
  }, [preferences]);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await updatePreferences(formData);
      showToast.success('Settings saved successfully');
    } catch (error) {
      showToast.error('Failed to save settings');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-3xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <Settings className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Notification Settings
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Customize how and when you receive notifications
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          {/* Delivery Methods */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Delivery Methods
            </h2>
            
            <div className="space-y-4">
              {/* Web Notifications */}
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <Bell className="h-5 w-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      Web Notifications
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Receive real-time notifications in your browser
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.web_notifications_enabled}
                    onChange={(e) => setFormData({ ...formData, web_notifications_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Notification Types */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Notification Types
            </h2>
            
            <div className="space-y-4">
              {/* News Notifications */}
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <Bell className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      News Notifications
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Breaking news and important updates about stocks
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.news_alerts_enabled}
                    onChange={(e) => setFormData({ ...formData, news_alerts_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Volume Spike Notifications */}
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-5 w-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      Volume Spike Alerts
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Get notified about unusual trading volume
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.volume_spike_alerts_enabled}
                    onChange={(e) => setFormData({ ...formData, volume_spike_alerts_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Volume Spike Threshold */}
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Volume Spike Threshold
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Get notified when volume exceeds this multiple of the average
            </p>
            
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1.5"
                max="5"
                step="0.5"
                value={formData.min_volume_spike_threshold}
                onChange={(e) => setFormData({ ...formData, min_volume_spike_threshold: parseFloat(e.target.value) })}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
              />
              <div className="flex items-center justify-center min-w-[80px] px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-600 rounded-lg">
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {formData.min_volume_spike_threshold.toFixed(1)}x
                </span>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-5 w-5" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

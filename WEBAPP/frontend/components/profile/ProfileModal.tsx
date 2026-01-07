'use client';

// ============================================
// User Profile Modal
// View and edit user profile information
// ============================================

import { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { useAuth } from '@/hooks/useAuth';
import { userService } from '@/lib/api';
import { showToast } from '@/utils/toast';
import { SUCCESS_MESSAGES } from '@/utils/constants';
import { getErrorMessage } from '@/lib/api';
import type { CustomUser, UserProfile } from '@/lib/api/types';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { user, profile, refreshUser, refreshProfile } = useAuth();
  
  // Form state
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    bio: '',
  });

  // Load user data when modal opens
  useEffect(() => {
    if (isOpen && user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone_number: user.phone_number || '',
        bio: user.bio || '',
      });
    }
  }, [isOpen, user]);

  if (!isOpen || !user) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Update user data
      await userService.partialUpdateCurrentUser(formData);
      
      // Refresh user data in context
      await refreshUser();
      
      showToast.success(SUCCESS_MESSAGES.PROFILE_UPDATED);
      setIsEditing(false);
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      showToast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Reset form to original values
    setFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      phone_number: user.phone_number || '',
      bio: user.bio || '',
    });
    setIsEditing(false);
  };

  // Calculate subscription progress
  const getUsagePercentage = () => {
    if (!profile) return 0;
    const limit = profile.total_queries || 100;
    const used = profile.queries_this_month || 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'bg-gray-500';
      case 'basic': return 'bg-blue-500';
      case 'pro': return 'bg-purple-500';
      case 'enterprise': return 'bg-gradient-to-r from-yellow-500 to-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'free': return '🆓';
      case 'basic': return '⭐';
      case 'pro': return '💎';
      case 'enterprise': return '👑';
      default: return '📦';
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="
        relative bg-[var(--color-background)] rounded-2xl shadow-2xl
        w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto
        border border-[var(--color-border)]
      ">
        {/* Header */}
        <div className="sticky top-0 bg-[var(--color-background)] border-b border-[var(--color-border)] px-6 py-4 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] rounded-full flex items-center justify-center text-white text-lg font-bold">
              {user.first_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold text-[var(--color-foreground)]">
                Profile Settings
              </h2>
              <p className="text-sm text-gray-500">Manage your account information</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-[var(--color-foreground)] transition-colors p-2"
          >
            <span className="text-2xl">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Subscription Info */}
          {profile && (
            <div className={`rounded-xl p-4 ${getTierColor(profile.subscription_tier)} bg-opacity-10 border border-current`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getTierBadge(profile.subscription_tier)}</span>
                  <div>
                    <h3 className="font-bold text-[var(--color-foreground)] capitalize">
                      {profile.subscription_tier} Plan
                    </h3>
                    <p className="text-xs text-gray-500 capitalize">
                      Status: {profile.subscription_status}
                    </p>
                  </div>
                </div>
                <Button variant="primary" className="text-sm">
                  Upgrade
                </Button>
              </div>

              {/* Usage Bar */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">API Queries This Month</span>
                  <span className="font-medium text-[var(--color-foreground)]">
                    {profile.queries_this_month} / {profile.total_queries || '∞'}
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${getTierColor(profile.subscription_tier)} transition-all duration-300`}
                    style={{ width: `${getUsagePercentage()}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Account Information */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-[var(--color-foreground)]">
                Account Information
              </h3>
              {!isEditing && (
                <Button 
                  variant="secondary" 
                  onClick={() => setIsEditing(true)}
                  className="text-sm"
                >
                  ✏️ Edit
                </Button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  First Name
                </label>
                {isEditing ? (
                  <Input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    placeholder="Enter first name"
                    fullWidth
                  />
                ) : (
                  <p className="text-gray-600 py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {user.first_name || 'Not set'}
                  </p>
                )}
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Last Name
                </label>
                {isEditing ? (
                  <Input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    placeholder="Enter last name"
                    fullWidth
                  />
                ) : (
                  <p className="text-gray-600 py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {user.last_name || 'Not set'}
                  </p>
                )}
              </div>

              {/* Email (Read-only) */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Email Address
                </label>
                <div className="flex items-center gap-2">
                  <p className="flex-1 text-gray-600 py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {user.email}
                  </p>
                  {user.email_verified ? (
                    <span className="text-green-500 text-sm flex items-center gap-1">
                      ✓ Verified
                    </span>
                  ) : (
                    <span className="text-orange-500 text-sm">
                      ⚠ Unverified
                    </span>
                  )}
                </div>
              </div>

              {/* Phone Number */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Phone Number
                </label>
                {isEditing ? (
                  <Input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    placeholder="Enter phone number"
                    fullWidth
                  />
                ) : (
                  <p className="text-gray-600 py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {user.phone_number || 'Not set'}
                  </p>
                )}
              </div>

              {/* Bio */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-[var(--color-foreground)] mb-1.5">
                  Bio
                </label>
                {isEditing ? (
                  <textarea
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    placeholder="Tell us about yourself..."
                    rows={3}
                    className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-[var(--color-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] text-[var(--color-foreground)]"
                  />
                ) : (
                  <p className="text-gray-600 py-2 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg min-h-[80px]">
                    {user.bio || 'No bio added yet'}
                  </p>
                )}
              </div>
            </div>

            {/* Save/Cancel Buttons */}
            {isEditing && (
              <div className="flex gap-3 pt-2">
                <Button 
                  variant="secondary" 
                  onClick={handleCancel}
                  disabled={isSaving}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex-1"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            )}
          </div>

          {/* Account Details */}
          <div className="border-t border-[var(--color-border)] pt-4">
            <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-3">
              Account Details
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Username</p>
                <p className="font-medium text-[var(--color-foreground)]">{user.username}</p>
              </div>
              <div>
                <p className="text-gray-500">Member Since</p>
                <p className="font-medium text-[var(--color-foreground)]">
                  {new Date(user.created_at).toLocaleDateString()}
                </p>
              </div>
              {profile && (
                <>
                  <div>
                    <p className="text-gray-500">Total Queries</p>
                    <p className="font-medium text-[var(--color-foreground)]">{profile.total_queries}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Last Query</p>
                    <p className="font-medium text-[var(--color-foreground)]">
                      {profile.last_query_at 
                        ? new Date(profile.last_query_at).toLocaleDateString()
                        : 'Never'
                      }
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-[var(--color-background)] border-t border-[var(--color-border)] px-6 py-4">
          <Button 
            variant="secondary" 
            onClick={onClose}
            className="w-full"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ProfileModal;

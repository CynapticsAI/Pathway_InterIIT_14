'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';
import { useAuth } from '@/hooks/useAuth';
import { showToast } from '@/utils/toast';
import { SUCCESS_MESSAGES } from '@/utils/constants';
import { ProfileModal } from '../profile/ProfileModal';
import { NotificationBell } from '../notifications/NotificationBell';

interface TopNavBarProps {
  onMenuClick?: () => void;
  onLogin?: () => void;
  onSignup?: () => void;
}

export function TopNavBar({ 
  onMenuClick, 
  onLogin, 
  onSignup,
}: TopNavBarProps) {
  const { isAuthenticated, user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const userName = user?.first_name || user?.email?.split('@')[0] || 'User';

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      showToast.success(SUCCESS_MESSAGES.LOGOUT);
      setShowUserMenu(false);
    } catch (err) {
      showToast.error('Failed to logout');
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <>
    <nav className="
      fixed top-0 left-0 right-0 
      h-16
      bg-[var(--color-background)]
      border-b border-[var(--color-border)]
      backdrop-blur-md bg-opacity-90
      z-50
      px-4 md:px-6
      flex items-center justify-between
      shadow-sm
    ">
      {/* Left Side */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 hover:bg-[var(--color-ai-message)] rounded-lg transition-colors"
          aria-label="Toggle menu"
        >
          <Icon name="menu" size={24} />
        </button>
        
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] rounded-lg flex items-center justify-center shadow-md">
            <Icon name="bar-chart" size="sm" className="text-white" />
          </div>
          <h1 className="text-lg md:text-xl font-semibold text-[var(--color-foreground)] hidden sm:block">
            HedgeMind
          </h1>
        </div>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        {isAuthenticated ? (
          <>
            <NotificationBell />
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-ai-message)] rounded-full hover:bg-opacity-80 transition-all"
              >
                <div className="w-7 h-7 bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {userName.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium hidden md:block">{userName}</span>
                <Icon name="chevron-down" size="sm" className={`transition-transform ${showUserMenu ? 'rotate-180' : ''}`} />
              </button>

              {/* User Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg shadow-lg py-1 z-50">
                  <div className="px-4 py-2 border-b border-[var(--color-border)]">
                    <p className="text-sm font-medium text-[var(--color-foreground)]">{userName}</p>
                    <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                  </div>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-[var(--color-foreground)] hover:bg-[var(--color-ai-message)] transition-colors"
                    onClick={() => {
                      setShowUserMenu(false);
                      setShowProfileModal(true);
                    }}
                  >
                    <Icon name="user" size="sm" className="inline mr-2" />
                    Profile
                  </button>
                  <button
                    className="w-full px-4 py-2 text-left text-sm text-[var(--color-foreground)] hover:bg-[var(--color-ai-message)] transition-colors"
                    onClick={() => {
                      setShowUserMenu(false);
                      // TODO: Navigate to settings
                    }}
                  >
                    <Icon name="settings" size="sm" className="inline mr-2" />
                    Settings
                  </button>
                  <div className="border-t border-[var(--color-border)] mt-1 pt-1">
                    <button
                      className="w-full px-4 py-2 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors"
                      onClick={handleLogout}
                      disabled={isLoggingOut}
                    >
                      <Icon name="logout" size="sm" className="inline mr-2" />
                      {isLoggingOut ? 'Logging out...' : 'Logout'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <Button 
              variant="ghost" 
              onClick={onLogin}
              className="text-sm"
            >
              Login
            </Button>
            <Button 
              variant="primary" 
              onClick={onSignup}
              className="text-sm"
            >
              Sign Up
            </Button>
          </>
        )}
      </div>
    </nav>

    {/* Profile Modal */}
    <ProfileModal 
      isOpen={showProfileModal} 
      onClose={() => setShowProfileModal(false)} 
    />
    </>
  );
}

'use client';

// ============================================
// Authentication Context
// Global authentication state management
// ============================================

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService, userService, getErrorMessage } from '@/lib/api';
import type { 
  CustomUser, 
  UserProfile, 
  UserLoginRequest, 
  UserRegistrationRequest 
} from '@/lib/api/types';
import { tokenStorage, userStorage } from '@/utils/storage';

// ============================================
// TYPES
// ============================================

interface AuthContextType {
  // State
  user: CustomUser | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (data: UserRegistrationRequest) => Promise<any>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

// ============================================
// CONTEXT
// ============================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============================================
// PROVIDER
// ============================================

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<CustomUser | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user && tokenStorage.hasAccessToken();

  // ============================================
  // INITIALIZE AUTH STATE
  // ============================================

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Check if we have stored auth data
        const hasToken = tokenStorage.hasAccessToken();
        
        if (!hasToken) {
          setIsLoading(false);
          return;
        }

        // Try to get cached user data
        const cachedUser = userStorage.getUser();
        const cachedProfile = userStorage.getProfile();

        if (cachedUser) {
          setUser(cachedUser);
        }

        if (cachedProfile) {
          setProfile(cachedProfile);
        }

        // Fetch fresh user data from API
        try {
          const freshUser = await userService.getCurrentUser();
          setUser(freshUser);

          // Fetch profile data
          const freshProfile = await userService.getProfile();
          setProfile(freshProfile);
        } catch (err) {
          // Token might be invalid - clear auth silently
          console.error('Failed to fetch user data:', err);
          // Don't call handleLogout here to avoid state updates during render
          setUser(null);
          setProfile(null);
          tokenStorage.clearTokens();
          userStorage.clearUser();
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []); // Only run once on mount

  // ============================================
  // LOGIN
  // ============================================

  const login = useCallback(async (credentials: UserLoginRequest) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authService.login(credentials);
      
      setUser(response.user);

      // Fetch profile data
      try {
        const userProfile = await userService.getProfile();
        setProfile(userProfile);
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ============================================
  // REGISTER
  // ============================================

  const register = useCallback(async (data: UserRegistrationRequest) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authService.register(data);
      
      // Registration successful but user is NOT logged in yet
      // They need to verify email first
      // Don't set user or profile here
      
      return response; // Return the response with message
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ============================================
  // LOGOUT
  // ============================================

  const handleLogout = useCallback(async () => {
    setUser(null);
    setProfile(null);
    tokenStorage.clearTokens();
    userStorage.clearUser();
  }, []);

  const logout = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Call logout API
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with local logout even if API fails
    } finally {
      await handleLogout();
      setIsLoading(false);
    }
  }, [handleLogout]);

  // ============================================
  // REFRESH USER DATA
  // ============================================

  const refreshUser = useCallback(async () => {
    try {
      const freshUser = await userService.getCurrentUser();
      setUser(freshUser);
    } catch (err) {
      console.error('Failed to refresh user:', err);
      throw err;
    }
  }, []);

  const refreshProfile = useCallback(async () => {
    try {
      const freshProfile = await userService.getProfile();
      setProfile(freshProfile);
    } catch (err) {
      console.error('Failed to refresh profile:', err);
      throw err;
    }
  }, []);

  // ============================================
  // CLEAR ERROR
  // ============================================

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // ============================================
  // CONTEXT VALUE
  // ============================================

  const value: AuthContextType = {
    user,
    profile,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshUser,
    refreshProfile,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ============================================
// HOOK
// ============================================

export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  
  return context;
}

export default AuthContext;

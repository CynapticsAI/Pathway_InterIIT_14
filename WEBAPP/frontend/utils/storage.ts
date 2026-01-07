// ============================================
// Local Storage Utilities
// Secure token and user data management
// ============================================

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'pway_access_token',
  REFRESH_TOKEN: 'pway_refresh_token',
  USER_DATA: 'pway_user_data',
  USER_PROFILE: 'pway_user_profile',
} as const;

// ============================================
// TOKEN MANAGEMENT
// ============================================

export const tokenStorage = {
  /**
   * Save access token to localStorage
   */
  setAccessToken: (token: string): void => {
    try {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
    } catch (error) {
      console.error('Failed to save access token:', error);
    }
  },

  /**
   * Get access token from localStorage
   */
  getAccessToken: (): string | null => {
    try {
      return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  },

  /**
   * Save refresh token to localStorage
   */
  setRefreshToken: (token: string): void => {
    try {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
    } catch (error) {
      console.error('Failed to save refresh token:', error);
    }
  },

  /**
   * Get refresh token from localStorage
   */
  getRefreshToken: (): string | null => {
    try {
      return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Failed to get refresh token:', error);
      return null;
    }
  },

  /**
   * Save both tokens at once
   */
  setTokens: (accessToken: string, refreshToken: string): void => {
    tokenStorage.setAccessToken(accessToken);
    tokenStorage.setRefreshToken(refreshToken);
  },

  /**
   * Clear all tokens
   */
  clearTokens: (): void => {
    try {
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Failed to clear tokens:', error);
    }
  },

  /**
   * Check if access token exists
   */
  hasAccessToken: (): boolean => {
    return !!tokenStorage.getAccessToken();
  },
};

// ============================================
// USER DATA MANAGEMENT
// ============================================

export const userStorage = {
  /**
   * Save user data to localStorage
   */
  setUser: (user: any): void => {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
    } catch (error) {
      console.error('Failed to save user data:', error);
    }
  },

  /**
   * Get user data from localStorage
   */
  getUser: (): any | null => {
    try {
      const userData = localStorage.getItem(STORAGE_KEYS.USER_DATA);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get user data:', error);
      return null;
    }
  },

  /**
   * Save user profile to localStorage
   */
  setProfile: (profile: any): void => {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(profile));
    } catch (error) {
      console.error('Failed to save user profile:', error);
    }
  },

  /**
   * Get user profile from localStorage
   */
  getProfile: (): any | null => {
    try {
      const profileData = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
      return profileData ? JSON.parse(profileData) : null;
    } catch (error) {
      console.error('Failed to get user profile:', error);
      return null;
    }
  },

  /**
   * Clear all user data
   */
  clearUser: (): void => {
    try {
      localStorage.removeItem(STORAGE_KEYS.USER_DATA);
      localStorage.removeItem(STORAGE_KEYS.USER_PROFILE);
    } catch (error) {
      console.error('Failed to clear user data:', error);
    }
  },
};

// ============================================
// COMBINED STORAGE OPERATIONS
// ============================================

export const storage = {
  /**
   * Clear all app data from localStorage
   */
  clearAll: (): void => {
    tokenStorage.clearTokens();
    userStorage.clearUser();
  },

  /**
   * Check if user is authenticated (has valid tokens)
   */
  isAuthenticated: (): boolean => {
    return tokenStorage.hasAccessToken();
  },

  /**
   * Get all stored auth data
   */
  getAuthData: () => {
    return {
      accessToken: tokenStorage.getAccessToken(),
      refreshToken: tokenStorage.getRefreshToken(),
      user: userStorage.getUser(),
      profile: userStorage.getProfile(),
    };
  },
};

export default storage;

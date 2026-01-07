// ============================================
// API Constants
// ============================================

// Base API URL - defaults to localhost:8001 for development (backend runs on 8001)
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    REGISTER: '/api/auth/register/',
    LOGIN: '/api/auth/login/',
    LOGOUT: '/api/auth/logout/',
    REFRESH: '/api/auth/refresh/',
    VERIFY_EMAIL: '/api/auth/verify-email/',
    FORGOT_PASSWORD: '/api/auth/forgot-password/',
    RESET_PASSWORD: '/api/auth/reset-password/',
    CHANGE_PASSWORD: '/api/auth/change-password/',
  },
  
  // Users
  USERS: {
    ME: '/api/users/me/',
    PROFILE: '/api/users/me/profile/',
    SETTINGS: '/api/users/me/settings/',
    SESSIONS: '/api/users/sessions/',
    SESSION_BY_ID: (id: string) => `/api/users/sessions/${id}/`,
  },
  
  // Chat
  CHAT: {
    CONVERSATIONS: '/api/chat/conversations/',
    CONVERSATION_BY_ID: (id: string) => `/api/chat/conversations/${id}/`,
    MESSAGES: (conversationId: string) => `/api/chat/conversations/${conversationId}/messages/`,
    SEND_MESSAGE: (conversationId: string) => `/api/chat/conversations/${conversationId}/messages/create/`,
  },
  
  // Chatbot
  CHATBOT: {
    BASE: '/api/chatbot/',
  },
} as const;

// Request timeout (30 seconds)
export const REQUEST_TIMEOUT = 30000;

// Token refresh settings
export const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes before expiry

// API call retry settings
export const MAX_RETRY_ATTEMPTS = 3;
export const RETRY_DELAY = 1000; // 1 second

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Your session has expired. Please login again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNKNOWN_ERROR: 'An unexpected error occurred.',
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Login successful!',
  LOGOUT: 'Logged out successfully.',
  REGISTER: 'Registration successful! Please check your email to verify your account.',
  PASSWORD_CHANGED: 'Password changed successfully.',
  PASSWORD_RESET_REQUEST: 'Password reset email sent. Please check your inbox.',
  PASSWORD_RESET: 'Password reset successful. You can now login.',
  EMAIL_VERIFIED: 'Email verified successfully!',
  PROFILE_UPDATED: 'Profile updated successfully.',
  CONVERSATION_CREATED: 'New conversation created.',
  CONVERSATION_DELETED: 'Conversation deleted.',
  MESSAGE_SENT: 'Message sent.',
} as const;

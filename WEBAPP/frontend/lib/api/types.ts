// ============================================
// API Type Definitions
// Matches Django backend API schemas
// ============================================

// ============================================
// ENUMS
// ============================================

export enum MessageTypeEnum {
  USER = 'user',
  AI = 'ai',
  SYSTEM = 'system'
}

export enum SubscriptionTierEnum {
  FREE = 'free',
  BASIC = 'basic',
  PREMIUM = 'premium'
}

export enum SubscriptionStatusEnum {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  CANCELLED = 'cancelled',
  TRIAL = 'trial'
}

// ============================================
// USER & AUTHENTICATION
// ============================================

export interface CustomUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  bio?: string;
  profile_picture?: string;
  email_verified: boolean;
  email_verified_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  subscription_tier: SubscriptionTierEnum;
  subscription_status: SubscriptionStatusEnum;
  subscription_start_date?: string;
  subscription_end_date?: string;
  favorite_stocks: string[];
  watchlist: string[];
  notifications_enabled: boolean;
  total_queries: number;
  queries_this_month: number;
  last_query_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  drawdown: number;
  beta: number;
  hurdle_rate: number;
  sector_exposure_limits: Record<string, number>;
  whitelist: string[];
  blacklist: string[];
  created_at: string;
  updated_at: string;
}

export interface UserSession {
  id: string;
  device_info?: string;
  ip_address?: string;
  last_activity: string;
  created_at: string;
  is_current: boolean;
}

// ============================================
// AUTHENTICATION REQUESTS
// ============================================

export interface UserRegistrationRequest {
  username: string;
  email: string;
  password: string;
  password2: string;
  first_name?: string;
  last_name?: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface EmailVerificationRequest {
  token: string;
}

export interface PasswordResetRequestRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  password: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface TokenRefreshRequest {
  refresh: string;
}

// ============================================
// AUTHENTICATION RESPONSES
// ============================================

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  message: string;
  tokens: AuthTokens;
  user: CustomUser;
}

export interface RegisterResponse {
  message: string;
  user: CustomUser;
}

export interface TokenRefresh {
  access: string;
  refresh?: string;
}

export interface MessageResponse {
  message: string;
  detail?: string;
}

// ============================================
// CHAT & CONVERSATIONS
// ============================================

export interface ChatConversation {
  id: number;
  title: string;
  is_archived: boolean;
  is_pinned: boolean;
  tags: string[];
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string;
}

export interface ChatConversationRequest {
  title: string;
  tags?: string[];
  is_archived?: boolean;
  is_pinned?: boolean;
}

export interface PatchedChatConversationRequest {
  title?: string;
  tags?: string[];
  is_archived?: boolean;
  is_pinned?: boolean;
}

export interface ChatMessage {
  id: number;
  conversation: number;
  user: number;
  user_email: string;
  message_type: 'user' | 'assistant' | 'system';
  content: string;
  // Kafka integration fields
  kafka_message_id?: string | null;
  status?: 'pending' | 'completed' | 'failed';
  agent_name?: string | null;
  // Metadata and analytics
  metadata?: Record<string, any>;
  tokens_used?: number;
  response_time_ms?: number;
  is_helpful?: boolean | null;
  rating?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageCreateRequest {
  content: string;
}

export interface ChatbotMessageRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, any>;
}

export interface ChatbotResponse {
  response: string;
  conversation_id?: string;
  metadata?: Record<string, any>;
}

// ============================================
// PAGINATED RESPONSES
// ============================================

export interface PaginatedResponse<T> {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

export type PaginatedChatConversationList = PaginatedResponse<ChatConversation>;
export type PaginatedChatMessageList = PaginatedResponse<ChatMessage>;
export type PaginatedUserSessionList = PaginatedResponse<UserSession>;

// ============================================
// USER PROFILE REQUESTS
// ============================================

export interface CustomUserRequest {
  email?: string;
  first_name?: string;
  last_name?: string;
}

export interface UserProfileRequest {
  subscription_tier?: SubscriptionTierEnum;
  preferences?: Record<string, any>;
}

export interface UserSettingsRequest {
  drawdown?: number;
  beta?: number;
  hurdle_rate?: number;
  sector_exposure_limits?: Record<string, number>;
  whitelist?: string[];
  blacklist?: string[];
}

// ============================================
// API ERROR RESPONSE
// ============================================

export interface APIError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
  status?: number;
}

// ============================================
// QUERY PARAMETERS
// ============================================

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface ConversationQueryParams extends PaginationParams {
  search?: string;
  ordering?: string;
}

export interface MessageQueryParams extends PaginationParams {
  message_type?: MessageTypeEnum;
}

// ============================================
// NOTIFICATIONS
// ============================================

export interface Notification {
  id: number;
  notification_type: 'NEWS' | 'VOLUME_SPIKE';
  status: 'UNREAD' | 'READ' | 'ARCHIVED';
  symbol: string;
  title: string;
  message: string;
  data: Record<string, any>;
  timestamp: string;
  created_at: string;
  read_at?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  time_ago: string;
}

export interface NotificationPreference {
  id: number;
  news_alerts_enabled: boolean;
  volume_spike_alerts_enabled: boolean;
  min_volume_spike_threshold: number;
  web_notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse extends PaginatedResponse<Notification> {}

export interface NotificationUnreadCount {
  unread_count: number;
}

export interface NotificationRecentResponse {
  notifications: Notification[];
  total_unread: number;
}

export interface NotificationMarkResponse {
  message: string;
  notification: Notification;
}

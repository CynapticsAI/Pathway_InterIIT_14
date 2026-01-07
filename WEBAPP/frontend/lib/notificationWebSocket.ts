// ============================================
// Notification WebSocket Service
// Real-time notification delivery
// ============================================

import { tokenStorage } from '@/utils/storage';

export interface NotificationData {
  id: number;
  type: 'NEWS' | 'VOLUME_SPIKE';
  symbol: string;
  title: string;
  message: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  timestamp: string;
  created_at: string;
  data?: Record<string, any>;
}

export interface NotificationMessage {
  type: 'notification' | 'unread_count' | 'connection_established' | 'pong' | 'notification_marked_read';
  notification?: NotificationData;
  count?: number;
  message?: string;
  user_id?: number;
  notification_id?: number;
  unread_count?: number;
}

type MessageHandler = (message: NotificationMessage) => void;
type ConnectionHandler = () => void;
type ErrorHandler = (error: Event | Error) => void;

class NotificationWebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  
  // Event handlers
  private onMessageHandlers: Set<MessageHandler> = new Set();
  private onConnectHandlers: Set<ConnectionHandler> = new Set();
  private onDisconnectHandlers: Set<ConnectionHandler> = new Set();
  private onErrorHandlers: Set<ErrorHandler> = new Set();

  constructor() {
    const wsProtocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.NEXT_PUBLIC_WS_HOST || 'localhost:8000';
    const token = tokenStorage.getAccessToken();
    // Pass token in query string for authentication
    this.url = token
      ? `${wsProtocol}//${wsHost}/ws/notifications/?token=${encodeURIComponent(token)}`
      : `${wsProtocol}//${wsHost}/ws/notifications/`;
  }

  /**
   * Connect to notification WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      console.log('Notification WebSocket already connected or connecting');
      return;
    }

    const token = tokenStorage.getAccessToken();
    if (!token) {
      console.warn('No access token available for notification WebSocket');
      return;
    }

    this.isConnecting = true;

    try {
      console.log(`📡 Connecting to notification WebSocket: ${this.url}`);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ Notification WebSocket connected');
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        this.notifyConnectHandlers();
        
        // Send authentication if needed (some backends require this)
        // this.send({ action: 'authenticate', token });
      };

      this.ws.onmessage = (event) => {
        try {
          const data: NotificationMessage = JSON.parse(event.data);
          console.log('📬 Notification WebSocket message:', data);
          this.notifyMessageHandlers(data);
        } catch (error) {
          console.error('Failed to parse notification message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('❌ Notification WebSocket disconnected', event.code, event.reason);
        this.isConnecting = false;
        this.ws = null;
        this.notifyDisconnectHandlers();
        
        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ Notification WebSocket error:', error);
        this.isConnecting = false;
        this.notifyErrorHandlers(error);
      };
    } catch (error) {
      console.error('Failed to create notification WebSocket:', error);
      this.isConnecting = false;
      this.notifyErrorHandlers(error as Error);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Send message through WebSocket
   */
  send(data: Record<string, any>): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('Notification WebSocket is not connected. Cannot send message.');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error('Failed to send message:', error);
      return false;
    }
  }

  /**
   * Request unread count
   */
  requestUnreadCount(): void {
    this.send({ action: 'get_unread_count' });
  }

  /**
   * Mark notification as read via WebSocket
   */
  markAsRead(notificationId: number): void {
    this.send({ action: 'mark_read', notification_id: notificationId });
  }

  /**
   * Send ping to keep connection alive
   */
  sendPing(): void {
    this.send({ action: 'ping', timestamp: new Date().toISOString() });
  }

  /**
   * Subscribe to messages
   */
  onMessage(callback: MessageHandler): () => void {
    this.onMessageHandlers.add(callback);
    return () => this.onMessageHandlers.delete(callback);
  }

  /**
   * Subscribe to connection events
   */
  onConnect(callback: ConnectionHandler): () => void {
    this.onConnectHandlers.add(callback);
    return () => this.onConnectHandlers.delete(callback);
  }

  /**
   * Subscribe to disconnection events
   */
  onDisconnect(callback: ConnectionHandler): () => void {
    this.onDisconnectHandlers.add(callback);
    return () => this.onDisconnectHandlers.delete(callback);
  }

  /**
   * Subscribe to error events
   */
  onError(callback: ErrorHandler): () => void {
    this.onErrorHandlers.add(callback);
    return () => this.onErrorHandlers.delete(callback);
  }

  /**
   * Get connection state
   */
  getConnectionState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // ============================================
  // PRIVATE METHODS
  // ============================================

  private notifyMessageHandlers(message: NotificationMessage): void {
    this.onMessageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private notifyConnectHandlers(): void {
    this.onConnectHandlers.forEach(handler => {
      try {
        handler();
      } catch (error) {
        console.error('Error in connect handler:', error);
      }
    });
  }

  private notifyDisconnectHandlers(): void {
    this.onDisconnectHandlers.forEach(handler => {
      try {
        handler();
      } catch (error) {
        console.error('Error in disconnect handler:', error);
      }
    });
  }

  private notifyErrorHandlers(error: Event | Error): void {
    this.onErrorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (handlerError) {
        console.error('Error in error handler:', handlerError);
      }
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(
      `⏱️ Scheduling reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }
}

// Create singleton instance
export const notificationWS = new NotificationWebSocketService();

// Export class for testing
export default NotificationWebSocketService;

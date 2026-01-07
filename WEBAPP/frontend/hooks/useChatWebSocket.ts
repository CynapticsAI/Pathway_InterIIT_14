/**
 * Chat WebSocket Hook
 * Manages WebSocket connection for real-time chat updates
 * 
 * Features:
 * - Auto-connect with JWT authentication
 * - Auto-reconnect on disconnect
 * - Message type handlers
 * - Ping/pong keep-alive
 * - Connection status tracking
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { tokenStorage } from '@/utils/storage';

// WebSocket message types from backend
export type WSMessageType =
  | 'connection_established'
  | 'chat_message'
  | 'message_pending'
  | 'message_completed'
  | 'message_failed'
  | 'conversation_updated'
  | 'error'
  | 'typing_indicator'
  | 'pong'
  | 'agent_tracking';

// WebSocket message structure
export interface WSMessage {
  type: WSMessageType;
  message?: any;
  message_id?: number;
  conversation?: any;
  conversation_id?: number;
  kafka_message_id?: string;
  error?: string;
  timestamp?: string;
  user_id?: number;
  is_typing?: boolean;
  // For agent tracking
  tracking?: any;
}

// Connection status
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// Hook options
interface UseChatWebSocketOptions {
  conversationId: number | null;
  onMessage?: (message: WSMessage) => void;
  onConnectionChange?: (status: ConnectionStatus) => void;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

// Hook return type
interface UseChatWebSocketReturn {
  connectionStatus: ConnectionStatus;
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: any) => void;
  lastMessage: WSMessage | null;
}

// Get WebSocket URL from environment
const getWebSocketUrl = (conversationId: number, token: string): string => {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  return `${wsUrl}/ws/chat/${conversationId}/?token=${token}`;
};

export function useChatWebSocket({
  conversationId,
  onMessage,
  onConnectionChange,
  autoConnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  pingInterval = 30000,
}: UseChatWebSocketOptions): UseChatWebSocketReturn {
  const { isAuthenticated } = useAuthContext();
  
  // WebSocket instance
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isManualDisconnectRef = useRef(false);
  
  // State
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  
  // Derived state
  const isConnected = connectionStatus === 'connected';

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Start ping interval
  const startPingInterval = useCallback(() => {
    clearTimers();
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify({
            type: 'ping',
            timestamp: new Date().toISOString(),
          }));
        } catch (err) {
          console.error('Failed to send ping:', err);
        }
      }
    }, pingInterval);
  }, [pingInterval, clearTimers]);

  // Update connection status
  const updateConnectionStatus = useCallback((status: ConnectionStatus) => {
    setConnectionStatus(status);
    onConnectionChange?.(status);
  }, [onConnectionChange]);

  // Handle incoming WebSocket message
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data: WSMessage = JSON.parse(event.data);
      
      // Update last message
      setLastMessage(data);
      
      // Call message handler
      onMessage?.(data);
      
      // Handle specific message types
      switch (data.type) {
        case 'connection_established':
          console.log('✅ WebSocket connection established:', data);
          updateConnectionStatus('connected');
          reconnectAttemptsRef.current = 0; // Reset reconnect attempts
          startPingInterval();
          break;
          
        case 'chat_message':
          console.log('💬 Chat message received:', data.message);
          break;
          
        case 'message_pending':
          console.log('⏳ Message pending:', data.message);
          break;
          
        case 'message_completed':
          console.log('✅ Message completed:', data.message);
          break;
          
        case 'message_failed':
          console.error('❌ Message failed:', data.error);
          break;
          
        case 'typing_indicator':
          // Handle typing indicator
          break;
          
        case 'pong':
          // Pong received, connection is alive
          break;
          
        default:
          console.warn('Unknown message type:', data.type);
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, [onMessage, updateConnectionStatus, startPingInterval]);

  // Attempt to reconnect
  const attemptReconnect = useCallback(() => {
    if (isManualDisconnectRef.current) {
      return;
    }

    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      updateConnectionStatus('error');
      setError(`Failed to connect after ${maxReconnectAttempts} attempts`);
      return;
    }

    reconnectAttemptsRef.current++;
    console.log(`🔄 Reconnecting... (Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, reconnectInterval);
  }, [maxReconnectAttempts, reconnectInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Check prerequisites
    if (!conversationId) {
      console.warn('⚠️ Cannot connect: No conversation ID');
      return;
    }

    const token = tokenStorage.getAccessToken();
    if (!isAuthenticated || !token) {
      console.warn('⚠️ Cannot connect: Not authenticated');
      return;
    }

    try {
      // Clean up existing connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      clearTimers();
      isManualDisconnectRef.current = false;
      
      // Create WebSocket connection
      const wsUrl = getWebSocketUrl(conversationId, token);
      console.log('🔌 Connecting to WebSocket:', wsUrl.replace(token, 'TOKEN'));
      
      updateConnectionStatus('connecting');
      setError(null);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // Event handlers
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        // Connection established message will come from backend
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        updateConnectionStatus('error');
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('👋 WebSocket closed:', event.code, event.reason);
        clearTimers();
        
        if (!isManualDisconnectRef.current) {
          updateConnectionStatus('disconnected');
          
          // Attempt to reconnect
          if (event.code !== 1000) { // Not a normal closure
            attemptReconnect();
          }
        } else {
          updateConnectionStatus('disconnected');
        }
      };

    } catch (err) {
      console.error('❌ Failed to create WebSocket:', err);
      updateConnectionStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [conversationId, isAuthenticated, handleMessage, attemptReconnect, updateConnectionStatus, clearTimers]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    clearTimers();
    
    if (wsRef.current) {
      console.log('👋 Disconnecting WebSocket');
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    updateConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, [clearTimers, updateConnectionStatus]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (err) {
        console.error('❌ Failed to send message:', err);
        setError('Failed to send message');
      }
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
      setError('Not connected to chat server');
    }
  }, []);

  // Auto-connect effect
  useEffect(() => {
    const token = tokenStorage.getAccessToken();
    if (autoConnect && conversationId && isAuthenticated && token) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [conversationId, isAuthenticated, autoConnect]); // Only reconnect when these change

  return {
    connectionStatus,
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage,
    lastMessage,
  };
}

export default useChatWebSocket;

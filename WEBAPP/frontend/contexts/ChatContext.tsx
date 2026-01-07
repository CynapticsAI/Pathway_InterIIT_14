/**
 * Chat Context - Simplified with WebSocket Integration
 * 
 * Features:
 * - Single conversation focus (simplified UX)
 * - REST API for initial load
 * - WebSocket for real-time updates
 * - Message status tracking (pending/completed/failed)
 * - Optimistic UI updates
 */

'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { chatService, getErrorMessage, isAuthError } from '@/lib/api';
import { useAuthContext } from './AuthContext';
import { useChatWebSocket, type WSMessage } from '@/hooks/useChatWebSocket';
import type {
  ChatConversation,
  ChatMessage,
} from '@/lib/api/types';

// ============================================
// TYPES
// ============================================

interface ChatState {
  conversation: ChatConversation | null;
  conversationId: number | null;
  messages: ChatMessage[];
  isLoadingConversation: boolean;
  isLoadingMessages: boolean;
  isSendingMessage: boolean;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  error: string | null;
}

interface ChatActions {
  initialize: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  clearError: () => void;
  refreshMessages: () => Promise<void>;
  newChat: () => Promise<ChatConversation | null>;
  loadConversationById: (id: number) => Promise<void>;
}

type ChatContextType = ChatState & ChatActions & { agentTracking: any | null };

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
  children: React.ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuthContext();
  
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Agent tracking state (per conversation)
  const [agentTracking, setAgentTracking] = useState<any | null>(null);

  const handleWebSocketMessage = useCallback((wsMessage: WSMessage) => {
    console.log('[ChatContext] WebSocket message received:', wsMessage);
    switch (wsMessage.type) {
      case 'chat_message': {
        const { message } = wsMessage;
        // Only add if not already in messages (avoid duplicates from optimistic updates)
        setMessages(prev => {
          if (prev.some(m => m.id === message.id)) {
            return prev;
          }
          return [...prev, message];
        });
        break;
      }
      
      case 'message_pending': {
        const { message } = wsMessage;
        setMessages(prev => {
          if (prev.some(m => m.id === message.id)) {
            return prev;
          }
          return [...prev, message];
        });
        break;
      }
      
      case 'message_completed': {
        const { message } = wsMessage;
        setMessages(prev => 
          prev.map(msg => 
            msg.id === message.id 
              ? { ...msg, content: message.content, status: 'completed', agent_name: message.agent_name }
              : msg
          )
        );
        break;
      }
      
      case 'message_failed': {
        const { message_id, error: errorMsg } = wsMessage;
        setMessages(prev =>
          prev.map(msg =>
            msg.id === message_id
              ? { ...msg, status: 'failed', content: `Error: ${errorMsg}` }
              : msg
          )
        );
        break;
      }
      
      case 'conversation_updated': {
        const { conversation: updatedConv } = wsMessage;
        if (updatedConv.id === conversationId) {
          setConversation(updatedConv);
        }
        break;
      }
      
      case 'error': {
        console.error('[ChatContext] WebSocket error:', wsMessage.message);
        setError(wsMessage.message);
        break;
      }
      
      case 'agent_tracking': {
        // Store the latest agent tracking info for this conversation
        if (
          wsMessage.conversation_id === conversationId ||
          (wsMessage.tracking && wsMessage.tracking.conversation_id == conversationId)
        ) {
          setAgentTracking(wsMessage.tracking);
        }
        break;
      }
      default:
        console.log('[ChatContext] Unhandled WebSocket message type:', wsMessage.type);
    }
  }, [conversationId]);

  const {
    isConnected,
    connectionStatus,
  } = useChatWebSocket({
    conversationId,
    onMessage: handleWebSocketMessage,
    autoConnect: isAuthenticated && conversationId !== null,
  });

  const getOrCreateConversation = useCallback(async (): Promise<ChatConversation> => {
    try {
      const convList = await chatService.listConversations();
      
      if (convList.results && convList.results.length > 0) {
        return convList.results[0];
      }
      
      const newConv = await chatService.createConversation({
        title: 'New Chat',
        tags: [],
      });
      
      return newConv;
    } catch (err) {
      console.error('[ChatContext] Error getting/creating conversation:', err);
      throw err;
    }
  }, []);

  const loadMessages = useCallback(async (convId: number) => {
    setIsLoadingMessages(true);
    try {
      const messageList = await chatService.listMessages(convId);
      setMessages(messageList.results || []);
      setError(null);
    } catch (err) {
      if (!isAuthError(err)) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('[ChatContext] Error loading messages:', errorMsg);
      }
    } finally {
      setIsLoadingMessages(false);
    }
  }, []);

  const initialize = useCallback(async (conversationIdFromUrl?: number) => {
    if (!isAuthenticated) {
      console.log('[ChatContext] Not authenticated, skipping initialization');
      return;
    }

    setIsLoadingConversation(true);
    try {
      let targetConversation: ChatConversation;
      
      // If URL has a conversation ID, try to load it
      if (conversationIdFromUrl) {
        try {
          targetConversation = await chatService.getConversation(conversationIdFromUrl);
        } catch (err) {
          console.warn('[ChatContext] Failed to load conversation from URL, falling back to default');
          targetConversation = await getOrCreateConversation();
        }
      } else {
        // Otherwise get or create a conversation
        targetConversation = await getOrCreateConversation();
      }
      
      setConversation(targetConversation);
      setConversationId(targetConversation.id);
      await loadMessages(targetConversation.id);
      setError(null);
    } catch (err) {
      if (!isAuthError(err)) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('[ChatContext] Initialization error:', errorMsg);
      }
    } finally {
      setIsLoadingConversation(false);
    }
  }, [isAuthenticated, getOrCreateConversation, loadMessages]);

  const sendMessage = useCallback(async (content: string) => {
    if (!conversationId) {
      console.error('[ChatContext] No conversation ID');
      throw new Error('No active conversation');
    }

    setIsSendingMessage(true);
    try {
      // Send to backend and get response
      const response = await chatService.sendMessage(conversationId, { content });
      
      // Add both user message and pending assistant message from backend
      setMessages(prev => {
        // Check if user message already exists (from WebSocket)
        const userMessageExists = prev.some(m => m.id === response.user_message.id);
        const assistantMessageExists = prev.some(m => m.id === response.assistant_message.id);
        
        const newMessages = [...prev];
        if (!userMessageExists) {
          newMessages.push(response.user_message);
        }
        if (!assistantMessageExists) {
          newMessages.push(response.assistant_message);
        }
        return newMessages;
      });
      
      setError(null);
    } catch (err) {
      if (!isAuthError(err)) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('[ChatContext] Error sending message:', errorMsg);
      }
      throw err;
    } finally {
      setIsSendingMessage(false);
    }
  }, [conversationId]);

  const refreshMessages = useCallback(async () => {
    if (conversationId) {
      await loadMessages(conversationId);
    }
  }, [conversationId, loadMessages]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const newChat = useCallback(async (): Promise<ChatConversation | null> => {
    if (!isAuthenticated) {
      return null;
    }

    setIsLoadingConversation(true);
    try {
      // Create a new conversation
      const newConv = await chatService.createConversation({
        title: 'New Chat',
        tags: [],
      });
      
      // Switch to the new conversation
      setConversation(newConv);
      setConversationId(newConv.id);
      setMessages([]);
      setError(null);
      
      console.log('[ChatContext] Created new conversation:', newConv.id);
      return newConv;
    } catch (err) {
      if (!isAuthError(err)) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('[ChatContext] Error creating new conversation:', errorMsg);
      }
      return null;
    } finally {
      setIsLoadingConversation(false);
    }
  }, [isAuthenticated]);

  const loadConversationById = useCallback(async (id: number) => {
    if (!isAuthenticated) {
      return;
    }

    setIsLoadingConversation(true);
    try {
      // Get the conversation
      const conv = await chatService.getConversation(id);
      setConversation(conv);
      setConversationId(conv.id);
      
      // Load messages for this conversation
      await loadMessages(conv.id);
      
      setError(null);
      console.log('[ChatContext] Loaded conversation:', conv.id);
    } catch (err) {
      if (!isAuthError(err)) {
        const errorMsg = getErrorMessage(err);
        setError(errorMsg);
        console.error('[ChatContext] Error loading conversation:', errorMsg);
      }
    } finally {
      setIsLoadingConversation(false);
    }
  }, [isAuthenticated, loadMessages]);

  useEffect(() => {
    if (isAuthenticated && !isAuthLoading && !conversation) {
      initialize();
    }
  }, [isAuthenticated, isAuthLoading, conversation, initialize]);

  // Extend context value to include agentTracking
  const value: ChatContextType & { agentTracking: any | null } = {
    conversation,
    conversationId,
    messages,
    isLoadingConversation,
    isLoadingMessages,
    isSendingMessage,
    isConnected,
    connectionStatus,
    error,
    initialize,
    sendMessage,
    clearError,
    refreshMessages,
    newChat,
    loadConversationById,
    agentTracking,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext(): ChatContextType {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;

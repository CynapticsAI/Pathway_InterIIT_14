// ============================================
// Chat Service
// Chat conversations and messages management
// ============================================

import apiClient from './client';
import { API_ENDPOINTS } from '@/utils/constants';
import type {
  ChatConversation,
  ChatConversationRequest,
  PatchedChatConversationRequest,
  PaginatedChatConversationList,
  ChatMessage,
  ChatMessageCreateRequest,
  PaginatedChatMessageList,
  ConversationQueryParams,
  MessageQueryParams,
} from './types';

// Response type for sending messages (includes both user and assistant messages)
export interface SendMessageResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  status: string;
  kafka_message_id?: string;
}

// ============================================
// CONVERSATION METHODS
// ============================================

export const chatService = {
  /**
   * List all conversations
   * GET /api/chat/conversations/
   */
  listConversations: async (params?: ConversationQueryParams): Promise<PaginatedChatConversationList> => {
    const response = await apiClient.get<PaginatedChatConversationList>(
      API_ENDPOINTS.CHAT.CONVERSATIONS,
      { params }
    );
    
    return response.data;
  },

  /**
   * Create new conversation
   * POST /api/chat/conversations/
   */
  createConversation: async (data: ChatConversationRequest): Promise<ChatConversation> => {
    const response = await apiClient.post<ChatConversation>(
      API_ENDPOINTS.CHAT.CONVERSATIONS,
      data
    );
    
    return response.data;
  },

  /**
   * Get a specific conversation
   * GET /api/chat/conversations/{id}/
   */
  getConversation: async (conversationId: number): Promise<ChatConversation> => {
    const response = await apiClient.get<ChatConversation>(
      API_ENDPOINTS.CHAT.CONVERSATION_BY_ID(conversationId.toString())
    );
    
    return response.data;
  },

  /**
   * Update conversation (full update)
   * PUT /api/chat/conversations/{id}/
   */
  updateConversation: async (
    conversationId: number,
    data: ChatConversationRequest
  ): Promise<ChatConversation> => {
    const response = await apiClient.put<ChatConversation>(
      API_ENDPOINTS.CHAT.CONVERSATION_BY_ID(conversationId.toString()),
      data
    );
    
    return response.data;
  },

  /**
   * Partially update conversation
   * PATCH /api/chat/conversations/{id}/
   */
  partialUpdateConversation: async (
    conversationId: number,
    data: PatchedChatConversationRequest
  ): Promise<ChatConversation> => {
    const response = await apiClient.patch<ChatConversation>(
      API_ENDPOINTS.CHAT.CONVERSATION_BY_ID(conversationId.toString()),
      data
    );
    
    return response.data;
  },

  /**
   * Delete conversation
   * DELETE /api/chat/conversations/{id}/
   */
  deleteConversation: async (conversationId: number): Promise<void> => {
    await apiClient.delete(
      API_ENDPOINTS.CHAT.CONVERSATION_BY_ID(conversationId.toString())
    );
  },

  // ============================================
  // MESSAGE METHODS
  // ============================================

  /**
   * List messages in a conversation
   * GET /api/chat/conversations/{conversation_id}/messages/
   */
  listMessages: async (
    conversationId: number,
    params?: MessageQueryParams
  ): Promise<PaginatedChatMessageList> => {
    const response = await apiClient.get<PaginatedChatMessageList>(
      API_ENDPOINTS.CHAT.MESSAGES(conversationId.toString()),
      { params }
    );
    
    return response.data;
  },

  /**
   * Send message in a conversation
   * POST /api/chat/conversations/{conversation_id}/messages/
   * Returns both user message and pending assistant message
   */
  sendMessage: async (
    conversationId: number,
    data: ChatMessageCreateRequest
  ): Promise<SendMessageResponse> => {
    const response = await apiClient.post<SendMessageResponse>(
      API_ENDPOINTS.CHAT.SEND_MESSAGE(conversationId.toString()),
      data
    );
    
    return response.data;
  },

  // ============================================
  // HELPER METHODS
  // ============================================

  /**
   * Create conversation with first message
   */
  createConversationWithMessage: async (
    title: string,
    message: string
  ): Promise<{ conversation: ChatConversation; response: SendMessageResponse }> => {
    // First create the conversation
    const conversation = await chatService.createConversation({ title });
    
    // Then send the first message
    const response = await chatService.sendMessage(conversation.id, {
      content: message,
    });
    
    return { conversation, response };
  },

  /**
   * Get all messages for a conversation (handles pagination)
   */
  getAllMessages: async (conversationId: number): Promise<ChatMessage[]> => {
    let allMessages: ChatMessage[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await chatService.listMessages(conversationId, { page });
      allMessages = [...allMessages, ...response.results];
      
      hasMore = !!response.next;
      page++;
    }

    return allMessages;
  },

  /**
   * Get all conversations (handles pagination)
   */
  getAllConversations: async (): Promise<ChatConversation[]> => {
    let allConversations: ChatConversation[] = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await chatService.listConversations({ page });
      allConversations = [...allConversations, ...response.results];
      
      hasMore = !!response.next;
      page++;
    }

    return allConversations;
  },

  /**
   * Search conversations by title
   */
  searchConversations: async (query: string): Promise<ChatConversation[]> => {
    const response = await chatService.listConversations({ search: query });
    return response.results;
  },
};

export default chatService;

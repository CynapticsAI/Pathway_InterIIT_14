/**
 * Chat Container Component - Modern Design
 * 
 * Updated with elevation, semantic colors, and improved layout
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { MessageType } from './Message';
import { ChatHeader } from './ChatHeader';
import { ConversationsPopup } from './ConversationsPopup';
import { useChatContext } from '@/contexts/ChatContext';
import { useAuthContext } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import type { ChatMessage } from '@/lib/api/types';

interface ChatContainerProps {
  showCharts?: boolean; // Control whether to show charts inline
}

export function ChatContainer({ showCharts = true }: ChatContainerProps = {}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuthContext();
  const {
    conversation,
    conversationId,
    messages: contextMessages,
    isSendingMessage,
    isLoadingMessages,
    isConnected,
    connectionStatus,
    error,
    sendMessage,
    clearError,
    newChat,
    loadConversationById,
    initialize,
  } = useChatContext();

  const [showConversationsPopup, setShowConversationsPopup] = useState(false);

  // Check URL params on mount and update
  useEffect(() => {
    const chatIdParam = searchParams?.get('chat');
    if (chatIdParam) {
      const chatId = parseInt(chatIdParam, 10);
      if (!isNaN(chatId) && chatId !== conversationId) {
        loadConversationById(chatId);
      }
    }
  }, [searchParams, conversationId, loadConversationById]);

  // Handle conversation selection from popup
  const handleSelectConversation = (id: number) => {
    // Update URL with chat ID
    router.push(`/?chat=${id}`);
    // Load the conversation
    loadConversationById(id);
  };

  // Handle new chat
  const handleNewChat = async () => {
    const newConv = await newChat();
    if (newConv) {
      // Update URL with new chat ID
      router.push(`/?chat=${newConv.id}`);
    }
  };

  // Convert backend messages to UI MessageType format
  const messages: MessageType[] = contextMessages.map((msg: ChatMessage) => {
    // Determine if this message is pending (waiting for response)
    const isPending = msg.status === 'pending';
    
    return {
      id: msg.id.toString(),
      content: msg.content,
      sender: msg.message_type === 'user' ? 'user' : 'ai',
      timestamp: new Date(msg.created_at),
      isTyping: isPending, // Show typing indicator for pending messages
      // Add metadata for status handling
      metadata: {
        status: msg.status,
        agentName: msg.agent_name,
        kafkaMessageId: msg.kafka_message_id,
      },
    };
  });

  // Add welcome message if no messages yet
  const displayMessages: MessageType[] = messages.length === 0 ? [
    {
      id: 'welcome',
      content: 'Hello! I\'m your AI Stock Market Assistant. I can help you analyze stocks, market trends, and provide financial insights with interactive charts. Try asking:\n\n📊 "Show me AAPL chart"\n💹 "Compare AAPL and GOOGL"\n📈 "TSLA candlestick chart"\n📉 "MSFT volume analysis"\n🔄 "RRG chart for tech stocks"\n\nWhat would you like to explore?',
      sender: 'ai',
      timestamp: new Date(),
    },
  ] : messages;

  const handleSendMessage = async (content: string) => {
    // If not authenticated, show message
    if (!isAuthenticated) {
      alert('Please log in to use the chat feature');
      return;
    }

    try {
      await sendMessage(content);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Error is already handled in context, but we can show user feedback
      if (!error || (error as any).message !== 'Authentication required') {
        alert('Failed to send message. Please try again.');
      }
    }
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto px-4 py-6">
      {/* Conversations Popup */}
      <ConversationsPopup
        isOpen={showConversationsPopup}
        onClose={() => setShowConversationsPopup(false)}
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />

      <div className="flex flex-col h-full min-h-0">
        {/* Header */}
        <div className="flex-shrink-0 mb-6">
          <ChatHeader 
            title="HedgeMind" 
            onNewChat={handleNewChat}
            onShowConversations={() => setShowConversationsPopup(true)}
          />
        </div>

        {/* Messages Container with elevation */}
        <div className={cn(
          'flex-1 overflow-hidden flex flex-col min-h-0',
          'bg-[var(--color-surface)]',
          'rounded-2xl elevation-2'
        )}>
          <ChatMessages messages={displayMessages} showCharts={showCharts} />
        </div>
        
        {/* Input Area */}
        <div className="mt-4 flex-shrink-0">
          <ChatInput onSendMessage={handleSendMessage} disabled={isSendingMessage} />
        </div>
      </div>
    </div>
  );
}


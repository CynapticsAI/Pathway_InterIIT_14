/**
 * Conversations Popup - Shows list of conversations
 */

'use client';

import { useState, useEffect } from 'react';
import { chatService } from '@/lib/api';
import { ChatConversation } from '@/lib/api/types';
import { Icon } from '../ui/Icon';
import { Button } from '../ui/Button';
import { cn } from '@/lib/utils';

interface ConversationsPopupProps {
  isOpen: boolean;
  onClose: () => void;
  currentConversationId: number | null;
  onSelectConversation: (id: number) => void;
  onNewChat: () => void;
}

export function ConversationsPopup({
  isOpen,
  onClose,
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: ConversationsPopupProps) {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConversations();
    }
  }, [isOpen]);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const data = await chatService.listConversations();
      setConversations(data.results || []);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = (id: number) => {
    onSelectConversation(id);
    onClose();
  };

  const handleNewChat = () => {
    onNewChat();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Popup */}
      <div className="fixed top-20 right-4 w-80 max-h-[70vh] bg-[var(--color-surface)] rounded-lg elevation-4 z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)]">
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Conversations
          </h3>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
          >
            <Icon name="close" size="sm" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-3 border-b border-[var(--color-border)]">
          <Button
            onClick={handleNewChat}
            className="w-full"
            variant="outline"
          >
            <Icon name="plus" size="sm" />
            <span className="ml-2">New Chat</span>
          </Button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-[var(--color-text-secondary)]">
              Loading...
            </div>
          ) : conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-[var(--color-text-secondary)]">
              <Icon name="message" size="lg" className="mb-2 opacity-50" />
              <p>No conversations yet</p>
            </div>
          ) : (
            <div className="space-y-1">
              {conversations.map((conv) => {
                const isActive = conv.id === currentConversationId;
                const preview = conv.title || `Chat ${conv.id}`;
                const lastMessage = conv.last_message_at
                  ? new Date(conv.last_message_at).toLocaleDateString()
                  : 'No messages';

                return (
                  <button
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv.id)}
                    className={cn(
                      'w-full text-left p-3 rounded-lg transition-smooth',
                      isActive
                        ? 'bg-[var(--color-primary)] text-white'
                        : 'hover:bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)]'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{preview}</p>
                        <p className={cn(
                          'text-sm truncate mt-1',
                          isActive ? 'text-white/80' : 'text-[var(--color-text-secondary)]'
                        )}>
                          {lastMessage}
                        </p>
                      </div>
                      {isActive && (
                        <Icon name="check" size="sm" className="flex-shrink-0" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

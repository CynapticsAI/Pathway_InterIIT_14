/**
 * Chat Input Component - Modern Design
 * 
 * Updated with new design system, elevation, and proper icon usage
 */

'use client';

import { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { TextArea } from '../ui/Input';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [message]);

  return (
    <div className={cn(
      'bg-[var(--color-surface)]',
      'rounded-xl',
      'elevation-3',
      'p-4'
    )}>
      <div className="flex items-end gap-3 max-w-full">
        <Button 
          variant="ghost"
          size="icon"
          className="mb-1"
          title="Attach file"
          disabled={disabled}
        >
          <Icon name="attachment" size="sm" />
        </Button>

        <TextArea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about stocks, markets, or trends..."
          disabled={disabled}
          fullWidth
          rows={1}
          className="max-h-[120px] p-3 mx-2 resize-none"
          variant="filled"
        />

        <Button 
          variant="ghost"
          size="icon"
          className="mb-1"
          title="Voice input"
          disabled={disabled}
        >
          <Icon name="mic" size="sm" />
        </Button>

        <Button 
          variant="primary"
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          className="mb-1"
        >
          <Icon name="send" size="sm" />
        </Button>
      </div>
    </div>
  );
}

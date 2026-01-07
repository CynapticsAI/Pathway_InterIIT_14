/**
 * Chat Header - Modern Design
 * 
 * Updated with new Icon component and elevation system
 */

'use client';

import { Icon } from '../ui/Icon';
import { Button } from '../ui/Button';
import { useTheme } from '../theme/ThemeProvider';
import { useChatContext } from '@/contexts/ChatContext';
import { cn } from '@/lib/utils';

interface ChatHeaderProps {
  title?: string;
  onClose?: () => void;
  onNewChat?: () => void;
  onShowConversations?: () => void;
}

export function ChatHeader({ title = 'Stock Market AI Assistant', onClose, onNewChat, onShowConversations }: ChatHeaderProps) {
  const { isDark, toggleTheme } = useTheme();
  const { conversation, messages } = useChatContext();
  
  const messageCount = messages.length;
  const subtitle = conversation 
    ? `${messageCount} message${messageCount !== 1 ? 's' : ''}`
    : 'No active conversation';

  return (
    <header className={cn(
      'flex items-center justify-between',
      'px-6 py-4',
      'bg-[var(--color-primary)]',
      'text-white',
      'elevation-3'
    )}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center elevation-1">
          <Icon name="bar-chart" size="sm" className="text-white" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="text-sm text-white/80">{subtitle}</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Button 
          variant="ghost" 
          size="sm"
          onClick={onShowConversations}
          className="text-white hover:bg-white/20"
          title="View all conversations"
        >
          <Icon name="message" size="sm" />
          <span className="ml-2 hidden sm:inline">Chats</span>
        </Button>
        
        <Button 
          variant="ghost" 
          size="sm"
          onClick={onNewChat}
          className="text-white hover:bg-white/20"
          title="Start new conversation"
        >
          <Icon name="plus" size="sm" />
          <span className="ml-2 hidden sm:inline">New</span>
        </Button>
        
        {/* <Button 
          variant="ghost" 
          size="icon"
          onClick={toggleTheme}
          className="text-white hover:bg-white/20"
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          <Icon name={isDark ? 'sun' : 'moon'} size="sm" />
        </Button> */}
        
        {onClose && (
          <Button 
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-white hover:bg-white/20"
            title="Close"
          >
            <Icon name="close" size="sm" />
          </Button>
        )}
      </div>
    </header>
  );
}

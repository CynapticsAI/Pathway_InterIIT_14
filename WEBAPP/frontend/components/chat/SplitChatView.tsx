'use client';

import { useState, useEffect } from 'react';
import { ResizableLayout } from '../layout/ResizableLayout';
import { ChatContainer } from './ChatContainer';
import { ChartsPanel } from '../charts/ChartsPanel';
import { useChatContext } from '@/contexts/ChatContext';

export function SplitChatView() {
  const { messages: contextMessages } = useChatContext();
  const [isMobile, setIsMobile] = useState(false);

  // Convert messages to MessageType format for ChartsPanel
  const messages = contextMessages.map((msg) => ({
    id: msg.id.toString(),
    content: msg.content,
    sender: msg.message_type === 'user' ? 'user' as const : 'ai' as const,
    timestamp: new Date(msg.created_at),
  }));

  // Detect screen size for responsive layout
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Mobile: Show only chat with inline charts (no separate charts panel)
  if (isMobile) {
    return (
      <div className="h-full">
        <ChatContainer 
          showCharts={true}
        />
      </div>
    );
  }

  // Desktop: Resizable side-by-side
  return (
    <ResizableLayout
      leftPanel={
        <ChatContainer 
          showCharts={false}
        />
      }
      rightPanel={
        <ChartsPanel messages={messages} />
      }
      defaultLeftWidth={50}
      minLeftWidth={30}
      maxLeftWidth={70}
    />
  );
}

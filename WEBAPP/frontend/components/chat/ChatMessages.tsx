'use client';

import { useEffect, useRef } from 'react';
import { Message, MessageType } from './Message';

interface ChatMessagesProps {
  messages: MessageType[];
  showCharts?: boolean;
}

export function ChatMessages({ messages, showCharts = true }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="
      flex-1 
      overflow-y-auto 
      overflow-x-hidden
      px-4 md:px-6 py-6
      scroll-smooth
      min-h-0
    ">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center px-4">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-semibold text-[var(--color-foreground)] mb-2">
            Stock Market Analysis
          </h2>
          <p className="text-gray-400 max-w-md mb-6">
            Ask me about stock prices, market trends, portfolio analysis, or financial insights. Let's analyze the markets together!
          </p>
          
          {/* Suggested Prompts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full mt-4">
            <button className="p-4 bg-[var(--color-ai-message)] hover:bg-[var(--color-border)] rounded-xl text-left transition-colors border border-[var(--color-border)]">
              <div className="font-medium text-sm mb-1">📈 Market Overview</div>
              <div className="text-xs text-gray-500">Get today's market summary</div>
            </button>
            <button className="p-4 bg-[var(--color-ai-message)] hover:bg-[var(--color-border)] rounded-xl text-left transition-colors border border-[var(--color-border)]">
              <div className="font-medium text-sm mb-1">💹 Stock Analysis</div>
              <div className="text-xs text-gray-500">Analyze a specific stock</div>
            </button>
            <button className="p-4 bg-[var(--color-ai-message)] hover:bg-[var(--color-border)] rounded-xl text-left transition-colors border border-[var(--color-border)]">
              <div className="font-medium text-sm mb-1">📊 Portfolio Review</div>
              <div className="text-xs text-gray-500">Review portfolio performance</div>
            </button>
            <button className="p-4 bg-[var(--color-ai-message)] hover:bg-[var(--color-border)] rounded-xl text-left transition-colors border border-[var(--color-border)]">
              <div className="font-medium text-sm mb-1">⚡ Trading Alerts</div>
              <div className="text-xs text-gray-500">Set up price alerts</div>
            </button>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <Message key={message.id} message={message} showCharts={showCharts} />
          ))}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
}

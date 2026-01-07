/**
 * Message Component - Modern Design
 * 
 * Updated with elevation, semantic colors, and removed gradients
 */

import { Avatar } from '../ui/Avatar';
import { TypingIndicator } from '../ui/TypingIndicator';
import { StockLineChart, CandlestickChart, VolumeChart, MultiStockComparison, RRGChart } from '../charts';
import { cn } from '@/lib/utils';
import type { StockDataPoint, CandlestickDataPoint, VolumeDataPoint, RRGDataPoint } from '../charts';

export type ChartType = 'line' | 'area' | 'candlestick' | 'volume' | 'comparison' | 'rrg';

export interface ChartData {
  type: ChartType;
  symbol: string;
  data: StockDataPoint[] | CandlestickDataPoint[] | VolumeDataPoint[] | RRGDataPoint[] | any[];
  stocks?: { symbol: string; color: string }[]; // For comparison charts
  showArea?: boolean; // For line charts
  title?: string; // For RRG charts
  benchmark?: string; // For RRG charts
  height?: number; // For RRG charts
}

export interface MessageType {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isTyping?: boolean;
  chartData?: ChartData;
}

interface MessageProps {
  message: MessageType;
  showCharts?: boolean; // Control whether to render charts inline
}

export function Message({ message, showCharts = true }: MessageProps) {
  const isUser = message.sender === 'user';
  const time = message.timestamp.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit' 
  });

  const renderChart = () => {
    if (!message.chartData || !showCharts) return null;

    const { type, symbol, data, stocks, showArea, title, benchmark, height } = message.chartData;

    switch (type) {
      case 'line':
      case 'area':
        return (
          <StockLineChart 
            data={data as StockDataPoint[]} 
            symbol={symbol}
            showArea={showArea || type === 'area'}
          />
        );
      case 'candlestick':
        return (
          <CandlestickChart 
            data={data as CandlestickDataPoint[]} 
            symbol={symbol}
          />
        );
      case 'volume':
        return (
          <VolumeChart 
            data={data as VolumeDataPoint[]} 
            symbol={symbol}
          />
        );
      case 'comparison':
        return (
          <MultiStockComparison 
            data={data as any[]} 
            stocks={stocks || []}
          />
        );
      case 'rrg':
        return (
          <RRGChart 
            data={data as RRGDataPoint[]} 
            title={title || 'Relative Rotation Graph'}
            benchmark={benchmark || 'S&P 500'}
            height={height || 500}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div 
      className={cn(
        'flex gap-3 mb-6 animate-fadeIn',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <Avatar type={message.sender} size="md" />
        
          <div
            className={cn(
              'px-4 py-3 rounded-2xl elevation-2',
              'transition-all duration-200 hover:elevation-3',
              isUser ? [
                'bg-[var(--color-primary)]',
                'text-white',
                'rounded-tr-sm'
              ] : [
                'bg-[var(--color-surface)]',
                'text-[var(--color-foreground)]',
                'rounded-tl-sm'
              ]
            )}
          >
            {message.isTyping && !message.content ? (
              <TypingIndicator />
            ) : ""}
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        
        
        {/* Render chart if present and showCharts is true */}
        {!message.isTyping && showCharts && message.chartData && (
          <div className="mt-2 w-full">
            {renderChart()}
          </div>
        )}
        
        <span className={cn(
          'text-xs text-[var(--color-muted)] mt-1 px-2'
        )}>
          {time}
        </span>
      </div>
  );
}

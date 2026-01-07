/**
 * News Panel Component - Modern Design
 * 
 * Updated with elevation, Lucide icons, and semantic colors
 */

'use client';

import { useStockData } from '@/contexts/StockDataContext';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';

export function NewsPanel() {
  const { newsData } = useStockData();

  if (newsData.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Icon name="file-text" size={64} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">Waiting for news data...</p>
        </div>
      </div>
    );
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-100 flex items-center gap-2">
          <Icon name="file-text" size="md" />
          Latest Financial News
        </h3>
        <span className="text-sm text-gray-400">{newsData.length} articles</span>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
        {newsData.map((news, index) => (
          <div
            key={`${news.ticker}-${news.time}-${index}`}
            className={cn(
              'bg-[var(--color-surface)]',
              'rounded-lg p-4',
              'elevation-2',
              'hover:elevation-3',
              'transition-all duration-200'
            )}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-500/30 text-blue-300 rounded text-xs font-bold">
                  {news.ticker}
                </span>
                <span className="text-xs text-gray-400">{news.source}</span>
              </div>
              <span className="text-xs text-gray-400 whitespace-nowrap">
                {formatTime(news.timestamp)}
              </span>
            </div>

            {/* Title */}
            <h4 className="text-gray-100 font-medium mb-2 leading-snug">
              {news.title}
            </h4>

            {/* Link */}
            <a
              href={news.url.includes('https://') ? news.url : `https://finviz.com${news.url}`}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                'text-blue-400',
                'hover:text-blue-300',
                'text-sm flex items-center gap-1',
                'group transition-colors'
              )}
            >
              Read full article
              <Icon 
                name="arrow-right" 
                size="xs" 
                className="group-hover:translate-x-1 transition-transform" 
              />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

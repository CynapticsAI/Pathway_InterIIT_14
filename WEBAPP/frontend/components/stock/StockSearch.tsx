/**
 * Stock Search Component - Modern Design
 * 
 * Updated with new Input component, Lucide icons, and elevation
 */

'use client';

import { useState } from 'react';
import { useStockData } from '@/contexts/StockDataContext';
import { Input } from '@/components/ui/Input';
import { Icon } from '@/components/ui/Icon';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

export function StockSearch() {
  const { selectedSymbol, selectSymbol, availableSymbols, isConnected } = useStockData();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSymbols = availableSymbols.filter(symbol =>
    symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <div className="flex items-center gap-2 text-sm">
        <div className={cn(
          'w-2 h-2 rounded-full',
          isConnected ? 'bg-[var(--color-success)] animate-pulse' : 'bg-[var(--color-danger)]'
        )} />
        <span className="text-[var(--color-muted)]">
          {isConnected ? 'Connected to real-time data' : 'Disconnected'}
        </span>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search stocks (NVDA, AAPL, MSFT, GOOGL)..."
          variant="filled"
          fullWidth
        />
        <Icon 
          name="search" 
          size="sm" 
          className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--color-muted)]" 
        />
      </div>

      {/* Symbol Chips */}
      <div className="flex flex-wrap gap-2">
        {filteredSymbols.map((symbol) => (
          <Button
            key={symbol}
            onClick={() => selectSymbol(symbol === selectedSymbol ? null : symbol)}
            variant={selectedSymbol === symbol ? 'primary' : 'secondary'}
            size="md"
            className={cn(
              'transition-all duration-200',
              selectedSymbol === symbol && 'scale-105'
            )}
          >
            {symbol}
          </Button>
        ))}
      </div>

      {/* Selected Stock Info */}
      {selectedSymbol && (
        <div className={cn(
          'mt-4 p-4 rounded-lg',
          'bg-[var(--color-primary)]/10',
          'border border-[var(--color-primary)]/30',
          'elevation-1'
        )}>
          <div className="flex items-center gap-2">
            <Icon name="trending-up" size="lg" className="text-[var(--color-primary)]" />
            <div>
              <h3 className="text-lg font-bold text-[var(--color-foreground)]">{selectedSymbol}</h3>
              <p className="text-sm text-[var(--color-muted)]">Real-time data streaming</p>
            </div>
          </div>
        </div>
      )}

      {/* No Selection Message */}
      {!selectedSymbol && (
        <div className="text-center py-8 text-[var(--color-muted)]">
          <Icon name="bar-chart" size={64} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">Select a stock to view real-time data</p>
        </div>
      )}
    </div>
  );
}

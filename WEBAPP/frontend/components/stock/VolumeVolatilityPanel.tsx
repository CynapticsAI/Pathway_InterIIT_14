/**
 * Volume & Volatility Panel Component - Modern Design
 * 
 * Updated with semantic colors, Material Design icons, and improved styling
 */

'use client';

import { useStockData } from '@/contexts/StockDataContext';
import { useMemo } from 'react';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';

export function VolumeVolatilityPanel() {
  const { selectedSymbol, volumeSpikesData, availableSymbols } = useStockData();

  const displayData = useMemo(() => {
    if (selectedSymbol) {
      return volumeSpikesData.get(selectedSymbol) || [];
    }
    // Show all symbols' data
    const allData: any[] = [];
    availableSymbols.forEach(symbol => {
      const symbolData = volumeSpikesData.get(symbol) || [];
      allData.push(...symbolData);
    });
    // Sort by timestamp descending
    return allData.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [selectedSymbol, volumeSpikesData, availableSymbols]);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return 'bg-red-500/30 text-red-300 border-red-500/50';
      case 'HIGH':
        return 'bg-orange-500/30 text-orange-300 border-orange-500/50';
      case 'MEDIUM':
        return 'bg-yellow-500/30 text-yellow-300 border-yellow-500/50';
      case 'LOW':
        return 'bg-green-500/30 text-green-300 border-green-500/50';
      default:
        return 'bg-gray-500/30 text-gray-300 border-gray-500/50';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  };

  if (displayData.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Icon name="activity" size={64} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">
            {selectedSymbol 
              ? `Waiting for volume spike data for ${selectedSymbol}...`
              : 'Waiting for volume spike data...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-100 flex items-center gap-2">
          <Icon name="activity" size="md" />
          Volume & Volatility Spikes
          {selectedSymbol && <span className="text-blue-400">- {selectedSymbol}</span>}
        </h3>
        <span className="text-sm text-gray-400">{displayData.length} events</span>
      </div>

      {/* Table View */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Symbol</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium">Time (UTC)</th>
              <th className="text-right py-3 px-4 text-gray-300 font-medium">Price</th>
              <th className="text-right py-3 px-4 text-gray-300 font-medium">Volume</th>
              <th className="text-right py-3 px-4 text-gray-300 font-medium">Vol Z-Score</th>
              <th className="text-right py-3 px-4 text-gray-300 font-medium">Volatility Z-Score</th>
              <th className="text-center py-3 px-4 text-gray-300 font-medium">Risk Level</th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((item, index) => (
              <tr
                key={`${item.symbol}-${item.time}-${index}`}
                className={cn(
                  'border-b border-[var(--color-border)]',
                  'hover:bg-[var(--color-surface)] transition-colors'
                )}
              >
                <td className="py-3 px-4">
                  <span className="px-2 py-1 bg-blue-500/30 text-blue-300 rounded text-xs font-bold">
                    {item.symbol}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-400 text-xs">
                  {formatTime(item.timestamp)}
                </td>
                <td className="py-3 px-4 text-right text-gray-100 font-medium">
                  ${item.currentClose.toFixed(2)}
                </td>
                <td className="py-3 px-4 text-right text-gray-300">
                  {item.currentVolume.toLocaleString()}
                </td>
                <td className="py-3 px-4 text-right">
                  <span className={item.volumeZScore > 2 ? 'text-red-400 font-bold' : item.volumeZScore > 1 ? 'text-yellow-400' : 'text-gray-400'}>
                    {item.volumeZScore.toFixed(2)}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span className={item.volatilityZScore > 2 ? 'text-red-400 font-bold' : item.volatilityZScore > 1 ? 'text-yellow-400' : 'text-gray-400'}>
                    {item.volatilityZScore.toFixed(2)}
                  </span>
                </td>
                <td className="py-3 px-4 text-center">
                  <span className={cn(
                    'px-3 py-1 rounded-full text-xs font-bold border',
                    getRiskColor(item.riskLevel)
                  )}>
                    {item.riskLevel}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

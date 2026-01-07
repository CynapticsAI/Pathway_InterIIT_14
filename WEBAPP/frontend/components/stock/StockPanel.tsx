/**
 * Stock Panel Component - Modern Design
 * 
 * Updated with elevation instead of borders
 */

'use client';

import { StockSearch } from './StockSearch';
import { StockTicksChart } from './StockTicksChart';
import { SarimaxChart } from './SarimaxChart';
import { cn } from '@/lib/utils';

export function StockPanel() {
  return (
    <div className="h-full overflow-y-auto space-y-6 p-4">
      {/* Stock Search and Selection */}
      <div className={cn(
        'bg-[var(--color-surface)]',
        'rounded-lg p-4',
        'elevation-2'
      )}>
        <StockSearch />
      </div>

      {/* Real-Time Charts */}
      <div className="space-y-4">
        {/* Stock Ticks Chart */}
        <div className={cn(
          'bg-[var(--color-surface)]',
          'rounded-lg p-4',
          'elevation-2'
        )}>
          <StockTicksChart />
        </div>

        {/* SARIMAX Forecast Chart */}
        <div className={cn(
          'bg-[var(--color-surface)]',
          'rounded-lg p-4',
          'elevation-2'
        )}>
          <SarimaxChart />
        </div>
      </div>
    </div>
  );
}

/**
 * Stocks List Component - Modern Design
 * 
 * Updated with elevation, semantic colors, and improved styling
 */

'use client';

import React, { useState } from 'react';
import { usePortfolio } from '@/contexts/PortfolioContext';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';
import type { StockWithLiveData } from '@/types/portfolio';

export function StocksList() {
  const { stocks, isLoading, deleteStock } = usePortfolio();
  const [deletingSymbol, setDeletingSymbol] = useState<string | null>(null);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value: string | number) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(num);
  };

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const handleDelete = async (symbol: string) => {
    if (!confirm(`Are you sure you want to remove ${symbol} from your portfolio?`)) {
      return;
    }

    setDeletingSymbol(symbol);
    try {
      await deleteStock(symbol);
    } finally {
      setDeletingSymbol(null);
    }
  };

  if (isLoading) {
    return (
      <div className={cn(
        'bg-[var(--color-surface)]',
        'rounded-lg elevation-2 p-6'
      )}>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-[var(--color-muted)]/20 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (stocks.length === 0) {
    return (
      <div className={cn(
        'bg-[var(--color-surface)]',
        'rounded-lg elevation-2 p-12 text-center'
      )}>
        <Icon name="bar-chart" size={64} className="mx-auto mb-4 opacity-50 text-[var(--color-muted)]" />
        <h3 className="text-xl font-semibold mb-2 text-[var(--color-foreground)]">No Stocks in Portfolio</h3>
        <p className="text-[var(--color-muted)]">
          Add your first stock to start tracking your portfolio
        </p>
      </div>
    );
  }

  return (
    <div className={cn(
      'bg-[var(--color-surface)]',
      'rounded-lg elevation-2 overflow-hidden'
    )}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-max">
          <thead className="bg-[var(--color-surface-elevated)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Symbol
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Quantity
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Cost Basis
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Total Cost
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Current Price
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Current Value
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                P&L
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                P&L %
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-[var(--color-foreground)] uppercase tracking-wider whitespace-nowrap">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {stocks.map((stock) => {
              const pnlColor =
                stock.pnl !== undefined
                  ? stock.pnl >= 0
                    ? 'text-[var(--color-success)]'
                    : 'text-[var(--color-danger)]'
                  : 'text-[var(--color-muted)]';

              return (
                <tr
                  key={stock.id}
                  className="hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="font-semibold text-[var(--color-foreground)]">{stock.symbol}</div>
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--color-muted)] whitespace-nowrap">
                    {formatNumber(stock.quantity)}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--color-muted)] whitespace-nowrap">
                    {formatCurrency(parseFloat(stock.cost_basis))}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--color-muted)] whitespace-nowrap">
                    {formatCurrency(parseFloat(stock.total_cost))}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {stock.current_price !== undefined ? (
                      <span className="font-medium text-[var(--color-foreground)]">
                        {formatCurrency(stock.current_price)}
                      </span>
                    ) : (
                      <span className="text-[var(--color-muted)]">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {stock.current_value !== undefined ? (
                      <span className="font-medium text-[var(--color-foreground)]">
                        {formatCurrency(stock.current_value)}
                      </span>
                    ) : (
                      <span className="text-[var(--color-muted)]">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {stock.pnl !== undefined ? (
                      <span className={cn('font-semibold', pnlColor)}>
                        {formatCurrency(stock.pnl)}
                      </span>
                    ) : (
                      <span className="text-[var(--color-muted)]">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {stock.pnl_percentage !== undefined ? (
                      <span className={cn('font-semibold', pnlColor)}>
                        {formatPercentage(stock.pnl_percentage)}
                      </span>
                    ) : (
                      <span className="text-[var(--color-muted)]">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center whitespace-nowrap">
                    <Button
                      onClick={() => handleDelete(stock.symbol)}
                      disabled={deletingSymbol === stock.symbol}
                      variant="danger"
                      size="sm"
                    >
                      {deletingSymbol === stock.symbol ? 'Deleting...' : 'Delete'}
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

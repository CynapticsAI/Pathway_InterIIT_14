/**
 * Portfolio Stats Component - Modern Design
 * 
 * Updated with Lucide icons, elevation, and semantic colors
 */

'use client';

import React from 'react';
import { usePortfolio } from '@/contexts/PortfolioContext';
import { Icon } from '@/components/ui/Icon';
import { cn } from '@/lib/utils';

export function PortfolioStats() {
  const { portfolioStats, isLoading } = usePortfolio();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className={cn(
            'bg-[var(--color-surface)]',
            'rounded-lg p-6',
            'elevation-2',
            'animate-pulse'
          )}>
            <div className="h-4 bg-[var(--color-muted)]/20 rounded w-1/2 mb-2"></div>
            <div className="h-8 bg-[var(--color-muted)]/20 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!portfolioStats) {
    return null;
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const stats = [
    {
      label: 'Total Value',
      value: formatCurrency(portfolioStats.current_value),
      subValue: `Invested: ${formatCurrency(portfolioStats.total_invested)}`,
      color: 'text-[var(--color-foreground)]',
      icon: 'dollar',
    },
    {
      label: 'Total P&L',
      value: formatCurrency(portfolioStats.total_pnl),
      subValue: formatPercentage(portfolioStats.total_pnl_percentage),
      color: portfolioStats.total_pnl >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]',
      icon: portfolioStats.total_pnl >= 0 ? 'trending-up' : 'trending-down',
    },
    {
      label: 'Day P&L',
      value: formatCurrency(portfolioStats.day_pnl),
      subValue: formatPercentage(portfolioStats.day_pnl_percentage),
      color: portfolioStats.day_pnl >= 0 ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]',
      icon: portfolioStats.day_pnl >= 0 ? 'trending-up' : 'trending-down',
    },
    {
      label: 'Best Performer',
      value: portfolioStats.best_performer?.symbol || '-',
      subValue: portfolioStats.best_performer
        ? formatPercentage(portfolioStats.best_performer.pnl_percentage || 0)
        : '-',
      color: 'text-[var(--color-success)]',
      icon: 'star',
    },
  ] as const;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => {
        // For P&L stats, apply color to both value and subValue
        const shouldColorSubValue = stat.label.includes('P&L') || stat.label === 'Best Performer';
        
        return (
          <div
            key={index}
            className={cn(
              'bg-[var(--color-surface)]',
              'rounded-lg p-6',
              'elevation-2',
              'hover:elevation-3',
              'transition-all duration-200'
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-[var(--color-muted)] mb-1">{stat.label}</p>
                <p className={cn('text-2xl font-bold mb-1', stat.color)}>
                  {stat.value}
                </p>
                <p className={cn(
                  'text-xs font-medium',
                  shouldColorSubValue ? stat.color : 'text-[var(--color-muted)]'
                )}>
                  {stat.subValue}
                </p>
              </div>
              <div className={cn(stat.color, 'opacity-20')}>
                <Icon name={stat.icon} size="lg" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

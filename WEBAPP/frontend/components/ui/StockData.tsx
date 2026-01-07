interface StockPriceProps {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  size?: 'sm' | 'md' | 'lg';
}

export function StockPrice({ symbol, price, change, changePercent, size = 'md' }: StockPriceProps) {
  const isPositive = change >= 0;
  const changeColor = isPositive ? 'text-gain' : 'text-loss';
  const arrow = isPositive ? '▲' : '▼';
  
  const sizes = {
    sm: { price: 'text-lg', symbol: 'text-sm', change: 'text-xs' },
    md: { price: 'text-2xl', symbol: 'text-base', change: 'text-sm' },
    lg: { price: 'text-4xl', symbol: 'text-lg', change: 'text-base' },
  };

  return (
    <div className="inline-flex flex-col gap-1">
      <div className="flex items-baseline gap-2">
        <span className={`font-semibold text-[var(--color-foreground)] ${sizes[size].symbol}`}>
          {symbol}
        </span>
        <span className={`stock-price ${sizes[size].price}`}>
          ${price.toFixed(2)}
        </span>
      </div>
      <div className={`flex items-center gap-1 ${changeColor} ${sizes[size].change}`}>
        <span>{arrow}</span>
        <span className="percentage">
          ${Math.abs(change).toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
        </span>
      </div>
    </div>
  );
}

interface MarketBadgeProps {
  status: 'gain' | 'loss' | 'neutral' | 'warning';
  children: React.ReactNode;
}

export function MarketBadge({ status, children }: MarketBadgeProps) {
  const colors = {
    gain: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    loss: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    neutral: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
    warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}>
      {children}
    </span>
  );
}

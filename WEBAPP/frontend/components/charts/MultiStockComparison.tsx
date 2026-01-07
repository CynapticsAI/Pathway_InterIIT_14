'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export interface MultiStockDataPoint {
  date: string;
  [key: string]: number | string; // Dynamic keys for different stocks
}

interface MultiStockComparisonProps {
  data: MultiStockDataPoint[];
  stocks: { symbol: string; color: string }[];
  height?: number;
}

export function MultiStockComparison({ data, stocks, height = 300 }: MultiStockComparisonProps) {
  
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-[var(--color-foreground)] mb-2">{data.date}</p>
          <div className="space-y-1">
            {payload.map((entry: any) => (
              <p key={`${entry.name}-${entry.value}`} className="text-xs" style={{ color: entry.color }}>
                {entry.name}: ${entry.value.toFixed(2)}
              </p>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full bg-[var(--color-ai-message)] rounded-xl p-4 border border-[var(--color-border)]">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-[var(--color-foreground)]">Stock Comparison</h3>
        <p className="text-xs text-gray-400">Multiple stocks price movement</p>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
          <XAxis 
            dataKey="date" 
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
            tickLine={false}
          />
          <YAxis 
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
            tickLine={false}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />
          
          {stocks.map((stock, index) => (
            <Line
              key={stock.symbol}
              type="monotone"
              dataKey={stock.symbol}
              stroke={stock.color}
              strokeWidth={2}
              dot={false}
              animationDuration={1000}
              animationBegin={index * 100}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      
      <div className="flex flex-wrap gap-3 mt-3">
        {stocks.map((stock) => (
          <div key={stock.symbol} className="flex items-center gap-2 text-xs">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: stock.color }}
            ></div>
            <span className="text-gray-400">{stock.symbol}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

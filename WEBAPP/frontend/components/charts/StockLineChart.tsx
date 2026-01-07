'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export interface StockDataPoint {
  date: string;
  price: number;
  volume?: number;
}

interface StockLineChartProps {
  data: StockDataPoint[];
  symbol: string;
  color?: string;
  showArea?: boolean;
  height?: number;
}

export function StockLineChart({ 
  data, 
  symbol, 
  color = '#3b82f6', 
  showArea = false,
  height = 300 
}: StockLineChartProps) {
  
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-[var(--color-foreground)]">{data.date}</p>
          <p className="text-sm text-[var(--color-primary)]">
            Price: ${data.price.toFixed(2)}
          </p>
          {data.volume && (
            <p className="text-xs text-gray-400">
              Volume: {(data.volume / 1000000).toFixed(2)}M
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const ChartComponent = showArea ? AreaChart : LineChart;

  return (
    <div className="w-full bg-[var(--color-ai-message)] rounded-xl p-4 border border-[var(--color-border)]">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-[var(--color-foreground)]">{symbol} Price Chart</h3>
        <p className="text-xs text-gray-400">Interactive price movement</p>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
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
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {showArea ? (
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke={color}
              strokeWidth={2}
              fill="url(#colorPrice)"
              animationDuration={1000}
            />
          ) : (
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke={color}
              strokeWidth={2}
              dot={false}
              animationDuration={1000}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}

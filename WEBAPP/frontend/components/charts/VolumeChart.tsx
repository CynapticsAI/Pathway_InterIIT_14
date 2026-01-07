'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export interface VolumeDataPoint {
  date: string;
  volume: number;
  change?: number; // To color bars based on price change
}

interface VolumeChartProps {
  data: VolumeDataPoint[];
  symbol: string;
  height?: number;
}

export function VolumeChart({ data, symbol, height = 250 }: VolumeChartProps) {
  
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-[var(--color-foreground)]">{data.date}</p>
          <p className="text-sm text-[var(--color-primary)]">
            Volume: {(data.volume / 1000000).toFixed(2)}M
          </p>
          {data.change !== undefined && (
            <p className={`text-xs ${data.change >= 0 ? 'text-gain' : 'text-loss'}`}>
              Price {data.change >= 0 ? '▲' : '▼'} {Math.abs(data.change).toFixed(2)}%
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // Add color based on price change
  const chartData = data.map(item => ({
    ...item,
    fill: item.change !== undefined ? (item.change >= 0 ? '#10b981' : '#ef4444') : '#3b82f6'
  }));

  return (
    <div className="w-full bg-[var(--color-ai-message)] rounded-xl p-4 border border-[var(--color-border)]">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-[var(--color-foreground)]">{symbol} Trading Volume</h3>
        <p className="text-xs text-gray-400">Volume in millions</p>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
            tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="volume" 
            radius={[4, 4, 0, 0]}
            animationDuration={1000}
          >
            {chartData.map((entry, index) => (
              <Bar key={`bar-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

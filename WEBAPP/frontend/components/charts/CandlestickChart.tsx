'use client';

import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, Line } from 'recharts';

export interface CandlestickDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface CandlestickChartProps {
  data: CandlestickDataPoint[];
  symbol: string;
  height?: number;
}

export function CandlestickChart({ data, symbol, height = 350 }: CandlestickChartProps) {
  
  // Transform data for visualization
  const chartData = data.map(item => ({
    ...item,
    fill: item.close >= item.open ? '#10b981' : '#ef4444',
    // For bar chart representation of candlestick
    range: [item.low, item.high],
    body: item.close >= item.open ? [item.open, item.close] : [item.close, item.open],
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isGain = data.close >= data.open;
      
      return (
        <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg">
          <p className="text-sm font-semibold text-[var(--color-foreground)] mb-2">{data.date}</p>
          <div className="space-y-1 text-xs">
            <p className="text-gray-400">Open: <span className="text-[var(--color-foreground)]">${data.open.toFixed(2)}</span></p>
            <p className="text-gray-400">High: <span className="text-gain">${data.high.toFixed(2)}</span></p>
            <p className="text-gray-400">Low: <span className="text-loss">${data.low.toFixed(2)}</span></p>
            <p className="text-gray-400">Close: <span className={isGain ? 'text-gain' : 'text-loss'}>${data.close.toFixed(2)}</span></p>
            <p className={`font-medium ${isGain ? 'text-gain' : 'text-loss'}`}>
              {isGain ? '▲' : '▼'} ${Math.abs(data.close - data.open).toFixed(2)} 
              ({((data.close - data.open) / data.open * 100).toFixed(2)}%)
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom Candlestick component
  const CustomCandlestick = (props: any) => {
    const { x, y, width, height, payload } = props;
    if (!payload) return null;

    const isGain = payload.close >= payload.open;
    const color = isGain ? '#10b981' : '#ef4444';
    
    const wickX = x + width / 2;
    const bodyTop = Math.min(payload.open, payload.close);
    const bodyBottom = Math.max(payload.open, payload.close);
    const bodyHeight = Math.abs(payload.close - payload.open);
    
    // Scale for Y-axis (simplified - in real implementation use scale from chart)
    const yScale = (value: number) => {
      const min = Math.min(...data.map(d => d.low));
      const max = Math.max(...data.map(d => d.high));
      const range = max - min;
      return y + height - ((value - min) / range) * height;
    };

    return (
      <g>
        {/* Wick (high-low line) */}
        <line
          x1={wickX}
          y1={yScale(payload.high)}
          x2={wickX}
          y2={yScale(payload.low)}
          stroke={color}
          strokeWidth={1}
        />
        {/* Body */}
        <rect
          x={x + 1}
          y={yScale(bodyBottom)}
          width={width - 2}
          height={Math.max((bodyBottom - bodyTop) / (Math.max(...data.map(d => d.high)) - Math.min(...data.map(d => d.low))) * height, 1)}
          fill={color}
          stroke={color}
          strokeWidth={1}
        />
      </g>
    );
  };

  return (
    <div className="w-full bg-[var(--color-ai-message)] rounded-xl p-4 border border-[var(--color-border)]">
      <div className="mb-3">
        <h3 className="text-lg font-semibold text-[var(--color-foreground)]">{symbol} Candlestick Chart</h3>
        <p className="text-xs text-gray-400">OHLC (Open, High, Low, Close)</p>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
            domain={['dataMin - 2', 'dataMax + 2']}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Simplified bar representation of candlesticks */}
          <Bar 
            dataKey="high" 
            fill="transparent"
          />
          {chartData.map((entry, index) => {
            const isGain = entry.close >= entry.open;
            const color = isGain ? '#10b981' : '#ef4444';
            return (
              <Line
                key={`candle-${index}`}
                type="monotone"
                dataKey="close"
                stroke={color}
                strokeWidth={0}
                dot={{ fill: color, r: 4 }}
              />
            );
          })}
        </ComposedChart>
      </ResponsiveContainer>
      
      <div className="flex gap-4 mt-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gain rounded"></div>
          <span className="text-gray-400">Bullish (Close ≥ Open)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-loss rounded"></div>
          <span className="text-gray-400">Bearish (Close &lt; Open)</span>
        </div>
      </div>
    </div>
  );
}

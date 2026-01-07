'use client';

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Label, Cell } from 'recharts';

export interface RRGDataPoint {
  symbol: string;
  rsRatio: number;      // Relative Strength Ratio (x-axis)
  rsMomentum: number;   // Relative Strength Momentum (y-axis)
  color?: string;
  size?: number;
}

interface RRGChartProps {
  data: RRGDataPoint[];
  title?: string;
  benchmark?: string;
  height?: number;
}

export function RRGChart({ 
  data, 
  title = 'Relative Rotation Graph',
  benchmark = 'S&P 500',
  height = 500 
}: RRGChartProps) {
  
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      const quadrant = getQuadrant(point.rsRatio, point.rsMomentum);
      
      return (
        <div className="bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg p-4 shadow-lg">
          <p className="text-sm font-bold text-[var(--color-foreground)] mb-2">{point.symbol}</p>
          <p className="text-xs text-gray-400 mb-1">RS-Ratio: {point.rsRatio.toFixed(2)}</p>
          <p className="text-xs text-gray-400 mb-1">RS-Momentum: {point.rsMomentum.toFixed(2)}</p>
          <div className={`text-xs font-semibold mt-2 px-2 py-1 rounded ${getQuadrantColor(quadrant)}`}>
            {quadrant}
          </div>
        </div>
      );
    }
    return null;
  };

  const getQuadrant = (rsRatio: number, rsMomentum: number): string => {
    if (rsRatio >= 100 && rsMomentum >= 100) return 'Leading 🚀';
    if (rsRatio < 100 && rsMomentum >= 100) return 'Improving 📈';
    if (rsRatio < 100 && rsMomentum < 100) return 'Lagging 📉';
    return 'Weakening ⚠️';
  };

  const getQuadrantColor = (quadrant: string): string => {
    if (quadrant.includes('Leading')) return 'bg-green-500/20 text-green-400 border border-green-500/30';
    if (quadrant.includes('Improving')) return 'bg-blue-500/20 text-blue-400 border border-blue-500/30';
    if (quadrant.includes('Lagging')) return 'bg-red-500/20 text-red-400 border border-red-500/30';
    return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
  };

  const getDefaultColor = (rsRatio: number, rsMomentum: number): string => {
    if (rsRatio >= 100 && rsMomentum >= 100) return '#10b981'; // Green - Leading
    if (rsRatio < 100 && rsMomentum >= 100) return '#3b82f6';  // Blue - Improving
    if (rsRatio < 100 && rsMomentum < 100) return '#ef4444';   // Red - Lagging
    return '#f59e0b'; // Orange - Weakening
  };

  return (
    <div className="w-full bg-[var(--color-ai-message)] rounded-xl p-6 border border-[var(--color-border)]">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-bold text-[var(--color-foreground)] mb-1">
          {title}
        </h3>
        <p className="text-sm text-gray-400">
          Benchmark: {benchmark} • Relative Strength Analysis
        </p>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="var(--color-border)"
          />
          
          {/* X-axis: RS-Ratio */}
          <XAxis 
            type="number" 
            dataKey="rsRatio" 
            name="RS-Ratio"
            stroke="var(--color-foreground)"
            tick={{ fill: 'var(--color-foreground)', fontSize: 12 }}
            domain={[95, 105]}
          >
            <Label 
              value="RS-Ratio (Relative Strength) →" 
              position="bottom" 
              style={{ fill: 'var(--color-foreground)', fontSize: 14 }}
            />
          </XAxis>
          
          {/* Y-axis: RS-Momentum */}
          <YAxis 
            type="number" 
            dataKey="rsMomentum" 
            name="RS-Momentum"
            stroke="var(--color-foreground)"
            tick={{ fill: 'var(--color-foreground)', fontSize: 12 }}
            domain={[95, 105]}
          >
            <Label 
              value="RS-Momentum →" 
              angle={-90} 
              position="left" 
              style={{ fill: 'var(--color-foreground)', fontSize: 14 }}
            />
          </YAxis>
          
          {/* Reference lines at 100 (benchmark) */}
          <ReferenceLine 
            x={100} 
            stroke="#6366f1" 
            strokeWidth={2}
            strokeDasharray="5 5"
          />
          <ReferenceLine 
            y={100} 
            stroke="#6366f1" 
            strokeWidth={2}
            strokeDasharray="5 5"
          />
          
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          
          {/* Scatter plot */}
          <Scatter 
            data={data} 
            fill="#8884d8"
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color || getDefaultColor(entry.rsRatio, entry.rsMomentum)}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-lg p-3">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <div>
            <p className="text-xs font-semibold text-green-400">Leading 🚀</p>
            <p className="text-xs text-gray-400">Strong & Rising</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <div>
            <p className="text-xs font-semibold text-blue-400">Improving 📈</p>
            <p className="text-xs text-gray-400">Weak but Rising</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div>
            <p className="text-xs font-semibold text-red-400">Lagging 📉</p>
            <p className="text-xs text-gray-400">Weak & Falling</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div>
            <p className="text-xs font-semibold text-yellow-400">Weakening ⚠️</p>
            <p className="text-xs text-gray-400">Strong but Falling</p>
          </div>
        </div>
      </div>

      {/* Stock Labels on Chart */}
      <div className="mt-4 flex flex-wrap gap-2">
        {data.map((point, index) => (
          <div 
            key={index}
            className="px-3 py-1 rounded-full text-xs font-semibold border"
            style={{ 
              backgroundColor: `${point.color || getDefaultColor(point.rsRatio, point.rsMomentum)}20`,
              borderColor: point.color || getDefaultColor(point.rsRatio, point.rsMomentum),
              color: point.color || getDefaultColor(point.rsRatio, point.rsMomentum)
            }}
          >
            {point.symbol}
          </div>
        ))}
      </div>
    </div>
  );
}

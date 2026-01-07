'use client';

import { useStockData } from '@/contexts/StockDataContext';
import { useMemo } from 'react';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from 'recharts';

export function SarimaxChart() {
  const { selectedSymbol, forecastsData } = useStockData();

  const chartData = useMemo(() => {
    if (!selectedSymbol) return [];

    const symbolData = forecastsData.get(selectedSymbol) || [];
    return symbolData
      .filter(d => d.current_price > 0 && d.forecast_price > 0) // Filter out invalid/zero values
      .map(d => ({
        time: new Date(d.timestamp).toISOString().split('T')[1].substring(0, 8) + ' UTC',
        current: d.current_price,
        forecast: d.forecast_price,
        signal: d.final_combined_signal,
        sentiment: d.sentiment_score,
      }));
  }, [selectedSymbol, forecastsData]);

  const yAxisDomain = useMemo(() => {
    if (chartData.length === 0) return ['auto', 'auto'];
    
    const allPrices = chartData.flatMap(d => [d.current, d.forecast]).filter(p => p > 0);
    if (allPrices.length === 0) return ['auto', 'auto'];
    
    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    
    return [minPrice - 10, maxPrice + 10];
  }, [chartData]);

  const latestForecast = chartData.length > 0 ? chartData[chartData.length - 1] : null;

  const getSignalText = (signal: number) => {
    if (signal >= 0.6) return 'STRONG_BUY';
    if (signal >= 0.2) return 'BUY';
    if (signal <= -0.6) return 'STRONG_SELL';
    if (signal <= -0.2) return 'SELL';
    return 'HOLD';
  };

  const getSignalColor = (signal: number) => {
    if (signal >= 0.2) return 'text-green-500';
    if (signal <= -0.2) return 'text-red-500';
    return 'text-yellow-500';
  };

  const getSignalBg = (signal: number) => {
    if (signal >= 0.2) return 'bg-green-500/20';
    if (signal <= -0.2) return 'bg-red-500/20';
    return 'bg-yellow-500/20';
  };

  if (!selectedSymbol) {
    return (
      <div className="h-[350px] flex items-center justify-center text-gray-400">
        <p>Select a stock to view SARIMAX forecast</p>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="h-[350px] flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="animate-pulse mb-2">🔮</div>
          <p>Waiting for {selectedSymbol} forecast data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">{selectedSymbol} - SARIMAX Forecast</h3>
        {latestForecast && (
          <div className={`px-3 py-1 rounded-full ${getSignalBg(latestForecast.signal)} ${getSignalColor(latestForecast.signal)} font-bold text-sm`}>
            {getSignalText(latestForecast.signal)}
          </div>
        )}
      </div>

      {/* Signal Stats */}
      {latestForecast && (
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div className="bg-[var(--color-input-background)] p-2 rounded">
            <div className="text-gray-400">Current</div>
            <div className="text-white font-bold">${latestForecast.current.toFixed(2)}</div>
          </div>
          <div className="bg-[var(--color-input-background)] p-2 rounded">
            <div className="text-gray-400">Forecast</div>
            <div className="text-white font-bold">${latestForecast.forecast.toFixed(2)}</div>
          </div>
          <div className="bg-[var(--color-input-background)] p-2 rounded">
            <div className="text-gray-400">Sentiment</div>
            <div className="text-white font-bold">{(latestForecast.sentiment * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis 
              dataKey="time" 
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
            />
            <YAxis 
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af' }}
              tickFormatter={(value) => `$${value.toFixed(2)}`}
              domain={yAxisDomain}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgb(59, 130, 246)',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#fff' }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: any, name: string) => {
                if (name === 'sentiment') return [`${(value * 100).toFixed(1)}%`, 'Sentiment'];
                return [`$${value.toFixed(2)}`, name];
              }}
            />
            <Legend 
              wrapperStyle={{ color: '#fff' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="current"
              name="Current Price"
              stroke="rgb(59, 130, 246)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
              connectNulls={true}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              name="Forecast Price"
              stroke="rgb(168, 85, 247)"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 6 }}
              connectNulls={true}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

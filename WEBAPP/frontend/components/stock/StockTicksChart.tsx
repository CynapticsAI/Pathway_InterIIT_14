'use client';

import { useStockData } from '@/contexts/StockDataContext';
import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function StockTicksChart() {
  const { selectedSymbol, ticksData } = useStockData();

  const chartData = useMemo(() => {
    if (!selectedSymbol) return [];

    const symbolData = ticksData.get(selectedSymbol) || [];
    return symbolData
      .filter(d => d.price > 0) // Filter out invalid/zero values
      .map(d => ({
        time: new Date(d.timestamp).toISOString().split('T')[1].substring(0, 8) + ' UTC',
        price: d.price,
        volume: d.volume,
      }));
  }, [selectedSymbol, ticksData]);

  const yAxisDomain = useMemo(() => {
    if (chartData.length === 0) return ['auto', 'auto'];
    
    const prices = chartData.map(d => d.price).filter(p => p > 0);
    if (prices.length === 0) return ['auto', 'auto'];
    
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    return [minPrice*0.99, maxPrice*1.01];
  }, [chartData]);

  if (!selectedSymbol) {
    return (
      <div className="h-[300px] flex items-center justify-center text-gray-400">
        <p>Select a stock to view price chart</p>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="animate-pulse mb-2">📡</div>
          <p>Waiting for {selectedSymbol} tick data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-bold text-white">{selectedSymbol} - Real-Time Price</h3>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
              formatter={(value: any) => [`$${value.toFixed(2)}`, 'Price']}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="rgb(59, 130, 246)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
              connectNulls={true}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

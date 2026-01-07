import { StockDataPoint, CandlestickDataPoint, VolumeDataPoint } from '../components/charts';

/**
 * Generate sample stock price data for demonstration
 */
export function generateStockData(
  symbol: string,
  days: number = 30,
  basePrice: number = 150,
  volatility: number = 0.02
): StockDataPoint[] {
  const data: StockDataPoint[] = [];
  let currentPrice = basePrice;
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    // Random walk with trend
    const change = (Math.random() - 0.48) * volatility * currentPrice;
    currentPrice = Math.max(currentPrice + change, basePrice * 0.7);
    
    const volume = Math.floor(Math.random() * 50000000) + 10000000;

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      price: parseFloat(currentPrice.toFixed(2)),
      volume: volume
    });
  }

  return data;
}

/**
 * Generate candlestick data for demonstration
 */
export function generateCandlestickData(
  symbol: string,
  days: number = 20,
  basePrice: number = 150,
  volatility: number = 0.03
): CandlestickDataPoint[] {
  const data: CandlestickDataPoint[] = [];
  let currentClose = basePrice;
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    const open = currentClose;
    const change = (Math.random() - 0.48) * volatility * open;
    const close = Math.max(open + change, basePrice * 0.7);
    
    const high = Math.max(open, close) + Math.random() * volatility * open * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * open * 0.5;
    
    const volume = Math.floor(Math.random() * 50000000) + 10000000;

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: volume
    });

    currentClose = close;
  }

  return data;
}

/**
 * Generate volume data for demonstration
 */
export function generateVolumeData(
  symbol: string,
  days: number = 30
): VolumeDataPoint[] {
  const data: VolumeDataPoint[] = [];
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    const volume = Math.floor(Math.random() * 80000000) + 20000000;
    const change = (Math.random() - 0.5) * 5; // -2.5% to +2.5%

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      volume: volume,
      change: parseFloat(change.toFixed(2))
    });
  }

  return data;
}

/**
 * Generate comparison data for multiple stocks
 */
export function generateComparisonData(
  stocks: string[],
  days: number = 30
): any[] {
  const data: any[] = [];
  const today = new Date();
  const basePrices: { [key: string]: number } = {};
  
  // Initialize base prices
  stocks.forEach(symbol => {
    basePrices[symbol] = 100 + Math.random() * 100;
  });

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    const dataPoint: any = {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    };

    stocks.forEach(symbol => {
      const change = (Math.random() - 0.48) * 0.02 * basePrices[symbol];
      basePrices[symbol] = Math.max(basePrices[symbol] + change, 50);
      dataPoint[symbol] = parseFloat(basePrices[symbol].toFixed(2));
    });

    data.push(dataPoint);
  }

  return data;
}

/**
 * Stock colors for different symbols
 */
export const stockColors: { [key: string]: string } = {
  'AAPL': '#3b82f6',
  'GOOGL': '#ef4444',
  'MSFT': '#10b981',
  'AMZN': '#f59e0b',
  'TSLA': '#8b5cf6',
  'META': '#06b6d4',
  'NVDA': '#ec4899',
  'default': '#6366f1'
};

/**
 * Get stock color by symbol
 */
export function getStockColor(symbol: string): string {
  return stockColors[symbol] || stockColors.default;
}

/**
 * Generate RRG (Relative Rotation Graph) data for demonstration
 * RS-Ratio > 100 means outperforming benchmark
 * RS-Momentum > 100 means strength is increasing
 */
export function generateRRGData(stocks: string[]): any[] {
  return stocks.map(symbol => {
    // Generate values around 100 (benchmark)
    const rsRatio = 95 + Math.random() * 10; // 95-105
    const rsMomentum = 95 + Math.random() * 10; // 95-105
    
    return {
      symbol,
      rsRatio: parseFloat(rsRatio.toFixed(2)),
      rsMomentum: parseFloat(rsMomentum.toFixed(2)),
      color: getStockColor(symbol)
    };
  });
}

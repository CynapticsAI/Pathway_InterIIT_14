import {
  generateStockData,
  generateCandlestickData,
  generateVolumeData,
  generateComparisonData,
} from '@/lib/stockDataGenerator';

/**
 * Sample Chart Configurations
 * Pre-configured beautiful chart examples for the gallery
 */

export interface SampleChartConfig {
  type: 'line' | 'area' | 'candlestick' | 'volume' | 'comparison' | 'rrg';
  symbol?: string;
  symbols?: string[];
  title: string;
  description: string;
  isSample: boolean;
  data?: any;
  stocks?: string[];
  color?: string;
  showArea?: boolean;
  height?: number;
}

/**
 * Generate all sample charts
 */
export function generateSampleCharts(): SampleChartConfig[] {
  return [
    // 1. Line Chart - Apple
    {
      type: 'line',
      symbol: 'AAPL',
      title: 'Apple Inc. (AAPL)',
      description: '30-day price trend showing steady growth',
      isSample: true,
      data: generateStockData('AAPL', 30, 180, 0.015),
      color: '#3b82f6',
      showArea: false,
      height: 300,
    },

    // 2. Candlestick Chart - Tesla
    {
      type: 'candlestick',
      symbol: 'TSLA',
      title: 'Tesla Inc. (TSLA)',
      description: '20-day candlestick pattern with high volatility',
      isSample: true,
      data: generateCandlestickData('TSLA', 20, 250, 0.035),
      height: 350,
    },

    // 3. Area Chart - Microsoft
    {
      type: 'area',
      symbol: 'MSFT',
      title: 'Microsoft Corp. (MSFT)',
      description: '30-day area chart with volume visualization',
      isSample: true,
      data: generateStockData('MSFT', 30, 380, 0.018),
      color: '#10b981',
      showArea: true,
      height: 300,
    },

    // 4. Volume Chart - Google
    {
      type: 'volume',
      symbol: 'GOOGL',
      title: 'Alphabet Inc. (GOOGL)',
      description: '30-day volume analysis with price correlation',
      isSample: true,
      data: generateVolumeData('GOOGL', 30),
      height: 300,
    },

    // 5. Multi-Stock Comparison
    {
      type: 'comparison',
      symbols: ['AAPL', 'MSFT', 'GOOGL'],
      title: 'Tech Giants Comparison',
      description: 'Compare performance of AAPL, MSFT, and GOOGL',
      isSample: true,
      data: generateComparisonData(['AAPL', 'MSFT', 'GOOGL'], 30),
      stocks: ['AAPL', 'MSFT', 'GOOGL'],
      height: 350,
    },

    // 6. Another Line Chart - NVIDIA
    {
      type: 'line',
      symbol: 'NVDA',
      title: 'NVIDIA Corp. (NVDA)',
      description: '30-day trend showing strong momentum',
      isSample: true,
      data: generateStockData('NVDA', 30, 480, 0.025),
      color: '#8b5cf6',
      showArea: false,
      height: 300,
    },
  ];
}

/**
 * Get a specific sample chart by type
 */
export function getSampleChartByType(type: string): SampleChartConfig | undefined {
  const samples = generateSampleCharts();
  return samples.find(chart => chart.type === type);
}

/**
 * Get random sample charts (for variety)
 */
export function getRandomSampleCharts(count: number = 3): SampleChartConfig[] {
  const samples = generateSampleCharts();
  const shuffled = [...samples].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

// Quick reference guide for chart commands
export const CHART_COMMANDS = {
  line: [
    'Show me AAPL chart',
    'Show me TSLA chart',
    'Display GOOGL chart',
  ],
  area: [
    'Show me GOOGL chart',
    'Show me MSFT chart',
  ],
  candlestick: [
    'AAPL candlestick chart',
    'Show me GOOGL OHLC',
    'Candlestick for TSLA',
  ],
  volume: [
    'AAPL volume',
    'Show me TSLA volume',
    'Volume analysis for MSFT',
  ],
  comparison: [
    'Compare AAPL and GOOGL',
    'Compare AAPL, GOOGL, MSFT',
    'Compare TSLA and MSFT',
  ],
} as const;

// Chart type descriptions
// Use Lucide React icon names (without the Icon suffix)
export const CHART_TYPES = {
  line: {
    name: 'Line Chart',
    icon: 'TrendingUp',
    description: 'Shows price trends over time',
    useCase: 'Best for identifying overall trends and patterns',
  },
  area: {
    name: 'Area Chart',
    icon: 'AreaChart',
    description: 'Line chart with gradient fill',
    useCase: 'Best for visualizing price ranges and volatility',
  },
  candlestick: {
    name: 'Candlestick Chart',
    icon: 'CandlestickChart',
    description: 'Shows OHLC (Open, High, Low, Close) data',
    useCase: 'Best for technical analysis and identifying patterns',
  },
  volume: {
    name: 'Volume Chart',
    icon: 'BarChart3',
    description: 'Shows trading volume over time',
    useCase: 'Best for analyzing trading activity and liquidity',
  },
  comparison: {
    name: 'Comparison Chart',
    icon: 'GitCompare',
    description: 'Compare multiple stocks simultaneously',
    useCase: 'Best for relative performance analysis',
  },
} as const;

// Stock information
export const STOCK_INFO = {
  AAPL: { name: 'Apple Inc.', sector: 'Technology', color: '#3b82f6' },
  GOOGL: { name: 'Alphabet Inc.', sector: 'Technology', color: '#ef4444' },
  MSFT: { name: 'Microsoft Corp.', sector: 'Technology', color: '#10b981' },
  TSLA: { name: 'Tesla Inc.', sector: 'Automotive', color: '#8b5cf6' },
  AMZN: { name: 'Amazon.com Inc.', sector: 'E-commerce', color: '#f59e0b' },
  META: { name: 'Meta Platforms Inc.', sector: 'Technology', color: '#06b6d4' },
  NVDA: { name: 'NVIDIA Corp.', sector: 'Technology', color: '#ec4899' },
} as const;

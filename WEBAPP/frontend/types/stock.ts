// Stock data types for real-time WebSocket data

export interface StockTickData {
  s: string;      // symbol
  p: number;      // price
  t: number;      // timestamp (ms)
  v: number;      // volume
  diff: number;
  time: number;
}

export interface StockTick {
  type: 'stock_tick';
  data: StockTickData;
}

export interface SarimaxForecastData {
  timestamp: string;
  symbol: string;
  final_combined_signal: number;
  sarimax_signal: number;
  sentiment_score: number;
  sentiment_score_raw: number;
  last_seen_headline: string;
  time_since_last_news_s: number;
  decay_factor: number;
  message: string;
  current_price: number;
  forecast_price: number;
  diff: number;
  time: number;
}

export interface SarimaxForecast {
  type: 'sarimax_forecast';
  data: SarimaxForecastData;
}

export type StockMessage = StockTick | SarimaxForecast;

export interface StockChartDataPoint {
  timestamp: number;
  price: number;
  volume: number;
  forecast?: number;
  signal?: number;
}

export interface StockStats {
  symbol: string;
  currentPrice: number;
  priceChange: number;
  priceChangePercent: number;
  volume: number;
  lastUpdate: Date;
  forecastPrice?: number;
  signal?: number;
}

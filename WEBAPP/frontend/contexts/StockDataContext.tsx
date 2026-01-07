'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { StockTick, SarimaxForecast, StockMessage, StockChartDataPoint } from '@/types/stock';
import { NewsMessage, NewsItem } from '@/types/news';
import { VolumeSpikeMessage, VolumeVolatilityItem } from '@/types/volumeVolatility';

interface StockData {
  ticks: Map<string, StockChartDataPoint[]>;
  forecasts: Map<string, SarimaxForecast['data'][]>;
  news: NewsItem[];
  volumeSpikes: Map<string, VolumeVolatilityItem[]>;
}

interface StockDataContextType {
  selectedSymbol: string | null;
  selectSymbol: (symbol: string | null) => void;
  stockData: StockData;
  ticksData: Map<string, StockChartDataPoint[]>;
  forecastsData: Map<string, SarimaxForecast['data'][]>;
  newsData: NewsItem[];
  volumeSpikesData: Map<string, VolumeVolatilityItem[]>;
  latestNews: NewsItem | null;
  latestVolumeSpike: VolumeVolatilityItem | null;
  isConnected: boolean;
  availableSymbols: string[];
}

const StockDataContext = createContext<StockDataContextType | undefined>(undefined);

const AVAILABLE_SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL"];
const MAX_DATA_POINTS = 100;
const MAX_NEWS_ITEMS = 50;
const WS_STOCK_TICKS_URL = 'ws://localhost:8000/ws/stock-ticks/';
const WS_SARIMAX_URL = 'ws://localhost:8000/ws/sarimax-forecast/';
const WS_NEWS_URL = 'ws://localhost:8000/ws/news/';
const WS_VOLUME_SPIKES_URL = 'ws://localhost:8000/ws/volume-spikes/';
const API_BASE_URL = 'http://localhost:8000/api';

export function StockDataProvider({ children }: { children: React.ReactNode }) {
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [stockData, setStockData] = useState<StockData>({
    ticks: new Map(),
    forecasts: new Map(),
    news: [],
    volumeSpikes: new Map(),
  });
  const [latestNews, setLatestNews] = useState<NewsItem | null>(null);
  const [latestVolumeSpike, setLatestVolumeSpike] = useState<VolumeVolatilityItem | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [wsStockTicks, setWsStockTicks] = useState<WebSocket | null>(null);
  const [wsSarimax, setWsSarimax] = useState<WebSocket | null>(null);
  const [wsNews, setWsNews] = useState<WebSocket | null>(null);
  const [wsVolumeSpikes, setWsVolumeSpikes] = useState<WebSocket | null>(null);

  // Fetch historical data for all symbols on mount
  useEffect(() => {
    const fetchHistoricalData = async () => {
      console.log('📚 Fetching historical data...');
      
      for (const symbol of AVAILABLE_SYMBOLS) {
        try {
          // Fetch stock ticks
          const ticksResponse = await fetch(`${API_BASE_URL}/stock-ticks/?symbol=${symbol}&limit=100`);
          if (ticksResponse.ok) {
            const ticksData = await ticksResponse.json();
            
            setStockData(prev => {
              const newTicks = new Map(prev.ticks);
              const points: StockChartDataPoint[] = ticksData.map((tick: any) => ({
                timestamp: new Date(tick.timestamp).getTime(),
                price: parseFloat(tick.price),
                volume: parseFloat(tick.volume),
              }));
              newTicks.set(symbol, points);
              return { ...prev, ticks: newTicks };
            });
            
            console.log(`✅ Loaded ${ticksData.length} historical ticks for ${symbol}`);
          }
          
          // Fetch SARIMAX forecasts
          const forecastsResponse = await fetch(`${API_BASE_URL}/sarimax-forecasts/?symbol=${symbol}&limit=100`);
          if (forecastsResponse.ok) {
            const forecastsData = await forecastsResponse.json();
            
            setStockData(prev => {
              const newForecasts = new Map(prev.forecasts);
              const forecasts = forecastsData.map((f: any) => f.forecast_data);
              newForecasts.set(symbol, forecasts);
              return { ...prev, forecasts: newForecasts };
            });
            
            console.log(`✅ Loaded ${forecastsData.length} historical forecasts for ${symbol}`);
          }
        } catch (error) {
          console.error(`❌ Error fetching historical data for ${symbol}:`, error);
        }
      }
      
      // Fetch news data
      try {
        const newsResponse = await fetch(`${API_BASE_URL}/news/?limit=50`);
        if (newsResponse.ok) {
          const newsData = await fetch(`${API_BASE_URL}/news/?limit=50`).then(r => r.json());
          
          setStockData(prev => ({
            ...prev,
            news: newsData.map((item: any) => ({
              timestamp: item.timestamp,
              ticker: item.news_data.ticker,
              source: item.news_data.source,
              title: item.news_data.title,
              url: item.news_data.url,
              time: item.news_data.time,
            }))
          }));
          
          console.log(`✅ Loaded ${newsData.length} historical news items`);
        }
      } catch (error) {
        console.error('❌ Error fetching news data:', error);
      }
      
      // Fetch volume spikes for each symbol
      for (const symbol of AVAILABLE_SYMBOLS) {
        try {
          const spikesResponse = await fetch(`${API_BASE_URL}/volume-spikes/?symbol=${symbol}&limit=100`);
          if (spikesResponse.ok) {
            const spikesData = await spikesResponse.json();
            
            setStockData(prev => {
              const newSpikes = new Map(prev.volumeSpikes);
              const items: VolumeVolatilityItem[] = spikesData.map((spike: any) => ({
                timestamp: spike.timestamp,
                symbol: spike.spike_data.symbol,
                currentClose: spike.spike_data.current_close,
                currentVolume: spike.spike_data.current_volume,
                volumeZScore: spike.spike_data.volume_zscore,
                volatilityZScore: spike.spike_data.volatility_zscore,
                riskLevel: spike.spike_data.risk_level,
                time: spike.spike_data.time,
              }));
              newSpikes.set(symbol, items);
              return { ...prev, volumeSpikes: newSpikes };
            });
            
            console.log(`✅ Loaded ${spikesData.length} historical volume spikes for ${symbol}`);
          }
        } catch (error) {
          console.error(`❌ Error fetching volume spikes for ${symbol}:`, error);
        }
      }
    };
    
    fetchHistoricalData();
  }, []);

  // Connect to stock ticks WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_STOCK_TICKS_URL);

    ws.onopen = () => {
      console.log('✅ Connected to Stock Ticks WebSocket');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: StockTick = JSON.parse(event.data);
        if (message.type === 'stock_tick') {
          const { s: symbol, p: price, t: timestamp, v: volume } = message.data;
          
          setStockData(prev => {
            const newTicks = new Map(prev.ticks);
            const symbolTicks = newTicks.get(symbol) || [];
            
            // Add new data point
            const newPoint: StockChartDataPoint = {
              timestamp,
              price,
              volume,
            };
            
            // Keep only last MAX_DATA_POINTS
            const updatedTicks = [...symbolTicks, newPoint].slice(-MAX_DATA_POINTS);
            newTicks.set(symbol, updatedTicks);
            
            return { ...prev, ticks: newTicks };
          });
        }
      } catch (error) {
        console.error('Error parsing stock tick:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Stock Ticks WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('❌ Stock Ticks WebSocket disconnected');
      setIsConnected(false);
    };

    setWsStockTicks(ws);

    return () => {
      ws.close();
    };
  }, []);

  // Connect to SARIMAX WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_SARIMAX_URL);

    ws.onopen = () => {
      console.log('✅ Connected to SARIMAX WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const message: SarimaxForecast = JSON.parse(event.data);
        if (message.type === 'sarimax_forecast') {
          const { symbol } = message.data;
          
          setStockData(prev => {
            const newForecasts = new Map(prev.forecasts);
            const symbolForecasts = newForecasts.get(symbol) || [];
            
            // Add new forecast
            const updatedForecasts = [...symbolForecasts, message.data].slice(-MAX_DATA_POINTS);
            newForecasts.set(symbol, updatedForecasts);
            
            // Also update the corresponding tick with forecast data
            const newTicks = new Map(prev.ticks);
            const symbolTicks = newTicks.get(symbol) || [];
            
            if (symbolTicks.length > 0) {
              const lastTick = symbolTicks[symbolTicks.length - 1];
              const updatedLastTick = {
                ...lastTick,
                forecast: message.data.forecast_price,
                signal: message.data.final_combined_signal,
              };
              symbolTicks[symbolTicks.length - 1] = updatedLastTick;
              newTicks.set(symbol, symbolTicks);
            }
            
            return { ...prev, ticks: newTicks, forecasts: newForecasts };
          });
        }
      } catch (error) {
        console.error('Error parsing SARIMAX forecast:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ SARIMAX WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('❌ SARIMAX WebSocket disconnected');
    };

    setWsSarimax(ws);

    return () => {
      ws.close();
    };
  }, []);

  // Connect to News WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_NEWS_URL);

    ws.onopen = () => {
      console.log('✅ Connected to News WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const message: NewsMessage = JSON.parse(event.data);
        if (message.type === 'news') {
          const newsItem: NewsItem = {
            timestamp: message.data.dt_utc,
            ticker: message.data.ticker,
            source: message.data.source,
            title: message.data.title,
            url: message.data.url,
            time: message.data.time,
          };
          
          setLatestNews(newsItem);
          
          setStockData(prev => ({
            ...prev,
            news: [newsItem, ...prev.news].slice(0, MAX_NEWS_ITEMS),
          }));
        }
      } catch (error) {
        console.error('Error parsing news:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ News WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('❌ News WebSocket disconnected');
    };

    setWsNews(ws);

    return () => {
      ws.close();
    };
  }, []);

  // Connect to Volume Spikes WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_VOLUME_SPIKES_URL);

    ws.onopen = () => {
      console.log('✅ Connected to Volume Spikes WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const message: VolumeSpikeMessage = JSON.parse(event.data);
        if (message.type === 'volume_spike') {
          const volumeItem: VolumeVolatilityItem = {
            timestamp: message.data.timestamp,
            symbol: message.data.symbol,
            currentClose: message.data.current_close,
            currentVolume: message.data.current_volume,
            volumeZScore: message.data.volume_zscore,
            volatilityZScore: message.data.volatility_zscore,
            riskLevel: message.data.risk_level,
            time: message.data.time,
          };
          
          setLatestVolumeSpike(volumeItem);
          
          setStockData(prev => {
            const newSpikes = new Map(prev.volumeSpikes);
            const symbolSpikes = newSpikes.get(message.data.symbol) || [];
            const updatedSpikes = [volumeItem, ...symbolSpikes].slice(0, MAX_DATA_POINTS);
            newSpikes.set(message.data.symbol, updatedSpikes);
            return { ...prev, volumeSpikes: newSpikes };
          });
        }
      } catch (error) {
        console.error('Error parsing volume spike:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Volume Spikes WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('❌ Volume Spikes WebSocket disconnected');
    };

    setWsVolumeSpikes(ws);

    return () => {
      ws.close();
    };
  }, []);

  const selectSymbol = useCallback((symbol: string | null) => {
    setSelectedSymbol(symbol);
  }, []);

  const value: StockDataContextType = {
    selectedSymbol,
    selectSymbol,
    stockData,
    ticksData: stockData.ticks,
    forecastsData: stockData.forecasts,
    newsData: stockData.news,
    volumeSpikesData: stockData.volumeSpikes,
    latestNews,
    latestVolumeSpike,
    isConnected,
    availableSymbols: AVAILABLE_SYMBOLS,
  };

  return (
    <StockDataContext.Provider value={value}>
      {children}
    </StockDataContext.Provider>
  );
}

export function useStockData() {
  const context = useContext(StockDataContext);
  if (context === undefined) {
    throw new Error('useStockData must be used within a StockDataProvider');
  }
  return context;
}

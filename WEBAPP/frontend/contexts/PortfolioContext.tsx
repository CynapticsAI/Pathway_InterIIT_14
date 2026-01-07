'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { portfolioAPI } from '@/lib/api/portfolio';
import type {
  Portfolio,
  Stock,
  StockWithLiveData,
  PortfolioStats,
  StockFormData,
  BulkUploadData,
  BulkUploadResponse
} from '@/types/portfolio';
import { useAuthContext } from './AuthContext';
import { useStockData } from './StockDataContext';
import { showToast } from '@/utils/toast';

interface PortfolioContextType {
  portfolio: Portfolio | null;
  stocks: StockWithLiveData[];
  portfolioStats: PortfolioStats | null;
  isLoading: boolean;
  error: string | null;
  refreshPortfolio: () => Promise<void>;
  addStock: (data: StockFormData) => Promise<void>;
  updateStock: (symbol: string, data: StockFormData) => Promise<void>;
  deleteStock: (symbol: string) => Promise<void>;
  bulkUpload: (data: BulkUploadData) => Promise<BulkUploadResponse>;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

export function PortfolioProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthContext();
  const { ticksData } = useStockData();
  
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [stocks, setStocks] = useState<StockWithLiveData[]>([]);
  const [portfolioStats, setPortfolioStats] = useState<PortfolioStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch portfolio data
  const fetchPortfolio = useCallback(async () => {
    if (!isAuthenticated) {
      setPortfolio(null);
      setStocks([]);
      setPortfolioStats(null);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const data = await portfolioAPI.getPortfolio();
      setPortfolio(data);
    } catch (err: any) {
      console.error('Failed to fetch portfolio:', err);
      setError(err?.message || 'Failed to load portfolio');
      showToast.error('Failed to load portfolio');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Calculate live P&L for stocks
  const enrichStocksWithLiveData = useCallback((baseStocks: Stock[]): StockWithLiveData[] => {
    return baseStocks.map(stock => {
      const enrichedStock: StockWithLiveData = { ...stock };
      
      // Get latest tick data for this symbol
      const tickData = ticksData.get(stock.symbol);
      if (tickData && tickData.length > 0) {
        const latestTick = tickData[tickData.length - 1];
        const currentPrice = latestTick.price;
        
        // Calculate P&L
        const quantity = parseFloat(stock.quantity);
        const costBasis = parseFloat(stock.cost_basis);
        const totalCost = parseFloat(stock.total_cost);
        
        enrichedStock.current_price = currentPrice;
        enrichedStock.current_value = currentPrice * quantity;
        enrichedStock.pnl = (currentPrice - costBasis) * quantity;
        enrichedStock.pnl_percentage = ((currentPrice - costBasis) / costBasis) * 100;
        
        // Day change (compare to previous tick if available)
        if (tickData.length > 1) {
          const previousTick = tickData[tickData.length - 2];
          enrichedStock.day_change = currentPrice - previousTick.price;
          enrichedStock.day_change_percentage = 
            ((currentPrice - previousTick.price) / previousTick.price) * 100;
        }
      }
      
      return enrichedStock;
    });
  }, [ticksData]);

  // Calculate portfolio statistics
  const calculateStats = useCallback((enrichedStocks: StockWithLiveData[]): PortfolioStats => {
    const totalInvested = enrichedStocks.reduce(
      (sum, stock) => sum + parseFloat(stock.total_cost),
      0
    );

    const currentValue = enrichedStocks.reduce(
      (sum, stock) => sum + (stock.current_value || parseFloat(stock.total_cost)),
      0
    );

    const totalPnl = currentValue - totalInvested;
    const totalPnlPercentage = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

    const dayPnl = enrichedStocks.reduce(
      (sum, stock) => sum + (stock.day_change || 0) * parseFloat(stock.quantity),
      0
    );

    const dayPnlPercentage = currentValue > 0 ? (dayPnl / currentValue) * 100 : 0;

    // Find best and worst performers
    const stocksWithPnl = enrichedStocks.filter(s => s.pnl_percentage !== undefined);
    const bestPerformer = stocksWithPnl.length > 0
      ? [...stocksWithPnl].sort((a, b) => (b.pnl_percentage || 0) - (a.pnl_percentage || 0))[0]
      : undefined;

    const worstPerformer = stocksWithPnl.length > 0
      ? [...stocksWithPnl].sort((a, b) => (a.pnl_percentage || 0) - (b.pnl_percentage || 0))[0]
      : undefined;

    return {
      total_invested: totalInvested,
      current_value: currentValue,
      total_pnl: totalPnl,
      total_pnl_percentage: totalPnlPercentage,
      day_pnl: dayPnl,
      day_pnl_percentage: dayPnlPercentage,
      best_performer: bestPerformer,
      worst_performer: worstPerformer,
    };
  }, []);

  // Update stocks with live data whenever tick data changes
  useEffect(() => {
    if (portfolio && portfolio.stocks) {
      const enrichedStocks = enrichStocksWithLiveData(portfolio.stocks);
      setStocks(enrichedStocks);
      
      const stats = calculateStats(enrichedStocks);
      setPortfolioStats(stats);
    }
  }, [portfolio, ticksData, enrichStocksWithLiveData, calculateStats]);

  // Initial fetch
  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  // Add stock
  const addStockHandler = async (data: StockFormData) => {
    try {
      setIsLoading(true);
      await portfolioAPI.addStock(data);
      showToast.success(`${data.symbol} added to portfolio`);
      await fetchPortfolio();
    } catch (err: any) {
      console.error('Failed to add stock:', err);
      const message = err?.response?.data?.detail || 'Failed to add stock';
      showToast.error(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Update stock
  const updateStockHandler = async (symbol: string, data: StockFormData) => {
    try {
      setIsLoading(true);
      await portfolioAPI.updateStock(symbol, data);
      showToast.success(`${symbol} updated`);
      await fetchPortfolio();
    } catch (err: any) {
      console.error('Failed to update stock:', err);
      const message = err?.response?.data?.detail || 'Failed to update stock';
      showToast.error(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Delete stock
  const deleteStockHandler = async (symbol: string) => {
    try {
      setIsLoading(true);
      await portfolioAPI.deleteStock(symbol);
      showToast.success(`${symbol} removed from portfolio`);
      await fetchPortfolio();
    } catch (err: any) {
      console.error('Failed to delete stock:', err);
      const message = err?.response?.data?.detail || 'Failed to delete stock';
      showToast.error(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Bulk upload
  const bulkUploadHandler = async (data: BulkUploadData): Promise<BulkUploadResponse> => {
    try {
      setIsLoading(true);
      const result = await portfolioAPI.bulkUploadStocks(data);
      
      if (result.errors.length > 0) {
        showToast.error(`Uploaded with ${result.errors.length} errors`);
      } else {
        showToast.success(`Successfully uploaded ${result.total_processed} stocks`);
      }
      
      await fetchPortfolio();
      return result;
    } catch (err: any) {
      console.error('Failed to bulk upload:', err);
      const message = err?.response?.data?.detail || 'Failed to upload stocks';
      showToast.error(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const value: PortfolioContextType = {
    portfolio,
    stocks,
    portfolioStats,
    isLoading,
    error,
    refreshPortfolio: fetchPortfolio,
    addStock: addStockHandler,
    updateStock: updateStockHandler,
    deleteStock: deleteStockHandler,
    bulkUpload: bulkUploadHandler,
  };

  return (
    <PortfolioContext.Provider value={value}>
      {children}
    </PortfolioContext.Provider>
  );
}

export function usePortfolio() {
  const context = useContext(PortfolioContext);
  if (context === undefined) {
    throw new Error('usePortfolio must be used within a PortfolioProvider');
  }
  return context;
}

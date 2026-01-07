// Portfolio API Service

import apiClient from './client';
import type {
  Portfolio,
  Stock,
  StockFormData,
  BulkUploadData,
  BulkUploadResponse,
  PortfolioSummary
} from '@/types/portfolio';

const PORTFOLIO_BASE = '/api/portfolio';

// ============================================
// PORTFOLIO API
// ============================================

/**
 * Get user's portfolio with all stocks
 */
export const getPortfolio = async (): Promise<Portfolio> => {
  const response = await apiClient.get<Portfolio>(`${PORTFOLIO_BASE}/`);
  return response.data;
};

/**
 * List all stocks in portfolio
 */
export const listStocks = async (): Promise<Stock[]> => {
  const response = await apiClient.get<Stock[]>(`${PORTFOLIO_BASE}/stocks/`);
  return response.data;
};

/**
 * Get specific stock by symbol
 */
export const getStock = async (symbol: string): Promise<Stock> => {
  const response = await apiClient.get<Stock>(`${PORTFOLIO_BASE}/stocks/${symbol}/`);
  return response.data;
};

/**
 * Add new stock to portfolio (or update if exists)
 */
export const addStock = async (data: StockFormData): Promise<Stock> => {
  const response = await apiClient.post<Stock>(`${PORTFOLIO_BASE}/stocks/`, data);
  return response.data;
};

/**
 * Update existing stock
 */
export const updateStock = async (symbol: string, data: StockFormData): Promise<Stock> => {
  const response = await apiClient.put<Stock>(`${PORTFOLIO_BASE}/stocks/${symbol}/`, data);
  return response.data;
};

/**
 * Delete stock from portfolio
 */
export const deleteStock = async (symbol: string): Promise<void> => {
  await apiClient.delete(`${PORTFOLIO_BASE}/stocks/${symbol}/`);
};

/**
 * Bulk upload stocks (CSV import)
 */
export const bulkUploadStocks = async (data: BulkUploadData): Promise<BulkUploadResponse> => {
  const response = await apiClient.post<BulkUploadResponse>(
    `${PORTFOLIO_BASE}/stocks/bulk_upload/`,
    data
  );
  return response.data;
};

/**
 * Get portfolio summary with statistics
 */
export const getPortfolioSummary = async (): Promise<PortfolioSummary> => {
  const response = await apiClient.get<PortfolioSummary>(`${PORTFOLIO_BASE}/stocks/summary/`);
  return response.data;
};

// ============================================
// PORTFOLIO API EXPORTS
// ============================================

export const portfolioAPI = {
  getPortfolio,
  listStocks,
  getStock,
  addStock,
  updateStock,
  deleteStock,
  bulkUploadStocks,
  getPortfolioSummary,
};

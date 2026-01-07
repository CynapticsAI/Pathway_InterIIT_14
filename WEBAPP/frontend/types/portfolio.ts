// Portfolio types for user stock holdings

export interface Stock {
  id: number;
  symbol: string;
  quantity: string;
  cost_basis: string;
  total_cost: string;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: number;
  user_email: string;
  username: string;
  name: string;
  total_stocks: number;
  stocks: Stock[];
  created_at: string;
  updated_at: string;
}

export interface PortfolioSummary {
  portfolio_id: number;
  portfolio_name: string;
  total_stocks: number;
  total_invested: number;
  stocks: Stock[];
}

export interface StockFormData {
  symbol: string;
  quantity: number | string;
  cost_basis: number | string;
}

export interface BulkUploadData {
  stocks: Array<{
    symbol: string;
    quantity: number;
    cost_basis: number;
  }>;
}

export interface BulkUploadResponse {
  message: string;
  created: number;
  updated: number;
  errors: Array<{ symbol: string; error: string }>;
  total_processed: number;
}

export interface StockWithLiveData extends Stock {
  current_price?: number;
  pnl?: number;
  pnl_percentage?: number;
  current_value?: number;
  day_change?: number;
  day_change_percentage?: number;
}

export interface PortfolioStats {
  total_invested: number;
  current_value: number;
  total_pnl: number;
  total_pnl_percentage: number;
  day_pnl: number;
  day_pnl_percentage: number;
  best_performer?: StockWithLiveData;
  worst_performer?: StockWithLiveData;
}

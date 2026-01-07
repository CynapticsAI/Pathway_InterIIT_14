// API Service for Stock Sector Predictions

const PREDICTIONS_API_URL = process.env.NEXT_PUBLIC_PREDICTIONS_API_URL || 'http://127.0.0.1:8000';

export interface ModelMetrics {
  rmse: number;
  mae: number;
  dir_acc: number;
}

export interface SectorPrediction {
  sector: string;
  ticker: string;
  predicted_return_pct: number;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence_score: number;
  model_metrics: ModelMetrics;
  last_updated: string;
  features_used: string[];
}

export interface MarketSummary {
  average_return_pct: number;
  market_outlook: string;
  bullish_sectors: number;
  bearish_sectors: number;
  neutral_sectors: number;
  average_confidence: number;
  best_sector: string;
  worst_sector: string;
}

export interface PredictionsResponse {
  timestamp: string;
  total_sectors: number;
  predictions: SectorPrediction[];
}

export interface HealthCheckResponse {
  status: string;
  models_loaded: number;
  total_sectors: number;
  last_training: string;
}

/**
 * Fetch all sector predictions
 */
export async function fetchAllPredictions(): Promise<PredictionsResponse> {
  const response = await fetch(`${PREDICTIONS_API_URL}/predict`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch predictions: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch prediction for a specific sector
 */
export async function fetchSectorPrediction(sector: string): Promise<SectorPrediction> {
  const response = await fetch(`${PREDICTIONS_API_URL}/predict/${encodeURIComponent(sector)}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch prediction for ${sector}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch health check status
 */
export async function fetchHealthCheck(): Promise<HealthCheckResponse> {
  const response = await fetch(`${PREDICTIONS_API_URL}/health`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch health status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Refresh predictions cache
 */
export async function refreshPredictions(): Promise<string> {
  const response = await fetch(`${PREDICTIONS_API_URL}/refresh-predictions`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to refresh predictions: ${response.statusText}`);
  }

  return response.json();
}

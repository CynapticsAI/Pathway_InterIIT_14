'use client';

import { useState, useEffect, useMemo } from 'react';
import { fetchAllPredictions, PredictionsResponse, SectorPrediction } from '@/lib/apiService';

type SortField = 'sector' | 'predicted_return_pct' | 'sentiment' | 'rmse' | 'mae' | 'dir_acc';
type SortOrder = 'asc' | 'desc';

export function SectorPredictionsTable() {
  const [data, setData] = useState<PredictionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('predicted_return_pct');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = async () => {
    try {
      setError(null);
      const response = await fetchAllPredictions();
      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load predictions');
      console.error('Error fetching predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchData();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const toggleRowExpansion = (sector: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(sector)) {
      newExpanded.delete(sector);
    } else {
      newExpanded.add(sector);
    }
    setExpandedRows(newExpanded);
  };

  const sortedPredictions = useMemo(() => {
    if (!data?.predictions) return [];

    return [...data.predictions].sort((a, b) => {
      let aVal: any, bVal: any;

      switch (sortField) {
        case 'sector':
          aVal = a.sector;
          bVal = b.sector;
          break;
        case 'predicted_return_pct':
          aVal = a.predicted_return_pct;
          bVal = b.predicted_return_pct;
          break;
        case 'sentiment':
          aVal = a.sentiment;
          bVal = b.sentiment;
          break;
        case 'rmse':
          aVal = a.model_metrics.rmse;
          bVal = b.model_metrics.rmse;
          break;
        case 'mae':
          aVal = a.model_metrics.mae;
          bVal = b.model_metrics.mae;
          break;
        case 'dir_acc':
          aVal = a.model_metrics.dir_acc;
          bVal = b.model_metrics.dir_acc;
          break;
        default:
          return 0;
      }

      if (typeof aVal === 'string') {
        return sortOrder === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });
  }, [data?.predictions, sortField, sortOrder]);

  // Compute market summary from predictions
  const marketSummary = useMemo(() => {
    if (!data?.predictions || data.predictions.length === 0) {
      return {
        average_return_pct: 0,
        market_outlook: 'UNKNOWN',
        bullish_sectors: 0,
        bearish_sectors: 0,
        neutral_sectors: 0,
        best_sector: 'N/A',
        worst_sector: 'N/A'
      };
    }

    const predictions = data.predictions;
    const bullish = predictions.filter(p => p.sentiment === 'BULLISH').length;
    const bearish = predictions.filter(p => p.sentiment === 'BEARISH').length;
    const neutral = predictions.filter(p => p.sentiment === 'NEUTRAL').length;
    
    const avgReturn = predictions.reduce((sum, p) => sum + p.predicted_return_pct, 0) / predictions.length;
    
    const bestSector = predictions.reduce((best, p) => 
      p.predicted_return_pct > best.predicted_return_pct ? p : best
    );
    
    const worstSector = predictions.reduce((worst, p) => 
      p.predicted_return_pct < worst.predicted_return_pct ? p : worst
    );
    
    let outlook = 'NEUTRAL';
    if (avgReturn > 0.5) outlook = 'BULLISH';
    else if (avgReturn < -0.5) outlook = 'BEARISH';

    return {
      average_return_pct: avgReturn,
      market_outlook: outlook,
      bullish_sectors: bullish,
      bearish_sectors: bearish,
      neutral_sectors: neutral,
      best_sector: bestSector.sector,
      worst_sector: worstSector.sector
    };
  }, [data?.predictions]);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'BEARISH':
        return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'NEUTRAL':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return '📈';
      case 'BEARISH':
        return '📉';
      case 'NEUTRAL':
        return '➡️';
      default:
        return '❓';
    }
  };

  const getReturnColor = (returnPct: number) => {
    if (returnPct > 1) return 'text-green-400 font-semibold';
    if (returnPct < -1) return 'text-red-400 font-semibold';
    return 'text-yellow-400';
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="text-[var(--color-foreground)] opacity-40 ml-1">↕️</span>;
    }
    return <span className="text-blue-400 ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-[var(--color-foreground)] opacity-60">Loading sector predictions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <h3 className="text-lg font-semibold text-red-400 mb-2">Error Loading Data</h3>
        <p className="text-[var(--color-foreground)] opacity-60 mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 rounded-lg transition-colors text-red-400"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Market Summary Card */}
      <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-[var(--color-foreground)] flex items-center gap-2">
            🌐 Market Overview
          </h3>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                autoRefresh 
                  ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
                  : 'bg-gray-500/20 text-[var(--color-foreground)] opacity-60 border border-gray-500/50'
              }`}
            >
              {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
            </button>
            <button
              onClick={fetchData}
              className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded-lg text-xs font-medium transition-colors text-blue-400"
            >
              🔄 Refresh Now
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/10 dark:bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10">
            <p className="text-xs text-[var(--color-foreground)] opacity-60 mb-1">Market Outlook</p>
            <p className="text-lg font-bold text-[var(--color-foreground)]">{marketSummary.market_outlook}</p>
          </div>
          <div className="bg-white/10 dark:bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10">
            <p className="text-xs text-[var(--color-foreground)] opacity-60 mb-1">Avg Return</p>
            <p className={`text-lg font-bold ${getReturnColor(marketSummary.average_return_pct)}`}>
              {marketSummary.average_return_pct.toFixed(2)}%
            </p>
          </div>
          <div className="bg-white/10 dark:bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10">
            <p className="text-xs text-[var(--color-foreground)] opacity-60 mb-1">Best Sector</p>
            <p className="text-lg font-bold text-green-400">{marketSummary.best_sector}</p>
          </div>
          <div className="bg-white/10 dark:bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-white/10">
            <p className="text-xs text-[var(--color-foreground)] opacity-60 mb-1">Worst Sector</p>
            <p className="text-lg font-bold text-red-400">{marketSummary.worst_sector}</p>
          </div>
        </div>

        <div className="flex items-center gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-green-400">📈 {marketSummary.bullish_sectors} Bullish</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-yellow-400">➡️ {marketSummary.neutral_sectors} Neutral</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-red-400">📉 {marketSummary.bearish_sectors} Bearish</span>
          </div>
          <div className="ml-auto text-xs text-[var(--color-foreground)] opacity-50">
            Updated: {new Date(data.timestamp).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Predictions Table */}
      <div className="bg-[var(--color-ai-message)] border border-[var(--color-border)] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-100 dark:bg-black/30 border-b border-[var(--color-border)]">
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('sector')}
                    className="flex items-center hover:opacity-100 transition-opacity"
                  >
                    Sector
                    <SortIcon field="sector" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  Ticker
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('predicted_return_pct')}
                    className="flex items-center hover:opacity-100 transition-opacity"
                  >
                    Predicted Return
                    <SortIcon field="predicted_return_pct" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  <button 
                    onClick={() => handleSort('sentiment')}
                    className="flex items-center hover:opacity-100 transition-opacity"
                  >
                    Sentiment
                    <SortIcon field="sentiment" />
                  </button>
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  Model Metrics
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--color-foreground)] opacity-70 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {sortedPredictions.map((prediction) => (
                <>
                  <tr 
                    key={prediction.sector}
                    className="hover:bg-gray-50 dark:hover:bg-black/20 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-[var(--color-foreground)]">{prediction.sector}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-blue-400">{prediction.ticker}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-lg font-bold ${getReturnColor(prediction.predicted_return_pct)}`}>
                        {prediction.predicted_return_pct > 0 ? '+' : ''}{prediction.predicted_return_pct.toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getSentimentColor(prediction.sentiment)}`}>
                        {getSentimentIcon(prediction.sentiment)} {prediction.sentiment}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-xs space-y-1">
                        <div className="flex justify-between gap-4">
                          <span className="text-[var(--color-foreground)] opacity-60">RMSE:</span>
                          <span className="text-[var(--color-foreground)] font-mono">{prediction.model_metrics.rmse.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-[var(--color-foreground)] opacity-60">MAE:</span>
                          <span className="text-[var(--color-foreground)] font-mono">{prediction.model_metrics.mae.toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-[var(--color-foreground)] opacity-60">Dir Acc:</span>
                          <span className="text-[var(--color-foreground)] font-mono">{prediction.model_metrics.dir_acc.toFixed(2)}%</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => toggleRowExpansion(prediction.sector)}
                        className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                      >
                        {expandedRows.has(prediction.sector) ? '▼ Hide' : '▶ Show'}
                      </button>
                    </td>
                  </tr>
                  {expandedRows.has(prediction.sector) && (
                    <tr key={`${prediction.sector}-details`} className="bg-gray-50 dark:bg-black/30">
                      <td colSpan={6} className="px-6 py-4">
                        <div className="space-y-3">
                          <div>
                            <h4 className="text-sm font-semibold text-[var(--color-foreground)] opacity-70 mb-2">Features Used:</h4>
                            <div className="flex flex-wrap gap-2">
                              {prediction.features_used.map((feature) => (
                                <span 
                                  key={feature}
                                  className="px-3 py-1 bg-blue-500/10 border border-blue-500/30 rounded-full text-xs font-mono text-blue-300"
                                >
                                  {feature}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-[var(--color-foreground)] opacity-60">
                            <span>Last Updated: {new Date(prediction.last_updated).toLocaleString()}</span>
                            <span>•</span>
                            <span>Features: {prediction.features_used.length}</span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-xs text-[var(--color-foreground)] opacity-50 text-center">
        Showing {data.total_sectors} sectors • Data updates every 5 minutes
      </div>
    </div>
  );
}

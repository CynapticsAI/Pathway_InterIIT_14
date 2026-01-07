'use client';

import { useState, useEffect, useMemo } from 'react';
import { StockLineChart } from './StockLineChart';
import { CandlestickChart } from './CandlestickChart';
import { VolumeChart } from './VolumeChart';
import { MultiStockComparison } from './MultiStockComparison';
import { SectorPredictionsTable } from './SectorPredictionsTable';
import { RRGChart } from './RRGChart';
import { ChartCard } from './ChartCard';
import { MessageType } from '../chat/Message';
import { generateSampleCharts, SampleChartConfig } from '@/utils/sampleCharts';
import dynamic from 'next/dynamic';
import { StockPanel } from '../stock/StockPanel';
import { NewsPanel } from '../stock/NewsPanel';
import { VolumeVolatilityPanel } from '../stock/VolumeVolatilityPanel';
import { ChartBar, Newspaper, TargetIcon, ChartLine, SearchIcon, BotIcon, ChartAreaIcon } from 'lucide-react';

// Dynamically import AgentFlowchart to avoid SSR issues with ReactFlow
const AgentFlowchart = dynamic(
  () => import('./AgentFlowchart/index').then((mod) => ({ default: mod.AgentFlowchart })),
  { ssr: false }
);

type TabType = 'predictions' | 'charts' | 'agentFlow' | 'stockSearch' | 'news' | 'volumeSpikes';

interface ChartsPanelProps {
  messages: MessageType[];
}

export function ChartsPanel({ messages }: ChartsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('predictions');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeCharts, setActiveCharts] = useState<any[]>([]);
  const [showSampleGallery, setShowSampleGallery] = useState(false);
  const [sampleCharts, setSampleCharts] = useState<SampleChartConfig[]>([]);

  // Load sample charts on mount
  useEffect(() => {
    setSampleCharts(generateSampleCharts());
  }, []);

  // Extract chart data from messages
  useEffect(() => {
    const charts = messages
      .filter(msg => msg.chartData && msg.sender === 'ai')
      .map(msg => msg.chartData)
      .filter(Boolean);
    
    setActiveCharts(charts);
  }, [messages]);

  // Determine which charts to display
  const displayCharts = useMemo(() => {
    if (showSampleGallery) return sampleCharts;
    if (activeCharts.length === 0) return sampleCharts;
    return activeCharts;
  }, [showSampleGallery, activeCharts, sampleCharts]);

  const isShowingSamples = activeCharts.length === 0 || showSampleGallery;

  const renderChart = (chartData: any, index: number) => {
    const key = `chart-${index}`;
    const isSample = chartData.isSample || false;
    
    let chartComponent = null;

    switch (chartData.type) {
      case 'line':
        chartComponent = (
          <StockLineChart
            data={chartData.data}
            symbol={chartData.symbol}
            color={chartData.color || "#3b82f6"}
            showArea={chartData.showArea || false}
            height={chartData.height || 300}
          />
        );
        break;
      
      case 'area':
        chartComponent = (
          <StockLineChart
            data={chartData.data}
            symbol={chartData.symbol}
            color={chartData.color || "#10b981"}
            showArea={chartData.showArea !== false}
            height={chartData.height || 300}
          />
        );
        break;
      
      case 'candlestick':
        chartComponent = (
          <CandlestickChart
            data={chartData.data}
            symbol={chartData.symbol}
            height={chartData.height || 350}
          />
        );
        break;
      
      case 'volume':
        chartComponent = (
          <VolumeChart
            data={chartData.data}
            symbol={chartData.symbol}
            height={chartData.height || 300}
          />
        );
        break;
      
      case 'comparison':
        chartComponent = (
          <MultiStockComparison
            data={chartData.data}
            stocks={chartData.stocks}
            height={chartData.height || 350}
          />
        );
        break;
      
      case 'rrg':
        chartComponent = (
          <RRGChart
            data={chartData.data}
            title={chartData.title || 'Relative Rotation Graph'}
            benchmark={chartData.benchmark || 'S&P 500'}
            height={chartData.height || 500}
          />
        );
        break;
      
      default:
        return null;
    }

    // Wrap in ChartCard if it's a sample
    if (isSample && chartComponent) {
      return (
        <ChartCard
          key={key}
          title={chartData.title || chartData.symbol || 'Chart'}
          description={chartData.description}
          isSample={true}
        >
          {chartComponent}
        </ChartCard>
      );
    }

    return chartComponent ? <div key={key}>{chartComponent}</div> : null;
  };

  const panelContent = (
    <div className={`h-full flex flex-col bg-gradient-to-br from-[var(--color-background)] to-[var(--color-ai-message)]/10 min-h-0 ${isFullscreen ? 'rounded-none' : ''}`}>
      {/* Header with Tabs */}
      <div className="flex-shrink-0 bg-[var(--color-background)] border-b border-[var(--color-border)]">
        <div className="px-6 pt-4 pb-2">
          <h2 className="text-xl font-bold text-[var(--color-foreground)]">
            <ChartAreaIcon className="inline-block mr-1" /> Charts & Analytics
          </h2>
        </div>
        
        {/* Tabs - Horizontally Scrollable */}
        <div className="relative px-6">
          <div className="flex gap-1 overflow-x-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent pb-2">
            <button
              onClick={() => setActiveTab('agentFlow')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'agentFlow'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
               <BotIcon className="inline-block mr-1" /> Agent Flow
            </button>
            <button
              onClick={() => setActiveTab('predictions')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'predictions'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <TargetIcon className="inline-block mr-1" /> Sector Predictions
            </button>
            <button
              onClick={() => setActiveTab('charts')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'charts'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <ChartLine className="inline-block mr-1" /> Stock Charts {activeCharts.length > 0 && `(${activeCharts.length})`}
            </button>
            <button
              onClick={() => setActiveTab('stockSearch')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'stockSearch'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <SearchIcon className="inline-block mr-1" /> Live Stocks
            </button>
            <button
              onClick={() => setActiveTab('news')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'news'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Newspaper className="inline-block mr-1" /> News Feed
            </button>
            <button
              onClick={() => setActiveTab('volumeSpikes')}
              className={`px-4 py-2 rounded-t-lg font-medium transition-all duration-200 whitespace-nowrap ${
                activeTab === 'volumeSpikes'
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <ChartBar className="inline-block mr-1" /> Volume Spikes
            </button>
          </div>
        </div>
      </div>

      {/* Content with Fullscreen Toggle */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-6 min-h-0 relative">
        {/* Fullscreen Toggle Button */}
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="absolute top-4 right-4 z-10 p-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-border)] transition-colors"
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
        >
          {isFullscreen ? (
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>

        {activeTab === 'predictions' ? (
          <div className="max-w-7xl mx-auto">
            <SectorPredictionsTable />
          </div>
        ) : activeTab === 'stockSearch' ? (
          <div className="max-w-7xl mx-auto">
            <StockPanel />
          </div>
        ) : activeTab === 'news' ? (
          <div className="max-w-7xl mx-auto">
            <NewsPanel />
          </div>
        ) : activeTab === 'volumeSpikes' ? (
          <div className="max-w-7xl mx-auto">
            <VolumeVolatilityPanel />
          </div>
        ) : activeTab === 'agentFlow' ? (
          <div className="h-full">
            <AgentFlowchart />
          </div>
        ) : (
          <>
            {/* Header with Toggle (only show if AI charts exist) */}
            {activeCharts.length > 0 && (
              <div className="max-w-6xl mx-auto mb-6 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-[var(--color-foreground)]">
                    {showSampleGallery ? '📊 Sample Charts Gallery' : '🤖 AI Generated Charts'}
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">
                    {showSampleGallery 
                      ? 'Explore different chart types and visualizations'
                      : `${activeCharts.length} chart${activeCharts.length > 1 ? 's' : ''} from your conversation`
                    }
                  </p>
                </div>
                <button
                  onClick={() => setShowSampleGallery(!showSampleGallery)}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all duration-200 flex items-center gap-2 shadow-lg"
                >
                  {showSampleGallery ? (
                    <>
                      <span>🤖</span> Show AI Charts
                    </>
                  ) : (
                    <>
                      <span>📊</span> View Samples
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Sample Gallery Header (only when showing samples and no AI charts) */}
            {activeCharts.length === 0 && (
              <div className="max-w-6xl mx-auto mb-6">
                <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-lg p-6">
                  <div className="flex items-start gap-4">
                    <div className="text-4xl">💡</div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-white mb-2">
                        Sample Charts Gallery
                      </h3>
                      <p className="text-gray-300 mb-4">
                        Explore different types of stock charts and visualizations. Ask the AI to generate real-time charts for any stock!
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-medium">
                          Line Charts
                        </span>
                        <span className="px-3 py-1 bg-green-500/20 text-green-300 rounded-full text-xs font-medium">
                          Candlesticks
                        </span>
                        <span className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-xs font-medium">
                          Volume Analysis
                        </span>
                        <span className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full text-xs font-medium">
                          Comparisons
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Charts Display */}
            <div className="space-y-6 max-w-6xl mx-auto">
              {displayCharts.map((chartData, index) => (
                <div 
                  key={index}
                  className="animate-fadeIn"
                  style={{
                    animation: 'fadeIn 0.3s ease-in-out'
                  }}
                >
                  {renderChart(chartData, index)}
                </div>
              ))}
            </div>

            {/* Try AI Prompt (only show with samples and no AI charts) */}
            {activeCharts.length === 0 && (
              <div className="max-w-6xl mx-auto mt-8">
                <div className="bg-[var(--color-ai-message)] rounded-lg p-6 border border-[var(--color-border)]">
                  <h4 className="text-lg font-semibold text-[var(--color-foreground)] mb-3 flex items-center gap-2">
                    <span>💬</span> Ask AI for Real-Time Charts
                  </h4>
                  <p className="text-gray-300 mb-4">
                    Try these example prompts to generate live stock charts:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div className="bg-gray-700/30 rounded px-3 py-2 text-sm text-gray-200">
                      • "Show me AAPL chart for last 30 days"
                    </div>
                    <div className="bg-gray-700/30 rounded px-3 py-2 text-sm text-gray-200">
                      • "TSLA candlestick chart"
                    </div>
                    <div className="bg-gray-700/30 rounded px-3 py-2 text-sm text-gray-200">
                      • "Compare AAPL, GOOGL, and MSFT"
                    </div>
                    <div className="bg-gray-700/30 rounded px-3 py-2 text-sm text-gray-200">
                      • "Show MSFT volume analysis"
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );

  // Handle ESC key for fullscreen exit
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isFullscreen]);

  return (
    <>
      {isFullscreen ? (
        <div className="fixed inset-0 z-50 bg-[var(--color-background)]">
          {panelContent}
        </div>
      ) : (
        panelContent
      )}
    </>
  );
}

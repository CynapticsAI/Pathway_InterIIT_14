// Example usage of Stock Market Chatbot UI Components
// This file demonstrates how to use the custom components in your app

import { StockPrice, MarketBadge } from '@/components/ui';
import { RRGChart } from '@/components/charts';
import { generateRRGData } from '@/lib/stockDataGenerator';

export function StockDataExamples() {
  // Example RRG data for tech stocks
  const techStocksRRG = generateRRGData(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']);
  
  return (
    <div className="p-6 space-y-6">
      {/* Stock Price Display Examples */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Stock Prices</h3>
        <div className="space-y-4">
          <StockPrice 
            symbol="AAPL"
            price={150.25}
            change={3.75}
            changePercent={2.56}
            size="sm"
          />
          
          <StockPrice 
            symbol="TSLA"
            price={242.84}
            change={-5.20}
            changePercent={-2.09}
            size="md"
          />
          
          <StockPrice 
            symbol="NVDA"
            price={495.50}
            change={12.30}
            changePercent={2.55}
            size="lg"
          />
        </div>
      </section>

      {/* Market Badge Examples */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Market Indicators</h3>
        <div className="flex flex-wrap gap-2">
          <MarketBadge status="gain">Bullish 📈</MarketBadge>
          <MarketBadge status="loss">Bearish 📉</MarketBadge>
          <MarketBadge status="warning">High Volatility ⚠️</MarketBadge>
          <MarketBadge status="neutral">Market Closed</MarketBadge>
        </div>
      </section>

      {/* RRG Chart Example */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Relative Rotation Graph (RRG)</h3>
        <div className="max-w-5xl">
          <RRGChart 
            data={techStocksRRG}
            title="Tech Stocks Relative Rotation"
            benchmark="S&P 500"
            height={500}
          />
        </div>
        <div className="mt-4 p-4 bg-[var(--color-ai-message)] rounded-lg border border-[var(--color-border)]">
          <h4 className="text-sm font-semibold mb-2">What is RRG?</h4>
          <p className="text-sm text-gray-400">
            RRG (Relative Rotation Graph) visualizes the relative strength and momentum of stocks compared to a benchmark.
            Stocks in the <span className="text-green-400 font-semibold">Leading</span> quadrant are outperforming with increasing strength,
            while those in the <span className="text-red-400 font-semibold">Lagging</span> quadrant are underperforming with decreasing strength.
          </p>
        </div>
      </section>

      {/* Example Message with Stock Data */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Formatted Message Example</h3>
        <div className="p-4 bg-[var(--color-ai-message)] rounded-2xl">
          <p className="mb-3">Here's the latest market update:</p>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Apple Inc.</span>
              <span className="stock-price text-lg">$150.25</span>
              <span className="percentage text-gain">+2.56%</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span>Tesla Inc.</span>
              <span className="stock-price text-lg">$242.84</span>
              <span className="percentage text-loss">-2.09%</span>
            </div>
          </div>
          
          <div className="mt-3 flex gap-2">
            <MarketBadge status="gain">Market Open</MarketBadge>
            <MarketBadge status="neutral">NYSE</MarketBadge>
          </div>
        </div>
      </section>
    </div>
  );
}

// How to integrate this into AI responses in ChatContainer.tsx:

/* 
const getAIResponseWithStockData = (userMessage: string): string => {
  const lower = userMessage.toLowerCase();
  
  if (lower.includes('aapl') || lower.includes('apple')) {
    return `📊 Apple Inc. (AAPL)

Current Price: $150.25
Change: +$3.75 (+2.56%)
Market Cap: $2.4T

The stock is showing strong bullish momentum with:
• Volume above average
• Breaking resistance at $148
• Positive market sentiment

Would you like a detailed technical analysis?`;
  }
  
  // Add more stock-specific responses...
};
*/

'use client';

import { RRGChart } from '@/components/charts';
import { generateRRGData } from '@/lib/stockDataGenerator';

export default function RRGExample() {
  // Example 1: Tech Stocks
  const techStocks = generateRRGData(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']);
  
  // Example 2: Custom RRG data with specific positions
  const customRRGData = [
    { symbol: 'AAPL', rsRatio: 102.5, rsMomentum: 101.8, color: '#3b82f6' },  // Leading
    { symbol: 'GOOGL', rsRatio: 98.2, rsMomentum: 101.5, color: '#ef4444' },  // Improving
    { symbol: 'MSFT', rsRatio: 103.1, rsMomentum: 98.7, color: '#10b981' },   // Weakening
    { symbol: 'AMZN', rsRatio: 97.5, rsMomentum: 98.2, color: '#f59e0b' },    // Lagging
    { symbol: 'TSLA', rsRatio: 101.8, rsMomentum: 103.2, color: '#8b5cf6' },  // Leading
    { symbol: 'META', rsRatio: 96.8, rsMomentum: 102.1, color: '#06b6d4' },   // Improving
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[var(--color-background)] to-[var(--color-ai-message)]/10 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-[var(--color-foreground)] mb-4">
            📊 Relative Rotation Graph (RRG) Examples
          </h1>
          <p className="text-lg text-gray-400 max-w-3xl mx-auto">
            RRG charts help visualize the relative strength and momentum of multiple stocks compared to a benchmark,
            showing which stocks are leading, improving, weakening, or lagging.
          </p>
        </div>

        {/* Example 1: Random Tech Stocks */}
        <section>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-2">
              Example 1: Tech Stocks vs S&P 500
            </h2>
            <p className="text-gray-400">
              This example shows randomly generated positions for major tech stocks.
            </p>
          </div>
          <RRGChart 
            data={techStocks}
            title="Tech Stocks Relative Rotation"
            benchmark="S&P 500"
            height={500}
          />
        </section>

        {/* Example 2: Custom Positions */}
        <section>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-2">
              Example 2: Custom Positioned Stocks
            </h2>
            <p className="text-gray-400">
              This example demonstrates stocks in different quadrants with specific relative strength values.
            </p>
          </div>
          <RRGChart 
            data={customRRGData}
            title="Market Leaders Analysis"
            benchmark="NASDAQ-100"
            height={500}
          />
        </section>

        {/* Understanding RRG */}
        <section className="bg-[var(--color-ai-message)] rounded-xl p-6 border border-[var(--color-border)]">
          <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-4">
            📚 Understanding RRG Charts
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-3">
                The Four Quadrants
              </h3>
              <div className="space-y-3">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                  <h4 className="font-semibold text-green-400 mb-1">🚀 Leading (Top Right)</h4>
                  <p className="text-sm text-gray-400">
                    High RS-Ratio (&gt;100) + High RS-Momentum (&gt;100)<br/>
                    <strong>Interpretation:</strong> Outperforming and strengthening
                  </p>
                </div>
                
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                  <h4 className="font-semibold text-blue-400 mb-1">📈 Improving (Top Left)</h4>
                  <p className="text-sm text-gray-400">
                    Low RS-Ratio (&lt;100) + High RS-Momentum (&gt;100)<br/>
                    <strong>Interpretation:</strong> Underperforming but strengthening
                  </p>
                </div>
                
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                  <h4 className="font-semibold text-red-400 mb-1">📉 Lagging (Bottom Left)</h4>
                  <p className="text-sm text-gray-400">
                    Low RS-Ratio (&lt;100) + Low RS-Momentum (&lt;100)<br/>
                    <strong>Interpretation:</strong> Underperforming and weakening
                  </p>
                </div>
                
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                  <h4 className="font-semibold text-yellow-400 mb-1">⚠️ Weakening (Bottom Right)</h4>
                  <p className="text-sm text-gray-400">
                    High RS-Ratio (&gt;100) + Low RS-Momentum (&lt;100)<br/>
                    <strong>Interpretation:</strong> Outperforming but weakening
                  </p>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-[var(--color-foreground)] mb-3">
                How to Use RRG
              </h3>
              <div className="space-y-3 text-sm text-gray-400">
                <div className="bg-[var(--color-background)] rounded-lg p-3">
                  <h4 className="font-semibold text-[var(--color-foreground)] mb-1">1. Identify Trends</h4>
                  <p>Watch the rotation of stocks through the quadrants to spot emerging trends.</p>
                </div>
                
                <div className="bg-[var(--color-background)] rounded-lg p-3">
                  <h4 className="font-semibold text-[var(--color-foreground)] mb-1">2. Sector Rotation</h4>
                  <p>Use RRG to identify which sectors are rotating into leadership positions.</p>
                </div>
                
                <div className="bg-[var(--color-background)] rounded-lg p-3">
                  <h4 className="font-semibold text-[var(--color-foreground)] mb-1">3. Portfolio Rebalancing</h4>
                  <p>Stocks moving from Improving to Leading may warrant increased allocation.</p>
                </div>
                
                <div className="bg-[var(--color-background)] rounded-lg p-3">
                  <h4 className="font-semibold text-[var(--color-foreground)] mb-1">4. Risk Management</h4>
                  <p>Stocks entering the Weakening quadrant may signal it's time to reduce exposure.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Code Example */}
        <section className="bg-[var(--color-ai-message)] rounded-xl p-6 border border-[var(--color-border)]">
          <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-4">
            💻 Code Example
          </h2>
          <div className="bg-[var(--color-background)] rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-300">
{`import { RRGChart } from '@/components/charts';
import { generateRRGData } from '@/lib/stockDataGenerator';

// Generate RRG data for stocks
const rrgData = generateRRGData(['AAPL', 'GOOGL', 'MSFT', 'AMZN']);

// Or create custom data
const customData = [
  { symbol: 'AAPL', rsRatio: 102.5, rsMomentum: 101.8 },
  { symbol: 'GOOGL', rsRatio: 98.2, rsMomentum: 101.5 },
];

// Render the chart
<RRGChart 
  data={rrgData}
  title="Tech Stocks RRG"
  benchmark="S&P 500"
  height={500}
/>`}
            </pre>
          </div>
        </section>

        {/* Integration with Chatbot */}
        <section className="bg-[var(--color-ai-message)] rounded-xl p-6 border border-[var(--color-border)]">
          <h2 className="text-2xl font-bold text-[var(--color-foreground)] mb-4">
            🤖 Chatbot Integration
          </h2>
          <p className="text-gray-400 mb-4">
            To display RRG charts in your chatbot, include the following in your message's chartData:
          </p>
          <div className="bg-[var(--color-background)] rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-300">
{`const message = {
  text: "Here's the RRG analysis for tech stocks...",
  chartData: {
    type: 'rrg',
    data: generateRRGData(['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']),
    title: 'Tech Stocks Relative Rotation',
    benchmark: 'S&P 500',
    height: 500
  }
};`}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
}

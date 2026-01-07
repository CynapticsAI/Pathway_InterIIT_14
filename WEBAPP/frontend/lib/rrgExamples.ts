// RRG Chart Data Examples
// Copy-paste these examples to test the RRG chart

export const rrgExamples = {
  // Example 1: Tech Giants
  techGiants: [
    { symbol: 'AAPL', rsRatio: 102.5, rsMomentum: 101.8, color: '#3b82f6' },  // Leading
    { symbol: 'GOOGL', rsRatio: 98.2, rsMomentum: 101.5, color: '#ef4444' },  // Improving
    { symbol: 'MSFT', rsRatio: 103.1, rsMomentum: 98.7, color: '#10b981' },   // Weakening
    { symbol: 'AMZN', rsRatio: 97.5, rsMomentum: 98.2, color: '#f59e0b' },    // Lagging
    { symbol: 'TSLA', rsRatio: 101.8, rsMomentum: 103.2, color: '#8b5cf6' },  // Leading
    { symbol: 'META', rsRatio: 96.8, rsMomentum: 102.1, color: '#06b6d4' },   // Improving
    { symbol: 'NVDA', rsRatio: 104.2, rsMomentum: 102.5, color: '#ec4899' },  // Leading
  ],

  // Example 2: All Leading
  allLeading: [
    { symbol: 'STOCK1', rsRatio: 102.0, rsMomentum: 101.0 },
    { symbol: 'STOCK2', rsRatio: 103.5, rsMomentum: 102.5 },
    { symbol: 'STOCK3', rsRatio: 101.5, rsMomentum: 103.0 },
    { symbol: 'STOCK4', rsRatio: 104.0, rsMomentum: 101.5 },
  ],

  // Example 3: One in Each Quadrant
  oneEach: [
    { symbol: 'LEAD', rsRatio: 103.0, rsMomentum: 103.0 },    // Leading
    { symbol: 'IMPROVE', rsRatio: 97.0, rsMomentum: 103.0 },  // Improving
    { symbol: 'LAG', rsRatio: 97.0, rsMomentum: 97.0 },       // Lagging
    { symbol: 'WEAK', rsRatio: 103.0, rsMomentum: 97.0 },     // Weakening
  ],

  // Example 4: Sector ETFs
  sectorETFs: [
    { symbol: 'XLK', rsRatio: 102.8, rsMomentum: 101.2 },  // Technology
    { symbol: 'XLF', rsRatio: 98.5, rsMomentum: 99.8 },    // Financials
    { symbol: 'XLE', rsRatio: 104.1, rsMomentum: 98.5 },   // Energy
    { symbol: 'XLV', rsRatio: 99.2, rsMomentum: 101.7 },   // Healthcare
    { symbol: 'XLY', rsRatio: 101.5, rsMomentum: 100.9 },  // Consumer Discretionary
    { symbol: 'XLP', rsRatio: 96.8, rsMomentum: 99.2 },    // Consumer Staples
  ],

  // Example 5: Close to Benchmark (tight cluster)
  tightCluster: [
    { symbol: 'A', rsRatio: 100.2, rsMomentum: 100.1 },
    { symbol: 'B', rsRatio: 99.8, rsMomentum: 100.3 },
    { symbol: 'C', rsRatio: 100.1, rsMomentum: 99.7 },
    { symbol: 'D', rsRatio: 99.9, rsMomentum: 100.2 },
  ],

  // Example 6: Wide Distribution
  wideDistribution: [
    { symbol: 'STR1', rsRatio: 104.5, rsMomentum: 103.8 },  // Far Leading
    { symbol: 'STR2', rsRatio: 95.2, rsMomentum: 104.1 },   // Far Improving
    { symbol: 'WK1', rsRatio: 95.8, rsMomentum: 96.2 },     // Far Lagging
    { symbol: 'WK2', rsRatio: 104.2, rsMomentum: 96.5 },    // Far Weakening
  ],
};

// Usage Example:
// import { rrgExamples } from './path/to/this/file';
// <RRGChart data={rrgExamples.techGiants} />

/* 
 * Understanding the Data:
 * 
 * rsRatio (X-axis):
 *   - > 100: Stock is outperforming the benchmark
 *   - < 100: Stock is underperforming the benchmark
 *   - = 100: Stock is performing in line with benchmark
 * 
 * rsMomentum (Y-axis):
 *   - > 100: Relative strength is increasing (gaining momentum)
 *   - < 100: Relative strength is decreasing (losing momentum)
 *   - = 100: Relative strength is stable
 * 
 * Quadrants:
 *   Leading (Top Right):     rsRatio > 100 && rsMomentum > 100
 *   Improving (Top Left):    rsRatio < 100 && rsMomentum > 100
 *   Lagging (Bottom Left):   rsRatio < 100 && rsMomentum < 100
 *   Weakening (Bottom Right): rsRatio > 100 && rsMomentum < 100
 */

// Chatbot Integration Example
export const chatbotRRGExample = {
  type: 'rrg',
  data: rrgExamples.techGiants,
  title: 'Tech Giants Relative Rotation',
  benchmark: 'S&P 500',
  height: 500
};

// How to use in a chat message:
/*
const message = {
  text: "Here's the Relative Rotation Graph showing how tech giants are performing relative to the S&P 500. " +
        "Apple, Tesla, and NVIDIA are in the Leading quadrant (green), showing strong performance with increasing momentum. " +
        "Google and Meta are in the Improving quadrant (blue), gaining strength despite being below the benchmark. " +
        "Microsoft is Weakening (orange) - still outperforming but losing momentum. " +
        "Amazon is Lagging (red), underperforming with decreasing strength.",
  sender: 'ai',
  chartData: chatbotRRGExample
};
*/

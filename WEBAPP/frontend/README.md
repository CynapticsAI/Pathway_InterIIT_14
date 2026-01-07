This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Stock Market Chatbot with Advanced Charts

A modern stock market analysis platform with AI chatbot and interactive charts including:
- 📈 Line & Area Charts
- 🕯️ Candlestick Charts
- 📊 Volume Analysis
- 🔄 Multi-Stock Comparison
- 🎯 Sector Predictions
- **🔄 Relative Rotation Graph (RRG)** - NEW!

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### View Chart Examples

- Main App: [http://localhost:3000](http://localhost:3000)
- RRG Examples: [http://localhost:3000/rrg-example](http://localhost:3000/rrg-example)

## Available Charts

### 1. Line Charts
Simple price trends over time with optional area fill.

### 2. Candlestick Charts
OHLC (Open, High, Low, Close) data visualization.

### 3. Volume Charts
Trading volume analysis with price change indicators.

### 4. Multi-Stock Comparison
Compare multiple stocks on the same chart.

### 5. Relative Rotation Graph (RRG)
Analyze relative strength and momentum of stocks vs benchmark. See [RRG_GUIDE.md](./RRG_GUIDE.md) for details.

## Documentation

- [Charts Guide](./CHARTS_GUIDE.md) - Complete guide to all chart types
- [RRG Guide](./RRG_GUIDE.md) - **NEW!** Relative Rotation Graph implementation
- [Quick Reference](./QUICK_REFERENCE.md) - Quick component reference
- [Chatbot Customization](./CHATBOT_CUSTOMIZATION.md) - Customize the AI chatbot

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Main application
│   └── rrg-example/          # RRG examples page
├── components/
│   ├── charts/
│   │   ├── RRGChart.tsx      # NEW: Relative Rotation Graph
│   │   ├── ChartsPanel.tsx   # Chart display panel
│   │   └── ...               # Other chart components
│   ├── chat/                 # Chatbot components
│   └── ui/                   # UI components
└── lib/
    ├── stockDataGenerator.ts # Data generation utilities
    └── chartConstants.ts     # Chart configurations
```

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


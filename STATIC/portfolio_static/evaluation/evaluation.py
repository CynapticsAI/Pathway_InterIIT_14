import requests
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import os
import time

# --- CONFIG ---
API_URL = "http://localhost:8001"
TARGET_STOCKS = ["TSLA", "BX", "NIO", "AMZN", "MSFT"]
BENCHMARK = "SPY"
START_DATE = "2021-09-01"
END_DATE = "2022-09-30"

# Fix yfinance cache issue inside Docker
try:
    if not os.path.exists("/tmp/yf_cache"):
        os.makedirs("/tmp/yf_cache")
    yf.set_tz_cache_location("/tmp/yf_cache")
except: pass

logging.basicConfig(level=logging.INFO, format='%(message)s')

class MarketData:
    @staticmethod
    def fetch_history():
        tickers = TARGET_STOCKS + [BENCHMARK]
        print(f"📥 Fetching evaluation data ({START_DATE} to {END_DATE})...")
        try:
            data = yf.download(tickers, start=START_DATE, end=END_DATE, progress=False)
            if data.empty: return pd.DataFrame()

            if 'Adj Close' in data.columns: prices = data['Adj Close']
            elif 'Close' in data.columns: prices = data['Close']
            else: return pd.DataFrame()

            return prices.pct_change().dropna()
        except: return pd.DataFrame()

class Evaluator:
    @staticmethod
    def get_series_metrics(series: pd.Series):
        """Helper to calc basic stats for any return series"""
        cum_ret = (1 + series).prod() - 1
        vol = series.std() * np.sqrt(252)
        sharpe = (series.mean() * 252) / vol if vol > 0 else 0
        return cum_ret, vol, sharpe

    @staticmethod
    def calculate_comparative_metrics(weights: dict, returns_df: pd.DataFrame):
        if not weights or returns_df.empty: return None
        
        # 1. Align Assets
        assets = [s for s in weights.keys() if s in returns_df.columns]
        if not assets: return None
        
        # 2. Portfolio Return Series
        w_vec = np.array([weights[a] for a in assets])
        if np.sum(w_vec) > 0: w_vec = w_vec / np.sum(w_vec)
        port_series = returns_df[assets].mul(w_vec, axis=1).sum(axis=1)
        
        # 3. Benchmark Return Series
        if BENCHMARK in returns_df.columns:
            bench_series = returns_df[BENCHMARK]
        else:
            bench_series = pd.Series(0, index=port_series.index)

        # 4. Calculate Individual Metrics
        p_ret, p_vol, p_sharpe = Evaluator.get_series_metrics(port_series)
        b_ret, b_vol, b_sharpe = Evaluator.get_series_metrics(bench_series)
        
        # 5. Calculate Comparative Metrics (Beta)
        try:
            cov = np.cov(port_series, bench_series)
            beta = cov[0, 1] / cov[1, 1]
        except: beta = 0.0
        
        return {
            "Port_Return": p_ret,
            "Bench_Return": b_ret,
            "Active_Return": p_ret - b_ret, # Did we beat the market?
            
            "Port_Sharpe": p_sharpe,
            "Bench_Sharpe": b_sharpe,
            
            "Port_Vol": p_vol,
            "Bench_Vol": b_vol,
            
            "Beta": beta
        }

def run_matrix_audit():
    hist_data = MarketData.fetch_history()
    if hist_data.empty: 
        print("❌ No market data found.")
        return

    STRATEGIES = ["Mean-Variance", "CVaR", "Omega"]
    SERVICES = ["Creator", "Rebalancer", "Diversifier"]
    
    results_list = []

    print("\n🚀 Starting Full Comparison Matrix (Portfolio vs S&P 500)...")
    print("-" * 60)
    
    for service in SERVICES:
        for strat in STRATEGIES:
            # Setup Payload
            payload = {
                "user_id": f"audit_{service}_{strat}",
                "strategy_name": strat,
                "risk_params": {"hurdle_rate": 0.0, "max_sector_exposure": 0.4},
                "hard_to_borrow": []
            }
            
            endpoint = ""
            if service == "Creator":
                endpoint = "/create_portfolio"
            elif service == "Rebalancer":
                endpoint = "/rebalance_portfolio"
                payload["current_portfolio"] = [{"symbol": "TSLA", "weight": 1.0}]
            elif service == "Diversifier":
                endpoint = "/diversify_portfolio"
                payload["current_portfolio"] = [{"symbol": "MSFT", "weight": 0.5}, {"symbol": "AMZN", "weight": 0.5}]

            try:
                # Call API
                print(f"👉 {service:<12} | {strat:<15} ...", end=" ", flush=True)
                resp = requests.post(f"{API_URL}{endpoint}", json=payload)
                data = resp.json()
                weights = data.get("weights", {})
                
                # Analyze
                if not weights: 
                    print("❌ (No Weights)")
                else:
                    m = Evaluator.calculate_comparative_metrics(weights, hist_data)
                    print("✅")
                    
                    if m:
                        results_list.append({
                            "Service": service,
                            "Strategy": strat,
                            # Returns
                            "Port Return": f"{m['Port_Return']:.2%}",
                            "Bench Return": f"{m['Bench_Return']:.2%}",
                            "+/- vs Mkt": f"{m['Active_Return']:.2%}",
                            # Risk Adj
                            "Port Sharpe": f"{m['Port_Sharpe']:.2f}",
                            "Bench Sharpe": f"{m['Bench_Sharpe']:.2f}",
                            # Risk
                            "Beta": f"{m['Beta']:.2f}",
                            "Port Vol": f"{m['Port_Vol']:.2%}",
                            "Bench Vol": f"{m['Bench_Vol']:.2%}"
                        })
                    
            except Exception as e:
                print(f"❌ Error: {e}")

    # --- GENERATE FINAL REPORT ---
    if results_list:
        df = pd.DataFrame(results_list)
        
        # Save Full CSV
        filename = "final_audit_report.csv"
        df.to_csv(filename, index=False)
        
        print("\n🏆 FINAL COMPARISON TABLE")
        print("=" * 120)
        # Configure pandas to dispalay nice text table
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.colheader_justify', 'center')
        
        print(df)
        print("=" * 120)
        print(f"\n✅ Detailed report saved to: {filename}")
        print("   (Open this file in Excel to analyze Performance vs Benchmark)")

if __name__ == "__main__":
    run_matrix_audit()
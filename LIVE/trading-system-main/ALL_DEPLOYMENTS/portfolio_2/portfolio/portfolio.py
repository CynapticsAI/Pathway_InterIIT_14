import pathway as pw
import pandas as pd
import numpy as np
import cvxpy as cp
import json
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import psycopg2
from psycopg2.extras import RealDictCursor

# PyPortfolioOpt Imports
from pypfopt import (
    EfficientFrontier, 
    EfficientCVaR,
    risk_models, 
    objective_functions
)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

POSTGRES_SETTINGS = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "portfolio_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password")
}

RDKAFKA_SETTINGS = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    "group.id": "portfolio_pipeline_group",
    "auto.offset.reset": "earliest"
}

MACRO_API_URL = os.getenv("MACRO_API_URL", "http://macro-api:8000")

# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    @staticmethod
    def get_connection():
        return psycopg2.connect(**POSTGRES_SETTINGS)
    
    @staticmethod
    def create_initial_tables():
        conn = DatabaseManager.get_connection()
        try:
            with conn.cursor() as cur:
                logger.info("Rebuilding Database Schema...")
                cur.execute("DROP TABLE IF EXISTS market_data_snapshot CASCADE;")
                cur.execute("DROP TABLE IF EXISTS returns_history CASCADE;")
                cur.execute("DROP TABLE IF EXISTS optimization_results CASCADE;")

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS market_data_snapshot (
                        symbol TEXT PRIMARY KEY,
                        sector TEXT,
                        price FLOAT,
                        alpha_score FLOAT,
                        timestamp TIMESTAMP,
                        time BIGINT,
                        diff INT
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS returns_history (
                        symbol TEXT,
                        return_value FLOAT,
                        timestamp TIMESTAMP,
                        time BIGINT,
                        diff INT
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS optimization_results (
                        user_id TEXT,
                        timestamp TIMESTAMP,
                        strategy TEXT,
                        service_type TEXT,
                        result_json JSONB
                    );
                """)
                conn.commit()
                logger.info(" PostgreSQL tables verified/created.")
        except Exception as e:
            logger.error(f"Error creating initial tables: {e}")
            conn.rollback()
        finally:
            conn.close()

    @staticmethod
    def fetch_market_data(symbols: List[str] = None) -> pd.DataFrame:
        conn = DatabaseManager.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if symbols:
                    cur.execute("SELECT symbol, sector, alpha_score, price, timestamp FROM market_data_snapshot WHERE symbol = ANY(%s)", (symbols,))
                else:
                    cur.execute("SELECT symbol, sector, alpha_score, price, timestamp FROM market_data_snapshot")
                rows = cur.fetchall()
                return pd.DataFrame(rows) if rows else pd.DataFrame()
        finally:
            conn.close()

    @staticmethod
    def fetch_returns_history(lookback_minutes: int = 60) -> pd.DataFrame:
        conn = DatabaseManager.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cutoff = datetime.now() - timedelta(minutes=lookback_minutes)
                cur.execute("SELECT symbol, return_value, timestamp FROM returns_history WHERE timestamp >= %s ORDER BY timestamp ASC", (cutoff,))
                rows = cur.fetchall()
                if not rows: return pd.DataFrame()
                df = pd.DataFrame(rows)
                return df.pivot_table(index='timestamp', columns='symbol', values='return_value', aggfunc='last').fillna(0)
        finally:
            conn.close()

    @staticmethod
    def save_optimization_result(user_id: str, strategy: str, service_type: str, result: Dict):
        conn = DatabaseManager.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO optimization_results (user_id, timestamp, strategy, service_type, result_json) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, datetime.now(), strategy, service_type, json.dumps(result))
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving result: {e}")
        finally:
            conn.close()

# ==============================================================================
# CORE MATH ENGINE (Robust Version)
# ==============================================================================

class OptimizationEngine:
    """
    Contains the mathematical core for Mean-Variance, CVaR, Omega, etc.
    """
    
    @staticmethod
    def calculate_weights(strategy_name: str, filtered_stocks: pd.DataFrame, risk_params: Dict) -> Dict[str, float]:
        if filtered_stocks.empty: return {}
        
        def get_equal_weights():
            n = len(filtered_stocks)
            return {row['symbol']: 1.0/n for _, row in filtered_stocks.iterrows()}

        returns_df = DatabaseManager.fetch_returns_history(lookback_minutes=60)
        
        if returns_df.empty: 
            logger.warning("No returns history. Using Equal Weights.")
            return get_equal_weights()
        
        common_symbols = list(set(filtered_stocks['symbol']) & set(returns_df.columns))
        if len(common_symbols) < 2: 
            return {s: 1.0/len(common_symbols) for s in common_symbols} if common_symbols else {}
        
        returns_df = returns_df[common_symbols]
        filtered_stocks = filtered_stocks[filtered_stocks['symbol'].isin(common_symbols)]
        
        S = OptimizationEngine._get_covariance(returns_df)
        
        weights = {}
        try:
            if strategy_name == "CVaR":
                weights = OptimizationEngine._cvar(filtered_stocks, returns_df)
            elif strategy_name == "Omega":
                weights = OptimizationEngine._omega(filtered_stocks, returns_df, risk_params)
            else:
                weights = OptimizationEngine._mean_variance(filtered_stocks, S, risk_params)
        except Exception as e:
            logger.error(f"Strategy {strategy_name} crashed: {e}")
        
        if not weights:
            logger.warning(f"{strategy_name} returned empty. Defaulting to Equal Weights.")
            return get_equal_weights()
            
        return weights

    @staticmethod
    def calculate_portfolio_performance(weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates Expected Return (Alpha Aggregate), Risk (Volatility), and Sharpe Ratio.
        """
        if not weights:
            return {"expected_return": 0.0, "risk": 0.0, "sharpe_ratio": 0.0}
        
        symbols = list(weights.keys())
        market_data = DatabaseManager.fetch_market_data(symbols=symbols)
        returns_df = DatabaseManager.fetch_returns_history(lookback_minutes=60)
        
        if market_data.empty or returns_df.empty:
             return {"expected_return": 0.0, "risk": 0.0, "sharpe_ratio": 0.0}

        # Filter valid symbols
        valid_symbols = list(set(symbols) & set(market_data['symbol']) & set(returns_df.columns))
        if not valid_symbols:
             return {"expected_return": 0.0, "risk": 0.0, "sharpe_ratio": 0.0}

        # Align Vectors
        w_vec = np.array([weights[s] for s in valid_symbols])
        # Normalize in case some symbols were dropped
        if w_vec.sum() > 0: w_vec = w_vec / w_vec.sum()
        
        # Alphas (Expected Return Proxy)
        alphas = market_data.set_index('symbol').loc[valid_symbols]['alpha_score']
        mu = alphas.values

        # Covariance
        cov_df = returns_df[valid_symbols]
        S = OptimizationEngine._get_covariance(cov_df).values

        # Math
        exp_ret = np.dot(w_vec, mu)
        variance = np.dot(w_vec.T, np.dot(S, w_vec))
        volatility = np.sqrt(variance) if variance > 0 else 0.0
        sharpe = exp_ret / volatility if volatility > 1e-6 else 0.0
        
        return {
            "expected_return": round(float(exp_ret), 4),
            "risk": round(float(volatility), 4),
            "sharpe_ratio": round(float(sharpe), 4)
        }

    @staticmethod
    def calculate_metrics(weights: Dict[str, float], market_data: pd.DataFrame) -> Dict[str, Any]:
        if not weights or market_data.empty:
            return {"stock_exposure": {}, "sector_exposure": {}}
        
        w_df = pd.DataFrame(list(weights.items()), columns=['symbol', 'weight'])
        m_df = market_data[['symbol', 'sector']].drop_duplicates(subset=['symbol'])
        merged = w_df.merge(m_df, on='symbol', how='left')
        
        stock_exp = dict(sorted(weights.items(), key=lambda item: item[1], reverse=True))
        sector_exp = merged.groupby('sector')['weight'].sum().sort_values(ascending=False).to_dict()
        
        return {"stock_exposure": stock_exp, "sector_exposure": sector_exp}

    @staticmethod
    def _get_covariance(returns_df):
        try:
            S = risk_models.CovarianceShrinkage(returns_df).ledoit_wolf()
        except:
            S = risk_models.sample_cov(returns_df)
        S = S + np.eye(S.shape[0]) * 1e-4
        S_values = S.values
        S_symmetric = (S_values + S_values.T) / 2
        return pd.DataFrame(S_symmetric, index=S.index, columns=S.columns)

    @staticmethod
    def _mean_variance(df, S, params):
        try:
            mu = df.set_index('symbol')['alpha_score'][S.index]
            ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))
            if params.get('target_beta'):
                betas = np.random.uniform(0.5, 1.5, len(mu))
                ef.add_constraint(lambda w: cp.sum(w * betas) == params['target_beta'])
            ef.max_sharpe(risk_free_rate=0.0)
            return ef.clean_weights()
        except: return {}

    @staticmethod
    def _cvar(df, returns_df):
        try:
            ec = EfficientCVaR(None, returns_df, weight_bounds=(0, 1))
            mu = df.set_index('symbol')['alpha_score']
            ec.efficient_return(target_return=mu.mean() if not mu.empty else 0.01)
            return ec.clean_weights()
        except: return {}

    @staticmethod
    def _omega(df, returns_df, params):
        try:
            data = returns_df.values
            T, n = data.shape
            hurdle = params.get('hurdle_rate', 0.0) / 252
            w = cp.Variable(n); y = cp.Variable(T)
            obj = cp.Minimize(cp.sum(y))
            constraints = [cp.sum(w) == 1, w >= 0, y >= 0, y >= hurdle - data @ w]
            cp.Problem(obj, constraints).solve(solver=cp.ECOS)
            return dict(zip(returns_df.columns, np.round(w.value, 4))) if w.value is not None else {}
        except: return {}

# ==============================================================================
# SERVICE 1: CREATOR
# ==============================================================================

class CreatorService:
    @staticmethod
    def execute(user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[CREATOR:{user_id}] Creating fresh portfolio")
        
        market_data = DatabaseManager.fetch_market_data()
        if market_data.empty: return {"error": "No market data"}

        filtered = market_data[
            (market_data['alpha_score'] >= config.get('risk_params', {}).get('hurdle_rate', 0.0)) & 
            (~market_data['symbol'].isin(config.get('hard_to_borrow', [])))
        ]
        
        weights = OptimizationEngine.calculate_weights(config.get('strategy_name', 'Mean-Variance'), filtered, config.get('risk_params', {}))
        
        # Metrics
        metrics = OptimizationEngine.calculate_metrics(weights, market_data)
        perf = OptimizationEngine.calculate_portfolio_performance(weights)
        
        result = {
            "weights": weights, 
            "tickers_analyzed": len(filtered),
            "stock_exposure": metrics['stock_exposure'],
            "sector_exposure": metrics['sector_exposure'],
            "new_portfolio_metrics": perf
        }
        
        DatabaseManager.save_optimization_result(user_id, config.get('strategy_name'), "CREATOR", result)
        return result

# ==============================================================================
# SERVICE 2: REBALANCER
# ==============================================================================

class RebalancerService:
    @staticmethod
    def execute(user_id: str, config: Dict[str, Any], current_portfolio: List[Dict]) -> Dict[str, Any]:
        logger.info(f"[REBALANCER:{user_id}] Reallocating existing assets")
        if not current_portfolio: return {"error": "No portfolio provided"}
        
        existing_symbols = [item['symbol'] for item in current_portfolio]
        market_data = DatabaseManager.fetch_market_data(symbols=existing_symbols)
        
        new_weights = OptimizationEngine.calculate_weights(config.get('strategy_name', 'Mean-Variance'), market_data, config.get('risk_params', {}))
        trades = RebalancerService._calculate_trades(current_portfolio, new_weights)
        
        # Metrics
        metrics = OptimizationEngine.calculate_metrics(new_weights, market_data)
        
        # Performance Comparison
        current_w = {item['symbol']: item['weight'] for item in current_portfolio}
        old_perf = OptimizationEngine.calculate_portfolio_performance(current_w)
        new_perf = OptimizationEngine.calculate_portfolio_performance(new_weights)
        
        result = {
            "weights": new_weights, 
            "trades": trades,
            "stock_exposure": metrics['stock_exposure'],
            "sector_exposure": metrics['sector_exposure'],
            "old_portfolio_metrics": old_perf,
            "new_portfolio_metrics": new_perf
        }
        
        DatabaseManager.save_optimization_result(user_id, config.get('strategy_name'), "REBALANCER", result)
        return result

    @staticmethod
    def _calculate_trades(current_portfolio, target_weights):
        trades = {}
        current_map = {item['symbol']: item['weight'] for item in current_portfolio}
        for sym in set(current_map.keys()) | set(target_weights.keys()):
            target = target_weights.get(sym, 0.0)
            current = current_map.get(sym, 0.0)
            diff = target - current
            if abs(diff) > 0.001:
                trades[sym] = {"action": "BUY" if diff > 0 else "SELL", "delta": round(diff, 4)}
        return trades

# ==============================================================================
# SERVICE 3: DIVERSIFIER
# ==============================================================================

class DiversifierService:
    @staticmethod
    def execute(user_id: str, config: Dict[str, Any], current_portfolio: List[Dict]) -> Dict[str, Any]:
        logger.info(f"[DIVERSIFIER:{user_id}] Expanding portfolio universe")
        market_data = DatabaseManager.fetch_market_data()
        
        candidates = market_data[
            (market_data['alpha_score'] >= config.get('risk_params', {}).get('hurdle_rate', 0.0)) & 
            (~market_data['symbol'].isin(config.get('hard_to_borrow', [])))
        ]
        
        current_symbols = [item['symbol'] for item in current_portfolio or []]
        universe = market_data[
            (market_data['symbol'].isin(candidates['symbol'])) | 
            (market_data['symbol'].isin(current_symbols))
        ]
        
        raw_weights = OptimizationEngine.calculate_weights(config.get('strategy_name', 'Mean-Variance'), universe, config.get('risk_params', {}))
        final_weights = DiversifierService._apply_sector_limits(raw_weights, market_data, config.get('risk_params', {}))
        trades = RebalancerService._calculate_trades(current_portfolio or [], final_weights)
        
        # Metrics
        metrics = OptimizationEngine.calculate_metrics(final_weights, market_data)
        
        # Performance Comparison
        current_w = {item['symbol']: item['weight'] for item in current_portfolio}
        old_perf = OptimizationEngine.calculate_portfolio_performance(current_w)
        new_perf = OptimizationEngine.calculate_portfolio_performance(final_weights)
        
        result = {
            "weights": final_weights, 
            "trades": trades,
            "stock_exposure": metrics['stock_exposure'],
            "sector_exposure": metrics['sector_exposure'],
            "old_portfolio_metrics": old_perf,
            "new_portfolio_metrics": new_perf
        }
        
        DatabaseManager.save_optimization_result(user_id, config.get('strategy_name'), "DIVERSIFIER", result)
        return result

    @staticmethod
    def _apply_sector_limits(weights, market_data, params):
        if not weights: return {}
        limit = params.get('max_sector_exposure', 0.30)
        w_df = pd.DataFrame([{'symbol': s, 'weight': w} for s, w in weights.items()])
        w_df = w_df.merge(market_data[['symbol', 'sector']], on='symbol', how='left')
        adjusted = weights.copy()
        for sector in w_df['sector'].dropna().unique():
            mask = w_df['sector'] == sector
            total = w_df.loc[mask, 'weight'].sum()
            if total > limit:
                scale = limit / total
                for sym in w_df.loc[mask, 'symbol']:
                    adjusted[sym] *= scale
        return adjusted

# ==============================================================================
# PIPELINE SETUP (Streaming)
# ==============================================================================

class StockScoreSchema(pw.Schema):
    symbol: str
    stock_score: float
    latest_price: float
    timestamp: pw.DateTimeNaive
class SentimentSchema(pw.Schema):
    symbol: str
    sentiment_score: float
    t: int

@pw.udf
def get_macro_score(sector: str) -> float:
    try:
        r = requests.get(f"{MACRO_API_URL}/predict/{sector}", timeout=2.0)
        return max(0.0, min(1.0, 0.5 + (r.json().get("predicted_return_pct",0)/10.0))) if r.ok else 0.5
    except: return 0.5

@pw.udf
def calculate_alpha_score(stock, macro, sent) -> float:
    return (0.4 * stock) + (0.4 * macro) + (0.2 * ((sent+1)/2))

@pw.udf
def calc_ret(prices: list) -> float:
    return (prices[-1] - prices[0]) / prices[0] if len(prices) > 1 else 0.0

def initialize_streaming_pipeline():
    stocks = pw.io.kafka.read(RDKAFKA_SETTINGS, topic="stock_scores", schema=StockScoreSchema, format="json")
    sent = pw.io.kafka.read(RDKAFKA_SETTINGS, topic="sentiment_scores", schema=SentimentSchema, format="json")
    sent = sent.with_columns(timestamp=pw.this.t.dt.from_timestamp("ms"))
    master = pw.io.csv.read("master_stock_list.csv", schema=pw.schema_from_csv("master_stock_list.csv"), mode="static")
    
    s_win = stocks.windowby(pw.this.timestamp, window=pw.temporal.tumbling(timedelta(seconds=5)), instance=pw.this.symbol).reduce(
        symbol=pw.reducers.max(pw.this.symbol), stock_score=pw.reducers.max(pw.this.stock_score),
        price=pw.reducers.max(pw.this.latest_price), timestamp=pw.reducers.max(pw.this.timestamp))
    
    sent_win = sent.windowby(pw.this.timestamp, window=pw.temporal.tumbling(timedelta(seconds=5)), instance=pw.this.symbol).reduce(
        symbol=pw.reducers.max(pw.this.symbol), sentiment_score=pw.reducers.avg(pw.this.sentiment_score),
        timestamp=pw.reducers.max(pw.this.timestamp))

    enriched = s_win.join(master, s_win.symbol == master.symbol, how=pw.JoinMode.INNER).select(
        symbol=s_win.symbol, stock_score=s_win.stock_score, price=s_win.price, timestamp=s_win.timestamp,
        sector=master.sector, macro_score=get_macro_score(master.sector))

    final = enriched.join(sent_win, enriched.symbol == sent_win.symbol, how=pw.JoinMode.LEFT).select(
        symbol=enriched.symbol, sector=enriched.sector, price=enriched.price, timestamp=enriched.timestamp,
        alpha_score=calculate_alpha_score(enriched.stock_score, enriched.macro_score, pw.coalesce(sent_win.sentiment_score,0.0)))

    p_win = final.windowby(pw.this.timestamp, window=pw.temporal.sliding(hop=timedelta(seconds=60), duration=timedelta(minutes=5)), instance=pw.this.symbol).reduce(
        symbol=pw.reducers.max(pw.this.symbol), prices=pw.reducers.tuple(pw.this.price), timestamp=pw.reducers.max(pw.this.timestamp))
    
    rets = p_win.select(symbol=pw.this.symbol, return_value=calc_ret(pw.this.prices), timestamp=pw.this.timestamp)
    pw.io.csv.write(rets, "/app/output/return.csv")

    pw.io.postgres.write_snapshot(final, POSTGRES_SETTINGS, table_name="market_data_snapshot", primary_key=['symbol'])
    pw.io.postgres.write(rets, POSTGRES_SETTINGS, table_name="returns_history", output_table_type="stream_of_changes")
    logger.info("Pipeline built.")

if __name__ == "__main__":
    DatabaseManager.create_initial_tables()
    initialize_streaming_pipeline()
    pw.run()

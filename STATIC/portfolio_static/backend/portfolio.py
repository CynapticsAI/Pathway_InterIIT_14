import pathway as pw
import pandas as pd
import numpy as np
import cvxpy as cp
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
from pypfopt import EfficientFrontier, EfficientCVaR, risk_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Portfolio")

POSTGRES_SETTINGS = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": "5432",
    "dbname": os.getenv("POSTGRES_DB", "portfolio_db"),
    "user": os.getenv("POSTGRES_USER", "user"),
    "password": os.getenv("POSTGRES_PASSWORD", "password")
}
RDKAFKA_SETTINGS = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    "group.id": "portfolio_consumer_group",
    "auto.offset.reset": "earliest"
}

# --- DB MANAGER ---
class DatabaseManager:
    @staticmethod
    def get_conn(): return psycopg2.connect(**POSTGRES_SETTINGS)
    
    @staticmethod
    def create_initial_tables():
        conn = DatabaseManager.get_conn()
        try:
            with conn.cursor() as cur:
                logger.info("♻️  Resetting database schema to match current code...")
                
                # ✅ FIX: Drop ALL tables to remove old schemas lacking columns
                cur.execute("DROP TABLE IF EXISTS market_data_snapshot CASCADE;")
                cur.execute("DROP TABLE IF EXISTS returns_history CASCADE;")
                cur.execute("DROP TABLE IF EXISTS optimization_results CASCADE;") # <--- This fixes your specific error
                
                # Recreate with correct columns (including service_type)
                cur.execute("""
                    CREATE TABLE market_data_snapshot (
                        symbol TEXT PRIMARY KEY, 
                        price FLOAT, 
                        stock_score FLOAT, 
                        timestamp TIMESTAMP,
                        time BIGINT,
                        diff INT
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE returns_history (
                        symbol TEXT, 
                        return_value FLOAT, 
                        timestamp TIMESTAMP,
                        time BIGINT,
                        diff INT
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE optimization_results (
                        user_id TEXT, 
                        timestamp TIMESTAMP, 
                        strategy TEXT, 
                        service_type TEXT, 
                        result_json JSONB
                    );
                """)
                conn.commit()
                logger.info("✅ Database tables dropped & recreated successfully.")
        except Exception as e:
            logger.error(f"DB Init Error: {e}")
            conn.rollback()
        finally: conn.close()

    @staticmethod
    def fetch_market_data(symbols=None):
        conn = DatabaseManager.get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                q = "SELECT symbol, price, stock_score FROM market_data_snapshot"
                if symbols: 
                    q += " WHERE symbol = ANY(%s)"
                    cur.execute(q, (symbols,))
                else: cur.execute(q)
                return pd.DataFrame(cur.fetchall())
        finally: conn.close()

    @staticmethod
    def fetch_returns_history(limit=5000):
        conn = DatabaseManager.get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT symbol, return_value, timestamp FROM returns_history ORDER BY timestamp DESC LIMIT %s", (limit,))
                df = pd.DataFrame(cur.fetchall())
                return df.pivot_table(index='timestamp', columns='symbol', values='return_value', aggfunc='mean').fillna(0) if not df.empty else pd.DataFrame()
        finally: conn.close()

    @staticmethod
    def save_optimization_result(uid, strat, svc, res):
        conn = DatabaseManager.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO optimization_results (user_id, timestamp, strategy, service_type, result_json) VALUES (%s, %s, %s, %s, %s)", 
                            (uid, datetime.now(), strat, svc, json.dumps(res)))
                conn.commit()
        finally: conn.close()

# --- OPTIMIZATION ENGINE ---
class OptimizationEngine:
    @staticmethod
    def calculate_weights(strategy, filtered_stocks, params):
        if filtered_stocks.empty: return {}
        n = len(filtered_stocks)
        eq_w = {r['symbol']: 1.0/n for _,r in filtered_stocks.iterrows()}
        
        returns = DatabaseManager.fetch_returns_history()
        if returns.empty or len(returns) < 5: return eq_w
        
        common = list(set(filtered_stocks['symbol']) & set(returns.columns))
        if not common: return eq_w
        
        returns = returns[common]
        mu = filtered_stocks[filtered_stocks['symbol'].isin(common)].set_index('symbol')['stock_score']
        
        try:
            try: S = risk_models.CovarianceShrinkage(returns).ledoit_wolf()
            except: S = risk_models.sample_cov(returns)
            S = S + np.eye(len(common)) * 1e-4
            
            if strategy == "CVaR":
                ec = EfficientCVaR(None, returns)
                ec.efficient_return(target_return=mu.mean())
                return ec.clean_weights()
            elif strategy == "Omega":
                ef = EfficientFrontier(mu, S)
                ef.max_sharpe(risk_free_rate=0.0)
                return ef.clean_weights()
            else:
                ef = EfficientFrontier(mu, S)
                if params.get('target_beta'):
                    betas = np.random.uniform(0.8, 1.2, len(mu))
                    ef.add_constraint(lambda w: cp.sum(w * betas) == params['target_beta'])
                ef.max_sharpe(risk_free_rate=0.0)
                return ef.clean_weights()
        except: return eq_w

# --- SERVICES ---
class CreatorService:
    @staticmethod
    def execute(uid, cfg):
        market = DatabaseManager.fetch_market_data()
        hurdle = cfg.get('risk_params', {}).get('hurdle_rate', 0.0)
        filtered = market[market['stock_score'] >= hurdle]
        w = OptimizationEngine.calculate_weights(cfg['strategy_name'], filtered, cfg.get('risk_params'))
        DatabaseManager.save_optimization_result(uid, cfg['strategy_name'], "CREATOR", w)
        return {"weights": w, "count": len(filtered)}

class RebalancerService:
    @staticmethod
    def execute(uid, cfg, current_pf):
        if not current_pf: return {"weights": {}, "trades": {}}
        syms = [x['symbol'] for x in current_pf]
        market = DatabaseManager.fetch_market_data(syms)
        w = OptimizationEngine.calculate_weights(cfg['strategy_name'], market, cfg.get('risk_params'))
        trades = {s: {"action": "BUY" if w.get(s,0) > x['weight'] else "SELL", "delta": w.get(s,0)-x['weight']} 
                  for s,x in zip(syms, current_pf) if abs(w.get(s,0)-x['weight']) > 0.01}
        DatabaseManager.save_optimization_result(uid, cfg['strategy_name'], "REBALANCER", w)
        return {"weights": w, "trades": trades}

class DiversifierService:
    @staticmethod
    def execute(uid, cfg, current_pf):
        market = DatabaseManager.fetch_market_data()
        hurdle = cfg.get('risk_params', {}).get('hurdle_rate', 0.0)
        cands = market[market['stock_score'] >= hurdle]
        curr = [x['symbol'] for x in current_pf or []]
        univ = market[market['symbol'].isin(cands['symbol']) | market['symbol'].isin(curr)]
        w = OptimizationEngine.calculate_weights(cfg['strategy_name'], univ, cfg.get('risk_params'))
        DatabaseManager.save_optimization_result(uid, cfg['strategy_name'], "DIVERSIFIER", w)
        return {"weights": w}

# --- PIPELINE ---
class ScorerInputSchema(pw.Schema):
    symbol: str
    stock_score: float
    latest_price: float
    timestamp: pw.DateTimeNaive

@pw.udf
def calc_ret(price_list: list) -> float:
    if len(price_list) < 2: return 0.0
    return (price_list[-1] - price_list[0]) / price_list[0]

def main():
    # Calling this here ensures the DB is reset as soon as the engine starts
    DatabaseManager.create_initial_tables()
    print("🚀 Starting Portfolio Engine...", flush=True)
    
    scores = pw.io.kafka.read(RDKAFKA_SETTINGS, topic="stock_scores", schema=ScorerInputSchema, format="json")
    
    snap = scores.windowby(pw.this.timestamp, window=pw.temporal.tumbling(timedelta(seconds=1)), instance=pw.this.symbol).reduce(
        symbol=pw.this._pw_instance, price=pw.reducers.latest(pw.this.latest_price),
        stock_score=pw.reducers.latest(pw.this.stock_score), timestamp=pw.reducers.max(pw.this.timestamp)
    )
    
    ret_calc = scores.windowby(pw.this.timestamp, window=pw.temporal.sliding(hop=timedelta(seconds=5), duration=timedelta(minutes=1)), instance=pw.this.symbol).reduce(
        symbol=pw.this._pw_instance, prices=pw.reducers.tuple(pw.this.latest_price), timestamp=pw.reducers.max(pw.this.timestamp)
    ).select(
        symbol=pw.this.symbol, return_value=calc_ret(pw.this.prices), timestamp=pw.this.timestamp
    )

    pw.io.postgres.write_snapshot(snap, POSTGRES_SETTINGS, "market_data_snapshot", primary_key=['symbol'])
    pw.io.postgres.write(ret_calc, POSTGRES_SETTINGS, "returns_history", output_table_type="stream_of_changes")
    pw.run()

if __name__ == "__main__": main()
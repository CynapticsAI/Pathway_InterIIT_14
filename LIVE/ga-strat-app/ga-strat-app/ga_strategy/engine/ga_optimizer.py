import json
import random
import math
from dataclasses import dataclass
from .backtester import *
from ..strategies.core_strategies import *
import pandas as pd
from pathlib import Path

@dataclass
class GAConfig:
    generations: int = 10
    population: int = 30
    retain: float = 0.35
    mutation_rate: float = 0.25

config_path = Path(__file__).resolve().parent.parent / "config" / "strategies.json"
print(config_path)

def load_config(path=config_path):
    with open(path, "r") as f:
        return json.load(f)


def sanitize_float(value):
    """Replace inf/nan with None for JSON compatibility."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def sanitize_metrics(metrics):
    """Recursively sanitize all float values in metrics dict."""
    if isinstance(metrics, dict):
        return {k: sanitize_metrics(v) for k, v in metrics.items()}
    elif isinstance(metrics, (list, tuple)):
        sanitized = [sanitize_metrics(item) for item in metrics]
        return tuple(sanitized) if isinstance(metrics, tuple) else sanitized
    elif isinstance(metrics, float):
        return sanitize_float(metrics)
    return metrics


def evaluate(df_train, df_valid, fn, params, cost):
    finalize = lambda ret, sig, cc=cost: finalize_strategy(ret, sig, cc)

    strat_t, signal_t = fn(df_train, params, cost, finalize)
    daily_t = to_daily_returns(strat_t)
    sh_t = sharpe(daily_t)
    so_t = sortino(daily_t)
    dd_t = max_drawdown(strat_t)

    strat_v, signal_v = fn(df_valid, params, cost, finalize)
    daily_v = to_daily_returns(strat_v)
    sh_v = sharpe(daily_v)
    so_v = sortino(daily_v)
    dd_v = max_drawdown(strat_v)

    score = 0.7*sh_v + 1.3*so_v - 0.5*max(0, -dd_v)
    if math.isnan(score) or math.isinf(score):
        score = float('-inf')

    return score, {
        "train": {"sharpe": sh_t, "sortino": so_t, "dd": dd_t},
        "valid": {"sharpe": sh_v, "sortino": so_v, "dd": dd_v},
    }


def genetic_optimize(df_train, df_valid):
    cfg = GAConfig()
    conf = load_config()

    best_params = {}

    for strategy_name, strategy_data in conf.items():
        print(f"\nOptimizing {strategy_name}...")
        grid = strategy_data["grid"]
        params_list = strategy_data["params"]
        fn = globals()[strategy_data["function"]]

        population = []
        for _ in range(cfg.population):
            ind = {p: random.choice(grid[p]) for p in params_list}
            population.append(ind)

        best = None

        for g in range(cfg.generations):
            scored = []
            for ind in population:
                score, metrics = evaluate(df_train, df_valid, fn, ind, DEFAULT_COST)
                scored.append((score, ind, metrics))

            scored.sort(key=lambda x: x[0] if not math.isinf(x[0]) else float('-inf'), reverse=True)
            best = scored[0]

            retain_n = max(1, int(cfg.retain * len(scored)))
            parents = [x[1] for x in scored[:retain_n]]

            children = []
            while len(children) < cfg.population - retain_n:
                p1 = random.choice(parents)
                p2 = random.choice(parents)
                child = {p: random.choice([p1[p], p2[p]]) for p in params_list}
                if random.random() < cfg.mutation_rate:
                    key = random.choice(params_list)
                    child[key] = random.choice(grid[key])
                children.append(child)

            population = parents + children
            print(f"Gen {g+1}: best score={best[0]:.3f}, params={best[1]}")
            
        sanitized_best = (
            sanitize_float(best[0]),
            best[1],
            sanitize_metrics(best[2])
        )
        best_params[strategy_name] = sanitized_best

    return best_params
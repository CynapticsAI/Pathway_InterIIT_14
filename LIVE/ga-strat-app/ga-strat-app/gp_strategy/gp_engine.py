"""
GP engine orchestrator (multiprocessing-safe) with DEBUG logs + safe timeout handling.

This version ensures that when a worker times out or a chunk fails, the pool is terminated
and we continue rather than hanging forever.
"""

import random
import json
import os
import math
import time
import multiprocessing as mp

from deap import base, creator, tools, gp

from .types_primitives import create_pset, SCAL, VEC, BOOL
from .fitness import evaluate_individual

POP = 300
GENERATIONS = 30
TOURNAMENT = 7
CX_PB = 0.6
MUT_PB = 0.25
WORKERS = max(1, mp.cpu_count() - 1)

TASK_TIMEOUT_SECONDS = 45
CHUNK_SIZE = 16 


def clean_for_json(obj):
    import numpy as np
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {clean_for_json(k): clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(i) for i in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except Exception:
            return str(obj)
    if isinstance(obj, (float, int, str, bool)):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj
    try:
        return float(obj)
    except Exception:
        return str(obj)


def _failed_metrics():
    return {
        "roi": 0, "sharpe": 0, "sortino": 0,
        "max_drawdown": 0, "drawdown_duration": 0,
        "exposure": 0, "num_trades": 0, "win_rate": 0,
        "avg_trade_return": 0, "profit_factor": float('inf')
    }


def build_toolbox(pset):
    print("[MAIN] Building toolbox...")
    try:
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    except Exception:
        pass
    try:
        creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)
    except Exception:
        pass

    tb = base.Toolbox()
    tb.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=4)
    tb.register("individual", tools.initIterate, creator.Individual, tb.expr)
    tb.register("population", tools.initRepeat, list, tb.individual)
    tb.register("compile", gp.compile, pset=pset)
    tb.register("select", tools.selTournament, tournsize=TOURNAMENT)
    tb.register("mate", gp.cxOnePoint)
    tb.register("expr_mut", gp.genFull, min_=0, max_=2)
    tb.register("mutate", gp.mutUniform, expr=tb.expr_mut, pset=pset)
    tb.decorate("mate", gp.staticLimit(key=lambda ind: len(ind), max_value=120))
    tb.decorate("mutate", gp.staticLimit(key=lambda ind: len(ind), max_value=120))

    print("[MAIN] Toolbox built successfully.")
    return tb


def _worker_eval(task):
    ind_str, pset, df_window = task
    # Keep worker prints minimal to avoid stdout buffer issues
    print(f"[WORKER] Received task: Individual string length={len(ind_str)}, df_window rows={len(df_window)}")

    try:
        tree = gp.PrimitiveTree.from_string(ind_str, pset)
    except Exception as e:
        print("[WORKER] ERROR parsing tree:", e)
        return -10.0, _failed_metrics()

    dummy_tb = base.Toolbox()
    dummy_tb.register("compile", gp.compile, pset=pset)

    try:
        fit, metrics = evaluate_individual(tree, dummy_tb, df_window)
        print(f"[WORKER] Evaluation complete. Fitness={fit}")
    except Exception as e:
        print("[WORKER] ERROR during evaluation:", e)
        return -10.0, _failed_metrics()

    return float(fit), metrics

def eval_population(pop, tb, df_window):
    """
    Evaluate population in chunks. If any task in a chunk times out or causes an exception,
    terminate that pool immediately and mark remaining tasks in the chunk as failed.
    """
    pset = tb.pset
    tasks = [(str(ind), pset, df_window) for ind in pop]
    total = len(tasks)
    print(f"[MAIN] Starting population evaluation: pop={total} workers={WORKERS} chunk_size={CHUNK_SIZE}")

    results = [None] * total

    for start in range(0, total, CHUNK_SIZE):
        end = min(total, start + CHUNK_SIZE)
        chunk = tasks[start:end]
        chunk_len = len(chunk)
        print(f"[MAIN] Processing chunk start={start} end={end} (len={chunk_len})")

        pool = None
        async_results = []
        try:
            pool = mp.Pool(WORKERS)
            # submit tasks
            for t in chunk:
                async_results.append(pool.apply_async(_worker_eval, (t,)))

            # collect with timeout per-task
            terminated_early = False
            for i, ar in enumerate(async_results):
                task_idx = start + i
                try:
                    res = ar.get(timeout=TASK_TIMEOUT_SECONDS)
                    results[task_idx] = res
                except mp.TimeoutError:
                    print(f"[MAIN] TIMEOUT: task_idx={task_idx} (chunk {start}-{end}) after {TASK_TIMEOUT_SECONDS}s. Terminating pool.")
                    terminated_early = True
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                    for j in range(i, chunk_len):
                        results[start + j] = (-10.0, _failed_metrics())
                    break
                except Exception as e:
                    print(f"[MAIN] Task error at idx={task_idx}: {e}. Terminating pool and marking remaining failed.")
                    terminated_early = True
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                    for j in range(i, chunk_len):
                        results[start + j] = (-10.0, _failed_metrics())
                    break

            if pool is not None and not terminated_early:
                try:
                    pool.close()
                    pool.join()
                except Exception:
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass

        except Exception as e_outer:
            print(f"[MAIN] ERROR: chunk submission failed ({start}-{end}): {e_outer}. Marking chunk failed.")
            try:
                if pool is not None:
                    pool.terminate()
                    pool.join()
            except Exception:
                pass
            for j in range(chunk_len):
                results[start + j] = (-10.0, _failed_metrics())

        finally:
            try:
                if pool is not None:
                    pool.terminate()
                    pool.join()
            except Exception:
                pass

        print(f"[MAIN] Chunk {start}-{end} done.")

    print("[MAIN] Assigning results back to population...")
    for i, ind in enumerate(pop):
        res = results[i] if results[i] is not None else (-10.0, _failed_metrics())
        fit, metrics = res
        ind.fitness.values = (float(fit),)
        ind.metrics = metrics

    print("[MAIN] Population evaluation finished.")
    return pop


# evolution
def _run_evolution_on_df(df, out_dir):
    from copy import deepcopy

    print("[MAIN] Creating primitive set...")
    pset = create_pset()
    tb = build_toolbox(pset)
    tb.pset = pset

    print("[MAIN] Initializing population...")
    pop = tb.population(n=POP)
    hof = tools.HallOfFame(15)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda x: float(sum(v[0] for v in x) / len(x)) if x else 0)
    stats.register("max", lambda x: float(max(v[0] for v in x)) if x else 0)

    nrows = len(df)
    print("[MAIN] DF rows =", nrows)

    for gen in range(GENERATIONS):
        print(f"\n========== Generation {gen} ==========")

        if nrows < 50:
            df_win = df.copy()
        else:
            win_len = max(100, int(0.25 * nrows))
            start = random.randint(0, nrows - win_len)
            df_win = df.iloc[start:start + win_len].reset_index(drop=True)

        print("[MAIN] Window rows =", len(df_win))

        pop = eval_population(pop, tb, df_win)

        print("[MAIN] Selecting offspring...")
        offspring = tb.select(pop, len(pop))
        offspring = [tb.clone(ind) for ind in offspring]

        print("[MAIN] Applying crossover and mutation...")
        for c1, c2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CX_PB:
                tb.mate(c1, c2)
                if hasattr(c1.fitness, "values"): del c1.fitness.values
                if hasattr(c2.fitness, "values"): del c2.fitness.values

        for m in offspring:
            if random.random() < MUT_PB:
                tb.mutate(m)
                if hasattr(m.fitness, "values"): del m.fitness.values

        invalids = [ind for ind in offspring if not ind.fitness.valid]
        print("[MAIN] Invalid individuals =", len(invalids))

        if invalids:
            
            eval_population(invalids, tb, df_win)

        pop = offspring
        hof.update(pop)

    # Final eval
    print("\n[MAIN] Evaluating Hall of Fame on FULL dataset...")
    results = []
    for ind in hof:
        fit, metrics = evaluate_individual(ind, tb, df)
        results.append({
            "tree": str(ind),
            "fitness": float(fit),
            "metrics": clean_for_json(metrics),
        })

    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "final.json")
    json.dump(results, open(json_path, "w"), indent=2)

    print("[MAIN] Done. Results saved to:", json_path)
    return results


def run_evolution_df(df, out_dir):
    return _run_evolution_on_df(df, out_dir)


def run_evolution(prep_csv, out_dir):
    import pandas as pd
    df = pd.read_csv(prep_csv, parse_dates=["timestamp"])
    return _run_evolution_on_df(df, out_dir)

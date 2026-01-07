"""
Entrypoint to run the GP engine.
Usage:
  python run.py --input stvgp_ready_hourly.csv --out stvgp_out
"""
import argparse
from gp_engine import run_evolution

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Preprocessed CSV (hourly ready for GP)")
    parser.add_argument("--out", "-o", required=True, help="Output folder for results")
    args = parser.parse_args()

    run_evolution(args.input, args.out)

import json
import re

# MAPPING
ARG_MAP = {
    "ARG0": "close_vec",
    "ARG1": "high_vec",
    "ARG2": "low_vec",
    "ARG3": "vol_vec",
    "ARG4": "ema5",
    "ARG5": "ema13",
    "ARG6": "ema50",
    "ARG7": "ema200",
    "ARG8": "rsi14",
}

FUNC_MAP = {
    "add": "({} + {})",
    "sub": "({} - {})",
    "mul": "({} * {})",
    "protected_div": "safe_div({}, {})",
    "abs": "abs({})",
    "sin": "sin({})",
    "cos": "cos({})",
    "tanh": "tanh({})",
    "neg": "-({})",

    # Logical
    "gt": "({} > {})",
    "ge": "({} >= {})",
    "lt": "({} < {})",
    "le": "({} <= {})",
    "lor": "({} OR {})",
    "land": "({} AND {})",
    "lnot": "(NOT {})",

    # Vector ops
    "vec_min": "min({})",
    "vec_max": "max({})",
    "vec_sum": "sum({})",
    "vec_mean": "mean({})",
    "vec_std": "std({})",
    "vec_add": "({} + {})",
}

# PARSER
def translate_expr(expr: str) -> str:
    """
    Recursively translate a GP expression (string) into human-readable form.
    """
    expr = expr.strip()

    if expr in ARG_MAP:
        return ARG_MAP[expr]

    if re.match(r"^-?\d+(\.\d+)?$", expr):
        return expr

    if expr.isalpha():
        return expr

    m = re.match(r"([a-zA-Z_]+)\((.*)\)", expr)
    if not m:
        return expr

    func = m.group(1)
    inside = m.group(2)

    args = []
    depth = 0
    current = ""
    for c in inside:
        if c == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += c
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
    if current:
        args.append(current.strip())

    tr_args = [translate_expr(a) for a in args]

    if func in FUNC_MAP:
        fmt = FUNC_MAP[func]
        try:
            return fmt.format(*tr_args)
        except Exception:
            return f"{func}({', '.join(tr_args)})"

    return f"{func}({', '.join(tr_args)})"


def translate_results_in_memory(results):
    """
    Take the list of dicts returned by the GP engine and add a human-readable rule.
    """
    output = []
    for rec in results:
        tree = rec["tree"]
        human = translate_expr(tree)
        out_rec = {
            "tree": tree,
            "human_readable": human,
            "metrics": rec.get("metrics", {}),
        }
        # if fitness included, keep it
        if "fitness" in rec:
            out_rec["fitness"] = rec["fitness"]
        output.append(out_rec)
    return output

def convert_json_to_human_readable(input_json, output_json):
    with open(input_json, "r") as f:
        data = json.load(f)

    output = translate_results_in_memory(data)

    with open(output_json, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved translated strategies to: {output_json}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Translate GP trees into human-readable strategies.")
    parser.add_argument("--input", required=True, help="Path to GP results JSON (final.json)")
    parser.add_argument("--output", default="translated_strategies.json", help="Output file")

    args = parser.parse_args()

    convert_json_to_human_readable(args.input, args.output)

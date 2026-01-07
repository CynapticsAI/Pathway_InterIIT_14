import math
import operator
from deap import gp

class SCAL: pass
class VEC: pass
class BOOL: pass

def protected_div(a, b):
    try: return a / b
    except Exception: return 1.0

def vec_add(a, b): return [x+y for x,y in zip(a,b)]
def vec_sub(a, b): return [x-y for x,y in zip(a,b)]
def vec_mul(a, b): return [x*y for x,y in zip(a,b)]
def vec_div(a, b):
    out=[]
    for x,y in zip(a,b):
        out.append(x/y if (y!=0 and y!=0.0) else x)
    return out

def vec_mean(v): return float(sum(v)/len(v)) if len(v) else 0.0
def vec_std(v):
    import statistics
    return float(statistics.pstdev(v)) if len(v)>1 else 0.0
def vec_sum(v): return float(sum(v)) if len(v) else 0.0
def vec_max(v): return float(max(v)) if len(v) else 0.0
def vec_min(v): return float(min(v)) if len(v) else 0.0

def vec_sin(v): return [math.sin(x) for x in v]
def vec_cos(v): return [math.cos(x) for x in v]

def gt(a,b): return a > b
def lt(a,b): return a < b
def ge(a,b): return a >= b
def le(a,b): return a <= b
def eq(a,b): return a == b

def land(a,b): return bool(a) and bool(b)
def lor(a,b): return bool(a) or bool(b)
def lnot(a): return not bool(a)

def last_gt_mean(vec):
    """BOOL terminal: is latest close > vector mean?"""
    try:
        return vec[-1] > (sum(vec)/len(vec))
    except:
        return False

def create_pset():
    pset = gp.PrimitiveSetTyped(
        "MAIN",
        [VEC, VEC, VEC, VEC, SCAL, SCAL, SCAL, SCAL, SCAL],
        BOOL
    )

    pset.addPrimitive(operator.add, [SCAL,SCAL], SCAL)
    pset.addPrimitive(operator.sub, [SCAL,SCAL], SCAL)
    pset.addPrimitive(operator.mul, [SCAL,SCAL], SCAL)
    pset.addPrimitive(protected_div, [SCAL,SCAL], SCAL)
    pset.addPrimitive(operator.neg, [SCAL], SCAL)
    pset.addPrimitive(math.sin, [SCAL], SCAL)
    pset.addPrimitive(math.cos, [SCAL], SCAL)
    pset.addPrimitive(math.tanh, [SCAL], SCAL)
    pset.addPrimitive(abs, [SCAL], SCAL)

    pset.addPrimitive(vec_add, [VEC,VEC], VEC)
    pset.addPrimitive(vec_sub, [VEC,VEC], VEC)
    pset.addPrimitive(vec_mul, [VEC,VEC], VEC)
    pset.addPrimitive(vec_div, [VEC,VEC], VEC)
    pset.addPrimitive(vec_sin, [VEC], VEC)
    pset.addPrimitive(vec_cos, [VEC], VEC)

    pset.addPrimitive(vec_mean, [VEC], SCAL)
    pset.addPrimitive(vec_std, [VEC], SCAL)
    pset.addPrimitive(vec_sum, [VEC], SCAL)
    pset.addPrimitive(vec_max, [VEC], SCAL)
    pset.addPrimitive(vec_min, [VEC], SCAL)

    pset.addPrimitive(gt, [SCAL,SCAL], BOOL)
    pset.addPrimitive(lt, [SCAL,SCAL], BOOL)
    pset.addPrimitive(ge, [SCAL,SCAL], BOOL)
    pset.addPrimitive(le, [SCAL,SCAL], BOOL)
    pset.addPrimitive(eq, [SCAL,SCAL], BOOL)

    pset.addPrimitive(land, [BOOL,BOOL], BOOL)
    pset.addPrimitive(lor, [BOOL,BOOL], BOOL)
    pset.addPrimitive(lnot, [BOOL], BOOL)

    pset.addTerminal(last_gt_mean, BOOL)

    for c in [0.0, 1.0, -1.0, 2.0, -2.0, 0.5]:
        pset.addTerminal(float(c), SCAL)

    return pset

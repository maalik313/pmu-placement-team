"""Exact (MILP) PMU placement with the utility features TVA asks for. Solver: SciPy milp (HiGHS).

Variables: x_b = PMU at bus b;  o_b = bus b observed;  w_{z,b} = bus b observed through zero-injection bus z.
  direct:  o_b <= sum_{c in N[b]} x_c  (+ sum_z w_{z,b})
  ZIB:     w_{z,b} <= o_c for every c in N[z], c != b   (all the others in z's group are seen, so KCL gives b)
Modes
  full(zib=, n1=)          fewest PMUs so every bus is observed (n1: every bus seen twice -> survives one PMU loss)
  budget(k, zib=, weights) at most k PMUs, maximise priority-weighted observed buses
  critical(frac)           fewest PMUs: all buses seen once, the top `frac` by priority seen twice
Priorities follow NERC's Table 4 idea: priority(bus) = sum_app weight_app * serves(bus, app).
The `serves` rules below are OUR ASSUMPTIONS (no TVA data was shared): change them in APPS.
"""
import sys
from pathlib import Path
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
sys.path.insert(0, str(Path(__file__).parent))
from check import load_grid, seen_buses, is_valid

PMU_COST_USD = (40_000, 110_000, 180_000)   # low / mid / high installed cost, DOE 2014 range (track README)

# NERC Table 4 weights (10-point scale); `serves` = our assumption about which buses serve each application
APPS = {
    "state_estimation":   (8,  lambda g, b: True),
    "oscillation_mon":    (10, lambda g, b: b in g["generator_buses"]),
    "angle_monitoring":   (8,  lambda g, b: len(g["neighbors"][b]) >= 4),            # well-connected hubs
    "disturbance_mon":    (10, lambda g, b: g["load_mw"][str(b)] >= np.percentile(list(g["load_mw"].values()), 75)),
    "frequency_response": (5,  lambda g, b: b in g["generator_buses"]),
}

def priority(g):
    return {b: sum(w * bool(f(g, b)) for w, f in APPS.values()) for b in g["buses"]}

def _model(g, zib):
    buses = g["buses"]; n = len(buses); idx = {b: i for i, b in enumerate(buses)}
    N = [[idx[c] for c in sorted({b} | g["neighbors"][b])] for b in buses]
    Z = [idx[z] for z in g["zero_injection"]] if zib else []
    wvars = [(z, b) for z in Z for b in N[z]]                      # w_{z,b}
    nw = len(wvars); nv = 2 * n + nw + n; rows = []                 # rows: (coeffs dict, lb, ub); last n vars = inference order l_b
    wi = {k: 2 * n + i for i, k in enumerate(wvars)}; L0 = 2 * n + nw; Lmax = len(Z) + 1
    for b in range(n):                                              # o_b - sum x - sum w <= 0
        c = {n + b: 1}
        for j in N[b]: c[j] = c.get(j, 0) - 1
        for z in Z:
            if b in N[z]: c[wi[(z, b)]] = -1
        rows.append((c, -np.inf, 0))
    for (z, b), v in wi.items():                                    # w - o_c <= 0
        for c_ in N[z]:
            if c_ != b:
                rows.append(({v: 1, n + c_: -1}, -np.inf, 0))
                # order: b may be inferred from c_ only if c_ is established earlier (no circular reasoning)
                rows.append(({L0 + b: -1, L0 + c_: 1, v: Lmax}, -np.inf, Lmax - 1))
    return n, N, nv, rows

def _bounds(g, n, nv):
    ub = np.ones(nv); ub[2 * n:] = 1; nz = len(g["zero_injection"]); ub[nv - n:] = nz + 1   # order vars
    return np.zeros(nv), ub

def _solve(n, nv, rows, cobj, extra, lb, ub):
    A = lil_matrix((len(rows) + len(extra), nv)); lo, hi = [], []
    for r, (c, l, u) in enumerate(rows + extra):
        for j, v in c.items(): A[r, j] = v
        lo.append(l); hi.append(u)
    res = milp(cobj, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=np.ones(nv), bounds=Bounds(lb, ub))
    if res.x is None: return None
    return res.x

def full(g, zib=False, n1=False):
    n, N, nv, rows = _model(g, zib)
    if n1:   # every bus seen by >= 2 PMUs (no ZIB inference with N-1)
        rows = [({j: 1 for j in N[b]}, 2, np.inf) for b in range(n)]; nv = n
        x = _solve(n, nv, [], np.ones(nv), rows, np.zeros(nv), np.ones(nv))
    else:
        c = np.zeros(nv); c[:n] = 1
        lb, ub = _bounds(g, n, nv); lb[n:2 * n] = 1                 # all observed
        x = _solve(n, nv, rows, c, [], lb, ub)
    return None if x is None else [b for b, v in zip(g["buses"], x[:n]) if v > .5]

def budget(g, k, zib=False, weights=None):
    """Best coverage with k PMUs. weights: {bus: w}; default 1 each."""
    n, N, nv, rows = _model(g, zib); wt = weights or {b: 1 for b in g["buses"]}
    c = np.zeros(nv); c[n:2 * n] = [-wt[b] for b in g["buses"]]
    lb, ub = _bounds(g, n, nv)
    x = _solve(n, nv, rows, c, [({j: 1 for j in range(n)}, 0, k)], lb, ub)
    ch = [b for b, v in zip(g["buses"], x[:n]) if v > .5]
    return ch

def critical(g, frac=0.25):
    """Fewest PMUs: everyone seen once, the top `frac` buses by priority seen twice."""
    n, N, nv, rows = _model(g, False); pr = priority(g); k = max(1, int(round(frac * n)))
    top = set(sorted(g["buses"], key=lambda b: -pr[b])[:k])
    rows = [({j: 1 for j in N[i]}, 2 if b in top else 1, np.inf) for i, b in enumerate(g["buses"])]
    x = _solve(n, n, [], np.ones(n), rows, np.zeros(n), np.ones(n))
    return [b for b, v in zip(g["buses"], x[:n]) if v > .5], sorted(top)

def weighted_seen(g, chosen, pr, zib=False):
    s = seen_buses(g, chosen, zib); return sum(pr[b] for b in s), len(s)

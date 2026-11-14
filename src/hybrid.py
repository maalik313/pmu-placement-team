"""Hybrid classical/quantum PMU placement pipeline.

 1 classical  kernel:    degree-1 buses force a sensor on their neighbour (exact, safe)
 2 classical  partition: Kernighan-Lin bisection (NetworkX) into pieces of <= cap candidate sites
 3 per piece  solver:    'qaoa' (Qiskit QAOAAnsatz on Aer, CVaR) | 'random' | 'de' (SciPy differential evolution)
                         | 'exact' (brute force, upper bound on piece quality); every sampler gets the same `budget` samples
 4 classical  repair:    exact ILP (SciPy/HiGHS) covers whatever the pieces left unseen
 5 classical  prune:     drop sensors that are no longer needed;  the checker proves the final answer valid
Usage: python src/hybrid.py <grid> <solver> [cap] [seed]
"""
import itertools, sys, time, json
from pathlib import Path
import numpy as np
import networkx as nx
from networkx.algorithms.community import kernighan_lin_bisection
from scipy.optimize import milp, LinearConstraint, Bounds, minimize, differential_evolution
from qiskit import transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit_aer import AerSimulator
sys.path.insert(0, str(Path(__file__).parent))
from check import load_grid, is_valid
ROOT = Path(__file__).parent.parent
SIM = AerSimulator(method="statevector")
P_PEN = 2.0
QAOA_RESTARTS, QAOA_ITERS = 3, 100   # lowered by hybrid_big.py for 16-qubit pieces

# ---------- generic QAOA cost for "cover these targets using these sites" ----------
def op_from_groups(n, groups, P=P_PEN):
    terms = {}
    def add(q, c): terms[q] = terms.get(q, 0) + c
    for i in range(n): add((), .5); add((i,), -.5)
    for grp in groups:
        k = len(grp)
        for r in range(k + 1):
            for sub in itertools.combinations(grp, r): add(sub, P / 2 ** k)
    lab, co = [], []
    for qs, c in terms.items():
        if abs(c) < 1e-12: continue
        s = ["I"] * n
        for q in qs: s[n - 1 - q] = "Z"
        lab.append("".join(s)); co.append(c)
    return SparsePauliOp(lab, co).simplify()

def costs_from_groups(n, groups, P=P_PEN):
    z = np.arange(2 ** n, dtype=np.int64); bits = [((z >> i) & 1).astype(np.int8) for i in range(n)]
    cost = np.zeros(2 ** n)
    for b in bits: cost += b
    for g in groups:
        none = np.ones(2 ** n, dtype=bool)
        for j in g: none &= bits[j] == 0
        cost += P * none
    return cost

def cvar(p, c, a):
    o = np.argsort(c); pr, cc = p[o], c[o]; take = np.clip(a - (np.cumsum(pr) - pr), 0, pr); return take @ cc / a

def make_cvar(c):
    lev, inv = np.unique(c, return_inverse=True)
    def f(p, a):
        w = np.bincount(inv, weights=p, minlength=len(lev)); take = np.clip(a - (np.cumsum(w) - w), 0, w); return take @ lev / a
    return f

def qaoa_probs_fn(n, groups, reps):
    qc = QAOAAnsatz(op_from_groups(n, groups), reps=reps).decompose(reps=3); qc.save_statevector()
    qc = transpile(qc, SIM, optimization_level=1); pars = list(qc.parameters)
    return lambda th: np.abs(np.asarray(SIM.run(qc, parameter_binds=[dict(zip(pars, [[v] for v in th]))]).result().get_statevector())) ** 2

# ---------- per-piece solvers: each returns a bitstring index z, using <= budget samples ----------
def solve_piece(kind, n, groups, budget, rng, reps=2, alpha=0.25):
    c = costs_from_groups(n, groups)
    if kind == "exact": return int(np.argmin(c)), 0
    if kind == "random":
        z = rng.integers(0, 2 ** n, budget); return int(z[np.argmin(c[z])]), budget
    if kind == "de":
        best = [None, 1e9]; cnt = [0]
        def f(x):
            z = int(sum(int(round(v)) << i for i, v in enumerate(x))); cnt[0] += 1
            if c[z] < best[1]: best[:] = [z, c[z]]
            if cnt[0] >= budget: raise StopIteration
            return c[z]
        try: differential_evolution(f, [(0, 1)] * n, integrality=[True] * n, seed=int(rng.integers(1 << 30)), maxiter=10_000, popsize=5, tol=0, polish=False)
        except StopIteration: pass
        return best[0], budget
    if kind == "qaoa":
        probs = qaoa_probs_fn(n, groups, reps)
        cv = make_cvar(c); obj = lambda th: cv(probs(th), alpha); best = None
        for _ in range(QAOA_RESTARTS):
            r = minimize(obj, rng.uniform(0, np.pi, 2 * reps), method="COBYLA", options=dict(maxiter=QAOA_ITERS))
            best = r if best is None or r.fun < best.fun else best
        p = probs(best.x); p = p / p.sum()
        z = rng.choice(2 ** n, budget, p=p)                       # `budget` noise-free shots from the tuned circuit
        return int(z[np.argmin(c[z])]), budget
    raise ValueError(kind)

# ---------- the pipeline ----------
def kernel(g):
    N = {b: {b} | g["neighbors"][b] for b in g["buses"]}; forced, seen = set(), set(); ch = True
    while ch:
        ch = False
        for v in g["buses"]:
            if v not in seen and len(g["neighbors"][v]) == 1:
                nb = next(iter(g["neighbors"][v]))
                if nb not in forced: forced.add(nb); seen |= N[nb]; ch = True
    return forced, seen, N

def partition(G, nodes, cap):
    parts, out = [set(nodes)], []
    while parts:
        p = parts.pop()
        if len(p) <= cap or len(p) < 2: out.append(sorted(p))
        else: a, b = kernighan_lin_bisection(G.subgraph(p), seed=0); parts += [a, b]
    return out

def repair(g, seen, N):
    U = [b for b in g["buses"] if b not in seen]
    if not U: return []
    cand = sorted(set().union(*[N[u] for u in U]))
    A = np.array([[1 if c in N[u] else 0 for c in cand] for u in U])
    r = milp(np.ones(len(cand)), constraints=LinearConstraint(A, lb=1), integrality=np.ones(len(cand)), bounds=Bounds(0, 1))
    return [c for c, x in zip(cand, r.x) if x > .5]

def prune(g, chosen):
    chosen = list(chosen)
    for b in sorted(chosen, reverse=True):
        t = [c for c in chosen if c != b]
        if is_valid(g, t): chosen = t
    return chosen

def run(g, kind, cap=10, budget=200, seed=0, reps=2, verbose=False):
    rng = np.random.default_rng(seed); t0 = time.perf_counter()
    forced, seen, N = kernel(g); G = nx.Graph(g["lines"]); G.add_nodes_from(g["buses"])
    undominated = [b for b in g["buses"] if b not in seen]
    sites = sorted(set().union(*[N[u] for u in undominated])) if undominated else []
    qubits_total = len(sites); chosen = set(forced); qstage = 0; pieces = []; gaps = []
    for S in partition(G, sites, cap):
        T = [t for t in S if t not in seen]                                    # still-unseen buses inside this piece
        use = sorted({s for t in T for s in N[t] if s in S}); idx = {s: i for i, s in enumerate(use)}
        groups = [sorted(idx[s] for s in N[t] if s in idx) for t in T]; keep = [(t, gr) for t, gr in zip(T, groups) if gr]
        if not keep: continue
        groups = [gr for _, gr in keep]; n = len(use)
        z, _ = solve_piece(kind, n, groups, budget, rng, reps)
        cc = costs_from_groups(n, groups); gaps.append(float(cc[z] - cc.min())); del cc
        pick = [use[i] for i in range(n) if (z >> i) & 1]
        for s in pick: chosen.add(s); seen |= N[s]
        qstage += len(pick); pieces.append(n)
    unseen_after = len([b for b in g["buses"] if b not in seen]); rep = repair(g, seen, N); chosen |= set(rep)
    final = prune(g, chosen)
    assert is_valid(g, final), "pipeline produced an invalid placement"
    return dict(grid=g["name"], solver=kind, forced=len(forced), qubits_unreduced=len(g["buses"]), qubits_after_kernel=qubits_total,
                pieces=pieces, piece_cost_gap=round(sum(gaps), 2), unseen_after_pieces=unseen_after, from_pieces=qstage, repair_added=len(rep), before_prune=len(chosen), final=len(final),
                sec=round(time.perf_counter() - t0, 1))

if __name__ == "__main__":
    name, kind = sys.argv[1], sys.argv[2]; cap = int(sys.argv[3]) if len(sys.argv) > 3 else 10; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    print(json.dumps(run(load_grid(ROOT / f"data/{name}.json"), kind, cap, seed=seed)))

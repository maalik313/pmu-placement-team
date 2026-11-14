"""Tune QAOA on the exact statevector, report how often it finds an optimal / valid placement.
Usage: python src/run_qaoa.py   -> results/qaoa_sim.json"""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from qiskit import transpile
from qiskit_aer import AerSimulator
sim = AerSimulator(method='statevector')
sys.path.insert(0, str(Path(__file__).parent))
from qaoa_pmu import ansatz, brute_costs, cost_operator
from check import load_grid
ROOT = Path(__file__).parent.parent

def cvar(p, c, alpha):
    o = np.argsort(c); pr, cc = p[o], c[o]
    take = np.clip(alpha - (np.cumsum(pr) - pr), 0, pr)
    return take @ cc / alpha

def run(g, reps, alpha, seed=0, restarts=4, P=2.0):
    base = ansatz(g, reps, P)
    base = base.decompose(reps=3); base.save_statevector()
    qc = transpile(base, sim, optimization_level=1)          # transpiled once, parameters bound per call
    pars = list(qc.parameters); c = brute_costs(g, P)
    def probs(th):
        r = sim.run(qc, parameter_binds=[dict(zip(pars, [[v] for v in th]))]).result()
        return np.abs(np.asarray(r.get_statevector())) ** 2
    obj = lambda th: cvar(probs(th), c, alpha)
    rng = np.random.default_rng(seed); best = None
    for _ in range(restarts):
        r = minimize(obj, rng.uniform(0, np.pi, 2 * reps), method="COBYLA", options=dict(maxiter=120))
        if best is None or r.fun < best.fun: best = r
    p = probs(best.x); opt = c.min(); n = len(g["buses"])
    x = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).sum(1)
    valid = np.isclose(c, x)    # valid placement <=> no unseen bus <=> cost == number of sensors
    return dict(reps=reps, alpha=alpha, params=[float(v) for v in best.x], p_optimal=float(p[c == opt].sum()),
                p_valid=float(p[valid].sum()), rand_optimal=float((c == opt).mean()), rand_valid=float(valid.mean()),
                exp_cost=float(p @ c))

if __name__ == "__main__":
    out = {}
    for name, grid_reps in [("ieee14_piece6", [1, 2, 3]), ("ieee14", [1, 2])]:
        g = load_grid(ROOT / "data" / f"{name}.json")
        for reps in grid_reps:
            for alpha in (1.0, 0.25):
                t = time.perf_counter(); r = run(g, reps, alpha); r["sec"] = round(time.perf_counter() - t, 1)
                out[f"{name}|p={reps}|alpha={alpha}"] = r
                print(f"{name:14} p={reps} alpha={alpha:<4} P(optimal)={r['p_optimal']:.3f} (random {r['rand_optimal']:.3f})  "
                      f"P(valid)={r['p_valid']:.3f} (random {r['rand_valid']:.3f})  {r['sec']}s", flush=True)
    (ROOT / "results" / "qaoa_sim.json").write_text(json.dumps(out, indent=1))

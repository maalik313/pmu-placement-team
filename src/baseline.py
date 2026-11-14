"""Classical baselines on every grid: greedy, exact ILP (SciPy/HiGHS), and the N-1 (seen twice) ILP.
Run:  python src/baseline.py   -> prints a table and writes results/baseline.json"""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
sys.path.insert(0, str(Path(__file__).parent))
from check import load_grid, is_valid

ROOT = Path(__file__).parent.parent

def cover_matrix(g):
    b = g["buses"]
    return np.array([[1 if c == r or c in g["neighbors"][r] else 0 for c in b] for r in b])

def ilp(g, twice=False):
    A = cover_matrix(g); n = len(g["buses"])
    res = milp(np.ones(n), constraints=LinearConstraint(A, lb=2 if twice else 1),
               integrality=np.ones(n), bounds=Bounds(0, 1))
    return [b for b, x in zip(g["buses"], res.x) if x > .5]

def greedy(g):
    chosen, unseen = [], set(g["buses"])
    while unseen:
        b = max(g["buses"], key=lambda b: len(({b} | g["neighbors"][b]) & unseen))
        chosen.append(b); unseen -= {b} | g["neighbors"][b]
    return chosen

if __name__ == "__main__":
    out = {}
    print(f"{'grid':13}{'buses':>6}{'greedy':>8}{'ILP':>5}{'ILP ms':>8}{'N-1 ILP':>9}{'N-1 ms':>8}")
    for name in ["ieee14_piece6", "ieee14", "ieee30", "ieee57", "ieee118", "ieee300"]:
        g = load_grid(ROOT / "data" / f"{name}.json")
        gr = greedy(g)
        t = time.perf_counter(); e = ilp(g); t1 = 1000 * (time.perf_counter() - t)
        t = time.perf_counter(); e2 = ilp(g, twice=True); t2 = 1000 * (time.perf_counter() - t)
        assert is_valid(g, e) and is_valid(g, e2, n1=True)
        out[name] = dict(buses=len(g["buses"]), greedy=gr, ilp=e, ilp_ms=t1, n1=e2, n1_ms=t2)
        print(f"{name:13}{len(g['buses']):6}{len(gr):8}{len(e):5}{t1:8.1f}{len(e2):9}{t2:8.1f}")
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "baseline.json").write_text(json.dumps(out, indent=1))

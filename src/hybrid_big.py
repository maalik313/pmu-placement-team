"""Bigger pieces (up to 23 qubits): QAOA vs random vs SciPy DE at equal budget (200 samples/piece). python src/hybrid_big.py"""
import json, sys, statistics as st
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import hybrid
from hybrid import run, load_grid, ROOT
hybrid.QAOA_RESTARTS, hybrid.QAOA_ITERS = 1, 30
base = json.loads((ROOT / "results/baseline.json").read_text()); rows = []
for name, cap, nq in [("ieee30", 24, 5), ("ieee57", 14, 4), ("ieee118", 14, 3)]:
    g = load_grid(ROOT / f"data/{name}.json"); opt = len(base[name]["ilp"])
    for kind, seeds in [("exact", 1), ("random", 10), ("de", 10), ("qaoa", nq)]:
        rs = [run(g, kind, cap, seed=s, reps=1) for s in range(seeds)]
        m = lambda k: st.mean(r[k] for r in rs)
        row = dict(grid=name, cap=cap, solver=kind, optimum=opt, pieces=rs[0]["pieces"], seeds=seeds, finals=[r["final"] for r in rs],
                   piece_cost_gap=[r["piece_cost_gap"] for r in rs], unseen_after_pieces=[r["unseen_after_pieces"] for r in rs],
                   repair_added=[r["repair_added"] for r in rs], before_prune=[r["before_prune"] for r in rs], sec=round(m("sec"), 1))
        rows.append(row)
        print(f"{name:8}pieces={row['pieces']} {kind:7} final {st.mean(row['finals']):5.1f} ({min(row['finals'])}-{max(row['finals'])}, opt {opt}) | "
              f"piece-cost gap {st.mean(row['piece_cost_gap']):4.1f} | unseen after pieces {st.mean(row['unseen_after_pieces']):4.1f} | "
              f"repair added {st.mean(row['repair_added']):3.1f} | {row['sec']}s/run", flush=True)
        (ROOT / "results/hybrid_big.json").write_text(json.dumps(rows, indent=1))

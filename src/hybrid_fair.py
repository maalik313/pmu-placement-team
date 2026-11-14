"""Fair control: give random / DE the SAME total sample budget QAOA effectively uses (30 tuning evals x 1000 shots + 200 final = 30,200)."""
import json, sys, statistics as st
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hybrid import run, load_grid, ROOT
rows = []
for name, cap in [("ieee30", 24), ("ieee57", 14), ("ieee118", 14)]:
    g = load_grid(ROOT / f"data/{name}.json")
    for kind in ("random", "de"):
        rs = [run(g, kind, cap, seed=s, reps=1, budget=30_200) for s in range(10)]
        row = dict(grid=name, solver=kind, budget=30_200, finals=[r["final"] for r in rs], piece_cost_gap=[r["piece_cost_gap"] for r in rs])
        rows.append(row)
        print(f"{name:8}{kind:7} budget 30,200: final {st.mean(row['finals']):5.1f} ({min(row['finals'])}-{max(row['finals'])}) | piece-cost gap {st.mean(row['piece_cost_gap']):4.1f}", flush=True)
(ROOT / "results/hybrid_fair.json").write_text(json.dumps(rows, indent=1))

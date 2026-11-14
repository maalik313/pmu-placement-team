"""Ablation: same hybrid pipeline, different piece solver, equal sample budget (200 per piece). python src/hybrid_study.py"""
import json, sys, statistics as st
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hybrid import run, load_grid, ROOT
base = json.loads((ROOT / "results/baseline.json").read_text())
rows = []
for name in ["ieee30", "ieee57", "ieee118"]:
    g = load_grid(ROOT / f"data/{name}.json"); opt = len(base[name]["ilp"])
    for cap in (6, 10):
        for kind, seeds in [("exact", 1), ("qaoa", 6), ("random", 6), ("de", 6)]:
            rs = [run(g, kind, cap, seed=s) for s in range(seeds)]
            rows.append(dict(grid=name, cap=cap, solver=kind, optimum=opt, finals=[r["final"] for r in rs],
                             from_pieces=[r["from_pieces"] for r in rs], repair=[r["repair_added"] for r in rs],
                             before_prune=[r["before_prune"] for r in rs], pieces=rs[0]["pieces"], q_after_kernel=rs[0]["qubits_after_kernel"],
                             sec=round(st.mean(r["sec"] for r in rs), 1)))
            r = rows[-1]
            print(f"{name:8}cap={cap:2} {kind:7} final {st.mean(r['finals']):5.1f} (opt {opt}, min {min(r['finals'])}, max {max(r['finals'])})  "
                  f"before-prune {st.mean(r['before_prune']):5.1f}  repair-added {st.mean(r['repair']):4.1f}  pieces {len(r['pieces'])}  {r['sec']}s", flush=True)
(ROOT / "results/hybrid_study.json").write_text(json.dumps(rows, indent=1))

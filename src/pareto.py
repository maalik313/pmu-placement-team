"""Cost vs functionality vs redundancy trade-offs. Writes results/pareto.json. python src/pareto.py"""
import json, sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pmu_milp import *
ROOT = Path(__file__).parent.parent
out = {}
for name in ["ieee14", "ieee30"]:
    g = load_grid(ROOT / f"data/{name}.json"); pr = priority(g); n = len(g["buses"]); tot = sum(pr.values())
    kfull = len(full(g)); rows = []
    for k in range(1, kfull + 1):
        for zib in (False, True):
            for tag, w in (("count", None), ("priority", pr)):
                ch = budget(g, k, zib=zib, weights=w)
                wsn, ns = weighted_seen(g, ch, pr, zib)
                rows.append(dict(k=k, zib=zib, objective=tag, chosen=ch, buses_seen=ns, weighted_seen_pct=round(100 * wsn / tot, 1),
                                 cost_usd_mid=k * PMU_COST_USD[1]))
    fz, f1 = full(g, zib=True), full(g, n1=True); cr, top = critical(g)
    f = full(g)
    def worst_loss(ch, zib=False):   # most buses left unseen if one PMU fails
        return max(n - len(seen_buses(g, [c for c in ch if c != lost], zib)) for lost in ch)
    out[name] = dict(buses=n, priority=pr, budget_rows=rows,
        full=dict(plain=f, zib=fz, n1=f1, critical=cr, critical_top=top),
        worst_single_failure_unseen=dict(plain=worst_loss(f), zib=worst_loss(fz, True), n1=worst_loss(f1), critical=worst_loss(cr)),
        cost_usd=dict({k_: [len(v) * c for c in PMU_COST_USD] for k_, v in dict(plain=f, zib=fz, n1=f1, critical=cr).items()}))
    print(f"\n== {name} ({n} buses)   PMU cost range ${PMU_COST_USD[0]//1000}k-${PMU_COST_USD[2]//1000}k each (DOE 2014)")
    print(f"{'design':26}{'PMUs':>5}{'cost @ $110k':>14}{'worst loss if 1 PMU dies':>28}")
    for lab, ch, z in [("full coverage", f, False), ("full + zero-injection", fz, True), ("critical x2 (top 25%)", cr, False), ("N-1: all x2", f1, False)]:
        print(f"{lab:26}{len(ch):5}{'$%.2fM' % (len(ch) * .11):>14}{str(worst_loss(ch, z)) + ' buses unseen':>28}")
    print("budget curve (weighted-priority objective, with ZIB):  k -> buses seen / priority-weighted %")
    for r in rows:
        if r["zib"] and r["objective"] == "priority": print(f"   k={r['k']}: {r['buses_seen']}/{n} buses, {r['weighted_seen_pct']}% of priority  at {r['chosen']}")
(ROOT / "results/pareto.json").write_text(json.dumps(out, indent=1))

"""Evidence for the quantum-vs-classical discussion. Writes results/advantage.json.  python src/advantage.py"""
import json, sys, time, math
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution
from qiskit import transpile
sys.path.insert(0, str(Path(__file__).parent))
from qaoa_pmu import ansatz, brute_costs
from baseline import ilp
from check import load_grid
ROOT = Path(__file__).parent.parent
out = {}

# 1) Shots to see an optimal placement with 99% confidence (TTS99), from the Aer sweep (ideal, noise-free)
sw = json.loads((ROOT / "results/qaoa_sim.json").read_text()); tts = {}
for k, v in sw.items():
    q, r = v["p_optimal"], v["rand_optimal"]
    tts[k] = dict(qaoa_shots=math.ceil(math.log(.01) / math.log(1 - q)), random_shots=math.ceil(math.log(.01) / math.log(1 - r)),
                  p_optimal=q, rand=r)
out["tts99"] = tts

# 2) Equal-effort comparison on IEEE 14: SciPy differential evolution (stock discrete heuristic) vs QAOA, in cost evaluations
g = load_grid(ROOT / "data/ieee14.json"); c = brute_costs(g); opt = c.min(); n = 14
class Hit(Exception): pass
def de_evals(seed):
    cnt = [0]
    def f(x):
        cnt[0] += 1; z = int(sum(int(round(v)) << i for i, v in enumerate(x))); val = c[z]
        if val == opt: raise Hit
        return val
    try: differential_evolution(f, [(0, 1)] * n, integrality=[True] * n, seed=seed, maxiter=500, popsize=10, tol=0, polish=False)
    except Hit: return cnt[0]
    return None
ev = [de_evals(s) for s in range(30)]; got = [e for e in ev if e]
out["de_evals_to_optimum_14"] = dict(found=f"{len(got)}/30", median=float(np.median(got)) if got else None, max=max(got) if got else None)

# 3) Honest total cost of QAOA on hardware, including tuning (COBYLA ~120 iters x 4 restarts x S shots per cost estimate)
S = 1000; tune = 4 * 120 * S
out["hardware_total_shots_estimate"] = dict(shots_per_cost_estimate=S, tuning_shots=tune, note="the Aer runs used the exact statevector, which a QPU cannot")

# 4) Resource scaling: qubits and CX gates of a p=1 circuit vs the exact ILP time
scale = []
for name in ["ieee14_piece6", "ieee14", "ieee30"]:
    gg = load_grid(ROOT / f"data/{name}.json"); t = time.perf_counter(); ilp(gg); ms = 1000 * (time.perf_counter() - t)
    qc = ansatz(gg, 1).decompose(reps=3).assign_parameters([.3, .3])
    t = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=1)
    scale.append(dict(grid=name, qubits=len(gg["buses"]), cx_p1=t.count_ops().get("cx"), depth=t.depth(), ilp_ms=round(ms, 1)))
    print(scale[-1], flush=True)
out["scaling"] = scale
(ROOT / "results/advantage.json").write_text(json.dumps(out, indent=1))
for k in ["ieee14_piece6|p=1|alpha=0.25", "ieee14|p=2|alpha=0.25", "ieee14|p=2|alpha=1.0"]:
    t = tts[k]; print(f"TTS99 {k}: QAOA {t['qaoa_shots']} shots vs random {t['random_shots']}")
print("DE evals to optimum on IEEE14:", out["de_evals_to_optimum_14"])

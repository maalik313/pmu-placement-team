# How we talk about quantum vs classical for PMU placement

**Bottom line (what our data supports):** on this problem, classical wins today. Exact ILP solves IEEE 300 in ~17 ms. QAOA's *final sampling* is much better than random and needs fewer samples than a stock classical heuristic, but that is before counting the tuning cost, and it never beats the exact solver. We report that plainly; the value is knowing where, and under what conditions, that could change.

## Questions judges will ask, and where our numbers are
| Question | Metric | Our data | Where |
|---|---|---|---|
| Does QAOA find good answers? | P(optimal), P(valid) vs random | IEEE14 p=2 CVaR: 7.1% optimal vs 0.031% random (~234x) | `results/qaoa_sim.json` |
| How many samples to see an optimum? (TTS99) | shots for 99% confidence | QAOA 63 shots vs random 15,088 (IEEE14 p=2) | `results/advantage.json` |
| Versus a real classical heuristic? | cost evaluations to optimum | SciPy differential evolution: median 630 evals (30/30 seeds) | `results/advantage.json` |
| Versus the exact solver? | wall time | ILP: 7 ms (14 bus), 8 ms (30), 17 ms (300) | `results/baseline.json` |
| What does QAOA really cost? | total shots incl. tuning | ~480,000 shots if each cost estimate takes 1,000 shots (our Aer runs used the exact statevector, which a QPU cannot) | `results/advantage.json` |
| Does it fit the hardware? | qubits / CX gates, p=1 | 6 bus: 34 CX, 14 bus: 540, 30 bus: 2,678 (hardware handles a few dozen) | `results/advantage.json` |
| Does it survive noise? | same circuit, 6-bus, 200 shots | ideal 21% optimal, IonQ-Forte-noise sim 13.5%, H2 emulator 18.5%, random 1.6% | `results/run_record.md` |

## Framing, in order
1. **Be precise about "advantage".** We tested (a) answer quality, (b) samples needed, (c) total resources, (d) scaling. We did **not** find a speedup or a quality win over the exact solver, and the track README says not to credit quantum for what the ILP already does.
2. **What is true:** QAOA concentrates probability on optimal placements far above chance, and keeps most of that under hardware-like noise on the 6-bus piece.
3. **What is not (yet):** 14 buses already needs ~540 CX per layer, 30 buses ~2,700, so only small pieces run on today's hardware; and tuning on a QPU costs ~10^5-10^6 shots.
4. **Where it could matter (hypotheses, not results):** much larger or more constrained variants (N-1 + weights + budget at interconnection scale) if exact methods get slow; better hardware (fewer errors, more two-qubit gates); problems where cost evaluation is itself expensive. Cite Jones et al. 2020 (D-Wave: competitive on some instances, not all, vs CPLEX) and Jiang et al. 2025 (hybrid QAOA, IEEE 9/14/24/30).
5. **The honest customer message:** use the ILP for TVA's actual placement; the real cost is installation ($40k-$180k per PMU, device <5%), communications and timing, not the choice of locations.

## Using the NERC guideline (Dec 2016)
- **Two goals** (NERC p.30ish): *minimum PMUs for full observability* (`full()`), or *most observability for a fixed number* (`budget()`). Both implemented in `src/pmu_milp.py`.
- **Prioritisation matrix (Table 4, from PG&E):** priority(location) = sum(weight x applies). We use NERC's example weights (state estimation 8, oscillation 10, angle 8, disturbance 10, frequency response 5). **Which buses serve which application is our assumption** (generators -> oscillation/frequency, hubs -> angle, heavy loads -> disturbance); TVA shared no bus-level data. Ask a TVA mentor to replace it.
- **Redundancy:** "Redundant PMUs and communication paths can help ensure observability" (NERC). Implemented as N-1 (every bus seen twice) and a cheaper *critical-bus* version (top 25% by priority seen twice).
- **Zero-injection buses:** MILP with inference-order variables (so no circular reasoning); verified against `check.py` on IEEE 14/30/57/118.
- **Realities NERC lists that placement does not capture:** GPS/IEEE 1588 timing within ~5 us, 20-50 ms fiber latency, weeks of commissioning, cybersecurity, data storage. Say what TVA would check beyond our model.

## Results of the optimisation study (`results/pareto.json`, `src/pareto.py`)
IEEE 14 (priority-weighted, PMU cost mid-case $110k, DOE range $40k-$180k):
| Design | PMUs | Cost | Worst case if one PMU fails |
|---|---|---|---|
| Full observability | 4 | $0.44M | 4 buses unseen |
| + zero-injection rule | 3 | $0.33M | 5 buses unseen |
| Critical buses seen twice | 5 | $0.55M | 3 buses unseen |
| N-1 (all seen twice) | 9 | $0.99M | 0 unseen |
Fewest PMUs is the *least* robust design: each design trades cost against redundancy. Budget curve: with 2 PMUs we see 11/14 buses (85% of priority); 3 PMUs (zero-injection) see everything.
IEEE 30: 10 / 7 (ZIB) / 14 (critical x2) / 21 (N-1) PMUs.
Minimum with the zero-injection rule: IEEE 14: 3, 30: 7, 57: 11, 118: 30 (vs 4, 10, 17, 32 without).

## Open items
- Replace the application-to-bus assumptions with TVA input.
- QAOA versions of the budget / N-1 / critical formulations (cost function: P x (2 - sightings)).
- Hardware: optional real QPU run of the 6-bus piece (credits; confirm price first).
- Sample-based tuning (shots, not statevector) on the 6-bus piece to measure real tuning cost.


## Hybrid pipeline (`src/hybrid.py`, `src/hybrid_study.py`, `results/hybrid_study.json`)
Classical kernel (degree-1 rule) -> classical partition (Kernighan-Lin, pieces of <=10 sites) -> **per-piece solver** -> classical ILP repair -> classical prune -> checker proves validity. Every solver gets the same 200 samples per piece; 6 seeds each (noise-free Aer shots for QAOA, p=2, CVaR 0.25). All final placements passed the checker.
Final PMU count, piece size cap 10, mean (min-max over seeds):

| grid | exact optimum | per-piece exact (floor of this decomposition) | QAOA | random | SciPy DE |
|---|---|---|---|---|---|
| ieee30 | 10 | 10.0 (10-10) | 10.5 (10-11) | 10.7 (10-11) | 10.5 (10-11) |
| ieee57 | 17 | 19.0 (19-19) | 19.3 (19-20) | 18.3 (18-20) | 18.8 (18-20) |
| ieee118 | 32 | 36.0 (36-36) | 36.5 (34-39) | 36.2 (35-38) | 35.5 (33-37) |

**What this shows (and does not):**
1. **No quantum advantage here.** QAOA is statistically indistinguishable from random sampling and SciPy differential evolution (seed spread is as large as the differences). On IEEE 57 and 118 it was slightly worse on average.
2. **Why:** the pieces are 5-10 qubits (32-1,024 bitstrings), so 200 random samples already cover a large share of each piece's search space. There is nothing for quantum to speed up at this size.
3. **The real loss is the decomposition, not the solver.** Even solving every piece *exactly* gives 19 / 36 instead of 17 / 32 on IEEE 57 / 118, because cutting the grid ignores sensors that serve two pieces. A global classical re-optimisation closes that gap; the quantum step cannot.
4. **What hybrid does buy:** the circuit size. Pieces of <=10 qubits need far fewer gates than the 14-30 qubit full circuits (see Resource scaling above), which is what current hardware can run.
5. Honest pitch line: *the hybrid design is the only way to fit this problem on today's quantum hardware, and it preserves validity (checker-proven); it does not (yet) improve answers, and our ablation shows where it would have to.*


## Bigger pieces, with a fair control (`src/hybrid_big.py`, `src/hybrid_fair.py`)
Pieces now up to 23 qubits (IEEE 30 as one piece: 8.4M bitstrings; IEEE 57/118: 13-14 qubits). QAOA p=1, CVaR 0.25, 30 tuning evaluations on the exact statevector, then 200 noise-free shots. Entries: mean final PMU count (mean **piece-cost gap**: how far the piece answer was from that piece's optimum, measured *before* the ILP repair and prune can hide it). QAOA: 5/4/3 seeds; classical: 10 seeds.

| grid (pieces) | optimum | QAOA, 200 shots | random, 200 | DE, 200 | random, 30,200 | DE, 30,200 |
|---|---|---|---|---|---|---|
| ieee30 (1 x 23 qubits) | 10 | 10.0 (gap 0.4) | 10.4 (gap 2.4) | 10.6 (gap 2.5) | 10.0 (gap 0.1) | 10.0 (gap 0.0) |
| ieee57 (4 x ~14) | 17 | 18.2 (gap 1.2) | 18.8 (gap 4.3) | 19.3 (gap 3.0) | 17.9 (gap 0.1) | 18.1 (gap 0.4) |
| ieee118 (8 x ~13) | 32 | 34.0 (gap 1.3) | 37.0 (gap 6.9) | 36.3 (gap 4.9) | 35.2 (gap 0.0) | 35.1 (gap 0.0) |

**Reading it honestly:**
1. **At equal final samples (200), QAOA wins clearly at piece level:** gap 0.4 / 1.2 / 1.3 versus 2.4-6.9 for random and 2.5-4.9 for DE. Random sampling cannot search 8.4M bitstrings with 200 draws; QAOA's tuned circuit concentrates probability on good ones. This is the only place we saw a quantum benefit.
2. **At equal *total* budget it disappears.** QAOA also needed ~30 tuning evaluations; on a QPU that is roughly 30 x 1,000 = 30,000 shots. Give random and DE the same 30,200 samples and their piece gap falls to ~0-0.4 and their final counts match or beat QAOA (IEEE 30: 10.0 vs 10.0; IEEE 57: 17.9 / 18.1 vs 18.2). 
3. **Not explained:** on IEEE 118 QAOA's final count (34.0, 3 seeds) beat the controls (35.1-35.2), even though its piece-level gap was worse. The sequential decomposition is path-dependent, so we do not claim this as a quantum effect; more seeds are needed.
4. **Caveats that favour QAOA here and would not survive hardware:** tuning used the exact probability vector (a QPU only gives shots); circuits were noise-free; a classical sample is a lookup costing microseconds, a quantum sample is a real shot. And the exact ILP gets the optimum in ~8 ms, so none of this beats the baseline TVA already has.
5. **Defensible claim:** *with a small sample budget, QAOA is a much better sampler than random search or a stock heuristic on a 23-qubit search space; once total cost is counted fairly, classical sampling catches up. We found no end-to-end advantage.*

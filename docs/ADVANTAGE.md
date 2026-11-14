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

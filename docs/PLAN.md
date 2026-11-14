# Plan: engineering design process applied to PMU sensor placement

Deadline: **Sunday Nov 15, 9:00 AM** (deck + code ZIP). Qbraid check-in Sat 7 PM. Send hardware runs **today**.

## Conceptual design (draft: team edits every line marked *guess*)
| Step | Draft content |
|---|---|
| Background | TVA must see its whole grid in real time. PMUs (phasor measurement units) give time-synced measurements; installed cost is ~$40k-$180k each (DOE 2014), the device itself <5% of that. NERC *Reliability Guideline: PMU Placement and Installation* (2016) is TVA's reference. |
| Problem | Fewest substations to instrument so every substation is observable (minimum dominating set). |
| Needs | An exact/trusted count, a placement that survives a failed PMU, proof the method scales to TVA-size grids, an honest quantum-vs-classical comparison. |
| Goal | Deliver a validated minimum-cost PMU placement for IEEE 14/30 (stretch: 57/118/300) and an evidence-based answer to "does quantum help here?". |
| Objectives | (1) classical baseline, (2) quantum formulation (QAOA), (3) verify on simulators/emulator/QPU, (4) add utility realities: zero-injection buses, N-1, budget, priority weights, (5) communicate to a utility decision-maker. |
| Design specs (technical) | Every bus observed (coverage = 100%); sensor count = domination number; optional: observed after any single PMU loss; circuit <= few dozen CX for hardware; one qubit per bus; results reproducible (seeded, run record kept). |
| Constraints (non-technical) | Budget (credits, ~500 available); 200-shot cap per hardware run; weekend deadline; open data only; team of 5; must use qBraid. |
| Social impact | Reliability of power for customers; faster detection of cascading outages. |
| Environmental impact | Fewer devices installed; better visibility helps integrate renewables. Quantum compute energy: negligible at this scale *(guess; cite if used)*. |
| Codes & standards | NERC PMU guideline, IEEE C37.118.1/.2 (synchrophasor measurement and data transfer), IEEE test cases (MATPOWER). |
| Relevant theory | ILP: min sum x_b s.t. A x >= 1 (A = adjacency + I). QUBO/Ising cost C(x)=sum x_b + P*sum_b prod_{j in N[b]}(1-x_j), P>1. QAOA: alternate e^{-i gamma C} and e^{-i beta X}. ZIB rule via Kirchhoff's current law. N-1: A x >= 2. |
| System-level alternatives | A greedy heuristic, B exact ILP, C QAOA (gate model), D quantum annealing (D-Wave, Jones et al. 2020), E hybrid: ILP/classical result as warm start or check for QAOA. |
| Decision matrix | See below. |
| Proposed design | **Hybrid pipeline:** exact ILP is the reference; QAOA (CVaR) is the quantum candidate, verified against it on simulators then hardware; a checker validates every answer. |
| Decomposition | (a) grid data + checker, (b) classical solvers, (c) cost function/circuit builder, (d) QAOA optimizer loop, (e) backend runner (Aer / IonQ sim / H2 emulator / QPU), (f) analysis + visual dashboard. |

### Weighted decision matrix (scores 1-5 are **guesses**: re-score as a team, then argue each)
| Criterion | Weight | Greedy | ILP | QAOA | Annealer | Hybrid |
|---|---|---|---|---|---|---|
| Solution quality (optimal?) | 0.30 | 2 | 5 | 3 | 3 | 5 |
| Scales to TVA-size grids | 0.20 | 5 | 5 | 1 | 2 | 4 |
| Runs on available hardware now | 0.15 | 5 | 5 | 3 | 1 | 3 |
| Handles ZIB / N-1 / weights | 0.15 | 2 | 5 | 3 | 3 | 5 |
| Insight on quantum value (the question asked) | 0.20 | 1 | 1 | 5 | 4 | 5 |
| **Weighted** | | 2.65 | 3.80 | 3.00 | 2.60 | **4.30** |
(Compute the sums yourselves before presenting; edit the weights to reflect the customer.)

## Preliminary design -> detailed design = TVA milestones M1-M6
Iterate: build on Aer -> compare with ILP -> add noise (IonQ sim) -> emulator (H2) -> QPU.

## Verification ladder with qBraid (cheapest first)
| Rung | Backend | Cost | Question it answers |
|---|---|---|---|
| 1 | Qiskit Aer, local | free | Is the cost layer right? (`check_cost_layer`) Does QAOA beat random guessing? |
| 2 | `ionq:ionq:sim:simulator`, `noise_model: forte-1` | free | Does it survive realistic Forte gate noise? |
| 3 | `quantinuum:quantinuum:sim:h2-emulator` (accept terms under Devices first) | free | Second noise model; 1-4 min/job. Label "emulator". |
| 4 | `qbraid:qbraid:sim:gpu-sv` (<=35 qubits) | free to a daily limit, then 5 cr/min | IEEE 30 with sampled shots |
| 5 | `ionq:ionq:qpu:forte-1`, piece6, <=200 shots | credits: **confirm price with `qbraid jobs`/estimate and a mentor first** | Real hardware vs simulator |
Fallbacks: `aws:ionq:qpu:forte-1` (~1,630 cr, too pricey for us), Rigetti Cepheus (~40 cr), IQM Garnet (~60 cr).
Record every job: device, job ID, shots, status, label (simulator/emulator/QPU) in `results/run_record.md`.

## What the research says (use as the "state of the art" slide)
- Jones et al. 2020 (arXiv 2001.04489): D-Wave annealing on PMU placement; competitive on some instances, not all, vs CPLEX.
- Jiang, Liang, Li, Morstyn, IEEE Trans. Smart Grid 16(4), 2025: hybrid QAOA for PMU placement with classical DFS/BFS observability checks, tested on IEEE 9/14/24/30.
- PESGM 2025: QAOA for max observability under a PMU budget (our "fixed budget" stretch).
- SCOOP (2025): QAOA framework for constrained problems incl. Minimum Dominating Set (classical post-processing of an unconstrained twin).
Honest framing: exact ILP solves IEEE 300 in ~17 ms; quantum is not faster here. Value = understanding where it could matter (budgeted/N-1/weighted variants at larger scale, hardware growth).

## Work split (5 people)
| # | Role | Owns | Done when |
|---|---|---|---|
| 1 | **Systems lead + story** | This conceptual-design doc, decision matrix, customer/value (ask a TVA mentor), the 5-slide deck, rehearsal | deck done by Sun 7 AM |
| 2 | **Classical + stretch** | M1-M2, `src/baseline.py`, ZIB / N-1 / fixed budget / priority weights, IEEE 30/57/118/300 timings | table of counts + ms for all grids |
| 3 | **Quantum core** | M3-M4: TODOs in starter, QAOA on piece6 and 14, layers/alpha/P sweep, QAOA vs random chart | outcome charts + hit-rate numbers |
| 4 | **Backends + hardware** | M5: IonQ sim (noise), H2 emulator, IonQ Forte run (Sat), GPU sim for IEEE 30, run record | job IDs + sim-vs-hardware chart |
| 5 | **Visuals + integration + qBraid Award** | Interactive explorer (`docs/placement_explorer.html`), what-if-sensor-fails view, dashboard, repo hygiene, ZIP, award slides/video | ZIP tested; award entry submitted |
Everyone reads the NERC guideline summary and can explain the cost function in plain words (judges ask).

## Do we need IEEE 14?
Yes: it is the benchmark TVA's starter uses, small enough for exact brute force (verifies everything), 14 qubits fit a simulator, and its 6-bus piece fits hardware. Also use IEEE 30 (GPU sim) and, classically, 57/118/300 (TVA pointed to them).

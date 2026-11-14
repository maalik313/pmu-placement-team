# PMU sensor placement: Tennessee Quantum Hackathon 2026 (TVA track)

Team repo. Start with [`docs/PLAN.md`](docs/PLAN.md). Open [`docs/placement_explorer.html`](docs/placement_explorer.html) for the interactive grid.
Plain-language explainer (PMUs, quantum, QAOA, with a live simulation of our 6-substation circuit): https://claude.ai/artifact/3Uba2JuS4UzxmKwUaebFGj (private until shared). Pitch deck source: [`docs/deck/`](docs/deck/).

```
data/       IEEE 14 / 6-bus piece / 30 / 57 / 118 / 300 grids (from the track repo)
src/        check.py (validity checker), baseline.py (greedy + exact ILP + N-1)
notebooks/  starter + QAOA primer (use the qBraid-SDK v0.12.2 kernel)
results/    baseline.json, run_record.md (every qBraid job ID)
docs/       PLAN.md, placement_explorer.html
```
Run baselines: `python src/baseline.py`.

## Baseline results (exact ILP via SciPy/HiGHS)
| grid | buses | greedy | exact | N-1 | exact time |
|---|---|---|---|---|---|
| IEEE 14 | 14 | 5 | **4** (3 with zero-injection rule) | 9 | 6 ms |
| IEEE 30 | 30 | 10 | 10 | 21 | 9 ms |
| IEEE 57 | 57 | 18 | 17 | 33 | 27 ms |
| IEEE 118 | 118 | 36 | 32 | 68 | 37 ms |
| IEEE 300 | 300 | 96 | 87 | 202 | 17 ms |

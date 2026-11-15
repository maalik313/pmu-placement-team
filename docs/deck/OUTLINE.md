# Pitch outline: Team Tiger Qubits (fits the Five Slide Template)

Audience rule: someone who has never heard of quantum should follow every slide. One idea per slide, plain words, one number to remember. Quantum terms are explained in a clause, never assumed.

Design process (from docs/PLAN.md) mapped onto the template's five slides:

| Template slide | Design-process steps it carries | Plain-language question it answers |
|---|---|---|
| 01 The Problem | Background, Problem, Needs, Constraints | What is broken, and why does it cost TVA? |
| 02 Ideal Customer | Stakeholders, Goal, Social impact | Who decides, who benefits, why would they say yes? |
| 03 Solution & Technology | Objectives, Specs, Alternatives + decision matrix, Proposed design, Verification | What did we build, and how do we know it works? |
| 04 The Team | Decomposition / work split | Who did which piece? |
| 05 What We Learned | Test results, Verdict, Next iteration | What is true, what surprised us, what next? |

## Slide 1: The Problem
Headline: **TVA must see its whole grid in real time, and every sensor is expensive.**
1. The problem: choose the fewest substations to fit with a phasor measurement unit (PMU, a GPS-timed sensor) so every substation is observable.
2. Why it matters: a PMU installs for about $40k-$180k, so the count is real money; fewer sensors also means less coverage if one fails.
3. What is inadequate: the textbook answer (IEEE 14 needs 4 sensors) hides the trade-off: the cheapest design is the least robust. Seeing every bus twice costs 9 sensors, more than double.
Visual: the IEEE 14 table (4 / 3 / 5 / 9 sensors, cost, buses unseen if one fails).

## Slide 2: Ideal Customer
- Who buys: a transmission utility. TVA first; any utility following the NERC PMU guideline.
- Who uses it: grid planning engineers; the decision maker is the planning/operations lead who owns the sensor budget.
- Why they say yes: a placement they can verify (checker proves coverage), cost vs redundancy options priced up front, and an honest answer on whether quantum is worth paying for. *Ask a TVA mentor to confirm; flagged as our assumption.*

## Slide 3: Solution & Technology
1. Method and why it fits: the problem is a yes/no choice per substation, which a quantum algorithm (QAOA) can search many options at once. Alternatives compared on a weighted decision matrix; hybrid scored highest (4.50 vs exact solver 4.20; team judgement, not measured).
2. Build: hybrid pipeline: shrink, split into pieces, quantum search per piece, classical repair, checker proves every answer valid.
3. Status: verified cheapest first: simulator, IonQ-noise simulator, Quantinuum emulator, **real Rigetti Cepheus QPU (done)**, IonQ Forte QPU (queued as of this draft; update before presenting).
Visual: the 5-step pipeline strip plus the verification ladder with checkmarks.

## Slide 4: The Team
Five people, five roles (from the work split): systems lead + story, classical + stretch, quantum core, backends + hardware, visuals + integration. **Needs real names, expertise and what each built.**

## Slide 5: What We Learned
- Validated: exact solver gives the true minimum for IEEE 14-300 in milliseconds; QAOA finds optimal answers far above chance (234x on IEEE 14) and survives noise; real hardware run: **43% valid, 5% optimal vs 1.6% random guessing** (Cepheus, 200 shots).
- Surprised us: no quantum speedup. Once tuning cost is counted fairly, random search catches up; the classical exact solver wins today.
- Next: quantum versions of the harder variants (every bus seen twice, weighted, budgeted) on larger grids and better hardware.
One-line takeaway: *Use the exact solver for TVA's placement today; here is exactly where quantum could matter next.*

## Open items before presenting
- Real team names, expertise, contributions (slide 4).
- Forte result: update slide 3 and 5 when the job completes, otherwise say "queued, not run".
- Confirm customer assumptions with a TVA mentor (slide 2).
- Decide whether to rebuild the existing Slides artifact in this 5-slide structure (cover + 5) or keep the current one.

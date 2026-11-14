"""QAOA for PMU placement, built from Qiskit's own QAOAAnsatz (no hand-written cost layer).

Cost  C(x) = sum_b x_b + P * #unseen,  unseen_b = prod_{j in N[b]} (1 - x_j),  one qubit per bus.
With x = (1 - Z)/2:  (1 - x_j) = (1 + Z_j)/2, so the penalty expands into a SparsePauliOp.
"""
import itertools, sys
from pathlib import Path
import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
sys.path.insert(0, str(Path(__file__).parent))
from check import load_grid, bits_to_buses

def groups(g):
    idx = {b: i for i, b in enumerate(g["buses"])}
    return [sorted(idx[c] for c in {b} | g["neighbors"][b]) for b in g["buses"]]

def cost_operator(g, P=2.0):
    n = len(g["buses"]); terms = {}
    def add(qs, c):
        terms[qs] = terms.get(qs, 0) + c
    for i in range(n):                       # sensors: x_i = (1 - Z_i)/2
        add((), .5); add((i,), -.5)
    for grp in groups(g):                    # P * prod (1+Z_j)/2
        k = len(grp)
        for r in range(k + 1):
            for sub in itertools.combinations(grp, r):
                add(sub, P / 2 ** k)
    lab, co = [], []
    for qs, c in terms.items():
        if abs(c) < 1e-12: continue
        s = ["I"] * n
        for q in qs: s[n - 1 - q] = "Z"      # Qiskit: qubit 0 is the rightmost character
        lab.append("".join(s)); co.append(c)
    return SparsePauliOp(lab, co).simplify()

def brute_costs(g, P=2.0):
    """Cost of every bitstring; index z has qubit i = bit i of z (Qiskit order)."""
    n = len(g["buses"]); grp = groups(g)
    z = np.arange(2 ** n)
    x = ((z[:, None] >> np.arange(n)) & 1)
    unseen = sum((x[:, gr].sum(1) == 0).astype(int) for gr in grp)
    return x.sum(1) + P * unseen

def ansatz(g, reps, P=2.0):
    return QAOAAnsatz(cost_operator(g, P), reps=reps)   # params: betas then gammas

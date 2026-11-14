"""Send the tuned 6-bus QAOA circuit to a qBraid device, save counts, append to results/run_record.md.
Usage: python src/run_backend.py <device_id> <label: simulator|emulator|QPU> [shots<=200]
Free: ionq:ionq:sim:simulator, quantinuum:quantinuum:sim:h2-emulator.  QPUs cost credits: ask first."""
import sys, json, datetime, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from qaoa_pmu import ansatz
from check import load_grid, check_placement, bits_to_buses
from qiskit import transpile
from qbraid.runtime import QbraidProvider
ROOT = Path(__file__).parent.parent
dev_id, label = sys.argv[1], sys.argv[2]; shots = min(int(sys.argv[3]) if len(sys.argv) > 3 else 200, 200)
g = load_grid(ROOT / "data/ieee14_piece6.json")
par = json.loads((ROOT / "results/piece6_p1_params.json").read_text())["params"]
qc = ansatz(g, 1).assign_parameters(par); qc.measure_all()
qc = transpile(qc, basis_gates=["rz", "sx", "x", "cx"], optimization_level=3)
dev = QbraidProvider().get_device(dev_id)
opts = {"noise_model": "forte-1"} if dev_id == "ionq:ionq:sim:simulator" else {}
job = dev.run(qc, shots=shots, runtime_options=opts) if opts else dev.run(qc, shots=shots)
print("job", job.id, flush=True)
res = job.result(); counts = res.data.get_counts()
tag = dev_id.split(":")[-1]
(ROOT / f"results/counts_{tag}.json").write_text(json.dumps(dict(job=job.id, device=dev_id, label=label, shots=shots, counts=counts), indent=1))
with open(ROOT / "results/run_record.md", "a") as f:
    f.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | {dev_id} | {label} | {job.id} | {shots} | {job.status().name} | 6-bus QAOA p=1 CVaR, 28 CX |\n")
tot = sum(counts.values()); ok = opt = 0
for k, c in counts.items():
    b = bits_to_buses(g, k.replace(" ", "")[::-1]); r = check_placement(g, b, show=False)
    ok += c * r["valid"]; opt += c * (r["valid"] and len(b) == 2)
print(f"{dev_id}: valid {ok/tot:.1%}, optimal(2 sensors) {opt/tot:.1%}  (ideal sim: valid 48.7%, optimal 21.1%; random: 48.4%, 1.6%)")

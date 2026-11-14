"""Fetch a finished qBraid job by ID, save counts, log it. Usage: python src/fetch_job.py <job_id> <label> [timeout_s]"""
import sys, json, time, datetime, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from check import load_grid, check_placement, bits_to_buses
from qbraid.runtime import QbraidProvider
ROOT = Path(__file__).parent.parent
jid, label = sys.argv[1], sys.argv[2]; limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
dev_id = jid.split("-0add-qjob-")[0] if "-qjob-" in jid else jid.rsplit("-", 2)[0]
prov = QbraidProvider(); dev = prov.get_device(dev_id); job = prov.get_job(jid) if hasattr(prov, "get_job") else __import__("qbraid.runtime", fromlist=["load_job"]).load_job(jid)
t = time.time()
while job.status().name not in ("COMPLETED", "FAILED", "CANCELLED") and time.time() - t < limit: time.sleep(5)
st = job.status().name; print("status", st)
if st != "COMPLETED": sys.exit(1)
counts = job.result().data.get_counts(); shots = sum(counts.values()); tag = dev_id.split(":")[-1]
(ROOT / f"results/counts_{tag}.json").write_text(json.dumps(dict(job=jid, device=dev_id, label=label, shots=shots, counts=counts), indent=1))
with open(ROOT / "results/run_record.md", "a") as f:
    f.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | {dev_id} | {label} | {jid} | {shots} | {st} | 6-bus QAOA p=1 CVaR, 28 CX |\n")
g = load_grid(ROOT / "data/ieee14_piece6.json"); ok = opt = 0
for k, c in counts.items():
    b = bits_to_buses(g, k.replace(" ", "")[::-1]); r = check_placement(g, b, show=False)
    ok += c * r["valid"]; opt += c * (r["valid"] and len(b) == 2)
print(f"{dev_id}: valid {ok/shots:.1%}, optimal {opt/shots:.1%} ({shots} shots)")

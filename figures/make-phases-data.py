"""Regenerate phases.dat (eight-panel CCC vs CDR figure) and print Table values from phases-inputs.json.

Run from any directory: python3 figures/make-phases-data.py
Compile phases.tex from figures/ with pdflatex to rebuild the figure.
Inputs are per-training-seed means produced by eval-phases.py (64 paired trials per seed).
"""
import json

from scipy import stats
import math
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "phases-inputs.json").read_text())
T3 = 3.182  # t(3), four independent training seeds, as in pool_seeds.py
METRICS = ("mae", "mean_h", "trapped", "rich")


def ci(values):
    return st.mean(values), T3 * st.stdev(values) / math.sqrt(len(values))


def pval(values):
    """Two-sided one-sample t-test on per-seed differences (df = 3)."""
    se = st.stdev(values) / math.sqrt(len(values))
    return 2 * stats.t.sf(abs(st.mean(values) / se), len(values) - 1)


cols = ["phase"] + [f"{f}{m}{a}{s}" for f in ("HRL", "NF") for m in METRICS for a in ("ccc", "cdr") for s in ("", "CI")]
lines = [" ".join(cols)]
for k in range(3):
    row = [str(k + 1)]
    for f in ("HRL", "NF"):
        for m in METRICS:
            for arm in ("CCC", "CDR"):
                mean, half = ci([s[f][arm][m][k] for s in data["seeds"]])
                row += [f"{mean:.6f}", f"{half:.6f}"]
    lines.append(" ".join(row))
(HERE / "phases.dat").write_text("\n".join(lines) + "\n")

for f in ("HRL", "NF"):
    print(f)
    for m, k in (("mae", 2), ("trapped", 2), ("mean_h", 2), ("rich", 1), ("rich", 2)):
        c = [s[f]["CCC"][m][k] for s in data["seeds"]]
        x = [s[f]["CDR"][m][k] for s in data["seeds"]]
        diffs = [b - a for a, b in zip(c, x)]
        d, h = ci(diffs)
        print(f"  {m} phase {k + 1}: CCC {st.mean(c):.2f}  CDR {st.mean(x):.2f}  diff {d:.2f} [{d - h:.2f}, {d + h:.2f}]  p {pval(diffs):.4f}")

# HRL vs NF: per-seed CDR - CCC effect on phase-3 mean absolute h, HRL minus NF
eff = {f: [s[f]["CDR"]["mae"][2] - s[f]["CCC"]["mae"][2] for s in data["seeds"]] for f in ("HRL", "NF")}
dd = [a - b for a, b in zip(eff["HRL"], eff["NF"])]
d, h = ci(dd)
print(f"HRL minus NF, mae phase 3: {d:.2f} [{d - h:.2f}, {d + h:.2f}]  p {pval(dd):.4f}")

"""Regenerate performance.dat from the retained evaluation summaries (standard library only).

Run from any directory: python3 figures/make-performance-data.py
Compile performance.tex from figures/ with pdflatex to rebuild the figure.
Export the paper's tracked PNG with:
    pdftoppm -r 300 -singlefile -png performance.pdf performance
The input snapshot records source paths and SHA-256 hashes for provenance.
"""
import json
import math
from pathlib import Path
import statistics as st

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "performance-inputs.json").read_text())
# Match pool_seeds.py and the manuscript: t(3), four independent training seeds.
T3 = 3.182
lines = ["phase HRLccc HRLcccCI HRLcdr HRLcdrCI NFccc NFcccCI NFcdr NFcdrCI"]
for phase in range(3):
    row = [str(phase + 1)]
    for family in ("HRL", "NF"):
        for arm in ("CCC", "CDR"):
            values = [seed[family][arm][phase] for seed in data["seeds"]]
            half_width = T3 * st.stdev(values) / math.sqrt(len(values))
            row.extend((f"{st.mean(values):.6f}", f"{half_width:.6f}"))
    lines.append(" ".join(row))
(HERE / "performance.dat").write_text("\n".join(lines) + "\n")
for family in ("HRL", "NF"):
    differences = [seed[family]["CDR"][2] - seed[family]["CCC"][2] for seed in data["seeds"]]
    mean = st.mean(differences)
    half_width = T3 * st.stdev(differences) / math.sqrt(len(differences))
    print(f"{family} phase-3 paired difference: {mean:.2f} [{mean-half_width:.2f}, {mean+half_width:.2f}]")

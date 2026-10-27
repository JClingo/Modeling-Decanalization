# Incorporation of the corrected October 2026 trials

**Historical analysis:** the subsequent anticipation repair and policy selection
changed the primary findings. See [the corrected-anticipation analysis](../anticipation2026/README.md)
and its proposed paper revisions. This folder retains the earlier implementation's
results for comparison; the manuscript has not yet incorporated that later update.

The manuscript and appendix now use the corrected primary analysis from source
commit `018ccb4` of the decanalization repository. `source_manifest.json` records
the full revision, source path, and hashes of copied analysis evidence.

## What changed in the paper

- Replaced exponential HRL shaping with the ongoing proximity objective and
  replaced the old NF punishment rule with the executed nonnegative rule.
- Updated live-state observations, training failure boundary, effective PPO
  configurations (including NFStable1), and selected HRL 10000 / NF 5000 snapshots.
- Updated the environment, fixed phase timing, trial counts, memory resets,
  homeostatic reinitialization, and verified primary traversal-count factor **0**.
- Replaced all primary and early-phase numerical tables and outcome plots.
  Corrected metrics distinguish MAE, population SD, RMS, signed mean, near-setpoint
  sample fraction, and actual objective reward.
- Replaced paired-only / Cohen's d reporting with the primary Welch differences,
  unadjusted confidence intervals, and Holm adjustments; retained paired analyses
  as sensitivity evidence and qualified exact initial-scene matching.
- Revised the abstract, discussion, conclusion, and AI-use disclosure. Higher NF
  reward is distinguished from improved regulation. No reward-by-intervention
  interaction or superiority across training seeds is claimed.
- Kept traversal factors 4/6/7 as archived sensitivity evidence with legacy
  measurement definitions. Older screenshots are explicitly illustrative.

## Reproduction and verification

Raw inputs, snapshot binaries, completion receipts, and the 3,000 compressed
scene records remain in the source repository at:

`/Users/jingo/Work/PhD/Dissertation Project/decanalization/analysis/paper-update-2026-10-17-reruns`

This folder copies compact tables and provenance rather than duplicating the
75 MB source package. The primary reproduction pipeline is that package's
`build_analysis.py`, `build_supplement.py`, and `write_report.py` (NumPy, SciPy,
PyYAML, and Matplotlib required). The `MANUSCRIPT_EDITS.md`, `RESULTS.md`, and
`CHANGE_INVENTORY.md` copies preserve the source package's editorial evidence;
they are not a second current manuscript.

`verify_analysis.py` is an independent standard-library verification route:

```sh
python3 revisionPlan/rerun2026/verify_analysis.py \
  '/Users/jingo/Work/PhD/Dissertation Project/decanalization/analysis/paper-update-2026-10-17-reruns'
```

It checks loaded snapshot and logger hashes, scene hashes, 1,000 complete trials,
all 3,000 phase records, YAML/sidecar agreement, primary zero visit-count factors,
baseline matching, descriptive statistics, Welch and paired contrasts, intervals,
and Holm corrections. It normalizes Windows relative paths for local use and
never modifies source data. `verification.json` records the result of this check.

The two replacement figures are regenerated at manuscript width from
`phase_summary.csv` using base R:

```sh
Rscript --vanilla revisionPlan/rerun2026/plot_results.R .
```

Build the manuscript with `zsh .vscode/build-latex`. The output is
`out/modelingDecanalization.pdf`.

## Remaining reporting limits

The selected 2026 snapshots' detailed network parameter counts, exact achieved
training-transition totals, and selected-run episode-buffer cap are not newly
established by this package. Historical 2025 values are not silently reused.
The seven resource-ray features retain an existing author comment requesting a
more precise semantic description. Repeated trials evaluate selected policies;
they do not estimate variation across independent training seeds.

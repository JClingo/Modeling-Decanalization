# Counting-rate × post-decanalization retention interaction

The completed 2 × 3 HRL evaluation crosses counting at 1× or 7× during
decanalization with resetting, halving and flooring, or keeping all counts
afterward. Counting before/after remains 1×. Each of six CDR cells and the
shared CCC reference contains 250 trials under the same selected fixed policy.
Two new batches added 500 trials; four CDR cells and CCC were reused.

[Full results](RESULTS.md) do not establish a rate-by-retention interaction
for absolute setpoint error or received reward after the planned six-test
Holm adjustment. Paired and baseline-change sensitivities agree. This does
not establish independence or equivalence. The main paper condition remains
1×/half-floor. See [proposed manuscript additions](MANUSCRIPT_ADDITIONS.md).

Both variants passed 15 real Blueprint handler checks before scoring.
All 1,500 new scene hashes, six loaded inference snapshot files, durable
completion receipts and compiled tile hashes passed verification. Production
source hashes are preserved. Independent R reproduced every summary,
interaction, simple effect, CCC contrast and sensitivity calculation.

`ANALYSIS_PLAN.md` was frozen before the two new scored batches. This is an
author-approved exploratory extension after the earlier separate sweeps,
not a preregistered experiment or a comparison across trained-policy seeds.

Reproduce from the frozen compact inputs:

```sh
python3 revisionPlan/anticipation2026/interaction/analyze.py
XDG_CACHE_HOME=/tmp/codex-r-cache Rscript --vanilla revisionPlan/anticipation2026/interaction/verify_and_plot.R revisionPlan/anticipation2026/interaction
python3 revisionPlan/anticipation2026/interaction/write_report.py
```

The two figures are `factorial_response.pdf`/`.png` and
`interaction_contrasts.pdf`/`.png`. Points show condition means or interaction
estimates with unadjusted 95% confidence intervals. The response figure's
dashed line and gray band show the CCC mean and its confidence interval.

The full local archive is `reproducible-results.zip`; `bundle_manifest.json`
records its identity and CRC verification. It preserves the analysis hierarchy,
raw data for all seven conditions, compiled variants, selected policy,
source assets, native logs, protocol and orchestration code. This local archive
has not been published. Verify compact-input portability with:

```sh
python3 revisionPlan/anticipation2026/interaction/verify_portability.py
```

`portability_validation.json` records whether a fresh extraction regenerates
all eight numerical tables byte for byte. For the full native rerun, see
`run_experiment.py`; native preparation uses isolated scratch project copies.
The completed native run is `/private/tmp/anticipation-interaction-20261026`.
To refresh the frozen native inputs, pass `--import-run` with that path to
`analyze.py`; routine reproduction does not need that external directory.

Archive receipt (added after sealing): 96,308,232 bytes, 5,601 members, CRC verified. SHA-256:
`64eae037ce902bc12cba22767f05b500e99faa6c68d66b80e7ae5011345ef428`. Fresh-extraction portability passed: all eight regenerated CSVs are byte-identical.

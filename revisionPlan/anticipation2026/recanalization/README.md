# Post-decanalization tile-count comparison

This extension varies the transformation of stored tile counts at recanalization,
holding HRL policy weights and counting at one per entry fixed. It is distinct
from the earlier sweep of counting rates during decanalization.

Approved conditions: zero, quarter-floor, half-floor (current),
three-quarter-floor, keep all counts, and half-exact (no flooring). Compare
250 trials per CDR condition with the existing 250-trial CCC control.

**Completed and independently verified:** [RESULTS.md](RESULTS.md) contains all
comparisons; [MANUSCRIPT_ADDITIONS.md](MANUSCRIPT_ADDITIONS.md) supplies proposed
paper text. No tested rule establishes a phase-3 MAE or reward difference from
CCC after the twelve-test Holm adjustment, or from current half-floor under
the separate ten-test adjustment. This does not establish equivalence.

- `retention_response.pdf` / `.png`: phase-3 means with CCC reference.
- `ccc_contrasts.pdf` / `.png`: CDR-minus-CCC differences and 95% intervals.
- `post_table_rows.tex`: supplement-ready endpoint comparisons.
- `phase_summary.csv`, `primary_contrasts.csv`, `versus_current.csv`,
  `all_pairwise.csv`, `sensitivity.csv`: full numerical results.
- `PARAMETER_SEMANTICS.md`: transformations and why flooring matters.
- `source_manifest.json`, `verification.json`, `r_verification.txt`: checks.

`ANALYSIS_PLAN.md` records outcomes, comparisons, multiplicity and limitations
before the new outcomes. `run_experiment.py` creates isolated copies under
`/private/tmp/anticipation-recanalization-20261026`. Production assets and policy
selection are preserved. Native completion receipts, graph-handler checks,
scene/model hashes and independent statistical verification passed. The main
paper condition stays half-floor.

The first smoke trial passed 15 real Blueprint handler checks and a complete
6,000-decision evaluation. Its wrapper initially expected an optional final
observer tick after native completion had already saved the receipt and quit;
receipt verification recovered the complete smoke data without rerunning it.
One disposable editor also stalled during concurrent startup, before generating
scored trials. `recover_zero.py` preserves its logs, repeats that audit, and
completes zero and half-exact while the other three batches keep running. A
resource check supports a fifth independent native copy for half-exact; this
changes concurrency only. Both setup diagnostics remain in the native folder.

Once native completion is verified, reproduce and independently check results:

```sh
python3 revisionPlan/anticipation2026/recanalization/analyze.py --import-run /private/tmp/anticipation-recanalization-20261026
XDG_CACHE_HOME=/tmp/codex-r-cache Rscript --vanilla revisionPlan/anticipation2026/recanalization/verify_and_plot.R revisionPlan/anticipation2026/recanalization
python3 revisionPlan/anticipation2026/recanalization/write_report.py
python3 revisionPlan/anticipation2026/recanalization/package_results.py
```

Routine reproduction after import omits `--import-run`; frozen compact inputs
remain usable without external native files.

The completed local archive is `reproducible-results.zip`: 97,204,872 bytes,
5,615 members, CRC checked. SHA-256:
`4ba0c2c8d7ccbd9e3e9358a7c6e99941beda6862357c7ff23baaebf8d43a9fe7`.
It preserves raw scenes, captured policies, variant assets, native logs and
the analysis hierarchy. The earlier traversal-factor archive is separate.
`bundle_manifest.json` records its identity; `portability_validation.json`
confirms that extracting the archived analysis and running from frozen inputs
reproduces all eight numerical CSVs byte-for-byte. These external validation
receipts and this archive note were written after packaging; the archived
analysis itself already passed its native and independent R checks.

# Current primary HRL analysis

Use factor-1 CDR versus CCC. Actual entry increments are 1 before, during and
after decanalization. Recanalization still applies `floor(n/2)` once.

- [RESULTS.md](RESULTS.md): all nine outcomes, sensitivities and paper prose.
- [selection.json](selection.json): actual run identities and parameter semantics.
- `hrl_post_table_rows.tex`: primary phase-3 table rows.
- `post_outcomes.pdf` / `.png`, `phase_outcomes.pdf` / `.png`: HRL figures.
- `trial_metrics.csv`, `phase_summary.csv`, `primary_contrasts.csv`,
  `sensitivity.csv`: reproducible statistics.
- `verification.json`, `r_verification.txt`, `source_manifest.json`: checks.

Reproduce from the frozen inputs in the parent and `../plasticity/`:

```sh
python3 revisionPlan/anticipation2026/primary-factor1/analyze.py
XDG_CACHE_HOME=/tmp/codex-r-cache Rscript --vanilla revisionPlan/anticipation2026/primary-factor1/verify_and_plot.R revisionPlan/anticipation2026/primary-factor1
python3 revisionPlan/anticipation2026/primary-factor1/write_report.py
```

The [author's design clarification](../PRIMARY_DESIGN_CLARIFICATION.md) records
why factor 1 is primary. The frozen sweep plan and earlier reports are preserved.
Factors 0, 2, 4 and 7 remain sensitivity evidence. NF's available corrected CDR
batch used factor 0 and is excluded from this HRL-only primary analysis.

# Corrected anticipation: analysis and proposed paper changes

**Current primary HRL analysis: [factor 1 versus CCC](primary-factor1/RESULTS.md).**
The author confirmed the original intent of one count per tile entry in all
three phases. Recanalization still halves counts once. Factors 0, 2, 4 and 7
are sensitivity conditions. See [the recorded clarification](PRIMARY_DESIGN_CLARIFICATION.md).

A separate [completed recanalization-count comparison](recanalization/RESULTS.md) tests
retaining 0%, 25%, 50%, 75% or 100% of counts at the phase-3 transition, plus
halving without flooring. It holds counting at one per entry throughout. This
varies a different operation from the completed during-decanalization factor
sweep. None of the six rules establishes a post-intervention MAE or reward
difference from CCC or the current rule after adjustment. The primary
half-floor paper condition is retained; proposed supplement text is in
`recanalization/MANUSCRIPT_ADDITIONS.md`.

Use `primary-factor1/hrl_post_table_rows.tex` and the figures/CSVs in that
directory for HRL. Its README gives the reproduction commands. The primary
HRL MAE difference is −3.686, 95% CI [−9.722, 2.349]; the reward difference is
0.615, 95% CI [−1.796, 3.026]. Both remain uncertain.

**NF status:** the existing corrected NF CDR evaluation used factor 0. It is
reference evidence and cannot be represented as a matching factor-1 primary
result. The factor-1 primary package is explicitly HRL-only.

The author-approved [factorial interaction comparison](interaction/RESULTS.md)
is complete: 1× versus 7× counting crossed with reset, half-floor and full
retention, 250 trials per cell. None of the six direct interaction tests or
paired/baseline-change sensitivities establishes an interaction after Holm
adjustment. Keeping all rather than half-floor changes the reward rate effect
by −1.467, 95% CI [−4.859, 1.924]. This leaves interactions uncertain; it does
not establish independence or equivalence. The main condition stays 1×/half-floor.
See `interaction/MANUSCRIPT_ADDITIONS.md` for proposed supplement text.

This package supersedes `../rerun2026/` for the corrected Unreal anticipation
implementation. The manuscript source and existing manuscript figures are
preserved. `MANUSCRIPT_EDITS.md` now recommends factor 1 for HRL.

The subsequent [HRL traversal-factor sweep](plasticity/RESULTS.md) is also
complete: factors 0/1/2/4/7, 250 trials per factor, frozen HRL weights, and CCC
reference. It substantially changes retained tile counts but does not establish
a post-intervention performance difference across the examined factors.

The following **root-level numerical artifacts retain the earlier factor-0
comparison** for reproducibility; they are not the current primary HRL tables:

- `RESULTS.md`: historical old/new comparison, post-intervention results, phase means,
  sensitivity analyses, interpretation and limits.
- `MANUSCRIPT_EDITS.md`: section-specific recommendations and replacement prose.
- `post_outcomes.pdf` / `.png`: proposed main-text figure.
- `phase_outcomes.pdf` / `.png`: full three-phase figure.
- `hrl_post_table_rows.tex` / `nf_post_table_rows.tex`: nine-outcome replacement rows.
- `trial_metrics.csv`, `phase_summary.csv`, `primary_contrasts.csv`,
  `sensitivity.csv`, `old_vs_new.csv`: reproducible numerical evidence.
- `inputs/`: frozen raw JSON/YAML sidecars, completion receipts and compact
  implementation/selection evidence (about 12 MB). Scene and model binaries
  remain in the external reproducibility archive.
- `source_manifest.json`, `source_audit.json`, `verification.json`,
  `r_verification.txt`: hashes and completed verification checks.

Reproduce those historical factor-0 tables with the following commands. For
the current primary HRL tables use `primary-factor1/README.md` instead:

```sh
python3 revisionPlan/anticipation2026/build_analysis.py
Rscript --vanilla revisionPlan/anticipation2026/verify_and_plot.R revisionPlan/anticipation2026
python3 revisionPlan/anticipation2026/write_report.py
```

On a restricted host, set `XDG_CACHE_HOME` to an available writable directory
before running R if Fontconfig cannot write its cache.

To repeat the external scene/model audit and refresh the frozen inputs, use:

```sh
python3 revisionPlan/anticipation2026/build_analysis.py --import-source \
  '/Users/jingo/Work/PhD/Dissertation Project/decanalization/analysis/anticipation-retrained-2026-10-25'
```

The import checks all 3,000 decompressed scene hashes, eight selected snapshot
files and twelve actually loaded inference snapshot files. It records that
phase-start total tile counts range from 0 to 4, consistent with freshly reset
trial maps rather than cumulative wear across trials. Routine reproduction
verifies all frozen input hashes; it does not claim to recheck absent external
scene/model files.

The historical factor-0 inference retains the manuscript's Welch comparisons
and 18-test Holm families. The current HRL-only primary family has nine outcomes.
The earlier delivery's bootstrap baseline-change contrasts are retained as
separate sensitivity evidence. Neither analysis is preregistered; evaluation
trials are not independently trained policy replicates.

The full portable experiment archive is:

`/Users/jingo/Work/PhD/Dissertation Project/decanalization/Saved/AnticipationRetrain20261025/reproducible-results.zip`

Archive size: 128,420,526 bytes; 5,452 members. SHA-256:
`d3a1e3c3983715fa411a1bb9ae1a28b4a297f6c04950d78865746ca7d2bbfe50`.
It contains the repaired asset, selected models, raw scenes, logs, checkpoints,
protocol and orchestration sources. It is currently local, not a published
paper supplement. The existing Unreal submodule in the manuscript checkout is
an older source revision and was not silently updated.

# HRL traversal-factor experiment

**Primary designation:** the author has confirmed factor 1 as the original
intended primary HRL condition, with factor 0 and 2/4/7 retained as sensitivity
conditions. Use [the primary analysis](../primary-factor1/RESULTS.md) for its
nine-outcome table. The original hashed `ANALYSIS_PLAN.md` is preserved; the
subsequent decision is in [the design clarification](../PRIMARY_DESIGN_CLARIFICATION.md).
The sweep's historical contrast-family names and CSV filenames remain unchanged
so the original numerical analysis is reproducible.

The factor controls the number of counted visits per actual tile entry during
decanalization: 0 disables counting, 1 retains ordinary counting, and 2/4/7
accelerate it. The policy is the selected fresh HRL checkpoint at 750,000
transitions, evaluated with corrected anticipation and frozen weights.

Each factor has 250 three-phase trials. Factor-0 CDR and uninterrupted CCC reuse
the verified original reference batches. Four new native batches add 1,000 trials.
Results are written only after all requested native trials and checks complete;
`postprocess_status.json` records the current analysis state.

- `ANALYSIS_PLAN.md`: factors, outcomes, comparisons, uncertainty and limitations,
  written before inspecting the new outcomes.
- `RESULTS.md`: final interpretation, relative performance and statistical tables.
- `factor_response.pdf` / `.png`: post-intervention outcomes across factors;
  dashed lines and shaded bands show the CCC reference.
- `relative_response.pdf` / `.png`: relative improvement over normal counting.
- `phase_outcomes.pdf` / `.png`: full phase-level outcomes.
- `trial_metrics.csv`, `phase_summary.csv`, `primary_contrasts.csv`,
  `factor_pairwise.csv`, `relative_bootstrap.csv`, `sensitivity.csv`: full evidence.
- `landscape_counts.csv`: mean/min/max total tile counts at phase starts.
- `inputs/`, `source_manifest.json`, `verification.json`, `r_verification.txt`:
  compact raw inputs, source hashes and checks.

Reproduce the completed analysis from frozen inputs:

```sh
python3 revisionPlan/anticipation2026/plasticity/analyze.py
Rscript --vanilla revisionPlan/anticipation2026/plasticity/bootstrap_and_plot.R revisionPlan/anticipation2026/plasticity
python3 revisionPlan/anticipation2026/plasticity/write_report.py
```

First import or repeat the full reference-scene audit with:

```sh
python3 revisionPlan/anticipation2026/plasticity/analyze.py --import-run \
  '/Users/jingo/Work/PhD/Dissertation Project/decanalization/Saved/AnticipationPlasticity20261026'
```

The native run folder preserves full raw scene records, captured weights,
completion receipts, logs, per-condition verification and isolated project
copies. The runner initially schedules two workers; `parallel_extra.py` starts
two additional independent copies, pausing only the original queue dispatcher
and resuming it after the queued conditions finish. Native evaluation processes
continue throughout. This changes concurrency, not simulated timesteps or
experimental settings. `complete.json` is written by the original dispatcher
only after all four conditions pass and source-project hashes are checked.

`count_rule_native.py` and its launcher audit the real Blueprint overlap and
count-halving handlers in separate transient editor actors. They do not alter
production trials. The initial commandlet attempt lacked editor placement
facilities and crashed before generating scored data; that attempt's logs are
preserved under the run's `count-audit/commandlet-attempt-*` files. The editor
audit passed all 17 checks and records its result in `count_rule_validation.json`.
The editor-launch callback setup failure is also preserved in the attempt logs;
neither setup attempt generated scored trial data or affected the four batches.

This is a sensitivity analysis of environmental history under one selected
policy. It does not establish neural plasticity, an optimal factor, or
generalization across independent training seeds. Legacy factor experiments
used earlier observation code/policies and remain separate historical evidence.

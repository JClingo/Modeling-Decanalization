# HRL performance under different post-decanalization count transformations

This experiment changes the stored tile counts at the CDR transition out of decanalization. Counting is one visit per actual entry in every phase, and the selected corrected-anticipation HRL policy is fixed. This directly tests a different manipulation from the earlier sweep of counting rates during decanalization.

## Answer: CDR versus CCC

No tested transformation establishes lower absolute setpoint error than CCC after the 12-test Holm adjustment.

No tested transformation establishes higher received objective reward than CCC after the 12-test Holm adjustment.

The comparisons retain all 250 trials per condition. Differences are CDR minus CCC; negative MAE and positive reward differences favor CDR. Brackets are unadjusted Welch 95% intervals. All six conditions and both endpoints form one 12-test phase-3 Holm family. An interval spanning zero does not establish equivalence.

| Counts retained at recanalization | CDR MAE | CDR reward | MAE difference vs CCC [95% CI] | MAE Holm p | Reward difference vs CCC [95% CI] | Reward Holm p |
|---|---:|---:|---:|---:|---:|---:|
| 0% retained | 13.965 | 80.988 | -4.510 [-10.521, 1.500] | 1 | +1.639 [-0.696, 3.974] | 1 |
| 25%, floored | 14.874 | 80.471 | -3.601 [-9.745, 2.544] | 1 | +1.122 [-1.365, 3.609] | 1 |
| 50%, floored (current) | 14.789 | 79.964 | -3.686 [-9.722, 2.349] | 1 | +0.615 [-1.796, 3.026] | 1 |
| 75%, floored | 13.753 | 81.052 | -4.722 [-10.711, 1.267] | 1 | +1.704 [-0.601, 4.008] | 1 |
| 100% retained | 14.180 | 80.919 | -4.295 [-10.344, 1.753] | 1 | +1.570 [-0.796, 3.935] | 1 |
| 50%, exact | 14.421 | 80.553 | -4.054 [-10.113, 2.005] | 1 | +1.204 [-1.182, 3.590] | 1 |

CCC means: MAE **18.475**, reward **79.349** per 100-second phase.

## Does changing the current rule change performance?

A difference from CCC alone does not show that a new transformation improved on the current implementation. These direct comparisons use half-floor as the reference, with a separate 10-test Holm family (five alternatives × two endpoints).

| Alternative to half-floor | MAE difference [95% CI] | Holm p | Reward difference [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| 0% retained | -0.824 [-3.770, 2.122] | 1 | +1.024 [-1.264, 3.312] | 1 |
| 25%, floored | +0.086 [-3.128, 3.299] | 1 | +0.507 [-1.936, 2.950] | 1 |
| 75%, floored | -1.035 [-3.937, 1.866] | 1 | +1.089 [-1.167, 3.345] | 1 |
| 100% retained | -0.609 [-3.633, 2.415] | 1 | +0.955 [-1.364, 3.274] | 1 |
| 50%, exact | -0.367 [-3.412, 2.678] | 1 | +0.589 [-1.751, 2.928] | 1 |

The half-exact versus half-floor comparisons do not establish a performance effect of flooring on either endpoint. This leaves rounding effects uncertain rather than proving that rounding is irrelevant.

## Counts and phase diagnostics

| Condition | Mean total counts at phase-3 start | MAE pre | MAE during | MAE post | Reward post |
|---|---:|---:|---:|---:|---:|
| 0% retained | 0.000 | 11.216 | 347.467 | 13.965 | 80.988 |
| 25%, floored | 93.612 | 11.216 | 347.467 | 14.874 | 80.471 |
| 50%, floored (current) | 336.180 | 11.205 | 347.053 | 14.789 | 79.964 |
| 75%, floored | 458.328 | 11.216 | 347.467 | 13.753 | 81.052 |
| 100% retained | 1284.344 | 11.216 | 347.467 | 14.180 | 80.919 |
| 50%, exact | 642.172 | 11.216 | 347.467 | 14.421 | 80.553 |
| CCC | 1289.180 | 11.216 | 12.764 | 18.475 | 79.349 |

At phase-3 start, exact halving retains a mean total count of 642.172, compared with 336.180 under current floored halving. Exact halving leaves an average of 611.656 tiles per trial with fractional counts in the captured scene. A once-visited tile retains 0.5 under exact halving and zero under floored halving. Thus the rounding comparison changes measurable environmental history, even if a performance contrast remains uncertain.

Count totals sum the 2,500 tiles captured at phase start; they are not numbers of distinct visited tiles. Native handler tests verify the exact transformation before scoring. Initial phase placement/overlap ordering may add ordinary entries around the count-transform operation, so a captured phase-3 total need not equal the transformation applied to a phase-2-start total.

Ordinary physical and predicted loss are still removed during decanalization. Phase boundaries restore the trial’s initial h, so these phase means do not represent uninterrupted homeostatic recovery. The unchanged phase-2 comparisons are diagnostic, not additional evidence of a post-transition effect.

| CDR condition vs current half-floor | Identical phase-1 MAE trials | Identical phase-2 MAE trials | Matching initial h / RNG / memory |
|---|---:|---:|---|
| 0% retained | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 25%, floored | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 75%, floored | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 100% retained | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 50%, exact | 249/250 | 249/250 | 250/250; 250/250; 250/250 |

## Sensitivity analyses

Welch baseline-change, paired-ID, paired-ID baseline-change and pretreatment-matched paired analyses are exported in sensitivity.csv. Each keeps the corresponding 12-test CCC or 10-test current-rule family, separately per phase/method. Pretreatment matching uses all nine phase-1 metrics and recorded start fields, not post-intervention outcomes. Exact engine-state identity is not assumed, and all trials remain in the primary Welch analysis.

| Condition vs CCC | Method | Matched/sample n | MAE difference [95% CI] | Holm p | Reward difference [95% CI] | Holm p |
|---|---|---:|---:|---:|---:|---:|
| 0% retained | Welch-change | 250 | -4.510 [-10.407, 1.387] | 1 | +1.639 [-0.530, 3.809] | 1 |
| 0% retained | paired-ID | 250 | -4.510 [-10.125, 1.104] | 0.9188 | +1.639 [-0.066, 3.345] | 0.6546 |
| 0% retained | paired-baseline-matched | 250 | -4.510 [-10.125, 1.104] | 0.9188 | +1.639 [-0.066, 3.345] | 0.6546 |
| 25%, floored | Welch-change | 250 | -3.601 [-9.639, 2.437] | 1 | +1.122 [-1.212, 3.456] | 1 |
| 25%, floored | paired-ID | 250 | -3.601 [-9.401, 2.200] | 0.9635 | +1.122 [-0.838, 3.082] | 0.9635 |
| 25%, floored | paired-baseline-matched | 250 | -3.601 [-9.401, 2.200] | 0.9635 | +1.122 [-0.838, 3.082] | 0.9635 |
| 50%, floored (current) | Welch-change | 250 | -3.676 [-9.599, 2.247] | 1 | +0.593 [-1.654, 2.840] | 1 |
| 50%, floored (current) | paired-ID | 250 | -3.686 [-9.361, 1.988] | 0.9635 | +0.615 [-1.257, 2.487] | 0.9635 |
| 50%, floored (current) | paired-baseline-matched | 249 | -3.661 [-9.358, 2.036] | 0.9635 | +0.542 [-1.332, 2.416] | 0.9635 |
| 75%, floored | Welch-change | 250 | -4.722 [-10.596, 1.152] | 1 | +1.704 [-0.425, 3.832] | 1 |
| 75%, floored | paired-ID | 250 | -4.722 [-10.303, 0.860] | 0.8724 | +1.704 [0.007, 3.400] | 0.589 |
| 75%, floored | paired-baseline-matched | 250 | -4.722 [-10.303, 0.860] | 0.8724 | +1.704 [0.007, 3.400] | 0.589 |
| 100% retained | Welch-change | 250 | -4.295 [-10.230, 1.640] | 1 | +1.570 [-0.633, 3.773] | 1 |
| 100% retained | paired-ID | 250 | -4.295 [-9.964, 1.374] | 0.9583 | +1.570 [-0.187, 3.327] | 0.7965 |
| 100% retained | paired-baseline-matched | 250 | -4.295 [-9.964, 1.374] | 0.9583 | +1.570 [-0.187, 3.327] | 0.7965 |
| 50%, exact | Welch-change | 250 | -4.054 [-10.000, 1.893] | 1 | +1.204 [-1.015, 3.423] | 1 |
| 50%, exact | paired-ID | 250 | -4.054 [-9.727, 1.620] | 0.9635 | +1.204 [-0.563, 2.970] | 0.9635 |
| 50%, exact | paired-baseline-matched | 250 | -4.054 [-9.727, 1.620] | 0.9635 | +1.204 [-0.563, 2.970] | 0.9635 |

## Interpretation for the paper

Keep half-floor with a one-count increment throughout as the main condition. Treat this author-approved extension as an exploratory sensitivity analysis, specifying each transformation and both comparison families. Report whether alternatives differ from CCC and whether they differ directly from the current transformation; a significant result in one condition and an uncertain result in another is not itself a significant difference between them.

Any altered count retention changes environmental history under one selected fixed policy. It does not establish changes in neural plasticity, effects across independently trained policies, or a biological intervention mechanism. Lower traversal costs need not improve regulation when the agent is above its setpoint. Extreme-error trials remain included, and uncertainty must be reported alongside the mean estimates.

## Verification and reproduction

Five new CDR batches contain 1,250 scored trials, added to the existing 250-trial current-rule batch and 250-trial CCC batch: 1,750 trials, 5,250 phases and 10,500,000 decisions. A separate one-trial smoke test is excluded from all scored tables. Native receipts, 3,750 new scene hashes, 15 new loaded inference snapshot files and 75 handler checks pass. The corrected anticipation asset and all selected loaded-model hashes match the earlier reference. Each variant’s compiled tile asset is retained and its hash matches the asset recorded by its scored run. Production source assets/maps are unchanged.

The smoke-test wrapper initially expected its observer’s final callback even though native completion had already saved a complete receipt and exited. This orchestration race was corrected to use the durable native receipt; the completed smoke data and the diagnostic are preserved. It did not change the simulation or generate discarded scored outcomes.

One concurrent disposable editor stalled during zero-count validation startup, before producing scored trials. Its logs were preserved and that audit was restarted successfully. The recovery kept the three ongoing native batches running and used a fifth independent copy for half-exact after a memory/CPU resource check. This changes concurrency only; simulated timesteps, trials and experimental settings are unchanged. The original dispatcher’s startup failure record and the successful recovery/completion record are retained together.

PASS: R independently reproduced 189 descriptive rows, 24 CCC contrasts, 20 current-rule contrasts, 60 all-pair contrasts and 176 sensitivities, including intervals, p values and Holm families.

Reproduce from frozen compact inputs with analyze.py, verify_and_plot.R and write_report.py, in that order. source_manifest.json identifies the raw sources and all frozen file hashes. Full native scenes, model captures, logs, approved protocol and script copies are retained in the experiment run folder and the local reproducibility archive. This report is generated only after all native and independent statistical checks complete.

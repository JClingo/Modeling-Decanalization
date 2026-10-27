# Does post-decanalization retention change the effect of faster counting?

This completed 2 × 3 evaluation crosses counting increments of 1 and 7 during decanalization with resetting tile counts, halving and flooring them, or keeping them at recanalization. Pre- and post-intervention counting remains one per entry. The same selected corrected-anticipation HRL policy is fixed in every condition. Each CDR cell and the shared CCC control contains 250 complete trials.

## Direct answer

The experiment does not establish that the post-decanalization count rule changes the performance effect of increasing counting from 1× to 7×. No direct interaction passes the planned six-test Holm adjustment. This leaves interactions uncertain rather than establishing independence or equivalence.

The interaction is a difference of rate effects, not a comparison of which separate p values fall below 0.05. For example, keep-versus-half is (7× keep − 1× keep) − (7× half − 1× half). The same CCC control cancels from this contrast.

## Post-intervention means and simple counting-rate effects

| Recanalization rule | 1× MAE | 7× MAE | MAE 7×−1× [95% CI] | Holm p | 1× reward | 7× reward | Reward 7×−1× [95% CI] | Holm p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Reset | 13.965 | 14.922 | +0.958 [-2.148, 4.063] | 1 | 80.988 | 80.340 | -0.648 [-3.042, 1.746] | 1 |
| Halve and floor | 14.789 | 15.506 | +0.717 [-2.558, 3.992] | 1 | 79.964 | 79.827 | -0.137 [-2.587, 2.313] | 1 |
| Keep all | 14.180 | 15.209 | +1.029 [-2.051, 4.110] | 1 | 80.919 | 79.314 | -1.605 [-3.955, 0.746] | 1 |

Simple effects have their own six-test family (three rules × two endpoints). Negative MAE differences favor faster counting; positive reward differences favor it. MAE uses recorded event/update samples; reward is the actual callback total per 100-second, 2,000-decision phase.

## Primary interaction contrasts

| First rule versus second | Change in MAE rate effect [95% CI] | Holm p | Change in reward rate effect [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| Reset vs Halve and floor | +0.241 [-4.267, 4.749] | 1 | -0.511 [-3.933, 2.910] | 1 |
| Keep all vs Halve and floor | +0.313 [-4.178, 4.803] | 1 | -1.467 [-4.859, 1.924] | 1 |
| Keep all vs Reset | +0.072 [-4.297, 4.441] | 1 | -0.956 [-4.307, 2.395] | 1 |

An interaction compares the 7×−1× effect under the first rule with that under the second. A negative MAE interaction means faster counting is more favorable under the first rule; a positive reward interaction has the same favorable interpretation. These are four-cell Welch-Satterthwaite comparisons with unadjusted 95% t intervals. Holm adjusts all three rule contrasts and both endpoints together, six tests. The three pairwise contrasts are dependent; no separate omnibus test is claimed.

The response figure shows condition means with unadjusted 95% t confidence intervals; the dashed line and gray band show the shared CCC mean and its interval. The interaction figure shows direct interaction estimates and unadjusted 95% intervals, with a dashed zero line.

## CDR versus the shared CCC control

CCC means are MAE 18.475 and reward 79.349. These secondary comparisons have a separate 12-test family. They compare the complete CDR intervention with CCC, not the isolated count transformation.

| CDR cell | MAE difference vs CCC [95% CI] | Holm p | Reward difference vs CCC [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| 1×, Reset | -4.510 [-10.521, 1.500] | 1 | +1.639 [-0.696, 3.974] | 1 |
| 1×, Halve and floor | -3.686 [-9.722, 2.349] | 1 | +0.615 [-1.796, 3.026] | 1 |
| 1×, Keep all | -4.295 [-10.344, 1.753] | 1 | +1.570 [-0.796, 3.935] | 1 |
| 7×, Reset | -3.553 [-9.667, 2.562] | 1 | +0.991 [-1.521, 3.503] | 1 |
| 7×, Halve and floor | -2.970 [-9.147, 3.207] | 1 | +0.478 [-2.017, 2.972] | 1 |
| 7×, Keep all | -3.266 [-9.330, 2.798] | 1 | -0.035 [-2.477, 2.407] | 1 |

## Sensitivity and alignment

| Rule contrast | Method | Trials per cell | MAE interaction [95% CI] | Holm p | Reward interaction [95% CI] | Holm p |
|---|---|---:|---:|---:|---:|---:|
| Reset vs Halve and floor | Welch-change | 250 | +0.251 [-3.913, 4.415] | 1 | -0.533 [-3.713, 2.646] | 1 |
| Reset vs Halve and floor | paired-ID | 250 | +0.241 [-1.830, 2.312] | 1 | -0.511 [-2.224, 1.201] | 1 |
| Reset vs Halve and floor | paired-ID-change | 250 | +0.251 [-1.820, 2.323] | 1 | -0.533 [-2.247, 1.180] | 1 |
| Reset vs Halve and floor | paired-baseline-matched | 249 | +0.237 [-1.842, 2.317] | 1 | -0.503 [-2.222, 1.216] | 1 |
| Keep all vs Halve and floor | Welch-change | 250 | +0.323 [-3.831, 4.477] | 1 | -1.489 [-4.662, 1.683] | 1 |
| Keep all vs Halve and floor | paired-ID | 250 | +0.313 [-1.700, 2.325] | 1 | -1.467 [-3.158, 0.223] | 0.5312 |
| Keep all vs Halve and floor | paired-ID-change | 250 | +0.323 [-1.690, 2.336] | 1 | -1.489 [-3.180, 0.201] | 0.5037 |
| Keep all vs Halve and floor | paired-baseline-matched | 249 | +0.313 [-1.708, 2.334] | 1 | -1.470 [-3.167, 0.227] | 0.5354 |
| Keep all vs Reset | Welch-change | 250 | +0.072 [-3.939, 4.083] | 1 | -0.956 [-4.071, 2.159] | 1 |
| Keep all vs Reset | paired-ID | 250 | +0.072 [-1.544, 1.688] | 1 | -0.956 [-2.463, 0.551] | 1 |
| Keep all vs Reset | paired-ID-change | 250 | +0.072 [-1.544, 1.688] | 1 | -0.956 [-2.463, 0.551] | 1 |
| Keep all vs Reset | paired-baseline-matched | 250 | +0.072 [-1.544, 1.688] | 1 | -0.956 [-2.463, 0.551] | 1 |

No phase-3 interaction sensitivity passes its corresponding six-test Holm adjustment.

Each sensitivity method uses its own six-test family per phase. Baseline-change subtracts phase 1 within trial before forming the contrast. Paired methods use same-ID four-cell contrasts. Pretreatment matching uses all nine phase-1 metrics plus recorded initial h, RNG and recurrent memory across all four cells. No trials are excluded from the primary analysis. Recorded start-field agreement does not prove complete engine-state identity.

| Rate | Rule vs half-floor | Identical phase-1 MAE trials | Identical phase-2 MAE trials | Matching initial h / RNG / memory |
|---|---|---:|---:|---|
| 1× | Reset | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 1× | Keep all | 249/250 | 249/250 | 250/250; 250/250; 250/250 |
| 7× | Reset | 250/250 | 250/250 | 250/250; 250/250; 250/250 |
| 7× | Keep all | 250/250 | 250/250 | 250/250; 250/250; 250/250 |

## Environmental history and interpretation

| Rule | Mean total tile counts, 1× | Mean total tile counts, 7× |
|---|---:|---:|
| Reset | 0.000 | 0.000 |
| Halve and floor | 336.180 | 2218.180 |
| Keep all | 1284.344 | 5055.072 |

These are summed counts across the 2,500 tiles captured at phase-3 start, not distinct-tile counts. Resetting erases the direct stored tile-count channel, while resource states, recurrent memory and trajectories created during decanalization can still differ. Higher retained counts lower later traversal costs nonlinearly. Lower loss need not improve regulation when h is positive.

Ordinary physical and predicted losses remain zero during the intervention. Phase boundaries restore initial h, so the evaluation does not represent uninterrupted homeostatic recovery. All fixed-horizon trials, including extreme errors, are retained. The findings concern one selected policy and do not establish robustness across training seeds or changes in neural plasticity.

Keep k=1/half-floor as the main paper condition. This author-approved factorial extension tests the interaction left unresolved by the earlier two separate sweeps. Do not select a replacement condition or claim an optimal rate/retention rule from these exploratory outcomes.

## Verification and reproduction

The two new cells contain 500 trials, 1,500 phases and 3,000,000 decisions. With four reused CDR cells and the shared CCC reference, the factorial package covers 1,750 trials, 5,250 phases and 10,500,000 decisions. Both variants passed 15 real Blueprint handler checks before scoring, including factor 7 during decanalization and ordinary increments of 1. All 1,500 new scene hashes, six loaded inference snapshot files, durable completion receipts and compiled tile hashes were verified. The corrected anticipation and selected weights match the references. Production source hashes are preserved.

PASS: independent R reproduced 189 summaries, 12 four-cell interactions, 12 simple rate effects, 24 CCC contrasts and 48 interaction sensitivities, including SEs, df, intervals, p values and Holm families.

Run analyze.py, verify_and_plot.R and write_report.py in order. Frozen input hashes and reference manifests are in source_manifest.json. The native run and local archive preserve raw scenes, model captures, variant assets, logs, protocol and exact source copies. The main report is generated only after native completion and independent statistical verification.

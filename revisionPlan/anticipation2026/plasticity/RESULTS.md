# HRL performance across decanalized traversal factors

This experiment changes environmental traversal counting while holding the selected HRL policy and corrected anticipation fixed. It does not retrain the policy. Each condition contains 250 complete trials with three 100-second phases. Factor 0 and CCC reuse the original corrected reference batches; factors 1, 2, 4 and 7 are new native evaluations.

**Current primary designation:** the author confirmed factor 1 as the originally intended condition after this sweep was reported. Use [the factor-1 HRL analysis](../primary-factor1/RESULTS.md) for primary inference; factors 0, 2, 4 and 7 are sensitivity conditions. The numerical families and CSV names below preserve the original sweep analysis, and “primary” within this sweep means its originally specified 16-test comparison family. See [the design clarification](../PRIMARY_DESIGN_CLARIFICATION.md). The original hashed analysis plan remains unchanged.

## Counting rule

The earlier corrected evaluation used factor 0, so traversal count did not increase during decanalization. The intended primary condition now uses factor 1. The Blueprint directly adds the factor on each tile entry. Factor 1 is ordinary counting, and 2/4/7 accelerate counting to two/four/seven visits per entry. Counts still increase by one in ordinary phases. Recanalization halves counts with rounding down. Thus, factor 1 gives one increment per entry throughout, while retaining the once-only count halving. Factor 0 disables counting during the intervention. Neither removes pre-intervention history.

These factors operationalize environmental plasticity: greater retained counts reduce later traversal costs. Policy weights remain frozen. The count-halving step and integer rounding can make the effective manipulation nonlinear. Performance itself need not improve monotonically as crossing becomes cheaper, because loss can help an agent above its setpoint.

## Post-intervention performance

Means are trial-level phase-3 summaries. MAE is sampled from the existing event/update history; reward is the actual HRL callback total for 2,000 decisions.

| Condition | Mean absolute h | HRL reward | Fraction within ±5 | Median MAE |
|---|---:|---:|---:|---:|
| CDR-0 | 15.144 | 80.186 | 0.3158 | 10.189 |
| CDR-1 | 14.789 | 79.964 | 0.3117 | 10.616 |
| CDR-2 | 15.145 | 80.056 | 0.3160 | 10.517 |
| CDR-4 | 14.968 | 79.893 | 0.3120 | 10.528 |
| CDR-7 | 15.506 | 79.827 | 0.3132 | 10.565 |
| CCC | 18.475 | 79.349 | 0.3067 | 10.965 |

Factor 1 has the lowest observed mean phase-3 MAE among the five CDR factors. This ranking is descriptive; these data do not establish an optimal factor.

No new factor establishes lower phase-3 MAE than CCC after the primary 16-test Holm adjustment. This is not evidence that all factors are equivalent.

The observed factor effects are small: factor 1 lowers mean MAE by 2.3% relative to factor 0, while factor 7 raises it by 2.4%; mean reward changes by less than 0.5% across all five factors. All phase-3 Welch comparisons, all-factor pairwise comparisons, baseline-change and paired/matched sensitivity comparisons have intervals spanning zero and Holm p=1.00. The retained landscape nevertheless changes substantially: mean total counts at phase-3 start rise from 78.512 at factor 0 to 2,218.180 at factor 7. The manipulation worked, but no corresponding performance advantage was established. These results do not demonstrate equivalence.

## Relative performance

Positive percentages mean improvement: reduction in mean MAE or increase in mean reward. Percentages compare group means. Brackets are descriptive trial-bootstrap 95% intervals, using independent condition resampling (10,000 resamples, base R seed 261026), not multiplicity-adjusted hypothesis tests.

| Factor | MAE improvement vs factor 0 | Reward improvement vs factor 0 |
|---|---:|---:|
| 0 | 0 (reference) | 0 (reference) |
| 1 | +2.3% [-21.3, +21.4] | -0.3% [-3.4, +2.9] |
| 2 | -0.0% [-24.2, +19.7] | -0.2% [-3.2, +3.0] |
| 4 | +1.2% [-23.3, +20.2] | -0.4% [-3.5, +2.7] |
| 7 | -2.4% [-28.0, +18.3] | -0.4% [-3.5, +2.8] |

| Factor | MAE improvement vs ordinary counting (factor 1) | Reward improvement vs ordinary counting |
|---|---:|---:|
| 0 | -2.4% [-27.2, +17.6] | +0.3% [-2.9, +3.5] |
| 1 | 0 (reference) | 0 (reference) |
| 2 | -2.4% [-25.8, +16.8] | +0.1% [-2.9, +3.2] |
| 4 | -1.2% [-24.0, +17.4] | -0.1% [-3.0, +2.9] |
| 7 | -4.8% [-29.2, +15.2] | -0.2% [-3.2, +2.9] |

## Primary absolute contrasts

Each new factor is compared with factor 0 and CCC. Differences are factor minus reference. Intervals are unadjusted Welch 95% intervals; Holm adjusts 16 phase-3 tests together (four new factors × two references × MAE/reward). See ANALYSIS_PLAN.md for the separate phase-2 and all-factor pairwise families.

| Factor | Reference | MAE difference [95% CI] | MAE Holm p | Reward difference [95% CI] | Reward Holm p |
|---|---|---:|---:|---:|---:|
| 1 | CDR-0 | -0.355 [-3.587, 2.877] | 1 | -0.223 [-2.712, 2.267] | 1 |
| 1 | CCC | -3.686 [-9.722, 2.349] | 1 | 0.615 [-1.796, 3.026] | 1 |
| 2 | CDR-0 | 0.001 [-3.363, 3.365] | 1 | -0.130 [-2.674, 2.414] | 1 |
| 2 | CCC | -3.330 [-9.437, 2.777] | 1 | 0.708 [-1.760, 3.175] | 1 |
| 4 | CDR-0 | -0.176 [-3.471, 3.119] | 1 | -0.293 [-2.801, 2.215] | 1 |
| 4 | CCC | -3.507 [-9.577, 2.562] | 1 | 0.545 [-1.885, 2.974] | 1 |
| 7 | CDR-0 | 0.362 [-3.129, 3.853] | 1 | -0.360 [-2.930, 2.210] | 1 |
| 7 | CCC | -2.970 [-9.147, 3.207] | 1 | 0.478 [-2.017, 2.972] | 1 |

## Acceleration relative to ordinary counting

These are secondary comparisons with factor 1, drawn from the complete ten-pair CDR comparison table. Their Holm family contains 20 tests (ten factor pairs × two outcomes), so adjusted p values can differ from the primary table for duplicated contrasts.

| Factor | MAE difference vs 1 [95% CI] | Holm p | Reward difference vs 1 [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| 2 | 0.356 [-2.783, 3.496] | 1 | 0.093 [-2.330, 2.515] | 1 |
| 4 | 0.179 [-2.886, 3.244] | 1 | -0.070 [-2.455, 2.314] | 1 |
| 7 | 0.717 [-2.558, 3.992] | 1 | -0.137 [-2.587, 2.313] | 1 |

## Phases and persistent landscape changes

| Condition | MAE pre | MAE during | MAE post | Reward pre | Reward during | Reward post |
|---|---:|---:|---:|---:|---:|---:|
| CDR-0 | 11.216 | 319.349 | 15.144 | 82.841 | 13.344 | 80.186 |
| CDR-1 | 11.205 | 347.053 | 14.789 | 82.863 | 12.749 | 79.964 |
| CDR-2 | 11.224 | 361.751 | 15.145 | 82.819 | 12.393 | 80.056 |
| CDR-4 | 11.216 | 350.075 | 14.968 | 82.841 | 13.061 | 79.893 |
| CDR-7 | 11.216 | 332.120 | 15.506 | 82.841 | 13.459 | 79.827 |
| CCC | 11.216 | 12.764 | 18.475 | 82.841 | 81.796 | 79.349 |

Phase boundaries restore the trial’s initial h. These phase means do not describe uninterrupted homeostatic recovery. All CDR conditions retain the same combined perceptual/physical decanalization and count-halving rule; CCC has no intervention.

| Condition | Mean total tile counts at start of phase 2 | Mean total tile counts at start of phase 3 |
|---|---:|---:|
| CDR-0 | 649.496 | 78.512 |
| CDR-1 | 649.452 | 336.180 |
| CDR-2 | 649.508 | 716.848 |
| CDR-4 | 649.492 | 1351.880 |
| CDR-7 | 649.496 | 2218.180 |
| CCC | 649.496 | 1289.180 |

These are totals across the 2,500 tile counts captured at phase start, not counts of distinct tiles. They audit the retained landscape manipulation, not a causal explanation of every performance difference.

## Matching and sensitivity

| Comparison | Identical baseline MAE trials | Matching recorded initial h / RNG / recurrent memory |
|---|---:|---|
| CDR-1 vs CDR-0 | 249/250 | 250/250; 250/250; 250/250 |
| CDR-1 vs CCC | 249/250 | 250/250; 250/250; 250/250 |
| CDR-2 vs CDR-0 | 249/250 | 250/250; 250/250; 250/250 |
| CDR-2 vs CCC | 249/250 | 250/250; 250/250; 250/250 |
| CDR-4 vs CDR-0 | 250/250 | 250/250; 250/250; 250/250 |
| CDR-4 vs CCC | 250/250 | 250/250; 250/250; 250/250 |
| CDR-7 vs CDR-0 | 250/250 | 250/250; 250/250; 250/250 |
| CDR-7 vs CCC | 250/250 | 250/250; 250/250; 250/250 |

The factor itself differs in recorded scene metadata; complete engine-state identity is not assumed. A few baseline trajectories also differ despite matching recorded start fields. The primary Welch comparison retains all trials. Baseline-change and paired-ID sensitivity analyses are reported separately; a further pretreatment-matched sensitivity retains only IDs with identical phase-1 metrics and captured start fields, as documented in the analysis-plan amendment.

| Factor vs CCC | Method | Trials per condition | MAE difference [95% CI] | Holm p |
|---|---|---:|---:|---:|
| 1 | Welch-change | 250 | -3.676 [-9.599, 2.247] | 1 |
| 1 | paired-ID | 250 | -3.686 [-9.361, 1.988] | 1 |
| 1 | paired-baseline-matched | 249 | -3.661 [-9.358, 2.036] | 1 |
| 2 | Welch-change | 250 | -3.339 [-9.322, 2.645] | 1 |
| 2 | paired-ID | 250 | -3.330 [-9.069, 2.409] | 1 |
| 2 | paired-baseline-matched | 249 | -3.359 [-9.121, 2.403] | 1 |
| 4 | Welch-change | 250 | -3.507 [-9.460, 2.445] | 1 |
| 4 | paired-ID | 250 | -3.507 [-9.164, 2.149] | 1 |
| 4 | paired-baseline-matched | 250 | -3.507 [-9.164, 2.149] | 1 |
| 7 | Welch-change | 250 | -2.970 [-9.037, 3.098] | 1 |
| 7 | paired-ID | 250 | -2.970 [-8.815, 2.876] | 1 |
| 7 | paired-baseline-matched | 250 | -2.970 [-8.815, 2.876] | 1 |

All trials, including large errors, remain included in the primary comparison. Full standard deviations, medians, minima and maxima are in phase_summary.csv. Independent R checks reproduce all 162 descriptive rows, 32 primary contrasts, 40 all-factor contrasts and 128 sensitivity contrasts.

## Implications for the paper

Use factor-1 CDR versus CCC as the primary HRL experiment, in accordance with the author’s clarified original plan. Present factor 0 and accelerated factors 2, 4 and 7 as sensitivity conditions around ordinary counting. Retain the factor-response curve and comparisons against both factor 0 and factor 1 with uncertainty. The designation follows the stated design intent, not a claim that the observed minimum identifies an optimal factor; document that the author’s clarification followed inspection of the sweep. The available NF CDR batch remains factor 0 and is not a matching factor-1 primary result.

Use these current measurements in place of claims based on the legacy traversal-factor files. The earlier data used different observation code/policies and cannot be pooled. A factor effect is an effect of changing environmental history under this selected policy; it does not establish neural plasticity, online learning, or variation across independent training seeds.

Suggested Results paragraph: “We varied the decanalized traversal factor over 0, 1, 2, 4 and 7 while holding the selected HRL policy fixed. Mean post-intervention absolute deviation ranged from 14.79 to 15.51, and mean objective reward ranged from 79.83 to 80.19 per 100-second phase. Although larger factors left substantially greater traversal counts after recanalization, the planned comparisons did not establish differences in subsequent absolute regulation or reward, or an advantage over uninterrupted canalization. Baseline-change and matched-trial sensitivity analyses retained this uncertainty. These results provide no clear dose-response relationship between this environmental-history parameter and post-intervention performance for the selected policy.”

## Reproduction and evidence

The same selected HRL snapshots were verified in all runs. Native receipts, 3,000 new scene hashes, 12 new loaded inference snapshot files and the requested factor on every tile were checked. Import additionally rechecks 1,500 reference scene hashes for the landscape-count audit. A separate editor audit passed 17 direct native event-handler checks for decanalized increments, ordinary counting and count-halving, with no saved asset changes. These are handler tests, not physical collision tests. All 1,500 trials across six conditions are complete: 4,500 phases and 9,000,000 decisions. Five source-project asset/map hashes were unchanged at native completion.

The frozen compact inputs and their hashes are in inputs/ and source_manifest.json. Full native scene records, matching snapshots, logs and isolated project copies remain under the source run recorded in that manifest. Reproduce using analyze.py, bootstrap_and_plot.R and write_report.py in that order. See README.md for commands.

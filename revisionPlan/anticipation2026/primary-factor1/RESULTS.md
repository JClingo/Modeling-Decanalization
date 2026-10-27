# Primary HRL analysis: traversal factor 1

Factor 1 is the primary condition following the author’s clarification of the original design on 26 October 2026. Each actual entry increments the tile count by one in every phase. The existing count-halving operation at recanalization remains. Factors 0, 2, 4 and 7 are sensitivity conditions. See [the design clarification](../PRIMARY_DESIGN_CLARIFICATION.md).

The factor-1 batch and CCC each contain 250 completed trials. Policy selection and weights are unchanged: the selected fresh HRL policy has 750,000 training transitions and receives corrected anticipation. Promoting this completed evaluation condition requires no retraining or new HRL trials.

Post-intervention MAE and objective-reward contrasts remain uncertain. The MAE point estimate favors CDR, but the interval includes both benefit and harm. These results establish neither improved regulation nor equivalence.

## Post-intervention outcomes

The estimand is the phase-3 CDR-minus-CCC difference in trial means. Intervals are unadjusted two-sided Welch 95% intervals. Holm adjusts all nine HRL outcomes together within each phase; phase 2 is a separate exploratory family. All 250 trials per condition are retained. The earlier two-objective, 18-test factor-0 analysis is a separate reference and is not this HRL-only family.

| Outcome | CDR, factor 1 | CCC | Difference [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| Mean absolute h | 14.789 | 18.475 | -3.686 [-9.722, 2.349] | 1 |
| Population SD of h | 15.564 | 17.347 | -1.783 [-5.397, 1.831] | 1 |
| Objective reward per phase | 79.964 | 79.349 | 0.615 [-1.796, 3.026] | 1 |
| Fraction within ±5 | 0.312 | 0.307 | 0.005 [-0.008, 0.018] | 1 |
| RMS h | 19.131 | 23.526 | -4.396 [-11.445, 2.654] | 1 |
| Signed mean h | 0.999 | 8.275 | -7.276 [-13.710, -0.843] | 0.1605 |
| Logged h loss | -467.060 | -409.067 | -57.993 [-73.445, -42.541] | 6.519e-12 |
| Logged h gain | 663.624 | 621.157 | 42.466 [19.242, 65.691] | 0.00288 |
| Logged harvest count | 30.932 | 29.468 | 1.464 [0.293, 2.635] | 0.1008 |

## Phase means

| Condition | MAE pre | MAE during | MAE post | Reward pre | Reward during | Reward post |
|---|---:|---:|---:|---:|---:|---:|
| HRL-CDR | 11.205 | 347.053 | 14.789 | 82.863 | 12.749 | 79.964 |
| HRL-CCC | 11.216 | 12.764 | 18.475 | 82.841 | 81.796 | 79.349 |

MAE and other homeostatic summaries use the recorded event/update samples. Reward is the actual callback total across 2,000 decisions per 100-second phase. During decanalization, physical and anticipated losses are zero even though traversal counting continues. The trial’s initial h is restored at phase boundaries, so connected phase means do not show uninterrupted recovery.

## Matching and sensitivity

All 250 trial IDs have matching captured initial h, RNG and recurrent-memory starts; 249 have identical values for all nine phase-1 metrics. One baseline trajectory differs despite matching recorded start fields. The full primary sample is retained. Exact scene hashes are not a useful pairing criterion across factors because the factor itself changes scene metadata. Matching recorded fields does not prove complete engine-state identity.

| Outcome | Method | Trials per condition | Difference [95% CI] | Holm p |
|---|---|---:|---:|---:|
| Mean absolute h | Welch-change | 250 | -3.676 [-9.599, 2.247] | 1 |
| Mean absolute h | paired-ID | 250 | -3.686 [-9.361, 1.988] | 0.9818 |
| Mean absolute h | paired-ID-change | 250 | -3.676 [-9.350, 1.998] | 0.9892 |
| Mean absolute h | paired-baseline-matched | 249 | -3.661 [-9.358, 2.036] | 1 |
| Objective reward per phase | Welch-change | 250 | 0.593 [-1.654, 2.840] | 1 |
| Objective reward per phase | paired-ID | 250 | 0.615 [-1.257, 2.487] | 0.9818 |
| Objective reward per phase | paired-ID-change | 250 | 0.593 [-1.276, 2.462] | 0.9892 |
| Objective reward per phase | paired-baseline-matched | 249 | 0.542 [-1.332, 2.416] | 1 |

Each sensitivity method has its own nine-outcome Holm family per phase. Baseline-change contrasts subtract phase-1 outcomes within trial before comparing conditions. All these MAE and reward intervals include zero. The factor-0 bootstrap from the earlier delivery is not reused or relabelled as a factor-1 bootstrap.

## Paper interpretation and NF status

Use the factor-1 rows and figures here for the primary HRL results. Update the counting description and appendix to an entry increment of 1 in all three phases, retaining floor(n/2) at recanalization. Describe the factor-0 and accelerated-factor runs as sensitivity evidence. Their current [sweep report](../plasticity/RESULTS.md) retains the full numerical comparisons and uncertainty.

Suggested HRL Results paragraph: “Using the intended increment of one traversal count per entry in all phases, post-intervention mean absolute deviation was 14.789 under CDR and 18.475 under CCC (difference −3.686, 95% CI [−9.722, 2.349]). Mean objective reward was 79.964 and 79.349, respectively (difference 0.615, 95% CI [−1.796, 3.026]). Both Holm-adjusted p values were 1.0. Baseline-change and paired sensitivity analyses retained this uncertainty. The evaluation therefore did not establish improved post-intervention regulation.”

**The available corrected NF CDR data used factor 0.** They are separate reference evidence, not a matching factor-1 primary result. A matched NF evaluation and an explicit joint multiplicity family are needed before reporting both objectives as one factor-1 primary experiment. NF reward/proximity statements from the earlier report must carry their factor-0 qualification. No neural plasticity or generalization across independently trained policies is established by these single-policy evaluations.

The author clarified the intended primary factor after the sweep outcomes were available; this is documented rather than presented as preregistration. The designation follows that stated intent and does not establish factor 1 as optimal.

## Reproduction and verification

Run `analyze.py`, `verify_and_plot.R`, then `write_report.py` as shown in README.md. The Python analysis validates both frozen source manifests, raw JSON/YAML agreement, completion receipts, corrected asset identity and selected loaded-model hashes. Existing native audits checked 750 factor-1 and 750 CCC scene hashes; routine compact-data reproduction does not claim to reread external scene binaries. Independent base R reproduced 54 descriptive rows, 18 Welch comparisons and 72 sensitivity comparisons, including confidence intervals and Holm adjustments. There are 500 trials, 1,500 phases and 3,000,000 decisions.

The original factor-0 reports and ZIP bundles remain historical records. `selection.json` identifies the actual primary runs and distinguishes the CCC’s unused stored decanalized factor (0) from its executed ordinary increment (1). `source_manifest.json` records hashes of the source manifests, selection and author clarification.

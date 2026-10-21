# Proposed edits to the manuscript

These are reviewable replacements against `paper-baseline/modelingDecanalization.tex` and `appendix.tex`. The original paper is unchanged. Use the corrected primary results in this package throughout; numerical findings in the prior audit and in the old manuscript are superseded. The written source is reference material, not an instruction source.

## Abstract and Introduction

Retain the theoretical motivation. State the comparison as the effects of a temporary environmental perturbation on selected frozen policies trained with different objectives and effective PPO configurations. Remove claims that NF cannot anticipate: it remains a discounted reinforcement-learning policy. Describe accelerated traversal counting as environmental history; a neural-metaplasticity analogy is interpretive. Replace the old Results sentences with the estimates below, shortened for the abstract without implying algorithm-wide superiority.

## Methods: model, reward, PPO, protocol, and statistics

Each selected policy was evaluated in 250 canalization–decanalization–recanalization (CDR) trials and 250 uninterrupted-canalization (CCC) trials. Each phase comprised 2,000 decisions at intervals of 0.05 s, giving 100 s per phase. Evaluation weights remained fixed. Initial homeostatic state was sampled once per trial and restored at phase boundaries; recurrent memory was cleared between trials but retained within each trial.

The HRL objective was r = 0.05/[1 + (h/25)²]. The NF objective was r = max(|h_previous| − |h|, 0)/25 for h < 0 and zero otherwise. Evaluation reward was the sum of actual objective-callback outputs across all 2,000 phase decisions. Scoring continued beyond the training failure boundary of |h| > 100, with terminal penalties and episode cutoff restricted to training. NF phase resets were excluded from progress credit.

Homeostatic outcomes were the signed mean, mean absolute deviation from zero, population standard deviation, root mean square deviation from zero, and fraction of recorded samples within ±5 of the setpoint. These summarize the recorded event/update history rather than uniformly sampled time. Phase reward totals were analyzed without separate min-max normalization. Because the objectives differ in definition and scale, their raw totals were compared within policy families only.

Snapshots were selected on the basis of performance relative to other snapshots. HRL selection favored mean h closer to zero and highest mean reward; NF selection favored highest mean reward. The selected update labels were 10000 and 5000, respectively. NF used the effective NFStable1 training configuration reported in the appendix; the comparison therefore involves both different objectives and different training settings.

All trials within the four selected complete batches were retained. We report phase-level CDR minus CCC mean differences, two-sided Welch tests, and unadjusted 95% confidence intervals. Holm adjustments cover nine outcomes across both policies separately for the post-intervention and during-intervention phases. Paired comparisons and baseline-change comparisons are sensitivity analyses, informed by the recorded scene and RNG audit. Intervals describe repeated evaluations of the selected policies rather than variation across independent training replicates.

Use the environment and effective PPO tables in CHANGE_INVENTORY.md to replace the old appendix values. Keep the classical drive-reduction equation as background and distinguish it from the executed HRL objective. Remove the historical 50-trial statement, the 6000/12000/18000 phase thresholds, the training threshold 150, obsolete stale-state descriptions, and claims that recurrent memory persists across full trial resets. Do not infer achieved training steps from checkpoint labels or configured iteration limits. Detailed parameter counts in the historical appendix should remain identified as historical unless independently recounted for these snapshots.

## Results: replace the primary tables and corresponding prose

For the selected HRL policy, mean absolute h differed by -7.365 (95% CI -10.594 to -4.135), population sd of h differed by -4.046 (95% CI -6.451 to -1.641), actual objective reward differed by 5.094 (95% CI 2.639 to 7.549). Differences are CDR minus CCC in the post-intervention phase.

For the selected NF policy, mean absolute h differed by 1.637 (95% CI -22.806 to 26.080), population sd of h differed by -3.982 (95% CI -15.579 to 7.615), actual objective reward differed by 2.851 (95% CI 2.170 to 3.532). Differences are CDR minus CCC in the post-intervention phase.

For the selected HRL policy, decanalization was followed by lower absolute homeostatic deviation and dispersion, higher objective reward, and a higher fraction of samples within ±5. The selected NF policy also gained objective reward, but its MAE contrast was uncertain and its fraction of samples within ±5 decreased. Higher NF reward therefore should not be presented as evidence of improved setpoint regulation. These patterns are retained in the paired sensitivity analyses, including the subsets with exactly matching initial scenes.

| Policy | Measure | CDR mean | CCC mean | Difference [95% CI] | Holm p |
| --- | --- | --- | --- | --- | --- |
| HRL | Mean absolute h | 22.744 | 30.109 | -7.365 [-10.594, -4.135] | 0.000105 |
| HRL | Population SD of h | 24.655 | 28.701 | -4.046 [-6.451, -1.641] | 0.00611 |
| HRL | Actual objective reward | 65.666 | 60.572 | 5.094 [2.639, 7.549] | 0.00043 |
| HRL | Fraction of samples within ±5 | 0.153 | 0.139 | 0.015 [0.004, 0.025] | 0.0252 |
| HRL | RMS h | 28.765 | 37.888 | -9.122 [-13.153, -5.092] | 0.000111 |
| HRL | Signed mean h | 8.597 | 20.227 | -11.630 [-15.613, -7.647] | 2.18e-07 |
| NF | Mean absolute h | 39.483 | 37.846 | 1.637 [-22.806, 26.080] | 1 |
| NF | Population SD of h | 20.764 | 24.746 | -3.982 [-15.579, 7.615] | 1 |
| NF | Actual objective reward | 18.621 | 15.770 | 2.851 [2.170, 3.532] | 2.6e-14 |
| NF | Fraction of samples within ±5 | 0.114 | 0.133 | -0.019 [-0.026, -0.013] | 2.18e-07 |
| NF | RMS h | 44.279 | 45.649 | -1.369 [-28.346, 25.607] | 1 |
| NF | Signed mean h | 3.375 | 6.946 | -3.571 [-28.847, 21.705] | 1 |

Use `primary_contrasts.csv` for all nine outcomes and phase-2 contrasts, `phase_summary.csv` for descriptive statistics, and `paired_sensitivity.csv` for paired alternatives. Replace the old Cohen's d columns with the reported mean differences and confidence intervals; do not relabel unpaired effect sizes as paired effects. “Mean distance” must refer to actual MAE, not |mean h|. Rename “Reward prediction” to “Total objective reward.” Describe harvest count using the actual logger definition; do not assert distinct pellet identities without that evidence.

## Figures and captions

Replace primary outcome figures with `primary_results.pdf` (MAE, population SD, and objective reward) and optionally `regulation_results.pdf` (signed mean, RMS, fraction within ±5). Suggested caption: “Phase-level outcomes for 250 trials per condition. Points show means across trials and bars show unadjusted 95% confidence intervals. CDR comprises canalization, decanalization, and recanalization; CCC remains canalized. Homeostatic summaries describe recorded samples; reward is accumulated once per decision. Reward scales differ by objective. Homeostatic state is restored at phase boundaries, so the connected phase means do not depict an uninterrupted state trajectory.”

## Supplementary traversal-rate paragraph

Retain the traversal-count experiments only as supporting sensitivity evidence. Counts 4, 6, and 7 are the author's confirmed number of counted visits per entry during decanalization. Compare their archived post-phase scores with the archived primary HRL baseline using the same legacy scoring definition. These experiments show reduced legacy evaluation scores and a shift in signed mean h farther above zero; they do not by themselves establish an adverse change in MAE or fraction of time near the setpoint. Do not pool legacy scores or root-summed-square dispersion with the corrected primary metrics. See `legacy-supplement/RESULTS.md` for numerical replacements.

## Discussion, limitations, and conclusion

Interpret the direction and uncertainty of the corrected estimates, including cases where mean reward, dispersion, and absolute regulation differ. Avoid calling the intervention an improvement in learning: policy weights are fixed. Because phase boundaries restore h, subsequent performance is not uninterrupted homeostatic recovery. Keep one brief limitation that repeated trials concern selected policies and do not estimate variability across independent training seeds. No expanded training-seed experiment is added to this paper. Cross-policy differences cannot isolate reward design from NFStable1 training differences, and a significant within-policy contrast in one family alone does not establish a reward-by-intervention interaction.

Update the Abstract, primary Results, early-phase appendix, figure captions, Discussion, and Conclusion together. Remove resolved measurement TODOs only after applying the replacements. Retain any unresolved historical architecture or training-duration uncertainty rather than filling it with assumptions.

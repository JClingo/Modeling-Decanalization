# Corrected primary results

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

All four conditions contain 250 complete trials, each with three 2,000-decision phases at dt = 0.05 s (100 s per phase). All 250 trials within each selected complete batch were retained; excluded or aborted batches are identified below. The analysis checks completion receipts, actual loaded snapshot bytes, every compressed scene hash, finite values, phase order, and agreement between YAML and JSON statistics. HRL uses snapshot 10000; NF uses snapshot 5000. The initial corrected NF-CDR batch 46379CD74E30DFBAC6A712BBC252E36A stopped after 185 completed trials following a Windows file-replacement conflict; it was replaced by a complete fresh batch after adding bounded I/O retries, with no change to reward or simulation calculations. The earlier NF-labeled runs 1653462949BBB05646037FB9A2AE3816 and 4BA6AF234A775A0C7B4B6A94835F7AE9 loaded HRL weights and are excluded from this primary dataset.

Within-phase `setpoint-dev` is population SD; the CSV's `sd` column is the sample SD across trial-level outcome summaries. MAE, RMS, and fraction within ±5 describe the recorded event/update samples, not uniformly timed observations. Reward totals are actual callback outputs accumulated once per decision; they are not critic predictions and are not min-max normalized. HRL and NF reward totals use different objective scales.

The main analysis uses two-sided Welch comparisons and unadjusted 95% confidence intervals. Holm p-values adjust the 18 post-phase tests together (nine outcomes × two policies); phase-2 tests form a separate exploratory family of 18. This is an exploratory evaluation of selected policies, not a preregistered confirmatory test. Paired tests on all trial IDs, paired tests restricted to exactly matching initial scene hashes, and paired changes from baseline are sensitivity analyses; their adjustments are separate by method and phase. Related outcomes are not independent replications of evidence. Repeated trials characterize these policies and do not supply independently trained policy replicates.

## Matching audit

- HRL: 230/250 exact phase-start scene hashes; baseline matches by metric: Mean absolute h 250/250, Population SD of h 250/250, Actual objective reward 250/250, Fraction of samples within ±5 250/250, RMS h 250/250, Signed mean h 250/250, Total h loss 250/250, Total h gain 250/250, Pellet harvest count 250/250. Scene differences: {"respawn_timer_active": 21, "respawn_timer_remaining": 21, "OverlapCount": 6, "hidden": 6}.
- NF: 226/250 exact phase-start scene hashes; baseline matches by metric: Mean absolute h 250/250, Population SD of h 250/250, Actual objective reward 250/250, Fraction of samples within ±5 250/250, RMS h 250/250, Signed mean h 250/250, Total h loss 250/250, Total h gain 250/250, Pellet harvest count 250/250. Scene differences: {"OverlapCount": 9, "hidden": 9, "respawn_timer_active": 24, "respawn_timer_remaining": 24}.

The matching audit does not prove complete engine-state identity. Resource timer, visibility, and overlap-count differences prevent an unqualified claim that every initial scene was identical. The main Welch analysis retains all trials; `paired_sensitivity.csv` documents the alternative analyses.

## Supplementary traversal experiments

The traversal-count conditions 4, 6, and 7 remain a separate legacy sensitivity demonstration. Their scores and dispersion were recorded before the logger correction. Compare them only with the legacy HRL baseline in `legacy-supplement/`; do not compare their reward values numerically with these corrected primary totals. Signed mean h alone cannot establish lower absolute homeostatic error.

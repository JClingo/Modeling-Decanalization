# Historical factor-0 analysis after the anticipation repair — 26 October 2026

**Superseded for primary HRL inference:** use [factor 1 versus CCC](primary-factor1/RESULTS.md), following [the author’s clarification](PRIMARY_DESIGN_CLARIFICATION.md). All numerical results below retain the earlier factor-0 condition. NF remains factor-0 reference evidence; no matching factor-1 NF result is implied. Root-level figures and LaTeX rows also retain factor 0.

The corrected evaluation no longer establishes a post-intervention HRL regulation benefit. HRL point estimates favor CDR, but the MAE, SD, RMS, proximity-fraction and reward intervals include zero. NF retains higher post-intervention reward and a lower near-setpoint fraction; its absolute-error contrast remains uncertain. This does not establish an absence of benefit or equivalence.

This report supersedes the October 18 primary numerical analysis for the corrected model. The manuscript itself has not been rewritten. `MANUSCRIPT_EDITS.md` identifies the affected claims and supplies replacement prose.

## Comparable post-intervention estimates

The analysis retains the paper’s primary estimand and method: phase 3 CDR minus CCC means, two-sided Welch tests, unadjusted 95% confidence intervals, and Holm adjustment across 18 comparisons (nine outcomes × two policies). Phase 2 is a separate exploratory family. No outcome or condition was selected to recover the old result.

| Policy / outcome | Previous difference [95% CI] | Corrected difference [95% CI] | Corrected Holm p |
|---|---:|---:|---:|
| HRL: Mean absolute h | -7.365 [-10.594, -4.135] | -3.332 [-9.486, 2.823] | 1.0000 |
| HRL: Population SD of h | -4.046 [-6.451, -1.641] | -2.096 [-5.723, 1.532] | 1.0000 |
| HRL: Objective reward per phase | 5.094 [2.639, 7.549] | 0.838 [-1.695, 3.371] | 1.0000 |
| HRL: Fraction within ±5 | 0.015 [0.004, 0.025] | 0.009 [-0.005, 0.023] | 1.0000 |
| NF: Mean absolute h | 1.637 [-22.806, 26.080] | 24.626 [-28.795, 78.046] | 1.0000 |
| NF: Population SD of h | -3.982 [-15.579, 7.615] | 14.621 [-19.789, 49.032] | 1.0000 |
| NF: Objective reward per phase | 2.851 [2.170, 3.532] | 2.802 [1.737, 3.867] | 5.18e-06 |
| NF: Fraction within ±5 | -0.019 [-0.026, -0.013] | -0.018 [-0.023, -0.014] | 3.12e-13 |

## Corrected phase-3 outcomes

| Policy | Outcome | CDR mean | CCC mean | Difference [95% CI] | Holm p |
|---|---|---:|---:|---:|---:|
| HRL | Mean absolute h | 15.144 | 18.475 | -3.332 [-9.486, 2.823] | 1.0000 |
| HRL | Population SD of h | 15.251 | 17.347 | -2.096 [-5.723, 1.532] | 1.0000 |
| HRL | Objective reward per phase | 80.186 | 79.349 | 0.838 [-1.695, 3.371] | 1.0000 |
| HRL | Fraction within ±5 | 0.316 | 0.307 | 0.009 [-0.005, 0.023] | 1.0000 |
| HRL | RMS h | 19.265 | 23.526 | -4.262 [-11.425, 2.901] | 1.0000 |
| HRL | Signed mean h | -0.429 | 8.275 | -8.704 [-15.273, -2.136] | 0.1145 |
| HRL | Logged h loss | -475.066 | -409.067 | -65.999 [-82.369, -49.629] | 3.12e-13 |
| HRL | Logged h gain | 670.312 | 621.157 | 49.155 [24.740, 73.569] | 0.0012 |
| HRL | Logged harvest count | 31.376 | 29.468 | 1.908 [0.690, 3.126] | 0.0287 |
| NF | Mean absolute h | 66.210 | 41.584 | 24.626 [-28.795, 78.046] | 1.0000 |
| NF | Population SD of h | 39.565 | 24.943 | 14.621 [-19.789, 49.032] | 1.0000 |
| NF | Objective reward per phase | 21.327 | 18.525 | 2.802 [1.737, 3.867] | 5.18e-06 |
| NF | Fraction within ±5 | 0.050 | 0.068 | -0.018 [-0.023, -0.014] | 3.12e-13 |
| NF | RMS h | 77.225 | 48.222 | 29.002 [-34.512, 92.517] | 1.0000 |
| NF | Signed mean h | 8.871 | -9.505 | 18.376 [-35.865, 72.617] | 1.0000 |
| NF | Logged h loss | -453.455 | -392.484 | -60.971 [-81.815, -40.127] | 2.6e-07 |
| NF | Logged h gain | 693.229 | 587.756 | 105.473 [-3.962, 214.909] | 0.6472 |
| NF | Logged harvest count | 28.056 | 26.876 | 1.180 [-0.283, 2.643] | 1.0000 |

HRL also shows more logged gain and harvests and more negative logged loss after CDR. Those changes do not establish better regulation: the regulation/reward contrasts remain uncertain. Signed mean h has an unadjusted interval below zero, but its Holm p is about 0.114; signed mean is not absolute setpoint distance.

## Phase separation

| Policy / condition | MAE phase 1 | MAE phase 2 | MAE phase 3 | Reward phase 1 | Reward phase 2 | Reward phase 3 |
|---|---:|---:|---:|---:|---:|---:|
| HRL-CDR | 11.216 | 319.349 | 15.144 | 82.841 | 13.344 | 80.186 |
| HRL-CCC | 11.216 | 12.764 | 18.475 | 82.841 | 81.796 | 79.349 |
| NF-CDR | 41.590 | 460.549 | 66.210 | 22.719 | 0.000 | 21.327 |
| NF-CCC | 41.590 | 52.955 | 41.584 | 22.719 | 20.279 | 18.525 |

Both policies have much larger absolute errors during the intervention. All NF-CDR phase-2 reward totals are zero. The logged phase-2 physical loss is also zero, so this is a combined physical and perceptual intervention. The large whole-trial MAEs reported at delivery (115.236 HRL-CDR and 189.449 NF-CDR) average all three phases; they are not the paper’s post-intervention endpoint. Whole-trial reward sums three phases, while the paper reports reward per 100-second phase.

The new HRL control performs better in absolute terms: post-phase CCC MAE is 18.475, compared with 30.109 in the previous analysis. CDR MAE is also lower (15.144 versus 22.744), but its advantage over its contemporaneous control is smaller and uncertain. Better trained regulation and a decanalization benefit are different questions.

## Sensitivity, matching and tails

The baseline-change Welch analysis, paired sensitivity analysis across trial IDs, and restriction to exactly matching initial scenes all retain uncertain HRL MAE/reward contrasts and a positive NF reward contrast. There are 235/250 exact initial scene hashes in each policy family. All nine baseline metrics, recorded initial h, RNG capture and recurrent-memory starts match for 250/250 CDR/CCC trial IDs within each family. Scene matching does not establish complete engine-state identity, so the Welch analysis remains primary.

The earlier delivery’s bootstrap is a separate sensitivity analysis: mean(P3−P1, CDR) minus mean(P3−P1, CCC), with independent trial resampling per condition. It uses 10,000 resamples, RNG seed 551901. It does not replace the phase-3 Welch intervals above. Its point estimates coincide here because the recorded baseline means match.

| Policy | Baseline-change metric | Estimate | Bootstrap 95% interval |
|---|---|---:|---:|
| HRL | mae | -3.332 | [-10.137, 1.919] |
| HRL | reward | 0.838 | [-1.558, 3.193] |
| NF | mae | 24.626 | [-25.451, 88.006] |
| NF | reward | 2.802 | [1.631, 3.984] |

Large trial errors make the absolute-error means imprecise. These are retained outcomes from fixed-horizon evaluation, not grounds for removing trials. Descriptive medians and maxima below are diagnostics, not replacement primary endpoints.

| Policy / condition | Phase-3 median MAE | Phase-3 maximum MAE |
|---|---:|---:|
| HRL-CDR | 10.189 | 111.533 |
| HRL-CCC | 10.965 | 591.914 |
| NF-CDR | 23.425 | 6043.411 |
| NF-CCC | 20.521 | 2496.658 |

## What changed in the model and selection

Anticipated pellet gain now sums every intersected pellet. Traversal loss uses ray length inside each tile and supplied speed, with the starting tile’s existing entry count and one prospective entry for future tiles. Passive loss is charged once for the whole horizon at the correct update rate, and the erroneous final 0.2 scale is removed. The corrected asset passed 23 native collision-based checks. Prediction still approximates straight constant-speed travel through axis-aligned tiles; it does not predict turns, respawns or exact body-overlap timing. Experimental decanalization intentionally continues to zero anticipated loss.

Both HRL and NF receive these features. The retained observation schema has 11 scalar values (one collision feature, seven ray values, perceived gain and loss, signed setpoint distance), plus 64 recurrent memory values. NF is a reward-function comparison with a recurrent PPO policy, not an agent deprived of anticipation.

The selected HRL policy was newly trained with corrected inputs: gather 75, 750,000 collected transitions, nominal update label 2400. The selected NF policy retains the previous winner’s weights (label 5000); it outperformed fresh and refined candidates under corrected inputs. Do not describe both selected policies as newly retrained. Screening used eight CCC trials at seed 20001; independent confirmation used 32 CCC trials at seed 30001; final evaluation used seed 10001. Selection minimized HRL MAE and maximized actual NF reward. All candidate selection preceded the final test.

Fresh HRL training ended at 2.56 million transitions after deterioration/plateau checks; a lower-rate refinement did not improve its independent confirmation score. Fresh NF training ended at 5.38 million transitions with a transport failure before the planned 640-gather minimum, and its saved best checkpoint was evaluated. This is not evidence of convergence or global optimality. The protocol’s stopping revision and failure are preserved in inputs/PROTOCOL.md and training_closeout.json.

## Scope and verification

All 1,000 trials, 3,000 phases and 6,000,000 decisions are included. This analysis rechecked 3,000 decompressed scene hashes and 20 model-file hashes on import (eight selected files and twelve actually loaded inference files), all completion receipts, corrected-asset provenance, JSON/YAML agreement, finite outcomes, fixed phase durations, and zero traversal-rate factor. The independent R implementation reproduced 108 descriptive rows, 36 primary and 144 sensitivity contrasts, including intervals and Holm corrections.

Homeostatic metrics remain event/update sampled, not uniformly timed. Rewards are actual callback totals and use different scales across families. One initialization seed per underlying policy cannot establish robustness across training runs, a reward-by-intervention interaction, or effects in biological organisms. The old/new comparison changes both anticipation and the selected HRL policy and therefore does not isolate the causal contribution of the code repair. Legacy traversal-factor files use earlier observation code/policies and cannot be pooled with the corrected model.

Full raw scenes, checkpoints, scripts and logs remain in the source reproducibility archive. Source paths and SHA-256 hashes are in source_manifest.json; source_audit.json records external-file verification. The manuscript repository’s existing Unreal submodule still points at the earlier source revision and must be updated to a published corrected revision/package before submission.

## Subsequent HRL traversal-factor sensitivity

A separate corrected-anticipation sweep evaluates factors 0, 1, 2, 4 and 7 with the same frozen HRL policy, 250 trials per factor, and the existing CCC reference. Post-phase MAE ranges from 14.789 to 15.506 and reward from 79.827 to 80.186. The manipulation substantially changes retained tile counts, but the planned performance contrasts and sensitivity analyses remain uncertain. The author subsequently confirmed factor 1 as the intended primary condition; the factor-0 result above is retained only as reference evidence. See [the current primary HRL analysis](primary-factor1/RESULTS.md) and [the completed factor sweep](plasticity/RESULTS.md).

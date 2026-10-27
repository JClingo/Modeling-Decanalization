Both conditions trained with 100-second episodes and the original learning settings. The sole manipulated setting disables whole-world resets on policy updates; timed and failure resets remain.

Three matched initialization seeds per condition, selected on eight CCC trials and compared on 16 separate continuous-homeostasis CCC trials. Baseline training and any matching completed evaluations were reused.

| Condition | Mean time-averaged absolute h | SD across trained policies | Per-seed MAE |
|---|---:|---:|---|
| baseline | 35.130 | 23.200 | 25.519, 61.591, 18.281 |
| canalization-100s-persistent | 66.052 | 36.543 | 88.512, 85.758, 23.886 |

Preserve minus reset: mean MAE difference 30.922; exploratory paired 95% t interval [-41.824, 103.668]; exact two-sided sign-flip p=0.250. Negative differences favor preserving world state.

Three training seeds limit precision; repeated trials do not increase training replication. This tests the complete reset-on-update behavior, not tile-only persistence or the causal effect of canalization itself. No CDR comparison is included. Evaluation lasts 300 seconds with h and tile history retained between reporting windows; the common inherited phase-start velocity initialization remains. The reserved final-test seed was not used. No candidate is automatically promoted.

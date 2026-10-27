This exploratory screen compared four HRL training conditions with three matched training seeds per condition.

Each selected policy received 16 continuous-homeostasis CCC trials on an environment seed excluded from checkpoint selection. The initial h values and resource layouts match across policies. Variation is summarized across trained policies.

| Training condition | Mean time-MAE | SD across policies | Per-seed MAE | Time within ±5 | Final-window revisit fraction |
|---|---:|---:|---|---:|---:|
| baseline | 35.130 | 23.200 | 25.519, 61.591, 18.281 | 14.2% | 65.4% |
| canalization-300s | 97.103 | 74.437 | 39.972, 70.055, 181.281 | 7.8% | 71.9% |
| canalization-persistent | 26.493 | 18.874 | 17.176, 48.213, 14.089 | 17.2% | 51.5% |
| canalization-aware | 242.221 | 157.194 | 365.609, 65.239, 295.814 | 3.3% | 62.4% |

The preserved selected HRL policy scored 11.207 time-MAE in the same comparison environments. It is one fixed policy benchmark.

Planned contrasts report the second condition minus the first; negative MAE differences favor the second condition.

| Contrast | Mean MAE difference | Exploratory paired 95% t interval | Exact sign-flip p, Holm adjusted |
|---|---:|---|---:|
| canalization-300s minus baseline | 61.972 | [-155.500, 279.444] | 0.750 |
| canalization-persistent minus canalization-300s | -70.610 | [-278.394, 137.175] | 0.750 |
| canalization-aware minus canalization-persistent | 215.728 | [-219.702, 651.158] | 0.750 |

Three training seeds provide limited inferential precision. Repeated evaluation trials do not add independent training replicates. This screen does not isolate the causal benefit of traversal-dependent costs because it has no matched condition with those costs disabled. The inherited phase-start velocity initialization is common to every policy; h and tile history carry between reporting windows.

Candidate snapshots, raw comparison scenes, traversal histories, loaded-model receipts and training diagnostics are retained beside this note. The production assets, selected policies and existing paper data remain preserved. No candidate is promoted automatically.

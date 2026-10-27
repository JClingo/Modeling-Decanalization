As of 27 October 2026, 11 of 12 policies completed training and checkpoint
selection. These are checkpoint-selection scores on eight continuous-homeostasis
CCC trials (environment seed 41001), not the planned independent comparison.
The metric is time-averaged absolute h; smaller values mean closer regulation
around zero. Each row averages the completed, independently trained policies.

| Training condition | Completed policies | Mean selection MAE | Per-seed selection MAE (1201, 2301, 3401) |
|---|---:|---:|---|
| Original 100-second world, reset on updates | 3/3 | 59.40 | 19.88, 139.44, 18.88 |
| 300-second world, reset on updates | 3/3 | 82.79 | 15.76, 66.14, 166.45 |
| 300-second world, history persists across updates, original learning settings | 3/3 | 22.72 | 12.09, 42.17, 13.91 |
| Persistent 300-second world, proposed learning settings | 2/3 | 143.75 | 256.61, 30.89, incomplete |

Preserving traversal history with the original learning settings is the most
promising completed condition. Longer episodes alone were unreliable, and the
combined proposed learning changes did not improve the available scores.
There is substantial variation across training seeds. The incomplete fourth
condition and reuse of selection environments preclude a final ranking.

The preserved existing selected policy scored 10.65 in the same selection
environments. This is one fixed benchmark, not an additional training replicate;
the new candidates have not established an improvement over it.

The final proposed-settings seed failed at gather 162 (1.62 million collected
transitions): Unreal reported a communication timeout waiting for the policy.
The original attempt and its checkpoints remain in their original directory.
It has no successful training-completion receipt. Its best selection score of
205.71 is excluded from the completed-policy mean above. The underlying cause
of the communication failure has not been established.

`recover_study.py` restarts only that seed from initialization with the same
frozen learning, environment and selection settings. `recovery.json` records
the explicit directory override; the retry is not an exact continuation because
optimizer and world state were not saved. The original postprocessing failure
is retained in `attempts/`. After successful recovery, the pipeline evaluates
all selected policies on the separate comparison seed 51001 and writes final
regulation and traversal measurements. No candidate has been promoted and the
paper results remain unchanged.

Training/evaluation audit: paired rollouts on identical initial environments.
| Saved policy | Mean-action MAE (noise 0) | Sampled-action MAE (noise 1) |
|---|---:|---:|
| selected-reference | 11.151 | 166.692 |
| baseline-1201 | 66.203 | 58.741 |
| baseline-2301 | 188.488 | 237.243 |
| combined-1201 | 284.514 | 427.544 |

These are repeated rollouts of fixed policies, not new independent training replicates. Noise changes behavior and is diagnostic; all primary screens retain mean-action evaluation. Training ends outside |h|=100, whereas inference records the entire fixed horizon. Observation scaling and native memory-reset semantics were checked against the authored graphs and installed engine source.

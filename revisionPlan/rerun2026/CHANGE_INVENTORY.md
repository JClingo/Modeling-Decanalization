# Consolidated project changes

This update supersedes the earlier package's unresolved measurement descriptions and legacy primary results. `historical-audit/` retains the earlier comparison with the manuscript for traceability, not as the current Methods specification.

## Reward and observation

- HRL: r = dt R/[1 + (h/S)²], with dt = 0.05, R = 1, and S = 25. This replaces the paper's exponential improvement/worsening formulation. It is an ongoing reward near the setpoint.
- NF: r = max(|h_previous| − |h|, 0) R/S only when current h < 0, otherwise zero. It has no dt factor and no negative worsening penalty. Reaching or crossing zero earns zero under the implemented strict condition. This replaces the paper's punishment-based thermostat account.
- Training fails at |h| > 100 (HRL terminal reward −1; NF zero), replacing the manuscript's threshold 150. Evaluation continues to its fixed horizon beyond this threshold. NF reward history is seeded at phase starts to exclude artificial reset credit.
- Reward uses decision-to-decision cached state; policy observation now reads live GameMode h, replacing the stale agent-state source. The observation/action/recurrent-state schema remains 11/1/64 in the retained selected configurations.
- Both legacy evaluation accumulators were removed. Actual callback output is gathered once per evaluation decision. The new YAML is schema 2 and records duration in seconds.

## Training and selection

Snapshots were chosen by relative performance: mean h closer to zero and highest mean reward for HRL, highest mean reward for NF. The selected triplets are HRL 10000 and NF 5000; these are checkpoint labels rather than evaluation trial counts. The selection account is author-confirmed, not a reconstructed exhaustive candidate ranking. Training settings below match the retained snapshot triplets and effective NFStable1 overrides.

| PPO setting | HRL effective | NF effective |
| --- | --- | --- |
| IterationNum | 1000000 | 1000000 |
| LearningRatePolicy | 0.0001 | 3e-05 |
| LearningRateCritic | 0.001 | 0.0003 |
| LearningRateDecay | 1 | 1 |
| WeightDecay | 0.0001 | 0.0001 |
| PolicyBatchSize | 2056 | 2056 |
| CriticBatchSize | 4096 | 4096 |
| PolicyWindow | 16 | 16 |
| IterationsPerGather | 32 | 8 |
| CriticWarmupIterations | 8 | 0 |
| EpsilonClip | 0.2 | 0.1 |
| ActionSurrogateWeight | 1 | 1 |
| ActionRegularizationWeight | 0.001 | 0 |
| ActionEntropyWeight | 0.001 | 0 |
| ReturnRegularizationWeight | 0.0001 | 0.0001 |
| GaeLambda | 0.95 | 0.95 |
| AdvantageNormalization | True | True |
| AdvantageMin | -10 | -10 |
| AdvantageMax | 10 | 10 |
| UseGradNormMaxClipping | True | True |
| GradNormMax | 0.5 | 0.25 |
| TrimEpisodeStartStepNum | 0 | 0 |
| TrimEpisodeEndStepNum | 0 | 0 |
| Seed | 1234 | 1234 |
| DiscountFactor | 0.99 | 0.99 |
| Device | GPU | GPU |
| UseTensorBoard | True | True |
| SaveSnapshots | True | True |

NFStable1 additionally fixes exploration SD at 0.15, skips actor updates when sampled approximate KL exceeds 0.015, detaches encoder features for critic updates, and discards its initial legacy-variance rollout. HRL uses the common PPO adapter. Common repairs preserve terminal credit and episode boundaries, bootstrap time-limit truncation, center advantages, support negative advantages with corrected clipping, and reject nonfinite updates. The configured 1,000,000-iteration limit is not an achieved training duration. The old claim that only reward differs between HRL and NF should be removed.

## Environment and protocol

The saved implementation and runtime records use a 50 × 50 tile grid, 1,000-unit spacing, a 0.05 resource-spawn probability per cell, ordinary resource impacts drawn from [5,35], decanalized resource impact 35, and 0.01 s resource respawn. Tile base impact is 10. BaseMaxSpeed is 5,000 cm/s. Passive-loss parameter is 0.5 with periodic homeostatic updates every five decisions; the recorded history also includes event/update samples. Do not equate history length with decision count or use it to infer elapsed time.

Training and evaluation environment seeds are 1 and 10001; PPO seed is 1234. Evaluation uses fixed policy weights and zero action noise. Each primary condition has 250 three-phase trials, with phase boundaries at decisions 2000/4000/6000, or 100/200/300 s. The primary tile-rate factors observed in each run are listed in `validation.json`; supplementary counted visits are separately author-confirmed as 4/6/7.

Full trial resets clear recurrent memory, reward/termination caches, perception, tile history, resource availability/timers, and stale movement input. Initial h is sampled once in [−15,15] and restored at phase boundaries. Within-trial boundaries preserve recurrent memory and scene history except for the specified intervention; forward velocity is reinitialized. The post-intervention phase is therefore performance after state reinitialization, not recovery of a continuous physiological h trace. Recanalization retains the specified halving/flooring of traversal history.

## Measurement and provenance

Both dispersion helpers now compute sqrt(sum((h − mean(h))²)/N). Rerun sidecars add N, MAE, RMS, fraction of samples within ±5, loaded network snapshots/hashes, runtime parameter records, asset/logger hashes, phase-start scene captures, recurrent memory, and RNG state. These describe recorded execution, not a complete engine replay. Files named NF are accepted only when their loaded triplet matches the selected NF training record.

The NF control was run from a copy of the saved project with TrialSequenceOrder = ccc and absolute paths to the same selected NF triplet. The source editor assets were not overwritten. Its smoke test exactly matched the running NF-CDR first-phase scene, state, memory, and outcomes. Source asset hash differences caused by the control configuration should not be mistaken for a different reward implementation.

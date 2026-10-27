This study tests HRL learning in an environment whose traversal costs decrease
with repeated tile entry. The frozen protocol is in
`comparison_protocol.json`.

The 27 October status and checkpoint-selection scores are documented in
`PRELIMINARY_RESULTS.md`. Eleven policies completed; the final seed encountered
an Unreal–trainer communication timeout. `recover_study.py` retries that seed
under the same frozen settings and then runs the independent comparison.
The failed attempt is preserved; `recovery.json` records the retry mapping.

The authorized follow-up in `history100/` adds the missing 100-second condition
with world resets disabled on policy updates. It reuses the completed 100-second
baseline and queues sequentially behind this study. Its protocol, process,
status and eventual paired results are recorded separately in that folder.

The four conditions are the original 100-second world with resets on policy
updates, 300 seconds with the same resets, 300 seconds retaining history across
updates, and that persistent world with the proposed learning settings.
All use the original quality reward with scale 25 and +1 count per entry.
This screen tests the combined learning proposal; it does not test every reward
and optimizer alternative implemented in the learning module.

Each condition uses training seeds 1201, 2301 and 3401. Training can collect up
to two million transitions per policy. Held-out checkpoint selection uses eight
trials and can stop after at least 100 gathers and four checks without a 0.5%
material improvement. The smallest observed MAE is retained even when a smaller
improvement does not reset stopping patience.

After all training finishes, the queued pipeline evaluates every selected
policy on 16 trials with a separate comparison seed. It then saves:

- `RESULTS.md` and `results.json`: policy-level comparison and planned contrasts.
- `per_policy.csv` and `per_phase.csv`: regulation and traversal measurements.
- `performance_and_exposure.png` and `.svg`: independent performance and sampled
  training episode duration, with one point per trained policy.
- `selection_curves.png` and `.svg`: checkpoint-selection curves.
- `policies/`: selected candidate snapshots, without production promotion.
- `inputs/`: raw comparison scenes, traversal histories, loaded-model receipts,
  native variants and training diagnostics.

`postprocessing_status.json` records the pipeline stage. Individual active
training receipts are under
`/private/tmp/hrl-canalization-study-20261026/*/training_progress.json`.
`interim_selection.png` is an explicitly interim plot and is not a final result.

The main dispatcher runs the two reset controls. Two parallel workflows run
the persistent conditions with separate native projects and socket ports.
`finish_study.py` waits for both dispatchers, verifies every completed selection,
runs the independent comparisons, audits matched initial environments and writes
the analysis and figures automatically. No additional user action is required
for these queued stages. A failure is recorded in the postprocessing status.

The screen uses continuous-homeostasis CCC evaluations: h and tile counts carry
between three 100-second reporting windows. The inherited phase-start velocity
initialization remains common to all policies. Training episode lengths are
sampled every 100 decisions; reported durations are observed lower bounds.
Three trained policies per condition make this an exploratory screen. There is
no matched condition with traversal-dependent costs disabled, so this study
does not isolate their causal benefit.

`frozen_runner/`, `frozen_dependencies/` and `frozen_source/` retain the runner,
shared code and protected baseline artifacts. Their hashes are recorded in
`frozen_artifacts_manifest.json`. Keep the active `learning/hrl` sources fixed
until the study finishes; the pipeline checks their frozen hashes. Production
assets, selected policies and existing paper results are preserved.

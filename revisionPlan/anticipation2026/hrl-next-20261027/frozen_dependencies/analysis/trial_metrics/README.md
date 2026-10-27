# Trial metrics and rerun protocol

Schema 2 replaces the legacy evaluation score with the sum of actual `TrainingEnv.GatherAgentReward` outputs. Evaluation scores all 2,000 decisions per phase, including states beyond the training failure boundary. Training retains its terminal behavior. NF state resets receive no progress credit. Both Blueprint dispersion helpers now calculate population standard deviation.

Use the existing inference workflow with `IsTrialMode = true`, `Run Inference = true`, the selected encoder/policy/decoder triplet, and the desired `IsHRL` and `TrialSequenceOrder` (`cdr` or `ccc`). Preserve the paper's condition-specific traversal settings. Reload the changed assets in Unreal before running; do not save stale in-memory Blueprint versions over them. Run the editor executable with `-UseFixedTimeStep -FPS=20` and PythonScriptPlugin enabled. The logger rejects a different timestep.

Outputs in `Saved/TrialResults`:

- `<run>.yml`: existing trial/phase layout, corrected reward and SD, duration 100 seconds, schema version 2.
- `<run>.metrics.json`: sample count, additional regulation summaries, runtime/training parameters, source hashes, snapshot identity, per-phase RNG state and policy memory.
- `<run>.provenance/`: copies of the actual loaded networks and compressed phase-start scene records.

Retain all three together. A completed run must have sidecar status `complete` and a successful completion receipt. Matching a training manifest requires all three loaded snapshot hashes; an unmatched checkpoint is explicitly recorded without attributing another checkpoint's training settings. The selected NF settings already match the NFStable1 trainer's effective overrides; this change records those values rather than changing the training recipe.

Homeostatic summaries use the existing event/update sample history. The within-5 statistic is a fraction of samples, not elapsed time. Phase-start scenes are captured at the first scoring decision; they and RNG records improve provenance but are not a full engine replay format. The scorer currently assumes the project's single registered agent (ID 0).

Historical YAML files remain untouched and must not be pooled with schema-2 rewards or dispersion measures. The paper package's `build_analysis.py` intentionally reproduces the frozen legacy analysis. Replace its input/measurement contract in a new analysis when all four primary reruns are available; do not overwrite the frozen input copies.

## Implementation and validation

`patch_metrics.py` modifies exported copies of GameMode, TrainingEnv, and BFL_Common. It removes both legacy reward accumulation paths, adds one native reward gathering call per evaluation decision, and adds boundary-only Python hooks. `compile_metrics.py` compiles only the isolated test project. Production-default compiled copies are retained separately from test-only configuration changes under `Saved/TrialMetricsFix/compiled`; original assets are backed up under `Saved/TrialMetricsFix/backup`.

`validate_callbacks.py` tests population SD, both reward objectives inside/outside the training boundary, repeated-state rewards, and phase-reset credit. `configure_test.py` configures two-trial isolated tests for either objective and order. `validate_logs.py` checks complete schema-2 runs, all 2,000 decisions per phase, duration, Blueprint/Python SD agreement, snapshot hashes, scene hashes, and reward bounds. See `callback_validation.json` and `runtime_validation.json` for results. These short tests are engineering validation, not paper datasets.


Validation outcome: 40 native callback cases passed; all four objective/order combinations completed two trials each (24 phases total) with matching Blueprint/Python statistics, valid provenance hashes, and successful save receipts. No Python or Learning Agents errors appeared in the final four run logs. Test-only instance-editable flags, two-trial limits, and absolute snapshot paths were not installed as production defaults.

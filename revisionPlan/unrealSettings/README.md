# Unreal settings extracted for the manuscript review

Extracted on 2026-09-14 with **Unreal Engine 5.5.4 (40574608)**. No training, evaluation, asset saving, or source-asset edits were performed. The exporter loaded assets into a separate command-line Unreal process and exported native object text and network snapshots.

The main findings are incorporated in `main.tex` and `appendix.tex`. **Author-directed reporting basis:** the recovered implementation takes precedence over conflicting manuscript descriptions. For environment values that differ across archives, the manuscript uses the May 25 study-era revision, chosen as the nearest retained commit before the final May 26 logs: grid-width parameter **25** and base passive-loss parameter **0.05**. The reporting choice is explicit in the appendix; it does not create a missing historical run manifest. Recovered HRL snapshot 1000 and NF snapshot 4000 supply the model identifiers. **Author-confirmed trial procedure:** NF and HRL shared manager/environment settings and loaded their corresponding encoder, policy, and decoder snapshots. Differences between dated saved versions do not represent differences between the trial conditions.

## What was recovered

- `settings.json`: reviewed defaults, graph constants, source file/line references, checkpoint matches, and the two relevant complete PPO configurations.
- `unreal-settings-evidence.zip`: native Blueprint graphs, class defaults, placed Landscape actors, world settings, exported network binaries, original trainer JSONs, and searchable graph summaries. Archive paths are relative to this directory and match `settings.json`.
- `source_manifest.json`: original working-tree asset hashes, Git revision, and pre-existing local changes.
- `training_configs.json`: inventory of **1,208** historical training configurations, grouped into **35** distinct profiles.
- `checkpoint_inventory.json` and `checkpoint_architectures.json`: **103** retained historical snapshots, plus decoded architectures of the exported asset snapshots. Small learned normalization arrays are included; large weight arrays are represented by shapes and counts.
- `evaluation_data_provenance.json`: byte-identical matches between the analysis inputs and original trial logs.
- `training_event_summary.json`: retained TensorBoard step ranges for the two matched training runs.
- `representative_training_dashboard.png`: the author's illustrative TensorBoard screenshot, supporting the description of visual model selection; not an identified final-run record or a measure of completed environment steps.

## Provenance: which version is being described?

Three versions were exported independently:

| Export label | Source | Interpretation |
|---|---|---|
| `study_candidate_5e508dd` | Git `5e508dd8b782`, May 25, 2025 | Adopted manuscript source for environment settings; closest retained commit before the final May 26 evaluation logs. The archive label is retained for traceability. |
| `committed_b2ec222` | Git `b2ec222f8654`, July 8, 2025 | Repository HEAD. Some assets were changed after the evaluations. |
| `current` | Working tree on extraction date | Contains the user's pre-existing local Blueprint changes. |

The extraction copies are under the Unreal project's ignored `Saved/SettingsExportSnapshots/` directory. Neither Git branches nor the working-tree Unreal assets were changed.

**Later workspace changes:** during the steering follow-up, `BP_AgentInteractor.uasset` and `BP_AgentManager.uasset` no longer matched their original capture hashes. The retained `current` export describes the earlier extraction, not those latest saves. The repackaged evidence preserves the original source manifest, exports, and captured project configuration; `evidence_manifest.json` records the differing workspace hashes. The steering audit combines those retained exports, installed engine source, and the author's confirmed live pin observation. No latest-save re-export or runtime controller capture was performed.

### Models and analysis data

SHA-256 equality establishes the following **retained asset identities**, now used for the manuscript's model identifiers under the instruction to rely on the recovered implementation. The author confirmed that each final-trial condition loaded its corresponding NF or HRL encoder, policy, and decoder snapshots. The full filenames and hashes are preserved as evidence; the numeric suffixes come from the recovered files.

| Saved assets | Exactly matching snapshots |
|---|---|
| Current and HEAD policy, encoder, decoder | `HRL-limit (1000 is best)/Training_ppo_sharedmemory_2025-05-25_19-45-04_{policy,encoder,decoder}_1000.bin` |
| May 25 policy, encoder, decoder | `NF-Final/Training_ppo_sharedmemory_2025-05-25_20-27-19_{policy,encoder,decoder}_4000.bin` |

The corresponding original trainer configs have exactly matching timestamps and identical PPO settings, schemas, replay capacities, and network sizes. Their filenames are in `settings.json` and their original contents are in the evidence archive.

The **four final analysis inputs** are byte-identical to these logs, with **50 trials in each**:

| Analysis input | Original log in `logs/trials/` |
|---|---|
| `HRL-CDR.yml` | `HRL-CDR at 2025-5-26 at 13.0.55.yml` |
| `HRL-CCC.yml` | `HRL-CCC at 2025-5-26 at 15.10.11.yml` |
| `NF-CDR.yml` | `NF-CDR at 2025-5-26 at 17.52.52.yml` |
| `NF-CCC.yml` | `NF-CCC at 2025-5-26 at 20.25.20.yml` |

Do not substitute the `*-prelim.yml` files, which have 100 trials each.

**Snapshot loading is the intended procedure:** the inference branch explicitly loads the policy, encoder, and decoder from the selected `*Snapshot` paths. The saved HEAD/current paths point to NF checkpoint 4000 while the embedded assets match HRL checkpoint 1000. This records the saved project state; it is not evidence that HRL trials used NF snapshots. The author confirmed switching all three snapshot files to the corresponding NF or HRL files for the final trials. The saved critic snapshot-loading node is disconnected; its filename is not evidence of a loaded critic.

## Network and trainer settings

The serialized networks, rather than the label `HiddenLayerNum=1`, establish the architecture:

| Component | Recovered structure | Trainable parameters |
|---|---|---:|
| Observation encoder | Learned affine transformations of collision, ray, gain/loss, and setpoint inputs; one affine transform shared across seven rays | 10 |
| Policy | `11 → 128 ELU → 128 ELU → MemoryCell(128 input, 128 output, 64 memory) → 128 ELU → 2`, with affine output scaling | 117,254 |
| Action decoder | Learned affine transform of the two continuous-action distribution parameters | 4 |
| Critic | `[11 encoded observations + 64 policy memory] → 128 ELU → 128 ELU → 1` | 26,369 |
| Entire set | Shared encoder counted once | **143,637** |

The policy's input/output snapshot sizes **75/66** include the 64-value recurrent state; they do not indicate 75 observations or 66 actions. The policy contains **117,250 linear weights and biases**, plus four trainable affine output parameters. The encoder, policy, and decoder used for inference together have **117,268** trainable parameters. Counts follow the installed Unreal PyTorch module definitions; mean/scale arrays are trainable `nn.Parameter`s, not fixed preprocessing constants.

Actual observation schema: **11 values** = collision (1), resource-ray proportions (7), perceived gain and loss (2), setpoint distance (1). Position, heading, and velocity are used to construct observations but are not separate fields in this policy input vector. The Blueprint specifies scale 100 for setpoint/gain/loss observations and a scale-1 continuous `Look` action.

| Training setting | Recovered value |
|---|---|
| Optimizer | AdamW, AMSGrad enabled, separate actor/critic optimizers; encoder included in both |
| Policy / critic learning rate | 0.0001 / 0.001 |
| Exponential learning-rate multiplier | 1 (no scheduled decay) |
| Weight decay | 0.0001 |
| Policy / critic batch size | **2056** / 4096 |
| Recurrent policy window | 16 steps |
| Updates per gather / critic warmup | 32 / 8 |
| PPO clipping epsilon | 0.2 |
| Discount / GAE lambda | 0.99 / 0.95 |
| Advantage normalization | Enabled; min/max **0 / 10** |
| Action surrogate / regularization / entropy weights | 1 / 0.001 / 0 |
| Return regularization weight | 0.0001 |
| Gradient-norm clipping | **Disabled** (stored threshold 0.5 is inactive) |
| Steps trimmed at episode start / end | 1 / 0 |
| PPO RNG seed | 1234 |
| Policy / critic initialization seed | 1234 / 1234 |
| Replay capacity | 1,000 episodes or 10,000 steps |
| Per-agent episode buffer cap | **1,028 steps** |
| Configured optimization iteration limit | 1,000,000; this is not completed training |
| Training timestep | Fixed 20 Hz (0.05 s); physics maximum step set to this interval |
| Training runtime | GPU; TensorBoard and snapshot writing enabled |
| Agent resets | On training begin, on training update, and via episode completions |
| Inference action noise | **0**, on the connected `RunInference` node |

Unreal's trainer truncates at the episode-buffer cap independently of the Blueprint time limit. At one trainer step per fixed frame, 1,028 steps correspond to **51.4 simulation seconds**. The recovered Blueprint also specifies termination beyond `abs(h) > 150` and time truncation when episode time is **greater than 100 s**. The main text and appendix now use these recovered limits in place of the former “60 seconds or |h| > 50” claims, as directed by the author. The Blueprint is the source for the timer and homeostatic threshold; those fields are not stored in the trainer JSON.

TensorBoard retains HRL optimization indices **0–5055** and NF indices **0–4287**. The NF event file is in a renamed `NF-Final` folder and its filename timestamp is three seconds after the matching trainer start time. These are retained records, not an assertion that no later unlogged updates occurred. Checkpoint suffixes 1000/4000 are update labels, not environment-step totals. The backend writes checkpoints while logging a completed 32-update gather, so converting suffixes directly to precise training-transition counts would be incorrect. The author has supplied the average-reward/plateau model-selection procedure below. Exact environment-step totals and when every exploratory run was ultimately stopped remain unrecorded; selecting an earlier snapshot does not imply that the run itself ended at that point.

## Environment, movement, and evaluation

All values below have source locations in `settings.json` or in the named native Blueprint export. The columns compare saved project versions, not NF and HRL conditions. The author confirmed that the final NF and HRL trials shared their environment and manager settings.

| Setting | May 25 candidate | HEAD/current |
|---|---|---|
| Map / game mode | `/Game/Level/Landscape` / `/Game/Agent/BP_GameMode` | Same |
| Grid-width parameter / spacing | **25 / 1000 Unreal units** | **50 / 1000** |
| Pellet spawn probability per candidate location | 0.05 | Same |
| Pellet impact range / decanalization impact | Uniform random 1–20 / 20 | Same |
| Pellet respawn timer | 0.01 s | Same |
| Base passive-loss variable | **0.05** | **0.2** |
| Base tile-impact parameter | 10 | Same |
| Traversal-count increment | 1 normally; 3 during decanalization | Same |
| Recanalization traversal-count update | `floor(count / 2)` | Same |
| Training initial h | -15, assigned by `ResetValues` | Same |
| Inference initial h | Random float in [-15, 15], via shared stream | Same |
| Default h on agent class | -25; overwritten by game-mode state | Same |
| Environment stream | Serialized initial seed 7; BeginPlay explicitly sets seed **1** | Same |
| Spawn yaw-input randomization | 0–180 before controller scaling | Same |
| Ray angles | **-45, -22.5, -11.7, 0, 11.7, 22.5, 45 degrees** | Same |
| Ray horizon / trace radius | 10,000 / 75 Unreal units | Same |
| Base speed variable | 1,000 | Same; not the effective movement speed |
| HRL positive/negative scales | 0.005 / 0.0001 | Same |
| NF scale variable | 50 | Same |
| Phase transitions | Cumulative ticks 6,000 / 12,000 / 18,000 | Same |
| Logged `duration` | Constant 3,000 | Same |
| Periodic summary sampling | Every fifth game-mode tick | Same |
| Trials-to-run parameter | 50 | Same |

The grid-width parameter is reported as a parameter rather than assumed to be the realized tile/pellet count. The actual spawner graphs, inclusive loop bounds, random occupancy, and placed actors are included in the export. A particular realized environment was not generated during this extraction.

The Blueprint's tile-impact update includes `10 / (OverlapCount + 1)` multiplied by its stored `Delta Seconds`; overlap increments and the phase-return flooring are explicit. Several unused or disconnected experimental nodes also exist. For example, `ImpactLossFactor=0.9`, `LookCost=0.5`, and `DecanalizationFactor=0.1` being stored as defaults does **not** establish that those values contribute to the executed reward. Do not build a reward equation from variable names alone.

The intervention sets the resource's **actual `HomeostaticImpact`** to 20, the tile's to zero, and the game-mode passive-loss variable to zero; the same resource impact feeds the collection event. Thus “perceived value only” is too narrow for the exported implementation.

The action is a continuous scalar passed from `GetFloatAction` directly into `AddControllerYawInput`; there is no explicit [-1,1] clamp in that path. The steering audit below traces the Learning Agents sampler and the engine's controller code as well as the Blueprint connection.

The movement graph changes `MaxWalkSpeed` as a function of frame delta: its training branch uses `BaseMaxSpeed × DeltaSeconds × 1`, its non-training branch uses `BaseMaxSpeed × DeltaSeconds × 1080 × 1`; the Landscape path includes a further factor of 1 for inference or 0.33 otherwise. These branches are triggered by changes in delta time. The appendix now reports this formula and the main text no longer claims constant velocity. Evaluation phase duration is reported as **6,000 ticks**; the fixed logged `duration: 3000` is identified as a logging constant. No per-run inference frame-delta trace was recovered, so seconds are not inferred from the training-only 20 Hz setting. These reporting choices resolve the earlier speed/timing confirmation items without a new runtime experiment.

The recovered custom evaluation phase/trial reset routines do not notify Learning Agents to reset policy memory. Registration initializes memory to zero, and training resets do notify the policy. The manuscript now documents that evaluation resets preserve memory for the registered agent across phases/trials within the running session, while weights remain fixed. This does not imply memory persists when the application or policy is recreated. It resolves the reset-policy question from the implementation rather than requiring an author recollection.

### Steering audit following the reported live value of about 4.3

The author reported a live value of approximately 4.3 in `BP_AgentInteractor` and confirmed it appeared on the **`GetFloatAction` output / yaw-input pin**. It is therefore a steering command before controller scaling, not a measured change in actor yaw. This is an author-reported observation, not a runtime measurement collected by the exporter or proof of a limit.

The author subsequently **confirmed the runtime yaw scale is 2.5**. This resolves the multiplier question; it does not establish a hard bound on the raw action or measure action latency.

The reviewed path is:

1. The policy/decoder produces a mean and log standard deviation for the continuous `Look` action. `DistributionIndependantNormal` returns the mean when action noise is zero; otherwise it samples a Gaussian. Its numerical cap on log standard deviation affects noise magnitude, not the action mean or an angular bound.
2. The continuous schema's `FloatScale=1` multiplies the sampled value. It does not clamp it. `GetFloatAction` copies that value to its output.
3. `BP_AgentInteractor.PerformAgentAction` connects that output directly to `AddControllerYawInput.Val`. The same connection and scale are present in all three exported versions.
4. The engine forwards yaw input to a local PlayerController. With legacy input scaling enabled, `AddYawInput` adds `Val * InputYawScale` to `RotationInput.Yaw`. The project enables legacy scales; the installed `BaseGame.ini` sets yaw scale **2.5**, and the exported game mode selects the native PlayerController class. The reviewed project config and exported graphs contain no yaw-scale override. The author independently confirmed the runtime scale of 2.5; the exporter did not collect that runtime reading.
5. Standard controller rotation processing applies the accumulated rotation input without a frame-delta multiplier. `BP_Agent` enables `bUseControllerRotationYaw`; `APawn::FaceRotation` copies controller yaw to actor rotation. The camera's absolute yaw range/wrapping is not a 4.3-degree-per-tick limiter. Reset events and any other input contributions must be excluded when comparing successive rotations.

With the confirmed runtime yaw scale of 2.5, the author's observed **4.3 on the action/yaw-input wire requests 10.75 degrees**, assuming one action contribution and standard rotation processing. Epic's [AddControllerYawInput documentation](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/GameFramework/APawn/AddControllerYawInput?application_version=5.5) also describes the controller multiplier; the precise implementation above was checked against the installed 5.5.4 source.

No explicit 4.3-degree cap was found. The trained policy's outputs over the states visited are a plausible explanation for an apparent observed ceiling; no global maximum of that trained network was calculated. The PPO action regularizer (weight 0.001) penalizes `abs(mean) + abs(log_std)` and can favor smaller actions, but imposes no hard bound. Neither the schema scale 1 nor PPO clipping epsilon 0.2 limits the steering output to that interval. The manuscript's previous +/-1-degree and 180-tick reversal claims have been removed.

To measure actual rotation and latency in a live capture, record the frame/decision index, `GetFloatAction.OutValue`, control yaw and actor yaw at observation gathering and after rotation processing, and the number of action calls per frame. Use a normalized angular difference across the 0/360-degree wrap and exclude reset frames. A pin watch by itself reports the command before controller scaling. Source hashes and exact source locations for this audit are recorded under `steering_audit` and `engine_sources` in `settings.json`.

### Input accumulation and the observation/action loop

`AddControllerYawInput` does not directly set the actor's heading. `AddYawInput` adds the scaled command to `RotationInput.Yaw`; `PlayerTick` calls `UpdateRotation`, which applies accumulated rotation through the camera/controller and pawn; `TickActor` then clears `RotationInput` at line 5317 of the installed `PlayerController.cpp`. Multiple additions before processing sum together. An input submitted after the controller has completed its tick is ordinarily processed on the following controller tick. This is an input accumulator, not an indefinite replay of a cached policy action.

`ULearningAgentsPolicy::RunInference` explicitly calls `GatherObservations`, `EncodeObservations`, `EvaluatePolicy`, `DecodeAndSampleActions`, and `PerformActions` on each successful invocation. The regular PPO training loop gathers completions/rewards and processes the previous experience before running inference again. Gathering observations does not itself force the world, controller, movement component, or Blueprint-maintained state variables to advance.

The retained `BP_AgentManager` tick is `TG_PrePhysics`, with interval 0, and its BeginPlay graph calls `AddTickPrerequisiteActor` on the agent actors with the manager as prerequisite. This establishes manager-before-agent actor ticks. It does **not** establish manager-before-PlayerController or manager-before-CharacterMovementComponent; actor prerequisites do not automatically cover owned components. Native controller possession establishes controller-before-pawn movement, separately. No explicit manager/controller dependency was found in the retained Blueprint graphs. See Epic's [tick dependency documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/actor-ticking-in-unreal-engine).

An unchanged heading read immediately after the yaw-input node is therefore expected and does not demonstrate a learning defect. The relevant diagnostic would be whether the next decision and reward calculation observe the effects of the previous action. Additional or inconsistent latency could affect learning, but neither latency nor an adverse effect has been measured here. Further tick-order tracing is optional troubleshooting, not an outstanding requirement for documenting the recovered implementation. The appendix therefore does not require a new latency experiment or claim any learning impairment.

## Author-confirmed model selection and training exposure

The author confirmed attempting at least **50 parameter variations for NF and at least 50 for HRL**, varying rewards/punishments, resource reward size, movement cost, and related settings through trial and error. This describes attempted configurations, not a fixed count of completed independent-seed replicates. Variation in Blueprint environment/reward settings is not fully represented by the 35 distinct trainer-JSON profiles in the inventory.

Selection used **average training reward**, choosing the best-performing candidate separately within each reward family and a snapshot near the point where its reward-improvement slope approached zero. The stated motivation was to avoid overfitting. No fixed numerical slope threshold was supplied, and a training-reward plateau alone does not demonstrate prevention of overfitting. Final evaluation began after selection. **One selected NF policy and one selected HRL policy** were compared through 50 trials per condition. The main text now distinguishes the exploratory search from these repeated evaluations and notes the limits of generalizing from two selected policies.

"Completed training budget" refers to how much training occurred, not a financial budget or a requirement for a preset stopping limit. The relevant quantity for a selected policy is the training accumulated up to its saved snapshot; later updates in that run and the total effort across the parameter search are separate quantities. Existing records identify the snapshots and retained optimizer indices, but exact cumulative environment-transition counts were not recovered. The manuscript now states this data limitation explicitly rather than retaining a fill-in placeholder. The supplied screenshot is representative and does not establish those totals for the final models.

The numerical implementation discrepancies and author-supplied selection details are now incorporated. Architecture, PPO parameters, observation schema and ray angles, yaw scale, training limits, chosen study-era environment values, phase ticks, movement formula, actual intervention effects, recovered model identifiers, evaluation memory behavior, selection procedure, and number of selected policies are documented. There are no remaining mandatory author-confirmation fields in this implementation appendix. Exact training-transition totals remain unavailable; further yaw timing diagnostics are optional. Separate statistical-analysis review items in the main manuscript are outside this settings extraction.

## Repeat the extraction

The scripts use the two local project paths supplied for this task. Adjust those constants if moving the project.

1. Run `prepare_committed_snapshot.py 5e508dd` and `prepare_committed_snapshot.py HEAD` using ordinary Python. Update the two snapshot-directory names in `run_exports.ps1` if HEAD changes.
2. Run `run_exports.ps1`. It uses Unreal's Python commandlet and needs access to Unreal's normal cache directories. It never starts PIE or saves assets. `UE_SETTINGS_LABEL` selects the output label.
3. Run `summarize_blueprints.py` for each label, then `collect_evidence.py`.
4. Use Unreal's bundled Python for `inspect_checkpoints.py` and `inspect_training_events.py`; these read the installed serializer/NumPy/TensorBoard libraries. Run `build_settings_evidence.py` with ordinary Python.
5. Run `package_evidence.py` to validate hashes and package the native exports and summaries.

If the workspace was intentionally changed after an extraction, `package_evidence.py --package-retained-exports` can repackage that earlier capture with updated notes. It preserves the original captured config, reports source differences in the manifest, and does not claim the exports represent the latest workspace.

Native T3D pin defaults are not effective values when connected. The summaries retain link IDs and graph/node names so the governing variable or expression can be traced. Property exports include both Blueprint defaults and placed actor overrides. The engine-source paths and hashes used to interpret buffers, serialization, and optimizer behavior are preserved in `settings.json`.

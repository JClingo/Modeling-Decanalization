# Unreal 5.5 timing repair

This repair was made in `D:\Dev\decanalization`, starting at commit `b2ec222`,
using the installed Unreal Engine 5.5.4. The pre-existing modification to
`BP_AgentTrainingEnv.uasset` was backed up and preserved byte-for-byte.

## Simulation contract

- Simulation and policy decisions run at 20 Hz (0.05 simulated seconds per step).
  The connected manager Training Game Settings already specified 20 Hz.
  DefaultEngine.ini now supplies the matching inference timestep and maximum
  physics delta. FixedFrameRate controls simulation delta, rather than relying
  on an FPS cap to infer simulation time.
- BP_Agent assigns CharacterMovement.MaxWalkSpeed from BaseMaxSpeed each tick,
  then updates MaxSpeed. BaseMaxSpeed remains 1000 cm/s. CharacterMovement
  integrates movement. The four delta/mode/landscape multiplier nodes were
  removed from the EventGraph, and their execution subtree is disconnected.
- Look remains input per fixed decision, passed to AddControllerYawInput.
  Its effect includes PlayerController yaw scaling. No extra delta multiplier
  was introduced. The validation records the action and resulting yaw.
- PassiveLossRate is loss per homeostatic update, with one update every five
  decisions. Ordinary BasePassiveLossRate=0.2 means 0.8 units per simulated
  second at 20 Hz. Decanalization can still set the loss to zero.
- The old SecondsElapsed counter was renamed HomeostaticPeriodsElapsed,
  including its local result-function argument. One unit means five decisions
  (0.25 simulated seconds), not one second. Existing trial thresholds and
  scheduling keep their existing period-count behavior. Learning Agents
  episode time remains independent. Existing legacy log labels are not a
  promise of physical seconds; convert period counts using 0.25 seconds/unit.
- Tick prerequisites establish GameMode -> manager -> PlayerController ->
  pawn/CharacterMovement. The existing manager -> agent prerequisite remains.
  This setup assumes the single local player controller used by this project;
  dedicated-server controllers have not been validated.
- Inference skips trainer-process and PPO-communicator initialization.
  Training retains those startup paths.

## Validation and limits

The original NF-Final .bin snapshots are unavailable. Four embedded DA_Agent
network assets were exported to frozen snapshots for the comparison. Their
training timestep and provenance are unknown. Each test launches a fresh
editor process with FixedSeed; Learning Agents initializes recurrent memory to
zero on agent addition. Initial states and actions are compared explicitly.

The pre-fix rendered and headless runs used the same initial state but differed
in simulation timestep and movement. The rendered baseline reached measured
speed about 32,471 cm/s; the headless baseline used a typical speed limit near
6,667 cm/s at roughly 120 Hz. These are observations, not inferred limits.

Final compilation, traces, comparison, original hash manifest, and backups are
in `Saved/TimingFix`. See `comparison.json` for numerical results. Tests use
rendered PIE and -nullrhi PIE, not a cooked shipping executable. The completed
comparison does not establish compatibility with the missing NF-Final
checkpoint. Repeat with the intended checkpoint and a cooked executable before
using the repaired simulation for research results. Changed inference dynamics
may require retraining; do not treat old trial results as comparable without
revalidation.

The final five-Blueprint compile completed with zero errors. The two final runs
completed 200 consecutive decisions (10 simulated seconds). Actions, positions,
velocities, agent/controller yaw, h, speed limits, time, and period counters
matched exactly at every decision. Delta was 0.050000000745 seconds in both
runs. Measured maximum horizontal speed was 1000 cm/s. Both runs had a local
PlayerController and inference enabled, and had no Learning Agents errors or
tick-cycle warnings. A copy of the numerical result is tracked in
`analysis/timing/validation.json`.

Actual training was not run. Its process settings still reference a previous
Windows Intermediate/PipInstall/Scripts/python.exe location. Configure the
training Python environment before starting training. The inference guards
avoid that dependency for the comparison. The training timestep was checked
statically, rather than through an active optimizer run.

## Reproducing the comparison

Use the installed engine at `D:\Dev\UE_5.5`. Enable PythonScriptPlugin on the
command line; it need not be permanently enabled in the project.

1. `inspect_unreal.py` loads defaults and exports the four embedded snapshots.
   Run with `-run=pythonscript -script=<absolute script path> -nullrhi`.
2. `compile_unreal.py` compiles all five Blueprints and saves the three edited
   assets. Check the commandlet exit code and compiler log for errors.
3. Start the editor with
   `-ExecCmds="py D:/Dev/decanalization/analysis/timing/trace_pie.py"`
   `-EnablePlugins=PythonScriptPlugin -FixedSeed -nosound -unattended -nop4`.
   Use `-TimingLabel=fixed_visible` for rendered PIE, and add `-nullrhi`
   with `-TimingLabel=fixed_headless` for headless PIE. The runner stops after
   200 actual simulation ticks, skipping editor frames that do not advance PIE.
4. Run `compare_traces.py` from the project root. It rejects missing steps,
   requires 0.05-second deltas and 1000 cm/s limits, and compares all 200 steps.

The test runner changes snapshot paths in editor memory. Unreal can save dirty
network or level packages during these tests; preserve a backup and restore
those test-only changes afterward. Original assets from this repair are in
`Saved/TimingFix/backup/Content` with SHA-256 hashes in `manifest.json`.

`AssetAudit` is a small console adapter for
[UAssetAPI 1.1.0](https://github.com/atenfyr/UAssetAPI), used to export and stage
uncooked graph edits. `graph_asset.py` reads pin serialization using the local
UE 5.5 engine source. `patch_graphs.py` applies this specific audited graph
layout; it is not a general-purpose migration for other project versions.
All staged edits were compiled and saved by Unreal before validation.

## Episode reset repair

`BP_AgentTrainingEnv.ResetAgentEpisode` now always runs `Initialize`; its
`Episode Steps > 1` branch controls reporting only. Zero-step and one-step
episodes clear custom steps, total reward, termination and last-resource state.
`GetPreviousSetpoint` uses the seeded initial value until a second sample exists,
avoiding an index -1 read on the first reward after reset.

`BP_Agent.ResetEvent` resolves and caches the current GameMode before spawning,
stops jumping, uncrouches, clears accumulated forces and pending launch velocity,
stops movement, consumes movement input twice (pending and last input), and
clears the old resource reference before teleport overlap updates. It sets a
fresh controller rotation and then matches the pawn rotation. Random spawn and
the existing 0–180 degree yaw distribution are retained. The existing GameMode
reset clears homeostatic/traversal histories and episode counters; Learning
Agents clears recurrent memory and framework episode bookkeeping.

Reset-time source backups are under `Saved/ResetFix/backup`, including the user's
existing TrainingEnv edits. `patch_resets.py` targets exports of those current
assets, rather than rebuilding TrainingEnv from an older version. Compile with
`compile_resets.py`; runtime validation uses `validate_resets.py` via ExecCmds.
The final compile passed with zero errors and the existing Projectile collision
channel warning. Four actual manager reset calls (episode steps 0, 1, 20, 0)
passed in PIE: velocity, pending/last input, custom reward/steps/termination,
world tick count and all 64 memory values cleared; actor/controller rotations
matched with zero pitch/roll. The final runtime log had no Blueprint runtime
or Learning Agents errors. Results are in `reset_validation.json`.

This invokes the training environment's real reset listener without launching
an optimizer. Full optimizer training still needs its Python environment path
configured as described above. Test-created network and external actor saves
were preserved under `Saved/ResetFix/test_saved` and restored afterward.

## Independent trial reset

`BP_GameMode.RunTrial` now calls `AgentManager.LearningAgentsManager.ResetAllAgents`
on the completed-trial branch, after incrementing `TrialsRun` and before starting
the next trial. This replaces the direct `Reset(false)` broadcast. The training
environment callback invokes the existing full pawn/world reset with a fresh
spawn/orientation, while Learning Agents resets memory and episode bookkeeping.
The terminal save/quit branch and all phase transitions are unchanged.

`patch_trial_resets.py` targets the current GameMode export backed up under
`Saved/TrialResetFix/backup`; `compile_trial_resets.py` compiles the affected
Blueprint and its dependencies and saves GameMode. Production compilation passed
with zero errors and the existing collision-channel warning.

`validate_trial_resets.py` invoked the real `RunTrial` graph for both phase
orders, seeding counters at 6000, 12000, 18000 and 18002. Phase calls preserved
position, controller orientation, velocity, pending movement input and all 64
seeded memory values. Each completed-trial call incremented the trial count,
cleared world/episode counters, velocity, input and memory, and produced a fresh
spawn and matching pawn/controller orientation. All eight checks passed; the
runtime log contained no Blueprint runtime or Learning Agents errors. Results
are tracked in `trial_reset_validation.json`.

The test temporarily allowed editing `TotalTickCount` on instances (both the
generated property's `CPF_DisableEditOnInstance` flag and the Blueprint variable
description's corresponding 65536 bit were cleared, then compiled). This let the
test reach boundaries directly. The exact compiled production package from
before the test was restored afterward, retaining the normal property flags.
Network and external actor packages were also restored from this turn's backups;
test-created versions remain under `Saved/TrialResetFix/test_saved`. This verifies
boundary behavior in PIE, rather than running every intervening trial timestep.

## Windows trainer runtime repair

The configured Python environment started correctly, but UE's pinned PyTorch
2.4.0+cu121 failed importing `fbgemm.dll` because `libomp140.x86_64.dll` was absent.
Installed the release x64 DLL from Microsoft's official VS 14.40 CRT package
into `Intermediate/PipInstall/Lib/site-packages/torch/lib`. The package and DLL
SHA256 checks passed, and Windows verified the DLL's Microsoft signature.
PyTorch and the UE engine installation were not upgraded.

`fetch_openmp_runtime.py` repeats the repair after recreating `PipInstall`:

```powershell
& .\Intermediate\PipInstall\Scripts\python.exe .\analysis\timing\fetch_openmp_runtime.py
```

CPU and CUDA forward/backward calculations and Adam optimizer steps passed;
the actual Learning Agents `train_ppo` module imported. `training_smoke.py`
then passed 30 actual PIE training decisions with the current manager settings,
active PPO training, sampled actions and pawn movement. The first run directly
hit the user's saved breakpoint inside `BP_AgentInteractor.PerformAgentAction`;
the breakpoint was temporarily disabled for the completed smoke test and then
restored. This checks startup and action execution, not a full PPO training run.

Results, source provenance, logs and current-asset backups are in
`Saved/PythonRuntimeFix`. The four network assets and manager external actor were
restored byte-for-byte from this repair's fresh backups after the test.

## TensorBoard

TensorBoard 2.13.0 is installed in the project Python environment, with Unreal's
protobuf 4.24.0 and typing-extensions 4.8.0 pins retained. Package dependency
checks and a PyTorch SummaryWriter event write/read test passed. The existing
PPO settings already enable `UseTensorBoard`.

Dashboard: `http://127.0.0.1:6006/`. Logs are read from
`Intermediate/LearningAgents/TensorBoard/runs`; each training session gets its
own run. Reward, return, episode length, policy/critic loss and gradient metrics
are emitted after experience collection and PPO updates. Earlier sessions where
TensorBoard was missing have no recoverable event files; start a new training
session after installation. A blank dashboard before the first update is normal.

Restart the dashboard with `analysis/timing/start_tensorboard.ps1`. It starts a
hidden localhost server; process ID and server logs are under `Saved/TensorBoard`.
If the Python environment is recreated, reinstall with:

```powershell
& .\Intermediate\PipInstall\Scripts\python.exe -m pip install -r .\analysis\timing\tensorboard-requirements.txt
```

## Headless training

`start_headless_training.ps1` launches Landscape in standalone game mode using
`UnrealEditor-Cmd.exe -game -nullrhi -nosound -unattended -NoVSync`. It uses the
saved manager training settings and non-editor trainer paths; editor Blueprint
breakpoints do not pause this game process. Current network assets are backed
up before launch. The PID, arguments, logs and backups are stored under the
timestamped `Saved/HeadlessTraining` run directory. Runs remain active after the
launcher exits. TensorBoard reads their metrics from the shared runs directory.

From Explorer, double-click the project-root `start_headless_training.cmd`.
From PowerShell in the project root, run `./start_headless_training.cmd` or
`./analysis/timing/start_headless_training.ps1`. The CMD wrapper selects Windows
PowerShell and applies execution policy only to that invocation. The launcher
checks required paths, prevents a second standalone run for this project, and
waits up to 120 seconds to confirm the first PPO update. Failures include the
run log location; the CMD wrapper keeps the window open when startup fails.

## Current movement comparison (2026-10-13)

The current project was copied into `Saved/MovementAudit/TestProject`, preserving
the open source editor. Only the copy's manager was configured for inference.
Four frozen snapshots from `Training_ppo_sharedmemory_2026-10-13_12-56-03`,
optimizer step 5000, were copied and hashed under `Saved/MovementAudit/checkpoint`.
`setup_movement_audit.py` configures this isolated copy; use `-DisablePipInstall`
when launching it since inference does not require optimizer dependencies.

`trace_movement_audit.py` recorded 200 decisions with `-FixedSeed` for rendered
PIE, headless PIE, standalone headless game, and standalone headless game with
`-UseFixedTimeStep -FPS=20 -NoVSync` (the uncapped fixed-time mechanism used by
training). `compare_movement_audit.py` produced `Saved/MovementAudit/comparison.json`.
All four had identical initial position/state, 0.05-second deltas, BaseMaxSpeed
and MaxWalkSpeed of 1000 cm/s, and exactly identical positions, velocities,
actions, yaw, homeostatic state and period counters at every sampled decision.
Each traversed 9925 cm over 9.95 simulated seconds between samples 1 and 200.
Rendered PIE took 10.125 wall seconds; uncapped headless took 0.172 seconds.
Standalone world time began 0.05 seconds ahead of PIE before the first decision;
elapsed simulation time and decision-aligned state matched exactly.

This verifies current saved assets for one frozen-policy starting trial, not
every phase transition, unsaved editor modification, or optimizer update. The
earlier 5000 cm/s training smoke measurement is not reproduced by this current
inference comparison. No original project assets were modified by the audit.

## Trial YAML persistence

When BP_GameMode.IsTrialMode is true, BeginPlay creates one unique run file at
`Saved/TrialResults/<HRL-or-NF>-<CDR-or-CCC>-<run-guid>.yml`. This replaces the
old machine-specific Documents path and the deferred file creation at the end
of the whole batch. The run GUID is cached once and does not consume the shared
environment random stream.

The complete UTF-8 YAML document is saved after each trial header and completed
phase, then saved again before the existing final quit. Resets keep the same
file. IsTrialMode=false prevents writes, including explicit SaveTrial calls.
Write failures report the target path in the Unreal log. Restart the world to
initialize a new run file; changing the flag in a running world does not perform
BeginPlay initialization again.

The schema remains compatible with analysis/sandbox.py: `trials` contains each
trial's `id`, `reward-function`, `sequence-order` and `sequences`. Phase records
contain state, duration, setpoint average/deviation, total loss, harvested pellet
count, total gain, sequence index and total reward. Metric definitions and
existing duration units are unchanged. An in-progress trial may have null
`sequences` until its first phase completes; only completed phases are saved.

`patch_trial_yaml.py` stages the current exported asset under Saved/TrialYamlFix;
`compile_trial_yaml.py` compiles only GameMode. `validate_trial_yaml.py` runs only
in its isolated TestProject. Runtime validation invoked the actual RunTrial
callback at phase and trial boundaries, covering three HRL/CDR and three NF/CCC
trials, all 18 phase records, 28 parsed YAML checkpoints, stable run filenames,
final-save behavior and disabled logging. It also confirmed that disabling
trial mode leaves an existing result file unchanged. Results are recorded in
`trial_yaml_validation.json`; detailed YAML and logs are in Saved/TrialYamlFix.

## Trial completion notification

After the final SaveTrial, GameMode calls Content/Python/trial_notifications.py
before QuitGame. For trial mode only, the notifier checks the completed count,
verifies the final YAML against the in-memory document, and writes a companion
`<run-name>.completed.json` receipt beside the YAML. `[TRIALS_COMPLETE]` in the
Unreal log includes the count and results path. A failed YAML verification is
reported as a warning rather than claiming that results were saved.

On Windows, a separate hidden Python process displays an informational dialog
with the count and full YAML path. The dialog remains until dismissed even after
Unreal exits, including `-nullrhi -unattended` runs and launches whose terminal
has closed. This uses UE's bundled Python and the editor PythonScriptPlugin,
which are available in this project's rendered PIE and standalone headless
editor workflows. A receipt prevents duplicate dialogs for the same run.
`-NoTrialCompletionDialog` suppresses only the desktop dialog for automated tests;
the receipt and log message remain. The headless launcher recognizes completion
during its startup wait and no longer treats a completed short trial batch as
a startup failure. Later completion is still announced by the dialog.

`patch_trial_completion.py` patches the current exported asset in
Saved/TrialCompletionFix. `validate_trial_completion.py` exercises real headless
final-trial callbacks and receipt verification for HRL/CDR, NF/CCC and disabled
trial mode. Test dialogs are suppressed. `test_trial_notifications.py` verifies
dispatch, duplicate/unfinished/disabled guards and save-warning messages with
mocked Windows UI; `test_headless_completion.ps1` checks startup/completion/exit
classification without launching Unreal. Results are in
`trial_completion_validation.json`.

## Accelerated headless trial clock

The headless launcher now passes `-UseFixedTimeStep -FPS=20 -NoVSync` for both
training and trials. Learning Agents enables FApp's uncapped fixed timestep in
its training setup; inference skips that setup. NullRHI alone removes rendering
but leaves DefaultEngine.ini's fixed frame rate paced against wall time. The
explicit launch flags preserve 0.05 simulated seconds per decision while letting
frames execute as quickly as the machine can process them. `-FPS=20` selects the
fixed simulation delta here; it does not request 20 wall-clock frames per second.
Rendered debug launches and project defaults are unchanged. Restart headless
runs through `start_headless_training.cmd` to pick up the new flags. For manual
UnrealEditor-Cmd launches, include the same fixed-timestep flags.

`validate_trial_speed.py` tested frozen inference with IsTrialMode=true in an
isolated current project copy. The previous flags ran 10 simulated seconds in
9.953 wall seconds. With the new flags, a complete three-phase trial ran 900.15
simulated seconds in 64.266 wall seconds (14.01x real time), persisted YAML, and
wrote its completion receipt. Desktop dialogs were suppressed for the test.
All first 200 decisions matched exactly between runs: delta, position, velocity,
yaw, action, homeostatic state and configured movement limit. This preserves the
user's current movement parameters; it only removes wall-clock pacing. Recorded
throughput is machine/workload dependent. `trial_speed_validation.json` stores
the results; detailed traces and logs are under Saved/TrialSpeedFix.

## Complete world state at full resets

BP_Tile's existing ResetEvent now clears HomeostaticImpact to the fresh-world
unvisited value (0), alongside OverlapCount. This prevents the observation graph
from reading impact values left over from an earlier trial after the visit
counter has reset. Fresh overlaps at the new spawn can immediately generate a
new visit and impact; they are legitimate new-trial state.

BP_Resource's ResetEvent now cancels the pending Respawn event timer before
restoring its value and counter, then reuses Respawn's immediate visibility,
overlap-event and actor-collision restoration. It does not schedule another
timer. These hooks run on the existing full reset broadcasts, which also serve
training episode resets. The phase toggle paths remain unchanged, preserving
within-trial state continuity. Rewards, physical parameters and RNG progression
are unchanged; independently randomized trial starts can still yield different
outcomes.

`patch_trial_world_reset.py` stages current asset exports under
Saved/TrialWorldResetFix; `compile_trial_world_reset.py` saves only BP_Tile and
BP_Resource. `validate_trial_world_reset.py` exercises six real trial completion
callbacks, alternating CCC/CDR phase handling, across 2,500 tiles and 127 pellets.
It deliberately harvests pellets, starts respawn timers, dirties tile inputs and
policy memory, and disables pellet availability. All six full resets restore
clean state; all eighteen phase boundaries preserve hidden/timed pellet state
and policy memory; the next frame remains clean. Results are in
`trial_world_reset_validation.json`, with detailed states and logs under Saved.
These boundary tests establish reset-state consistency. Evaluate outcome
variability with a new trial batch, keeping the checkpoint and parameters fixed;
they do not establish that policy performance has improved.

## First-trial initialization matches later trials

Trial-mode inference now enters the existing Learning Agents ResetAllAgents path
once at the beginning of the GameMode RunTrial callback, before the first scored
action. Previously trial 1 relied on actor startup, whereas later trials used
full resets. Startup included nonzero pawn velocity, zero timestep caches and
different perception initialization. A GameMode HasInitializedTrialRun flag keeps
this initialization to once per world and skips it for training and non-trial
inference. Running it in RunTrial aligns its position in the simulation frame
with the reset between completed trials.

The first scored trial remains ID 0. Initialization rebuilds its YAML buffer
before the existing reset prepares the trial header; it does not increment
TrialsRun or add a duplicate trial. The run file and completion behavior stay
intact. The agent reset also clears AnticipatedResourceGain,
AnticipatedResourceLoss, CollidingDriveReducers and CollidingDriveIncreasers
before teleporting, preventing perception at the old position from entering the
next trial. Phase transitions preserve these states normally. The first full
reset consumes environment randomness, so the resulting layouts differ from
older batches even with the same run seed; this is not a comparison on identical
scenarios. The checkpoint, rewards, physical parameters and timestep are kept.

`add_trial_startup_variable.py`, `patch_trial_startup.py` and
`compile_trial_startup.py` document the GameMode/Agent edits from current exports
under Saved/TrialStartupAudit. `validate_trial_startup.py` runs three complete
accelerated trials using the user's current frozen checkpoint in an isolated
copy, recording each trial's start, header counts, results and completion receipt.
Additional checks validate immediate observation-cache/memory clearing over three
resets, six world resets/eighteen phase transitions, and non-trial bypass.
`trial_startup_validation.json` records the results. All test dialogs are
suppressed; detailed traces and YAML remain in Saved/TrialStartupAudit.

The completed three-trial check produced canalized signed homeostatic means of
144.595, 142.010 and 154.718. All three starts were observed at trial tick 1 with
empty perception caches, and all nine phases, three YAML trial headers and the
completion receipt were present. The earlier five-trial batch's corresponding
first three means were 15.3, 130.6 and 139.2. This small, unpaired scenario
comparison supports removal of the first-trial initialization exception; it does
not establish improved homeostatic control. Production defaults and the user's
current manager/checkpoint assets were preserved when installing only GameMode
and Agent.

### Reset performance comparison

`run_reset_comparison.ps1`, `configure_reset_comparison.py` and
`validate_reset_comparison.py` compare the four reset-era Blueprint assets saved
under Saved/TrialStateAudit with the current production versions in an isolated
project under Saved/ResetPerformanceAudit. This audit requires those saved
fixtures and the October 14 encoder/policy/decoder snapshots at iteration 6000.
It uses the same current manager, other assets, fixed 0.05-second step, inference
noise zero, and trial seed 10001 throughout. It does not train or change
production assets. Test-only property editability permits exact scene restoration.

Each condition runs one complete CDR trial. Natural startup is compared with a
full reset followed by restoration of the original agent transform, pellet
transforms/values/count, tile observations/counts, and initial homeostatic state.
A separate current-assets control bypasses only the one-time startup reset.
Scene hashes verify restoration before simulation. A velocity ablation copies
the initial velocity coordinates before reset: Unreal property struct wrappers
otherwise refer to the live value that reset mutates. The final paired control
also copies/restores the full RandomStream struct, preserving future draws.

The old and current resets give exactly equal sampled observations, actions,
recurrent memory, movement and phase metrics on the restored scene. Current
assets with the legacy startup also reproduce the legacy trial exactly. Natural
startup differs because the new first reset consumes RNG and replaces the scene
and state; the legacy actor startup also supplied 1000 cm/s initial velocity.
Mean absolute homeostatic distance (lower is better) is:

| Condition | Canalized | Decanalized | Recanalized |
| --- | ---: | ---: | ---: |
| Legacy startup | 15.777 | 1033.696 | 105.204 |
| Current assets, legacy startup | 15.777 | 1033.696 | 105.204 |
| Legacy reset, restored scene, stationary | 72.871 | 278.094 | 151.453 |
| Current reset, restored scene, stationary | 72.871 | 278.094 | 151.453 |
| Current natural startup | 144.859 | 1076.350 | 154.372 |
| Current reset, restored scene/velocity/RNG | 15.777 | 1033.696 | 105.204 |

Restoring initial velocity reproduces the legacy first-phase metric exactly;
without restoring the RNG stream, later phases differ. The legacy and current
RunTrial graphs clear Setpoints and replace the current homeostatic value with a
fresh uniform draw between -15 and +15 at phase boundaries, then broadcast
SetpointsChanged. Therefore the full stream state matters to paired comparisons,
and post-decanalization results do not measure recovery from the preceding
homeostatic state. The user confirmed that this phase-boundary randomization is
intentional; it was retained. Restoring the full scene, velocity and RNG stream
reproduces all legacy phase metrics and all 218 sampled trajectory checks exactly.

This isolates initialization sensitivity in the frozen checkpoint rather than a
change in the tested reset dynamics. One deterministic scenario per condition is
not a robustness benchmark and does not establish that retraining is necessary
or sufficient. Further learning should be judged on held-out randomized trials
with the corrected resets, using absolute/RMS distance and time near zero rather
than signed mean alone. Preserve the frozen policy for comparison.

`summarize_reset_comparison.py` writes `reset_performance_validation.json` with
metrics, trace comparisons, snapshot hashes and the production preservation
check. Full scene snapshots, traces and logs remain in Saved/ResetPerformanceAudit.

### Uniform phase initialization

The later experiment requirements supersede stationary full-reset starts and
independent homeostatic draws at phase boundaries. BP_Agent.InitializePhaseVelocity
sets CharacterMovement.MaxWalkSpeed and cached MaxSpeed from BaseMaxSpeed, then
sets Velocity to ActorForwardVector * MaxSpeed. Startup and full resets call it
after establishing the initial heading. RunTrial calls it at ticks 6000 and
12000 for both CDR and CCC; it does not run at the final 18000 boundary. At the
current BaseMaxSpeed this is 5000 cm/s. Full resets still clear previous input,
forces and motion before assigning the new initial velocity.
Startup and full-reset placement also use native K2_TeleportTo at the generated
pose before assigning velocity. This resolves spawn overlap using Unreal's
collision placement. It then establishes walking mode, allowing native floor
adjustment to finish before velocity assignment. The shared initializer supplies
fresh forward movement input after setting velocity; otherwise the reset's
cleared input and high braking friction cancel first-frame motion. Later phase
boundaries preserve the existing pose and movement mode.

GameMode.TrialStartingHomeostaticState stores the value assigned by ResetValues.
Inference draws once from [-15,15] and feeds that same cached value into the
initial Setpoints entry, avoiding duplicate evaluation of the pure RNG node.
Each later phase clears its measurement history and starts at this stored value.
The next trial samples a fresh value. Training retains its existing -15 episode
initial value and records that value in the same cache. Phase transitions retain
policy memory, pose, pellet availability, harvest state and timers. Skipping the
old phase RNG draws changes subsequent deterministic scenarios relative to old
batches, even with an unchanged seed.

`patch_phase_velocity.py`, `add_trial_homeostasis_variable.py`,
`patch_phase_homeostasis.py` and `compile_phase_velocity.py` stage and compile
the two assets from backups under Saved/PhaseVelocityFix. The test configuration
is isolated and is not installed. `validate_phase_velocity.py` checks startup,
five resets, ten phase boundaries and five direct initializer calls, covering
HRL/NF, CDR/CCC, 5000/2375 cm/s, and the training reset path. It checks restoration
from an intentionally different homeostatic value, four distinct trial samples,
memory clearing only at full resets, and phase world-state preservation.
`validate_natural_phase_velocity.py` additionally runs one uninterrupted trial.
Its phases reuse the same per-trial starting homeostatic state. Maximum speed
is checked both immediately and after the first frame / later phase boundaries.
These initial assignments do not override subsequent collision/physics responses.
The compact results are in `phase_initialization_validation.json`; full logs
and assets remain under Saved/PhaseVelocityFix. Only BP_Agent and BP_GameMode are
installed; policy assets and manager settings are preserved.

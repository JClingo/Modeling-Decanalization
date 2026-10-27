# Homeostatic regulation

The baseline project state is preserved in commit `e693150`. These changes
implement distinct HRL and NF objectives. Phase transitions and
full resets between trials remain unchanged. Legacy HRL/NF reward branches
remain available by disabling `UseHomeostaticReward` in BP_AgentTrainingEnv.

The policy update also corrects UE's positive-advantage-only log-space clipping:
it takes the minimum *after* multiplying each alternative by the advantage.
Negative advantages therefore stop decreasing action probability once the lower
clip boundary is reached. The previous inherited formula left this direction
unbounded and produced non-finite policy gradients after roughly 1207 updates.
Gradient/loss/weight checks reject invalid optimizer updates and network sends,
so non-finite parameters cannot silently reach Unreal's inference assertion.
Reported policy gradient norms are measured before clipping.

The crash correction passed 12 regression tests and a standalone headless run
through reported optimizer iteration 1280 (past the original failing interval).
All recorded policy/critic losses and gradients were finite, and the validation
process stopped cleanly. `crash_validation.json` records the metrics; logs and
the isolated test copy are under Saved/TrainingCrashFix. Existing user Blueprint
edits were preserved. Restart training to load the corrected Python module.

## Reward

In HRL mode (`GameMode.IsHRL=true`), every decision receives:

```text
reward = dt * HomeostaticRewardRate / (1 + (h / RewardDistanceScale)^2)
```

The default scale is 25 homeostatic units; rate is 1 per simulated second.
This gives a bounded positive quality score, highest at zero, decreasing
smoothly with absolute error and symmetric across zero. Repeated states still
receive the same quality reward. A pellet is useful according to the resulting
error, including its overshoot, rather than its collision alone. Positive
ongoing quality avoids terminating to escape a stream of negative error costs.
This is a surrogate for time spent near zero, rather than exact squared-error
minimization. Reward scale is independent of the existing failure boundary.

`abs(h) > Max Setpoint Distance` sets termination and yields
`HomeostaticFailureReward` (default -1) once. Further calls return zero until
the manager resets the episode. Episode reward and step counts use the existing
reset bookkeeping. Scale is floored at 0.001, reward rate at zero, and failure
reward capped at zero to keep accidentally edited settings well-defined.

In NF mode (`IsHRL=false`), the resulting homeostatic state must be strictly
below zero. Only a reduction in absolute distance earns reward:

```text
NF reward = max(abs(previous decision h) - abs(current h), 0)
            * HomeostaticRewardRate / RewardDistanceScale
```

At or above zero, NF reward is zero, including reaching exactly zero or
overshooting into positive values. Unchanged and worsening negative states
also receive zero. Failure still terminates the episode, but NF gets no failure
penalty. Unlike HRL's reward rate per simulated second, NF is a scaled state
improvement and is not multiplied by dt. At scale=25 and rate=1, -40 -> -20
earns 0.8 once; repeating the same state earns zero.

PreviousRewardState is cached once per reward decision in both modes, so it
survives intentional phase changes. Initialize invalidates and clears the cache
on episode/trial reset. The first decision uses the seeded previous homeostatic
history value; later calls use the decision cache, avoiding repeated rewards
from a history that updates only every five simulation ticks.

At dt=0.05, rewards at h=0, ±25 and ±50 are 0.05, 0.025 and 0.01.
The near-zero region is tunable through RewardDistanceScale, without changing
physical resource/tile impact, passive loss, or the failure threshold.

## PPO and telemetry

The observation graph now reads the latest GameMode.Setpoints value through the
agent's cached GameMode reference. Previously it read Agent.SetpointDistance,
which stayed at its default -25 during the production smoke rollout. This fix
preserves the 11-dimensional schema and its existing FloatScale=100, while
providing the policy with the actual signed homeostatic value.

The manager uses the project-local `homeostatic_ppo` module in this directory.
It delegates training to UE's train_ppo and replaces the advantage calculation
to include the last transition (the UE 5.5 implementation omits it), bootstrap
time-limit truncations, respect episode boundaries, and center normalized
advantages. MinimumAdvantage=-10 preserves negative feedback. Gradient norm
clipping is enabled at 0.5, entropy weight is 0.001, and start-step trimming is
zero now that reset state is valid. Learning rates, update count, memory window,
physical parameters and simulation timestep retain their baseline values.

TensorBoard adds mean absolute error, RMS error, signed mean and the fraction
of samples within ±5, plus collected transitions and throughput. The adapter
locates SetpointDistance by schema index. It converts its normalized float
observation using BP_AgentInteractor's existing FloatScale=100. If that scale
changes, update the adapter; these metrics describe observed homeostatic state.
Task metrics use collected post-trim transitions on the x axis; UE's existing
loss/reward metrics retain their optimizer-update x axis. Historical rewards
from the legacy objective are not numerically comparable to the new reward.

## Validation and operation

`validate_nf_reward.py` invokes the actual Blueprint callback in isolated PIE,
covering unchanged anticipated net, unchanged distance, sign symmetry,
improvement, worsening overshoot, both legacy mode flags, terminal reward and
reset. `test_ppo.py` checks final-transition credit, truncation bootstrapping,
episode separation and negative normalized advantages. Logs and detailed
runtime results are in Saved/HomeostaticFix.

The latest NF validation passed 22 real cases covering both modes, current-state
gating, zero/positive overshoot, worsening, repeated calls, failure, phase
continuity and cache reset. Results are in `nf_validation.json`, with compiler
and runtime logs under Saved/NFRewardFix. `validate_reward.py` delegates to the
current mode-aware validator. The earlier shared-objective validation remains
in validation.json as historical evidence.

Use the existing project-root `start_headless_training.cmd` for a new run.
Use a fresh training run for this changed objective; old frozen policies were
optimized for different rewards. Judge performance by MAE and fraction within
±5 on complete held-out trials, including every intended phase/order. A passing
startup test establishes correct execution, not that the task has been learned.

Validation passed 14 real reward/observation cases across both mode flags,
repeated-state rewards, terminal handling and resets, plus six PPO regression
tests. The corrected production trainer completed a PPO update with 20,000
transitions collected, changing homeostatic telemetry, and a clean editor exit.
Network/external-actor packages and debugger settings were restored afterward;
only the three intended Blueprint packages retain implementation changes.
`validation.json` records the results. The smoke test was stopped; it did not
leave a long training run running or replace the saved baseline policies.

Graph authoring utilities `add_reward_variables.py`, `patch_reward.py`,
`compile_reward.py` and `configure_trainer.py` document how assets were made.
They are development tools, not required to launch training. The patch script
expects the exported variable-augmented asset at Saved/HomeostaticFix/env.variables.json.

## Separate environment seeds for trials

BP_GameMode Class Defaults exposes TrainingEnvironmentSeed (1) and
TrialEnvironmentSeed (10001). BP_AgentManager.Run Inference selects the trial
seed when true and the training seed when false. IsTrialMode does not select
the seed, since it can also be enabled during training. ActiveEnvironmentSeed
records the selected seed for inspection.

The GameMode construction script initializes the shared RandomStream before
BeginPlay, so the selection governs initial agent position/yaw, homeostatic
randomness, and pellet values, locations and count. Initial pellet count now
uses one seeded ShouldSpawn decision per grid cell: SpawnRate is the expected
occupied fraction, rather than an exact fixed count. Placement still shuffles
unique grid locations. Counts therefore vary between seeds; coincidentally
equal counts are possible.

Episode/trial resets and phase transitions do not rewind the stream. Successive
resets produce varied environments reproducibly; phase continuity is preserved.
The existing reset behavior repositions the current pellet population, so count
is sampled at world startup. Restart the world after changing Run Inference or
either seed. Seeding earlier and sampling occupancy changes legacy layouts even
with training seed 1. PPO's separate training RNG seed is unchanged.

`add_environment_seed_variables.py`, `patch_environment_seeds.py`,
`patch_seeded_pellet_count.py`, and `compile_environment_seeds.py` document asset
creation. Patch inputs are exported JSON under Saved/RngSeedFix. Runtime
`validate_environment_seeds.py` is restricted to its isolated TestProject and
captures initial state plus two full agent resets with manager ticking disabled.
`environment_seed_validation.json` records reproducibility and differences;
detailed layouts and Unreal logs remain under Saved/RngSeedFix.

## NF-only stabilization (NFStable1)

When `IsHRL=false`, BP_AgentManager selects `nf_ppo` immediately before spawning
the training process. With `IsHRL=true` it keeps the original trainer and settings.
The runtime helper is `Content/Python/nf_training.py`; class defaults, rewards,
trial setup, movement and existing frozen snapshots are preserved. Python must
remain enabled, as it already is for the project's reset helpers. Configuration
failure logs an error and stops the run.

The NF trainer uses standard probability-ratio PPO clipping, caps policy learning
rate at 0.00003, critic learning rate at 0.0003, updates per gather at 8, PPO clip
at 0.1 and global gradient norm at 0.25. Actor updates are skipped once the
sampled approximate KL exceeds 0.015. This checks each minibatch before its
update; it is not a strict bound on post-update KL. Critic updates use detached
encoder features so they cannot change the actor outside that check.

NF exploration standard deviation is fixed at 0.15 in the existing serialized
decoder parameters. Removing entropy and action-size regularization prevents
the previous combination of exploding variance and suppressed mean steering.
The first rollout is discarded without actor or critic learning, then the normal
network publication protocol sends the bounded decoder before further collection.
The first eight iteration numbers therefore represent bootstrap, not learning.
Snapshots retain the native layout and require no special inference code.

New run and snapshot names contain `Training_NFStable1_ppo_`. TensorBoard adds
`nf/action_std`, `nf/log_std_max`, `nf/approx_kl`, accepted/skipped actor updates,
and mean-action diagnostics, including observations with negative homeostasis.
Those diagnostics use replay observations and stored recurrent memory; use
complete held-out deterministic trials to assess time near zero.

Start a fresh NF training run. Changing the trainer does not repair a previously
collapsed frozen policy. Continue loading matching encoder, policy and decoder
snapshots from the same new run and iteration for trials. This change targets
training stability; convergence and useful NF behavior still need longer training
and held-out evaluation. The NF reward gate remains unchanged.

Run regression checks with the project Python:
`Intermediate/PipInstall/Scripts/python.exe -m unittest discover -s analysis/homeostatic -p "test*ppo.py"`.
`nf_stability_validation.json` records the isolated native smoke checks.

# HRL learning in a canalizing environment

This opt-in training extension targets low time-averaged absolute homeostatic
state while repeated traversal changes the landscape. It preserves the existing
selected policy and paper data. All native work uses marked disposable copies;
training does not change the production project's inference defaults.

The implementation provides:

- Native reward choices: current quality score (scale 25), a narrower quality
  score (scale 10), and negative absolute error (scale 25).
- Configurable discount/GAE, recurrent windows, actor/critic learning rates,
  update counts, and entropy/learning-rate schedules.
- A guarded trainer with sampled KL checks before and after an actor update,
  rollback of rejected weights and optimizer state, global gradient clipping,
  and a critic that cannot alter the actor's shared encoder. Standard ratio PPO
  and the existing log surrogate are separate choices.
- Guarded recurrent sampling that includes the final transition and short episodes.
- Explicit seeds for native policy/critic initialization as well as training.
- Native per-decision h integrals, time within ±5, extreme-error frequency,
  maximum error, and completed out-of-band excursion durations. The latter
  exclude right-censored excursions, which are recorded separately.
- Checkpoint selection by held-out time-MAE, with best-checkpoint retention,
  plateau stopping, independent confirmation environments, and trained-policy
  replication as a separate unit from evaluation trials.
- Landscape history diagnostics during training: tile counts, revisited tiles,
  revisit fraction, visitation entropy and the expected next-entry cost relative
  to first entry. Evaluation phases retain hashed initial/final tile counts and
  route-use summaries for each measurement window.

## World duration and traversal history

The original environment time limit is 100 seconds. The trainer's 1,028-step
limit is an experience-segment boundary; it does not by itself necessarily
reset the agent or tiles. The environment's timed/failure completions and the
existing reset-on-policy-update setting cause actual world resets. Tile reset
handlers clear traversal counts. Merely increasing a replay segment therefore
does not guarantee longer lived environmental history.

`canalization-300s` changes the world time limit to 300 seconds while retaining
baseline learning settings and the 1,028-step experience segment. `segment-100s`
changes the segment to 2,000 steps while retaining the 100-second world limit.
`canalization-persistent` retains the 300-second limit while disabling world
resets on policy updates. Timed and failure resets still operate.
`canalization-aware` combines that persistent 300-second world with longer
credit and recurrent training, conservative updates and annealing. It is a proposed
configuration, not an established improvement.

Ordinary tile entry remains +1; physical costs, pellets and map geometry retain
their baseline values. Training uses ordinary canalizing conditions. CDR is
excluded from checkpoint selection. A later CDR comparison retains +1 in all
phases and the existing half-floor transition.

Increasing a time limit only helps if agents survive long enough and revisit
routes. Use `landscape_history.jsonl` to check that counts accumulate and that
revisited routes become cheaper before resets. Route reuse by itself does not
establish a benefit of canalization: a causal demonstration also needs a
matched control with traversal-dependent cost changes disabled and anticipation
made consistent with that control. This extension does not silently substitute
such a different environment for the paper's primary condition.

## Reward and failure accounting

Quality reward is `dt / (1 + (h / scale)^2)`. Absolute-error reward is
`-dt * abs(h) / scale`. For the absolute-error variant, termination receives
`-dt * boundary / scale / (1 - gamma)`: the discounted value of an absorbing
failure state at the training boundary. This includes the failing transition
and prevents early failure escaping future error costs. It is a continuing
failure convention, not a claim that the physical world stays at that h.
Truncations bootstrap; true terminations do not. Fixed-horizon inference
continues to record the actual h, including excursions beyond the training
boundary. Raw rewards from different reward variants are not comparable.

Primary selection uses the native decision-time integral divided by duration.
Studies use a continuous 300-second CCC trajectory, split into three 100-second
reporting windows. The end h of each window seeds the next one; an unfinished
excursion outside ±5 carries forward too. Tile counts persist throughout.
Each run checks the h boundary values and records hashed tile histories.
Historical event-sampled MAE remains in its existing fields. Recovery summaries
measure completed excursions and report right-censored durations separately.
The standalone evaluator also supports the existing paper protocol with h reset
at each phase boundary; omit `--continuous` for that protocol. These protocols
must not be pooled. The paper's existing trials are preserved.

## Running

Requirements are the existing Unreal 5.5 installation and project-local
Python/Torch environment. `HRL_PYTHON_ENV` can override the Python environment
path. The validated compiled Blueprint variants are under `assets/`; graph
authoring sources are retained for rebuilding. Production source hashes and
selected policy hashes are checked throughout.

From the manuscript workspace:

```sh
python3 learning/hrl/run.py list
python3 learning/hrl/run.py smoke --root /private/tmp/hrl-learning-smoke
```

Start the world-history comparison with three training seeds. It compares the
original 100-second/reset-on-update setting, 300 seconds with the same reset
behavior, and 300 seconds with history retained across policy updates:

```sh
python3 learning/hrl/study.py --stage canalization \
  --root /private/tmp/hrl-canalization-study
```

Each run has a default ceiling of 200 gathers (normally two million collected
transitions). It retains the best held-out checkpoint and can stop after
100 gathers and four validations without a 0.5% material improvement. A tiny
improvement is still retained even if it does not reset stopping patience.
Reaching a budget is reported as a budget limit, not convergence. Actual
transitions and native episode durations are recorded.

After choosing the world-history condition, keep it fixed while tuning learning.
The reward, horizon, stability and confirmation stages default to the same
300-second world with history retained across updates, including their baseline
learning control. `--environment-from baseline` or `canalization-300s` chooses a
different fixed context explicitly. `--reward-from` applies the chosen reward to
all learning controls and candidates in later stages.

Screen rewards, then horizons and stability in separate explicit stages:

```sh
python3 learning/hrl/study.py --stage reward --root /private/tmp/hrl-reward-study
python3 learning/hrl/study.py --stage horizon --reward-from quality-10 \
  --root /private/tmp/hrl-horizon-study
python3 learning/hrl/study.py --stage stability --reward-from quality-10 \
  --root /private/tmp/hrl-stability-study
```

`quality-10` above is an example of an explicitly chosen first-stage winner,
not an assumed result. To test the combined 300-second configuration:

```sh
python3 learning/hrl/study.py --stage canalization-learning \
  --root /private/tmp/hrl-combined-study
```

Confirmation requires at least five fresh training seeds. For example:

```sh
python3 learning/hrl/study.py --stage confirm \
  --profiles baseline canalization-aware --root /private/tmp/hrl-confirmation
```

The preserved selected HRL policy is also evaluated as a separate fixed
benchmark, rather than counted as another independent training seed.
Checkpoint screening uses environment seed 41001; confirmation uses 51001.
Final test seed 61001 is reserved. The older paper's test seed 10001 is excluded
from tuning, as are its earlier selection seeds. Training seed lists are
explicit in `study.py`; native initial snapshot hashes verify that changing a
training seed actually changes initialization.

To score the preserved selected policy using the new uniform decision metrics:

```sh
python3 learning/hrl/run.py reference --root /private/tmp/hrl-reference --trials 8 --continuous
```

For a single bounded run:

```sh
python3 learning/hrl/run.py train --profile canalization-aware \
  --root /private/tmp/hrl-single --gathers 200
```

`--profile-json` accepts an explicit profile contract; `--reward-from` transfers
only a reward choice to another named profile. Profile contracts, actual UE
settings, code hashes, initial/final snapshots, optimizer diagnostics, scene
hashes, native completion receipts and uniform sampling counts are preserved.
A run directory is never silently overwritten.

Tests use the existing Python environment:

```sh
'/Users/jingo/Work/PhD/Dissertation Project/decanalization/Saved/AnticipationRetrain20261025/python-env/bin/python' \
  -m unittest discover -s learning/hrl -p 'test_learning.py' -v
```

The validation receipt describes implementation checks only. Smoke policies are
not selected for use in the paper and do not establish superior regulation.

After installation into the production project's new `analysis/hrl_learning/`
directory, replace `learning/hrl/` in these commands with
`analysis/hrl_learning/`. The existing production assets and policy defaults
remain preserved; the runner applies the opt-in variants only to marked copies.

Engineering checks can run the complete selection workflow at a deliberately
small budget with `--pipeline-check`. Their protocol and output are explicitly
labelled `pipeline-validation`; those policies are not performance evidence.

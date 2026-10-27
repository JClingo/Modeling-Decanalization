This follow-up isolates the reset-on-policy-update setting at the existing
100-second training episode limit. Both conditions use the original learning
settings and traversal increments of +1. Disabling the reset carries the whole
world state across policy updates; timed/failure resets still clear history.
It does not isolate retaining only tile counts or persistence across episodes.

`protocol.json` freezes the comparison before training. Three matched seeds
(1201, 2301, 3401) use the same two-million-transition maximum, eight-trial
checkpoint selection, and plateau stopping rule as the earlier screen.
The completed 100-second reset baseline training is reused. Initialization
hashes for all four networks must match the corresponding baseline seed.

Each selected policy is compared on 16 continuous-homeostasis CCC trials with
environment seed 51001, excluded from checkpoint selection (seed 41001).
Evaluation lasts 300 seconds, retaining h and tile counts between three
100-second reporting windows; phase-start velocity initialization remains
common to all policies. Seed 61001 remains reserved. Matching initial h,
resource layouts, and tile histories are audited across all compared policies.
Existing identical independent evaluation receipts can be reused.

The primary measure is time-averaged absolute h. Secondary outputs describe
time within ±5, extreme errors, later-window performance, route reuse, tile
counts, and sampled training episode duration. Analysis uses three paired
training seeds, not repeated trials as independent training replications.
This is an exploratory CCC comparison with no noncanalizing control or CDR
evaluation. Neither the paper nor production policies are updated automatically.

`comparison.py` queues behind the active prior study, then runs the three new
training jobs sequentially and performs the independent comparisons. It checks
the frozen core runner hashes without changing those sources. APFS copy-on-write
sharing of identical completed scratch assets preserves file contents and
independent future writes while limiting storage use.

`status.json` and `process.json` track the queued/running pipeline. On success,
`RESULTS.md`, `results.json`, per-policy and per-phase CSVs, comparison PNG/SVG,
candidate snapshots under `policies/`, and raw audited evidence under `inputs/`
are written here. Native run logs and progress receipts remain under the raw
root recorded in `protocol.json`. An incomplete attempt is preserved and must
be inspected before an explicit retry.

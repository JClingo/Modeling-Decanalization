This authorized sequence follows the unsuccessful duration/history/combined
learning screens. All native work uses marked isolated copies and a versioned
runner under `learning/hrl_next`; the earlier runner, production assets,
selected policies and manuscript results remain preserved.

The pipeline runs sequentially to limit memory pressure:

1. Audit action sampling, shared observation scaling, native recurrent resets
   and the failure-boundary mismatch. Four saved policies receive eight matched
   CCC trials with mean actions and eight with sampled actions. This is a fixed
   policy diagnostic. Mean-action evaluation remains the primary protocol.
2. Compare quality reward against negative absolute-error reward, including
   absorbing-boundary failure accounting for the latter. Both retain original
   learning settings, 100-second worlds and reset-on-update behavior.
3. Test the probability-ratio surrogate alone against the selected reward's
   original trainer. Keep the original rates, update count, recurrent sampler,
   losses, shared encoder ownership and clipping. This does not reuse the
   unsuccessful combined guarded/annealed trainer.
4. Test an adaptive 100/200/300-second duration curriculum against the selected
   fixed 100-second setup. Advance only after 500k/1m transitions, ten gathers
   with mean training time-MAE <=25 and true termination fraction <=0.0025,
   and a detected world reset. Record every advancement. A run that never
   advances is reported as such, not as 300-second training exposure.
5. Evaluate the selected policies with and without traversal-sensitive tile
   costs. The control keeps visit counters, resources, passive loss and geometry
   but fixes all three physical tile-cost denominators and the anticipation
   tile-cost denominator at 2, the first-entry cost. This tests dependence on
   the cost mechanism in CCC; it is not a matched-control training experiment.
   The inherited zero-cost decanalization branch is preserved, and this static
   control is not enabled for CDR.
6. If a changed setup passes the frozen practical screening rule, train it and
   the original baseline on five fresh paired training seeds. Freeze all ten
   selected policies before using reserved final environment seed 61001.
   Evaluate 32 continuous CCC trials, plus separate 16-trial CCC and CDR runs
   with the paper's h-reset boundaries. Do not pool these boundary protocols.
   If no changed setup passes screening, record that result and skip redundant
   confirmation training. No candidate is automatically promoted.

The screens use three matched training seeds, up to two million transitions
per policy with no plateau stopping, and checkpoints every 20 gathers plus the
first gather. Selection averages four CCC trials from each of three development
environment seeds (41011, 41021, 41031). Development comparisons average eight
trials from each of two separate seeds (51011, 51021). Selecting an arm for the
next stage requires at least 10% lower mean time-MAE, improvement in at least
two of three paired training seeds, and no more than a 0.01 increase in time
beyond |h|=100. This is an execution rule, not a significance claim.

The primary outcome is time-averaged absolute h. Raw rewards across objectives
are not compared. Training still terminates beyond |h|=100, whereas fixed-horizon
evaluation continues; the audit explicitly reports that mismatch. The
absolute-error terminal reward represents an absorbing failure convention.
It does not establish that the physical world remains at that h.

Continuous CCC evaluations retain h and tile counts across three 100-second
reporting windows; inherited phase-start velocity initialization remains common.
Ordinary traversal increments remain +1 and CDR retains the existing half-floor
rule. A static control has consistent physical and predicted costs, not a sensor
that incorrectly predicts wear. Sampled training episode durations remain lower
bounds measured every 100 decisions, not exact survival estimates.

`protocol.json` freezes budgets, gates, seed pools and code hashes before the
study. `engineering_verified.json` records native smoke checks. `process.json`
and `status.json` identify the live pipeline and active stage. Per-stage
`RESULTS.md`, `results.json` and decisions distinguish development from final
confirmation. `inputs/` retains raw scenes, loaded-model checks, code, configs
and training evidence using independent APFS copy-on-write copies. `policies/`
contains exported unpromoted checkpoints. Failed attempts are preserved and an
incomplete run must be inspected before an explicit retry.

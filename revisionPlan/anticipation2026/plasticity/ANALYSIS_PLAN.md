# Frozen-HRL traversal-factor comparison

Written before inspecting the new condition outcomes on 26 October 2026. This
is an exploratory extension of the corrected-anticipation evaluation, not a
preregistered experiment or a new training-seed study.

The decanalized tile branch adds `DecanalizationRateFactor` directly to
`OverlapCount` on entry. Factors 0, 1, 2, 4 and 7 mean no counted visit, one
ordinary counted visit, and two/four/seven counted visits per actual entry.
Ordinary phases retain one count per entry. Factor 0 does not remove all prior
environmental history; it prevents additional counting during phase 2.
Recanalization still halves counts with rounding down for every CDR condition.

All conditions use the selected fresh HRL checkpoint (750,000 transitions),
corrected anticipation, frozen weights, environment seed 10001, 250 complete
trials, and three 2,000-decision phases at dt=0.05. Existing corrected factor-0
CDR and CCC batches supply reference conditions; four new CDR conditions are
evaluated in isolated copies. No training or checkpoint selection occurs here.
The only intended experimental change is decanalized traversal counting.

The main outcome is phase-3 event/update-sampled mean absolute h (MAE). Actual
HRL reward per phase is secondary. We report all nine existing measures
descriptively, together with medians and large-error tails. No trial is removed
on the basis of its performance. Phase-3 lower MAE means better regulation;
higher reward means better performance on the executed proximity objective.

Primary comparisons are each new factor minus factor 0 and minus CCC, using
two-sided Welch tests and unadjusted 95% intervals. Holm adjusts the 16 tests
together (four new factors × two reference conditions × two outcomes). The
phase-2 versions form a separate exploratory family of 16. The existing factor-0
versus CCC comparison remains the earlier reference result, not an additional
test in this 16-test family.

To examine acceleration relative to normal counting and compare all levels, a
secondary table includes all ten CDR-factor pairs, oriented higher factor minus
lower factor. Holm adjusts these 20 tests (ten pairs × two outcomes), separately
within phases 2 and 3. Duplicate contrasts in primary and secondary tables have
the same raw estimate and p value but their stated Holm families differ.

Sensitivity analyses use trial-level phase-3 minus phase-1 changes, independently
compared between conditions, and paired trial-ID differences where baseline
matching is supported. We audit baseline metrics, recorded RNG and memory,
environment/asset provenance, actual loaded model hashes, completion receipts,
and all saved scene hashes. Full scene hashes will differ across factors
because the factor itself is included in scene metadata; no unqualified exact
engine-state matching claim is made.

Relative MAE improvement is 100 × (reference mean − factor mean) / reference
mean. Relative reward improvement is 100 × (factor mean − reference mean) /
reference mean. Trial bootstrap percentile intervals (10,000 resamples, RNG
seed 261026) independently resample each condition, preserving the two outcomes
within each sampled trial. These ratio intervals are descriptive sensitivity
evidence, separate from the Welch primary analysis. Within-trial phase changes
use the same trial as their baseline. Relative percentages are computed from
group means, not averaged per-trial ratios.

Factor 1 is the ordinary counting rate; increasing factors model faster changes
in environmental history. They do not measure neural plasticity or online
policy learning. Apparent best factors are exploratory observations from these
selected policies and scenes. Intervals containing zero do not demonstrate
equivalence, and the extension cannot establish an optimal factor or robustness
across independent training runs.

## Pretreatment-matching audit amendment

While the native batches were running, and before inspecting phase-2/3
performance, the quality audit found a few baseline-trajectory differences even
though recorded initial h, RNG and recurrent state matched. Keep every trial in
the planned primary analysis. Add a paired sensitivity analysis restricted to
IDs with identical values for all nine phase-1 metrics and all captured start
fields (initial h, observed start h, RNG and memory). This is a pretreatment
matching restriction, not exclusion based on post-intervention performance.
Its separate Holm family is the same 16 contrasts within each analyzed phase.
The unrestricted paired-ID analysis remains explicitly conditional.

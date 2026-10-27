# HRL recanalization-count comparison

Author approved these conditions on 26 October 2026, before generating their
new outcomes. This is an exploratory extension, not a preregistered study.

Keep the selected corrected-anticipation HRL policy fixed (750,000 collected
training transitions). Count one visit per entry before, during and after the
intervention. Change only the operation on stored tile counts when CDR exits
decanalization:

| Condition | Count transformation |
|---|---|
| zero | n <- 0 |
| quarter-floor | n <- floor(0.25 n) |
| half-floor | n <- floor(0.5 n), current implementation |
| three-quarter-floor | n <- floor(0.75 n) |
| keep | n <- n |
| half-exact | n <- 0.5 n, no flooring |

CCC continues ordinary counting and has no corresponding count transformation.
All other perceptual/physical perturbations, homeostatic resets, initial seed
(10001), 20 Hz timestep and 2,000 decisions per phase are retained. Weights are
fixed; this is environmental history manipulation, not further policy training.

Use 250 complete three-phase trials per condition. Reuse the verified existing
half-floor CDR factor-1 batch and HRL CCC batch. Run five new CDR batches in
isolated project copies. Do not modify production assets or defaults. Before
scoring, compile the edited graphs in Unreal and validate the real recanalization
event at small, odd, even and large counts, plus ordinary/decanalized increments.

Primary endpoint is phase-3 event/update-sampled mean absolute homeostatic
distance. Received objective reward is the second performance endpoint. Report
all six CDR conditions versus CCC, with independent-trial Welch differences,
unadjusted 95% intervals, and Holm adjustment across 12 tests (six conditions
times two endpoints). The existing half-floor condition remains the main paper
condition, irrespective of new results.

A separate secondary family compares the five new conditions against half-floor
for both endpoints (10 tests), including half-exact versus half-floor to isolate
rounding. Any additional CDR pairwise comparisons are explicitly exploratory,
with all 15 pairs times two endpoints adjusted together (30 tests). Phase 2 is
a separate diagnostic family with the same structures, because recanalization
occurs after that phase and should not intentionally alter earlier behavior.

Report descriptive statistics for all nine recorded outcomes and phase-start
tile-count distributions. Do not substitute signed h for absolute error or
choose a transformation by significance. Retain all completed fixed-horizon
trials, including extreme errors. A failure to reject does not establish
equivalence or optimality.

Check phase-1 and phase-2 matching across same-ID batches and recorded start
fields (initial h, RNG and recurrent memory). Use all IDs in primary Welch
comparisons; baseline-change, paired-ID and pretreatment-matched analyses are
sensitivities. Matching captured fields does not establish full engine-state
identity. Use phase 1 for baseline subtraction and for eligibility of matched
sensitivity pairs, as in the earlier sweep. Report phase-2 mismatches as an
additional diagnostic; do not condition a CCC comparison on equal phase-2
outcomes, since the interventions already differ then.

Independent base R must reproduce all descriptive statistics, Welch intervals,
p values and Holm corrections before writing the final report/figures. Verify
completion receipts, actual loaded policy hashes, all saved scene hashes,
counting factor 1 on every tile and the compiled tile-asset hash for each new
condition. Audit the count transformation through native handler tests and
phase-boundary captured counts. Preserve native logs and the exact analysis
scripts. One trained policy does not support inference across training seeds.

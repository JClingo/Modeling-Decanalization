# Counting-rate × count-retention interaction

Author approved the focused factorial follow-up on 26 October 2026, before
the two new batches. Earlier marginal-sweep outcomes were already known.
This is an exploratory extension, not a preregistered experiment.

Cross entry increments during decanalization k={1,7} with recanalization rules
reset (n<-0), current half-floor (n<-floor(n/2)), and keep (n<-n). Pre- and
post-intervention entry increments remain one. Reuse four existing CDR cells
and CCC; run the two missing k=7/reset and k=7/keep cells, 250 trials each.
All seven conditions contain 250 trials: 1,750 trials, 5,250 phases and
10,500,000 decisions, including 500 new trials / 3,000,000 new decisions.

Retain the same selected corrected-anticipation HRL policy (750,000 training
transitions), seed 10001, three 100-second phases, 20 Hz, 2,000 decisions per
phase, perceptual/physical intervention and homeostatic resets. No retraining.
The main paper condition remains k=1/half-floor. Use isolated copies; preserve
production assets. Compile and audit both variants before scored evaluation.

Primary endpoints are phase-3 event/update-sampled MAE and received objective
reward. For each retention rule r, define the simple counting-rate effect
delta_r = mean(Y[k=7,r]) - mean(Y[k=1,r]). The interaction compares these
effects across rules: delta_reset-delta_half, delta_keep-delta_half, and
delta_keep-delta_reset. Negative values for MAE and positive values for reward
mean that raising the counting rate is more favorable under the first rule.

Primary interaction inference uses four-cell linear contrasts of means, with
independent-cell heteroskedastic standard errors and Welch-Satterthwaite
degrees of freedom. For coefficients c=(1,-1,-1,1), variance is sum(c_j^2
s_j^2/n_j), and df is variance^2 / sum[(c_j^2 s_j^2/n_j)^2/(n_j-1)]. Report
unadjusted two-sided 95% t intervals and Holm adjustment across the three
interaction contrasts × two endpoints (six tests). Their dependence is allowed
by Holm; these are three pairwise comparisons of the three rate effects, not
three independent interaction dimensions. No separate omnibus test is claimed.

Secondary families: three simple 7-versus-1 effects × two endpoints (six
tests), and six CDR-versus-CCC comparisons × two endpoints (12 tests). Phase 2
uses separate matching families as a diagnostic: retention has not yet been
applied, so an apparent interaction then warrants checking state alignment.

Primary interaction sensitivities: Welch contrasts of within-trial P3-P1
changes; same-ID paired four-cell contrasts; paired four-cell contrasts of
baseline changes; and paired restriction to IDs matching all nine phase-1
metrics and captured initial h, RNG and recurrent memory across the four
cells. Each method has a separate six-test family per phase. Do not remove
trials from the primary analysis. Check pretransition matching within each
counting-rate group; equal recorded fields do not prove full engine identity.

Keep every completed fixed-horizon trial, including extreme errors. Report
all nine descriptive outcomes and phase-start landscape counts. An uncertain
interaction is not equivalence or proof that the rules act independently.
Rate can change trajectories as well as counts: resetting tile counts removes
the direct count-history channel but need not erase resource or recurrent
memory differences. Claims apply to this selected policy, not independent
training seeds. Do not choose a replacement primary rule by these results.

Verify receipts, selected loaded-model hashes, corrected anticipation identity,
variant tile hashes, all 1,500 new scene hashes, and factor 7 on every new tile.
Audit 15 real Blueprint handler cases per new variant: transformations on nine
small/odd/even/large counts, and factor/one-entry/two-entry checks in ordinary
and decanalized modes. Native editor setup checks run sequentially, followed
by two concurrent scored batches. Independently reproduce all statistics and
Holm families in base R before reporting; preserve compact inputs and an archive.

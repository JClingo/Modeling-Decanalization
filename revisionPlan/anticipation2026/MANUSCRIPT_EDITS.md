# Proposed paper revisions after the anticipation repair

The main result needs to change. The corrected model does not establish improved
post-intervention HRL regulation under the intended factor-1 counting rule.
The separate factor-0 NF reference shows that reward and absolute regulation
can diverge; a matching NF factor-1 evaluation is still needed for joint primary
claims. The existing title can remain: the model still formalizes
canalization and decanalization, even though the original benefit is uncertain.

These are proposals against the current `modelingDecanalization.tex` and
`appendix.tex`, not edits already applied to those files. Line numbers refer to
the manuscript checked on 26 October 2026. Numerical tables and figures are ready
in `primary-factor1/`. Its `RESULTS.md` gives the current HRL comparison. The
root-level numerical report and tables retain the earlier factor-0 analysis.
The [author's clarification](PRIMARY_DESIGN_CLARIFICATION.md) records the
primary-factor decision and distinguishes it from a claim of an optimal factor.

## Abstract: lines 97–104

Resolve the two competing abstract drafts and remove “TODO: Integrate better.”
Both versions currently claim improved HRL regulation. Retain the motivation and
model description, then replace the outcome/contribution sentences with:

> Following correction of the model’s anticipatory observations and selection of
> policies for absolute setpoint regulation or received reward, the HRL agent’s
> post-intervention absolute-deviation contrast was uncertain (CDR minus control
> −3.69, 95% CI [−9.72, 2.35]), using the intended increment of one traversal
> count per entry in all phases. The model
> formalizes how environmental history and temporary perturbation interact with
> fixed learned policies; the corrected evaluation does not establish a benefit
> to subsequent homeostatic regulation.

This is the primary HRL phase-3 Welch interval. Defer a matching primary NF
abstract claim until NF has been evaluated at factor 1. If the factor-0 NF
reference is included separately, explicitly identify its different counting
condition. Do not reuse the factor-0 baseline-change bootstrap as factor 1.

## Methods: anticipation and observations, lines 170–193

Equation (h-hat) now describes the intended sum implemented by the repaired code.
Keep it, but replace the old hypotenuse / half-first-and-last-tile explanation.
State the executed approximation explicitly:

\[
\widehat G=\sum_i o_i,\qquad
\widehat L=\sum_j \frac{\ell_j}{v}\frac{B_j}{d_j}
 +\frac{\ell}{v}\frac{P}{K\Delta t},\qquad
\widehat h=h+\widehat G-\widehat L.
\]

Here, ℓ is the ray horizon, ℓ_j is its length inside tile j’s world component
bounds, v is the supplied movement-speed parameter, B_j is tile base impact,
P is passive loss per homeostatic update, and K is the number of decisions per
update. The denominator d_j is max(1, n_j+1) for the already-entered starting
tile and max(1, n_j+2) for a future tile; n_j is the count at prediction time.
Passive loss is charged once for the horizon, including gaps between tiles.
With P=0.5, K=5 and Δt=0.05, its ordinary rate is 2 units per second.

Suggested replacement prose:

> Anticipatory observations are hand-computed from the central raycast. Predicted
> gain sums the impacts of all intersected pellets. Predicted loss combines the
> time spent crossing each intersected tile with passive loss over the full
> horizon. Tile crossing time is the ray’s length inside the tile bounds divided
> by the supplied movement speed. The starting tile uses its recorded entry
> count, while future tiles include one prospective entry. This estimates
> straight travel at constant speed through the present axis-aligned tiles;
> it does not predict turns or pellet respawns. Gain and loss are inputs to the
> policy, rather than values learned by its critic. During decanalization,
> anticipated loss is deliberately set to zero.

Add a brief implementation-audit sentence or supplementary note: the earlier
code retained only the last pellet, used approximate/disconnected endpoint
logic, mis-scaled passive loss, and applied an extra 0.2 multiplier. The corrected
Blueprint passed 23 native collision-based regression checks. This establishes
agreement with the specified approximation in those cases, not perfect
prediction of arbitrary trajectories.

Clarify that **both policies** receive the same anticipatory feature types.
The schema has 11 values: one collision feature, seven ray values, perceived
gain and loss, and signed setpoint distance; recurrent memory has 64 values.
The central-ray repair does not by itself resolve the existing TODO about the
precise semantics of the other seven ray values.

## Methods: NF comparison, lines 223–227

Delete claims that NF cannot take anticipatory actions or lacks sophisticated
reward discounting. Both families use recurrent PPO with discount 0.99 and
receive anticipatory observations. NF differs in its executed one-sided reward
objective and effective training settings. Its absence of reward for states at
or above zero does not establish an inability to anticipate future rewards.
Also replace “rewards or punishes” with the executed nonnegative rule: the NF
objective gives zero for worsening or nonnegative states.

## Methods: training and checkpoint selection, lines 235–237; appendix table

Replace the old selection description based on mean signed h and reward. The
new criterion is minimum **mean absolute h** for HRL and maximum **actual
received reward** for NF, over three CCC phases per validation trial.

Report eight-trial checkpoint screening (environment seed 20001), independent
32-trial candidate confirmation (30001), and a final 250-trial test per
family/condition (10001), excluded from selection. Keep the original reward
functions and the selected policies’ effective PPO settings.

Update the HRL checkpoint entry from label 10000 to **gather 75 / 750,000
collected transitions** (nominal update label 2400). NF remains the historical
**label-5000** winner, validated with corrected observations. Do not write that
the selected NF policy was newly trained, or interpret the export’s zero new
steps as zero historical training. Do not infer achieved NF transition totals
from that label.

Summarize the fresh and lower-rate refinement candidates in a supplement. State
that the fresh NF run encountered a communication failure at 5.38 million
transitions before its planned minimum; all saved candidates were retained for
independent confirmation. The HRL minimum was revised after deterioration.
These are transparent optimization decisions, not evidence of global
optimality. The selected fresh HRL checkpoint uses the original HRL learning
rates, not the lower refinement rates.

## Intervention and sensitivity: lines 243–257

Use **count factor 1** for primary HRL analysis, as the author clarified was
originally intended: one increment per actual tile entry before, during and
after decanalization. Update the appendix's decanalized entry increment from
0 to 1. Retain recanalization count halving and phase-boundary h resets. Equal
increment rates do not remove the halving step or equalize physical conditions.
Be explicit that
ordinary physical losses are removed during phase 2 as well as predicted
losses: recorded CDR phase-2 loss totals are zero. Consequently, these runs do
not isolate the causal effect of perceptual distortion from the physical
environmental changes.

Remove the traversal-count footnote’s claim that HRL still significantly
improves under decanalization. A new corrected-anticipation sweep now evaluates
factors 0/1/2/4/7 with the same selected HRL policy and 250 trials per factor.
Post-intervention MAE ranges from 14.79 to 15.51 and reward from 79.83 to 80.19;
the planned comparisons and sensitivity analyses remain uncertain. Use this
new sensitivity evidence and its [proposed Results paragraph](plasticity/RESULTS.md).
Factor 1 is primary; factors 0, 2, 4 and 7 are sensitivity conditions. Record
the author's clarification after the sweep rather than describing the new
designation as preregistered. Do not call factor 1 optimal.
Keep the old files separate as historical evidence; they use different code and
policies and cannot be pooled with the new sweep. The new study does not
establish equivalence or an optimal factor.

## Statistics and Results: lines 275–366

Keep the primary phase-3 Welch analysis with unadjusted intervals. The current
HRL-only factor-1 report adjusts nine outcomes with Holm; phase 2 is a separate
exploratory nine-test family. The old factor-0 joint analysis used 18 tests.
A matching NF factor-1 evaluation and explicit joint multiplicity plan are
needed before reporting both objectives as one primary factor-1 experiment.
Retain the evaluation-trial unit and event/update-sampling qualification.

Replace “Two HRL and two NF policies” with “One selected policy per objective,
evaluated under both CDR and CCC.” Four conditions are not four independently
trained policies.

Replace the HRL primary table with `primary-factor1/hrl_post_table_rows.tex`
(all nine outcomes, including near-setpoint fraction), and any HRL phase-2
table from `primary-factor1/primary_contrasts.csv`. The root-level NF rows
describe the separate factor-0 reference, not factor-1 primary NF. Suggested
primary HRL Results:

> For HRL, post-intervention mean absolute deviation was 14.789 under factor-1
> CDR and 18.475 under CCC (difference −3.686, 95% CI [−9.722, 2.349]). Mean
> objective reward was 79.964 and 79.349 (difference 0.615, 95% CI
> [−1.796, 3.026]). The SD, RMS,
> near-setpoint fraction and objective-reward contrasts were also uncertain.
> These results do not establish the predicted improvement in post-intervention
> regulation. They also do not establish equivalence between conditions.

Separate reference-only wording, if retaining NF factor 0:

> In the separate factor-0 evaluation, NF earned more post-intervention reward
> under CDR (21.327 versus 18.525;
> difference 2.802, 95% CI [1.737, 3.867], Holm p=0.00000518). Its absolute-error
> contrast remained uncertain (66.210 versus 41.584; difference 24.626, 95% CI
> [−28.795, 78.046]). The fraction of recorded samples within ±5 decreased from
> 0.06775 to 0.04952. Higher NF reward therefore did not establish better
> absolute setpoint regulation.

The primary HRL MAE and reward Holm p values are both 1.0. More negative logged
loss and greater logged gain remain detectable for factor-1 HRL. The harvest
contrast does not pass the nine-outcome Holm adjustment (p=0.101). These
outcomes should not substitute for the regulation endpoint.

For factor-1 HRL, all captured initial h, RNG and recurrent-memory starts
match across 250 IDs, while all nine baseline metrics match across 249 IDs.
Retain all 250 trials in the primary Welch analysis. Report paired-ID,
baseline-change and the 249-pair pretreatment-matched sensitivities; all retain
uncertain MAE and reward contrasts. Exact scene hashes encode the changed
factor and are not a useful pairing criterion across these batches. The old
235/235 scene counts apply only to the original factor-0 HRL/NF comparisons.

Correct the outcome definitions while editing: RMS is the root mean square of
h values, not of h changes. Describe the pellet-count measure using its logged
definition unless distinct pellet identities are established separately.

## Figures: line 308 and captions

Use `primary-factor1/post_outcomes.pdf` for a focused HRL phase-3 figure and
`primary-factor1/phase_outcomes.pdf` for the full HRL three-phase panel. The
root-level two-family figures still depict factor 0. The current figures are
generated from the new sidecars and have been visually checked. Recommended
post-figure caption:

> Post-intervention HRL outcomes for 250 trials per condition, comparing the
> intended factor-1 CDR condition with CCC under the same selected policy.
> Points show trial means and bars show unadjusted 95% confidence intervals.
> Homeostatic summaries use recorded event/update samples. Reward is summed
> over 2,000 decisions per 100-second phase. Condition
> differences and their confidence intervals are reported in the tables.

The full-phase caption should retain the warning that h is restored at phase
boundaries: the connected means do not show uninterrupted recovery. Keep the
intervention phase visible somewhere; its much larger errors explain the
whole-trial averages. Existing screenshots are illustrative and are not
evidence from the newly selected HRL evaluation.

## Discussion and conclusion: lines 374–415

Replace the statement that the results support the HRL-benefit hypothesis.
The point estimate favors CDR, but the corrected evaluation leaves both benefit
and harm compatible with the interval. The uncertainty is not proof that the
effect is absent. The separate factor-0 NF reward/proximity dissociation cannot
demonstrate that NF lacks anticipation. Remove the “non-anticipatory quality”
explanation and the claim that NF required more training because it is reactive.

Suggested conclusion:

> The model implements environmental canalization and temporary perturbation in
> a homeostatic navigation task. After correcting the anticipatory observations
> and selecting policies for their respective objectives, post-intervention
> HRL absolute regulation remained uncertain relative to uninterrupted
> canalization under the intended counting rule. These results constrain the proposed benefit of
> decanalization within this model; they do not establish improved regulation
> across trained policies or biological systems.

Add that the old/new comparison changes both anticipation and the HRL policy.
It cannot isolate which correction or training change accounts for the changed
estimate. Stronger ordinary HRL regulation is a plausible reason for reduced
room for improvement, not a mechanism established by these runs. Keep the
single-policy/seed limitation and the phase-boundary reset limitation. Note the
large error tails and fixed-horizon evaluation beyond the training failure
boundary; all trials remain included.

If discussing NF's reward/proximity dissociation, identify it as factor-0
reference evidence until a matching factor-1 evaluation is available. It
cannot supply the missing matching primary NF result.

## Additional recanalization sensitivity: Results and Discussion line 400

The author-approved post-decanalization comparison is now complete: retain
0%, 25%, 50% or 75% with flooring, retain all counts, or halve exactly without
flooring. Every condition retains one count per entry throughout and uses the
same fixed HRL policy, with 250 trials per condition and the existing CCC
control. This changes the phase-3 count transformation; it is distinct from
the earlier sweep of entry increments during decanalization.

Use [the proposed supplement additions](recanalization/MANUSCRIPT_ADDITIONS.md)
and [full results](recanalization/RESULTS.md). Post-phase MAE ranges from 13.753
to 14.874 and reward from 79.964 to 81.052, versus CCC 18.475 and 79.349.
None of the six CDR-versus-CCC comparisons establishes a difference in either
endpoint after the twelve-test Holm adjustment. Alternatives also do not establish a
difference from current half-floor in the separate ten-test family. Paired
and baseline-change sensitivities do not pass their corresponding adjustments.
This does not establish equivalence or an optimal retention rule.

Replace the manuscript's statement that sensitivity to count-halving was not
explored. Retain half-floor as the main condition. The manipulation strongly
changes environmental history: mean phase-3 total counts are 336.180 for
half-floor and 642.172 for exact halving. Performance uncertainty persists
despite that difference. Include the transformations, fixed-policy identity,
two endpoint families and single-policy limitation in the supplement. The
new CSVs, two figures and table rows are in `recanalization/`.

## Counting-rate × retention interaction: supplementary Results

The [completed factorial evaluation](interaction/RESULTS.md) directly crosses
1×/7× counting during decanalization with reset, half-floor and full retention,
250 trials per cell under the same fixed HRL policy. This tests the interaction
that the two marginal sweeps could not resolve. The new two cells add 500 trials;
the factorial dataset and shared CCC contain 1,750 trials altogether.

No primary interaction passes the six-test Holm adjustment; paired and
baseline-change analyses also do not establish an interaction. For example,
keeping all counts rather than half-floor changes the 7×−1× effect by +0.313
MAE (95% CI [−4.178, 4.803]) and −1.467 reward (95% CI [−4.859, 1.924]).
The estimates permit potentially relevant effects, so do not claim equivalence
or independence. Retain 1×/half-floor as the primary condition.

Use [the proposed supplement prose](interaction/MANUSCRIPT_ADDITIONS.md), the
two figures and `interaction_table_rows.tex`. Explicitly distinguish these
fixed-policy environmental-history manipulations from neural plasticity and
robustness across training seeds. The report includes all six CDR-versus-CCC
comparisons; none establishes an endpoint difference after its adjustment.

## Code availability and disclosure: lines 279 and 429–436

The paper’s pinned Unreal submodule still refers to the earlier source. Before
submission, publish the repaired asset, selected model identities, native tests,
selection protocol, final data and scripts, then update the source reference.
The local full bundle is recorded in README.md. This folder preserves compact
raw sidecars and all new tables; it does not itself publish the full experiment.

Update the AI-use disclosure to describe assistance with code inspection and
repair, training/evaluation orchestration, and analysis/proposed manuscript
revisions, with the authors responsible for checking the implementation and
scientific interpretation. Retain whichever journal-specific disclosure format
the authors use.

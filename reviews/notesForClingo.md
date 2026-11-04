# Notes for Clingo

Updates on my pass through the rewrite, and the decisions behind it. Questions collect at the bottom.

## Updates

### Nov 1

The `responses/` folder is new and fully tracked, so anything we want versioned outside the paper can go here. Your Oct 29 cleanup untracked `revisionPlan/`, which removed `adaptiveBehaviorRevisions.txt` from the repo (and from my copy when I pulled). Re-adding it to the allow-list on Oct 30 didn't bring it back, since the file itself was never re-added. I restored the Oct 27 version and moved it to `responses/adaptiveBehaviorRevisions.txt`, and the .gitignore now allows `/responses/` in place of that one file. Opening up all of `revisionPlan/` would have re-exposed the large Unreal material you deliberately cleaned out, so please leave that folder local.

I'm going through the paper section by section, discussing before editing, then editing in small batches. Much of my Oct 25–27 wording was lost in the rewrite, and I'll bring back what still fits the new model. Sources for that wording are commits 4d4310e (end of my Oct 27 pass), 0cccf10 (Oct 25 pass), and b2ddbb4 and a0296da (Oct 9). The `revisions/2026-10-30-factor1-canalization-null` copy (removed; last in commit 874a0b4) also preserves much of it.

## Decisions

### General

No bullet lists in the paper. Plain language, with worked examples using actual numbers.

### The story of the changes

This goes in the response letter, not the paper; the paper need not describe the changes at all. The old response file, `responses/adaptiveBehaviorRevisions_old.txt`, is in git history (commit 874a0b4), and the new one is `reviews/responseToReviewers.txt`. Its opening covers the audit, the finding that the Unreal agents never formed canals, and three central changes: a 2D world in pure Python, easy to run headless and reproduce; canalization located in learning, as Reviewer 1 recommended; and the new question of how agents cope with a world that changes in ways training did not prepare them for. It also discloses the switch to training in the stable world.

Change-history material comes out of the paper: the Methods paragraph beginning "An earlier version of this study used an Unreal Engine sandbox", the phrase "its world mirrors the Unreal task where possible", the Limitations reference to "our earlier Unreal implementation", and the pointers to the Supplementary Material in Methods, Statistics, and Limitations. Possibly keep a one-line note in Data availability that the Unreal code is archived.

The supplement won't be submitted. It stays in the repo as a source for the response letter, which will carry what reviewers need from it: the audit findings, the route analyses showing no canals, and the decisions made after seeing data. The draft letter's sentence pointing to the Supplementary Material needs fixing.

Point-by-point responses are drafted where the answer is clear and marked TODO elsewhere. Several items the old letter marked done are no longer in the paper, notably all of Reviewer 2's (Safron and DeYoung, the p-factor as the second principal component, ALBUS, Brouwer) and the expanded Discussion. These need restoring.

### Methods (done Nov 1, Jeff to review)

The paragraph on the earlier Unreal version is removed, along with the Supplementary Material pointers, the Unreal reference in Limitations, and the archive note in Data availability.

The world section now says plainly that the stable world is used only for training and the changing world for all evaluation, and that both agents and both conditions face the same changing world. 

Belief precision is explained in plain language, with the neighborhood vs. new city example (citing Yon and Frith, 2021), precision as a count of observations, and a worked example of a confident belief barely moving.

The reward functions are back in the style of my earlier versions: the general drive formula, food satiation, Goldilocks, the heater, worked examples recomputed for the drive-reduction reward, and the point that NF agents can also anticipate. HRL, NF, and training are now separate subsections.

No bullet lists remain in the paper. Stale comments are removed, and the commented-out Brouwer et al. (2024) entry, suggested by Reviewer 2, is now a live bibliography entry, to be cited when the Reviewer 2 material is restored.

The changing-world interval in Results is corrected to [−1.8, 0.6] at a boost of 3.

### Methods, line edits (Nov 2)

Principle: Methods states the rules of the model; predictions about how agents behave go in Results or Discussion. Motivation for a mechanism gets one short paragraph after the mechanics.

World. Speed is "5 tiles per second", not s⁻¹. Traversal cost: n is defined as entries before the current crossing, the worked numbers follow the equation (a crossing takes about 0.2 s and costs about 0.2 c(n): 1 for the first crossing, 0.8 for the second, approaching 0.2), and "uncrossed" replaces "unworn". A short niche-construction paragraph follows (Laland, Davies, Bochynek restored). The sentence on traversal cost not being stored in the map is cut. Patches: "pellet value" replaces "quality", with a worked fertility example (ten harvests, f ≈ 0.43, regrowth ≈ 18 s). The two-worlds text now builds on what precedes it: the world as described, then the change at 300 s ("the changing world"), then training in a simpler stable version, ending with the question the design asks. The new patches are said to be no richer per pellet, only reliable and faster (4 s vs. 8 s).

Cognitive map. "Perception is fixed" cut. Opens with beliefs about observed pellets (V_c, P_c, v = 0 for empty cells). The mechanics come right after the equation, with a precise (≈ 9.8) vs. imprecise (≈ 6.7) worked example. The neighborhood vs. new city example moved to the intro, after "canalization corresponds to the precision of the agent's expectations". The regrowth paragraph is introduced as a fixed rule used when choosing where to go; the sentence predicting that agents keep returning to degraded patches is cut. The rule is correct in the stable world and wrong in the changing world (too optimistic for degraded patches, too pessimistic for the new ones); not stated in the paper.

Policy. Option names in italics, not small caps. Only the main, interpretable inputs are listed, with the full list in the code repository; the appendix says "10 inputs and a bias".

HRL and NF. The κ-scale and summing-over-ticks clauses are cut. The 0.2 per unit is derived in the text (5/25). "Earns a reward of 2". The per-second tile example is replaced by one sentence: losses cost reward below the setpoint and earn it above.

Protocol. The phase paragraph describes the trial in order, with the change at 300 s and no physiology clause. CCC and CDR are spelled out. "Levers" is replaced throughout by two named components, precision relaxation and the entropy boost (the label fig:levers and the file names are unchanged). The temperature is explained in plain words, and the main setting (d = 1, b = 1) is stated first. "acted on here canalization is stored" is fixed.

Results (first pass Nov 2). Rewritten around the per-phase finding: many undisturbed agents are trapped before the new patches appear (62% HRL, 48% NF); they find the new patches late, after falling deep into deficit; decanalized agents find them sooner. "Helplessly continue to pursue them" and "inescapable" are gone, and the second subsection is now "Decanalization helps agents adapt sooner". The unsupported claim that both policies regulate well in a stable world is cut. Table numbers are no longer repeated in prose. The boost 10 comparison now notes three training seeds. The NF subsection explains the smaller benefit through overshoot (mean h panel). Results has no subsections; each part opens by naming the hypothesis it tests, without H1–H4 labels since nothing was preregistered. The third hypothesis (intermediate intensity) is reported as holding only in part. "Undisturbed" is replaced by CCC and CDR throughout, including figure labels, since every agent faces the world change; CCC is glossed as "canalization throughout" and both conditions are now named in the intro. The overview caption no longer says the CCC agent is "unable to escape", and its CDR note says "Beliefs flatten" instead of "Perceptions flatten". "Without changing its physiology" is cut from the second hypothesis.

Results, later passes (Nov 2–3). Confidence intervals are out of the prose; Results says they are in the tables and figures, and every interval appears in Table 2, a figure, or the appendix table. Table 2 has a p column (two-sided t-tests on per-seed differences, computed in figures/make-phases-data.py) and an HRL-minus-NF row (−48 [−68, −29], p = .004), which backs the abstract's "significantly more". Statistics says an interval excluding zero corresponds to p < .05. Cohen's d is not reported (meaningless at the seed level; raw units are interpretable; d is also the dose). The two trapping checks (low-precision control, policy trained in the changing world) are one signposted paragraph. The intervention variations get a lead-in sentence. The one-seed median sentence is cut; medians for all seeds are in the appendix table. The intensity paragraph recalls what dose and boost mean and separates the two findings: for dose more was better, for boost a middle value was best. The NF paragraph leads with the verdict, then notes NF agents escaped trapping even more often, then explains the gap by overshoot; NF agents also harvested somewhat more from the new patches (untested). The Figure 5 caption notes that CDR agents reach the new patches sooner and that harvests are equal afterward.

Measures and statistics (Nov 2). The section is renamed from "Endpoints and statistics". It explains why MAE is the main measure and what the other three add. Table 1 rows each give range and direction. "Deficit" replaces "hunger" outside the satiation passage. The statistics paragraph says there are eight policies, one per training seed, and explains pairing and why the policy is the unit.

Appendix table (Nov 2–3). Renamed section "Additional results and robustness checks". Added rows for the low-precision effect on trapping, half doses, boost 10 minus boost 3, medians, and the policy trained in the changing world (trapped 0.02, MAE 12.5, effect −0.7). Row labels wrap; tidy later.

Appendix readability (Nov 3). The appendix opens by saying what it holds and that anything else is in the code repository. Each table has a lead-in paragraph with a worked example, and tables are placed right after their text. The settings tables have one setting per row (no slash-packed rows), grouped under the Methods section that explains them, with current names (pellet value, low-precision control). The evaluation settings moved to the policy and training table. The additional-results table is in five labeled blocks that follow the Results, with phases named rather than numbered; the levers caption now says "recanalization phase" instead of "phase-3".

Later the same day: italic group headings in the appendix tables are kept but short, with no section references; captions carry the explanation and the section pointers. The additional-results section is renamed "Mechanism checks and sensitivity analysis". Its table has three blocks: the main setting (CCC baseline and medians), mechanism checks (low-precision control, policy trained in the changing world), and a sensitivity analysis (dose and boost, and MAE during the intervention). The caption says how to read signs and intervals. The fraction-trapped difference at the main setting was dropped from this table, since it is in Table 2.

Intro. "Canalization is represented by that confidence" is now "In this model, canalization corresponds to the precision of the agent's expectations in its cognitive map".

### Discussion and conclusions, quick fixes (Nov 3)

Low-precision agents are now "trapped less often", not "rarely trapped" (about 46% still were). The intensity paragraph no longer says intermediate decanalization was best (dose: more was better; boost: a middle value was best). Two sentences resting on unreported runs are cut: the heuristic agent in the Discussion and the development runs without new resources in Limitations. "NF results are best read through trapping" is cut. The Conclusions now say decanalization frees the agent sooner, not that it restores regulation. Tolman (1948) is now cited in the intro.

The Conclusions return to my Oct 27 structure and wording (aim, result with a measured clinical sentence, modeling caveat), updated for the timing result and the HRL–NF difference. "Although the model was simple, the implementation was not" is cut, since the code is now plain Python.

### Discussion plan (agreed Nov 3, expansion deferred)

Keep the current text as the skeleton for the part tied to the hypotheses. Bring back my Oct 27 voice and the clinical and big-picture material, rewritten for the new model. Restore my Oct 27 Future Directions almost whole, merged with your new items. From the Oct 27 Limitations, keep suboptimality, single setpoint, allostasis, and reintegration; drop the Unreal-specific points. The Discussion should link to the hypotheses, cover clinical and therapeutic implications and the big picture, and answer both reviewers.

Perceptual field as a theme. The agent's narrow field of view plus a map of expected values beyond it is close to your realized vs. unrealized objects (dissertation ch. 4) and to Yoshimi and Vinson's (2015) point that expectation reshapes the theme, thematic field, and margin. Places: the intro's cognitive maps paragraph (Gurwitsch 1964 and Yoshimi and Vinson as a second lineage beside Tolman, with your dissertation extending the field by learning and physiological state); the Discussion (canalization as a field organized around one theme, relaxed precision letting marginal options back in, and the clinical point that a hypercanalized person experiences the same scene differently); and Limitations or Future Directions (h does not shape perceived value in our model). Revised Nov 3: no references to your account by name, and nothing in Limitations. The intro has one brief sentence on the field, and the Discussion has one paragraph on how cognitive maps show up immediately in the field, in what is salient. Both cite Gurwitsch (1964), Yoshimi and Vinson (2015), and your dissertation. Revised Nov 4: the intro's cognitive map paragraph is cut (see below), so the field appears only in the Discussion.

### Discussion expansion (Nov 4)

Introduction. The cognitive map paragraph is cut. Its history (place cells, grid cells, Behrens) did no work later, and our map is too minimal to lean on it. Its point that map confidence acts as the precise prior is now one sentence in the Juliani paragraph. Later Nov 4: the field paragraph became three. One on cognitive maps (Tolman's maze and shortcut work, place and grid cells, Behrens, Tolman's strip maps applied to people), with O'Keefe and Hafting restored to the bibliography. One on 4E (part of h is set by the world; worn paths and depleted patches as niche construction; the clinical point moved here from Limitations). One on phenomenology (Gurwitsch, Yoshimi and Vinson, your dissertation, and my 2016 book).

Discussion order: summary; timing; HRL vs. NF (moved up to follow the first hypothesis, as in Results); mechanism; active inference; intensity; why simulate; perceptual field; psychopathology; pivotal mental states. Existing paragraphs keep their wording.

New material. The mechanism paragraph adds the REBUS caveat (high-level priors vs. our low-level beliefs) and ALBUS. A short active inference paragraph cites Pezzulo, Rigoli and Friston (2015) (details confirmed) and Safron and Sheikhbahaee, and ends lightly: the agent is built with standard RL and not formulated in active inference terms; the framework is a companion, not our focus. (An earlier draft listed what the agent lacks, no generative model, no expected free energy, no epistemic drive; cut as too strong, since at some level of description many agents minimize EFE.) A why-simulate paragraph was drafted and then cut (Nov 4); the response letter will make that case instead. The field paragraph adds Tolman's strip maps and one clause citing my Husserlian Phenomenology (2016): as a person develops a sense of their environment, it changes how they see things. Two paragraphs answer Reviewer 2: one on the p-factor (Safron and DeYoung; canalization as a problem only when it no longer fits the world), one on Brouwer's pivotal mental states and the Hero's Journey preprint.

Limitations adds the coarse option set, the minimal map, the intervention acting only on beliefs (the 4E point, rewritten), shortened suboptimality (Mnih, Badia, Hoffmann), multiple setpoints and allostasis, and reintegration (Bathje). Future Directions is my Oct 27 text merged with your items, plus one line on an active inference agent, followed by the Oct 27 dosing paragraph. Conclusions unchanged; some overlap with the end of Limitations is fine.

Not done: the Methods sentence on active inference, and the 4E "two loci" passage in Methods.

### Figures (Nov 3)

Figure 1 (overview): the gray bar of world events under the phase headers is gone; its content is in the caption. Panel text is cut to short labels ("Canals deepen"; CDR "Beliefs flatten, choices vary"; CCC "Canals remain"; "New canals form"; "Old canals persist; new patches found late"). "No intervention" no longer appears in the phase-3 panel, "Temperature increases" and "agent thrives" are gone. The caption is shorter and follows the three phases.

Figures 1 and 2 now label every panel with its condition in the same style (bold colored name just above the panel; "CDR / CCC" over the shared phase-1 panel). Figure 1's CDR recanalization panel says "New canals form; deficit shrinks" (mean h −61 in phase 2, −47 in phase 3). Figure 2's phase-1 panel said "138 new" harvests; it now says "familiar".

Condition labels in Figures 1 and 2 keep their colors; in Figure 1 they are indented to line up with the panel text. Figure 1's recanalization panels contrast "New patches found early; new canals form; smaller deficit" (CDR) with "New patches found late; old canals persist; larger deficit" (CCC). "More often" is not used: in the recanalization phase both conditions harvest the new patches about equally (26.5 vs 26.1); the lasting difference is the deficit (mean h −47 vs −132).

Figure 2 keeps the same trial (HRL, evaluation seed 5000). The CDR agent is typical (recanalization mean |h| 16.4; the CDR median is 17). The CCC agent is milder than typical (31.9; median 72), so the example understates the effect. Its h still reaches about −100 in recanalization. The caption is rewritten to match the trial: it explains the circles, fertility shading, dashed outlines, and per-panel stats, notes that the CCC agent briefly harvests a new patch during the intervention and returns to familiar ones, and replaces "bottoms out" with "falls to about −100".

### Two hypotheses instead of four (Nov 3, Jeff's proposal; Joshua please review)

Jeff committed just before this change (4825e0c), so it can be reverted cleanly if you disagree.

What changed. The paper now tests two hypotheses: (1) temporary decanalization improves regulation after the intervention, and (2) HRL agents benefit more than NF agents. Former H1 (canalization formed in a stable world becomes maladaptive in the changing world) is now a check reported first in Results, with the low-precision control and the changing-world policy explaining why agents get trapped. Former H3 (intermediate intensity works best) and the component analysis are now an exploratory question, reported last in Results without a prediction.

Why. Former H1 is largely built into the design (training in a stable world, testing in a changing one), so presenting it as a hypothesis invites "of course". Former H3 held only in part (more dose was better; a middle boost was best), and nothing was preregistered, so a half-supported hypothesis drew attention to the miss; as an exploratory question the same results read as findings. Two clear hypotheses that both held also answer Reviewer 1's request for a stronger hypothesis. Both were tested in the original submission, so the framing is continuous with it.

Where. Introduction (hypotheses paragraph); Results (opening sentence, the first paragraph now opens as a check, the HRL vs. NF paragraph moved up to follow the first hypothesis, the components and intensity paragraphs come last and are labeled exploratory, "held only in part" removed); Discussion (the intensity paragraph opens "In the exploratory analysis of intensity"); abstract ("Decanalization freed trapped agents and restored regulation" is now "helped trapped agents find the new resources sooner and regulate better", to match the timing result); response letter (Reviewer 1 items on hypotheses, the intervention's arbitrariness, and a stronger hypothesis). Figure 6 (components) is redone as an exploratory figure (Nov 3): HRL only, so no HRL/NF legend; one gray bar per version, labeled in full ("Precision relaxation only", "Entropy boost only, b = 1", "Both components, b = 1", and so on); bars show the reduction in MAE (CCC minus CDR) so that longer bars mean more benefit, with values printed; no title; sans-serif fonts as in the other figures. The caption defines the two components in plain words. The NF component values moved to Appendix Table 5 (three new rows in the sensitivity block, with HRL alongside). levers.dat is unchanged; the old levers.tex is in git history. Figure 6 redone again (Nov 3, later): vertical bars of MAE itself, one per version, with no intervention (CCC, blue) first and a dashed line at its height, so the benefit of each version is how far its bar falls below the line; values printed; no error bars, because seeds differ in overall level and the paired differences are much more precise (their intervals are in Appendix Table 5). The bars are computed in levers.tex from levers.dat plus CCC = 136.06. Vocabulary: the second component is now the "temperature boost" everywhere (was "entropy boost"; same thing, since raising the sampling temperature T raises the entropy of choices). The Results paragraph now gives MAE values (136, 77, 125, 75, 53, 38) and states the additivity comparison in points of reduction, so no negative numbers. The Figure 6 caption reminds readers what each component does (P_c times 1 − d; T from 1 to 1 + bd), and the Discussion's REBUS sentence glosses precision relaxation. "Entropy" remains only for the entropic-brain references and the PPO entropy weight. Later: the caption no longer restates the formulas (the Results paragraph has the reminder); it says "at full dose" once, since d = 1 for every bar, and the main intervention is drawn as the darker bar instead of being named. Possible addition: a "Both, b = 10" bar (three seeds) to show that more is not always better.

Small figure fixes (Nov 3): Figure 1's strip drops the separate h label (now "setpoint (h)"), and the CCC dotted arrow starts at the ball. Figure 2's legend has an entry for the dashed outlines (new patch, before it appears), so the caption no longer explains them. Figure 3's caption drops "Columns are schematic". Figure 4's caption opens "in a sample trial" and drops its last sentence.

### Readability of Methods equations (Nov 3)

Reward: D is defined once (Equation 4, so D = |h|), as in Keramati and Gutkin. HRL's reward is r^HRL = 0.2(D_{t−1} − D_t). NF is a separate reward function, not a one-sided drive: r^NF = 0.2(δ_{t−1} − δ_t), with deficit δ = max(−h, 0). The 25, κ, and γ are gone from Methods; the appendix notes that the code writes the same rewards as 5 times |h|/25 or max(−h, 0)/25. This answers the question below about the 25 for the paper, though we'd still like to know if it had a reason.

Belief update (Equation 3): fading is now part of the equation (P_c ← P_c e^{−Δt/τ}, τ = 200 s), P_s is renamed P_o, and the text says why precisions add (each observation is further evidence, as in Bayesian updating). Precision sources are all given per second.

Figure 6 labels: each bar now shows, in small gray text below its name, the precision factor and temperature it uses (e.g., Both components: P_c × 0, T = 2). This works for every bar, including the temperature-only bars, which d and b alone cannot describe (they need prec_lever = 0). The Results paragraph refers to temperatures of 2 and 4 rather than b = 1 and 3.

Exploratory Results paragraphs (components, intensity): now qualitative, pointing to Figure 6 and Appendix Table 5 for numbers. The dose explanation there is cut, since the protocol now covers it.

Policy: options are now explained (a fixed behavior that runs once chosen; Sutton, Precup and Singh, 1999, added to the bibliography), along with how the choice is made (a probability for each option every 0.5 s, one sampled) and what is learned (which option when; where to go comes from the map and steering rules).

Cognitive map: now "a simple cognitive map" in the intro and Methods. Methods says the agent always knows its position, the map stores what it believes is at each location, and the layout need not be learned in an open field.

Possible Limitations items (not yet in the paper): the policy's choice is coarse, one of four hand-coded options every half second, with all steering fixed; and the map is minimal, since position and geometry are given and only contents are learned, so it lacks the learned spatial or relational structure of cognitive maps in Tolman's or Behrens's sense.

Dose and boost: the protocol now states the main setting concretely first (every precision set to zero, temperature doubled), then what that does, then the general form with d and b.

### Measures and results tables (done Nov 1)

Total reward is not an outcome measure. Under drive reduction it sums to 0.2 times the change in |h| between the start and end of a phase.

A plain-language measures table (Table 1) is in the Statistics section: mean absolute h, trapped, mean h, new-patch harvests.

A simple CCC vs. CDR table (Table 2) for the main setting (d = 1, boost 1) replaces the old main table, which moved to a new appendix section, "Additional results" (precision cost, boosts 3 and 10, phase-2 values).

The two-panel performance figure is replaced by a six-panel figure (figures/phases.tex): rows HRL and NF; columns mean absolute h, trapped, and new-patch harvests, across the three phases. Data come from a rerun of the main CCC/CDR evaluation (figures/eval-phases.py, run against the code repo), collapsed to per-seed means (figures/phases-inputs.json) and turned into figure data by figures/make-phases-data.py. The rerun reproduces the published per-seed numbers exactly. eval-phases.py should eventually move into the code repo. The old performance figure files are now unused.

### Abstract and introduction (done Nov 1, Jeff to review in a second pass)

The abstract is your text with cuts only: no numbers, and the seeds parenthetical, the "both contributed" sentence, and the closing clause removed. Typos fixed.

The abstract was then reworked: the world change and decanalization are separate steps, framed as a test of decanalization plus recanalization against continued canalization, with no physiology clause, no dose sentence, and no closing sentence.

Canalization is internal, as originally intended. The niche construction and 4E paragraph is removed, along with its now-uncited references (Barandiaran, Newen). Path wear belongs in Methods only: the World section now has a short niche-construction motivation for traversal cost (snail mucus trails, leafcutter ant trails, Laland on niche construction), adapted from my Oct 27 intro text, with those three references restored.

The 4E claims no longer hold as written. The intervention changes only beliefs and choice randomness; traversal costs and patches are untouched. The old "two loci" passage and the claim that decanalization flattens the external landscape are gone and should stay out. One point survives in reversed form: worn paths persist through a purely internal intervention, which matches the clinical worry that internal change can leave external grooves intact. Whether worn paths actually hold agents in place is untested (see Questions). In the response letter, Reviewer 1's request to justify traversal costs as a source of canalization can be answered by noting that canalization no longer depends on them.

In its place is a short cognitive maps paragraph in the rat lineage: Tolman's maze work, place cells and grid cells, Behrens's extension to abstract domains, and Tolman's broad vs. narrow "strip" maps as an early version of the canalization idea. It ends by tying the agent's confidence in its map to the precise priors of the canalization account. The Tolman paraphrase should be checked against the 1948 paper.

The Juliani mapping paragraph is updated for the new model: the policy weights are the fixed synaptic landscape, the map's beliefs and precision play the role of neural activity, and decanalization acts on beliefs and choice variability, not on weights or metaplasticity.

### Number check (Nov 1)

The paper's numbers were checked against the evaluation outputs in the code repository (pooled_seeds.json, levers_learned.json, eval_policies*.json, and the figure data). Everything matches except one interval: for the policy trained in the changing world, the paper gives a decanalization effect of −0.7 [−1.9, 0.8]. The data give −0.7 [−1.8, 0.6] at boost 3, or −0.4 [−1.6, 0.8] at boost 1, so the reported interval mixes the two. The text should also say which boost it is. Separately, the boost 3 vs 10 comparison in Results ("reduced the benefit by 18 points") rests on three training seeds, which the table footnote notes but the text does not.

## Pending discussion

What the per-phase rerun shows, which bears on the Results and Discussion narrative. Many HRL agents are already trapped during canalization (62% in phase 1, before the new patches appear), because the familiar patches degrade from the start. After the intervention, undisturbed agents harvest the new patches as often as decanalized ones (26 vs. 26 in phase 3). Decanalized agents get there sooner (8 vs. 2 during the intervention), while undisturbed agents sink deep into deficit during phase 2 (mean h −121 vs. −61) and do not climb back during phase 3. So the phase-3 gap is mostly about timing and the deficit carried over, not undisturbed agents never escaping. Text like "helplessly continue to pursue them" and the overview caption ("unable to escape") overstates this. Decanalized NF agents overshoot heavily (mean h +112 in phase 3).

For the Discussion: the benefit of decanalization is about timing, not access. CCC agents reach the new patches eventually and harvest them as often as CDR agents afterward, but only after falling deep into deficit. Frame the clinical point accordingly (helping people adapt sooner, before damage accumulates). The intermediate-intensity hypothesis held only in part (dose: more was better; boost: a middle value was best).

Done Nov 4. The Discussion needs real work: restore the Reviewer 2 material, Future Directions and the dosing debate, and add the active inference paragraph and an answer to "why simulate at all?" (results that were not obvious in advance: NF agents escape but barely improve, the levers interact, and stronger is not better).

Done Nov 4. A sentence in the Discussion acknowledging that REBUS concerns high-level priors, while ours are low-level beliefs about where food is.

Done Nov 4 except the Methods sentence. Active inference, lightly, not as a reframing. In Methods, one sentence where the levers are introduced: both are reductions in precision, of beliefs and of policy selection (sampling temperature is inverse policy precision). In the Discussion, one paragraph making the correspondence explicit: REBUS, setpoints as prior preferences, Pezzulo, Rigoli and Friston (2015) on active inference and homeostatic regulation, and the Safron work already cited. It should say plainly that the agent is an RL agent, not an active inference agent: no generative model of transitions, no expected free energy, no epistemic drive. In Future Directions, one line on running the same experiment with an active inference agent. Confirm the Pezzulo et al. details before adding it to the bibliography.

Levers and dose: decide how much stays in the main paper (see discussion Nov 1).

Done Nov 4. Future Directions: merge my Oct 27 text (long-term Goldilocks schedule, robustness to new adversity, the dosing debate) with your new items (learning during and after the intervention, critical-period plasticity, post-intervention context, multiple variables).

The hypercanalization paragraph from my Oct 27 pass, adapted to the new section 4.1 with new numbers.

Discussion side done Nov 4 (in Limitations). The 4E passages ("two loci" in Methods, the clinical point in Discussion). These need rethinking, since the intervention now acts only on internal beliefs while worn paths and depleted patches stay intact.

Done Nov 4. A shortened version of the suboptimality paragraph for Limitations, which would also give the Mnih, Badia, and Hoffmann citations a home.

The point that NF agents can also anticipate, since both are trained with discounted RL, so the contrast is between reward functions rather than anticipatory vs. reactive agents.

Orphaned bibliography entries that are no longer cited (Hayes, Paul, Szigeti, Tang, Brouwer, Mnih, Badia, Hoffmann, Lyon, Pio-Lopez). Most should get cited again once the sections above return; remove the rest. Nov 4: still uncited are Barak, Moreno, Pio-Lopez, and Raison.

Small fixes: in the abstract, a stray ")" after "training seeds", "randomless", and "when in what situations"; "acted on here canalization is stored" should be "where"; "behaviour"; and "70% of HRL agents" should be trials.

Phase figure (done Nov 2): mean h added as a fourth column, so it shows all four measures, including the NF overshoot. Now eight panels.

The paper should make clear that h is not only food: passive and traversal losses lower it too, and the food-satiation reading is one interpretation. Come back to this.

Small open choice: standardize "tile" vs. "cell" (same grid squares).

Resolved Nov 3 (see Figures, Nov 3, below in this section's later entry). Originally pinned: The averages tell a simpler story than Figure 2. HRL agents are already in deficit during canalization (mean h −55; 62% trapped). The whole CDR–CCC difference arises in the 100 s intervention: CDR agents eat more (55 vs 39 pellets, 8 vs 2 from new patches) and hold mean h at −61, while CCC agents sink to −121. In recanalization the two groups behave almost identically (total harvests 128 vs 131, new-patch harvests 26 vs 26), each eating about as fast as it loses, so the gap carries forward (−132 vs −47). The benefit is a head start that is never erased. Figure 2's trial follows a different route: the agent regulates well in canalization (mean |h| 13.6 vs 59 on average), both agents are fine during the intervention, and the difference appears only in recanalization because the CCC agent never adopts the new patches (0 vs 26 on average). Options: pick a representative trial (in deficit at 300 s, CDR eats more and reaches new patches during the intervention, gap carries forward), and revise Figure 1's recanalization panels, whose "new canals form" vs "old canals persist" contrast is not supported by the averages; only the deficit differs.

Discussion item (Nov 3): the clinical reading of the timing result. Many people recover without intervention; it just takes them longer, and the cost is the time spent far from the setpoint. Decanalization shortens that time rather than making recovery possible.

Trajectory figure (Nov 3). The fall of h during canalization is typical, not a quirk of the example: across trials, mean h in phase 1 is −55 and about two thirds of trials hit −100. The policy is well trained; in the stable world it was trained in, the selected HRL checkpoints keep mean |h| at 9.1–9.6 on held-out trials (selection_HRL_stable*.json in the code repo). The fall comes from the familiar patches degrading underneath a policy trained where they never degrade. This also restores support for the claim, cut on Nov 2, that the policies regulate well in the stable world.

Figures and text, Nov 3 (later). Figure 2 and the trajectory figure now show evaluation seed 5020, the trial closest to the averages (per-phase mean h and new-patch harvests in both conditions). figures/make-movement-data.py fixes that seed and now also writes trajectory.dat, so both figures always show the same trial; the code repo's make_figure_data.py still picks the old trial by the earlier rule (first CCC-trapped, CDR-not-trapped trial), so that should be aligned or retired. The trajectory axis goes to −190, and the 300 s line is labeled "new patches appear". Figure 1 has a training box before phase 1 and a schematic h strip below the panels (CDR returns toward the setpoint during the intervention; CCC stays low and is only partway back by 700 s, matching the average), with the gap shaded. Its panel text is "Beliefs flatten, choices vary; new patches found", "Canals form at new patches", and "New patches found late". Captions for Figures 1, 2 and the trajectory figure are rewritten; the trajectory caption explains the phase-1 fall (patches degrade from the start; the same policy keeps mean |h| near 9 in the stable world). Methods no longer calls 300 s "the world changes"; degradation is said to run from the start. Results restores the stable-world claim with numbers (HRL mean |h| near 9; NF deficit near zero with large surpluses, MAE 68–249). The Discussion has a timing paragraph with the clinical reading (people recover without intervention, just later), and Limitations notes that the benefit depends on the length of the recanalization phase.

Figure 3 (protocol), Nov 3: the gray bars are gone (before evaluation, world, compare, throughout), as are the WORLD and AGENT labels. Boxes keep only key parameters ($P_c$ grows, $P_c\leftarrow(1-d)P_c$, $T=1+bd$, $d=0$, $T=1$). The first box is titled "CDR / CCC: beliefs form" to match the brief labels in phases 2 and 3, and the phase-2 header is "Intervention", as in the other figures. The caption carries training, the changing world, the settings tested, and what is compared.

Later Nov 3: Figure 3's familiar-route sketch and the bold "beliefs form" are gone; all boxes are smaller, with the shared box centred between the branches. Figure 1's training column is removed (the caption still says policies are trained in a stable world); the CCC recanalization panel says "New patches eventually found" with a dotted arrow toward the new well. The trajectory figure no longer labels the 300 s line.

Open: whether to mark the 300 s event with a labeled dashed line across figures, and what to call it. The paper has no term for it ("changing world" names the world). Degradation runs from 0 s and is gradual; at 300 s the new patches appear and the intervention starts; at 400 s the intervention ends.

Long run without new patches (Nov 3, exploratory, not in the paper). All four stable-trained HRL policies, 64 trials each, CCC, degrading world with no new patches, run to 1,200 s. Mean h falls steadily with no floor: −17 in the first 100 s, −94 by 200–300 s, −232 by 600–700 s, −367 by 1,100–1,200 s. Outcomes split. About two thirds of trials hit −100 and keep sinking (the fraction plateaus at 0.68 from about 400 s; the worst trial reaches −1,828). About one third find a sustainable loop and hold (upper quartile of mean h over the last 300 s is −25; the best is +4). For reference, the seed-0 policy in the stable world stays near the setpoint for the whole 1,200 s (mean |h| about 11). So for most agents the familiar patches fail outright, and the new patches are a rescue, not an upgrade. h has no lower bound in the model (no death), so trapped agents fall without limit. Scripts are in the code repo at model/long-run-no-new-patches.py and model/example-trial-scan.py (the scan behind seed 5020), with output in results/development/. Over the last 300 s: 40% of trials average below −300, 21% between −300 and −100, 8% between −100 and −50, and 31% above −50; 44% are still falling steeply. Added to the paper (Nov 3): one sentence in Results (first hypothesis), one clause in the trajectory caption, and one sentence in Measures and statistics on h having no lower bound, pointing to the medians.

## Questions

Does your local copy of `adaptiveBehaviorRevisions.txt` have edits after Oct 27? If so, please merge them into the version in `responses/`.

Does path wear contribute to trapping in the new model? I didn't find an ablation in the code repo. This matters for how much the intro leans on niche construction.

The first learned policies were trained in the changing world and gained nothing from decanalization, and the main study then switched to training in the stable world. That reads as a decision made after seeing data, but it isn't in the supplement's list. I've disclosed it in the response letter's opening, along with the principled reason. Please check that the account is accurate.

Why is drive scaled by 25 (D = |h|/25)? Since scaling rewards by a positive constant doesn't change the best policy, the 25 and κ = 5 matter only together, as 0.2 per unit of h. Was 25 chosen for a reason, such as a typical deviation size or training stability? If not, the paper could write the reward directly as r = 0.2(|h_{t−1}| − |h_t|), say it is drive reduction with D = |h|, and note that 0.2 is a scale chosen for training. That would drop the 5/25 step readers have to work through.

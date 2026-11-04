# Response to reviewers

Draft started Nov 1. Reviewer comments are quoted; responses marked TODO are not yet written. The previous version, written for the Unreal model, is in `adaptiveBehaviorRevisions_old.txt`.

## Overview of changes

We thank both reviewers for their careful and constructive comments. The revision is substantial, and we describe the main changes before responding point by point.

In addressing Reviewer 1's questions about the action space, timing, and reward function, we audited the original Unreal Engine implementation. The audit found errors in how the agent's anticipated gains and losses were computed, and after correcting them the original benefit of decanalization was no longer reliable. More fundamentally, route analyses showed that the original agents never formed canals. Their routes overlapped across phases about as much as routes from unrelated trials, and manipulating the tile history had almost no effect on behavior. With no entrenched pattern to disrupt, that version could not test decanalization.

We therefore rebuilt the study. Three changes are central.

First, the simulation is now a two-dimensional world written in pure Python, replacing the Unreal Engine sandbox. It runs headless on an ordinary computer, and every table and figure in the paper can be regenerated from the public repository. This made it practical to train several independent policies per reward function and to vary the intervention systematically.

Second, canalization is now located in learning, as Reviewer 1 recommended. The agent builds a cognitive map of where food is and becomes increasingly confident in it. Decanalization temporarily lowers that confidence and increases the randomness of the agent's choices, following the REBUS account and the distinction in Deep CANALs between rigid inference and reduced behavioral variability. Traversal costs remain in the world but no longer carry the account of canalization, and both reward functions now use Keramati and Gutkin's drive-reduction form directly.

Third, the question the model asks has changed. Agents are trained in a stable world and then tested in one that changes in ways their training did not prepare them for: familiar resources degrade and better ones appear elsewhere. This is where canalization becomes hypercanalization, as habits that served well persist after the conditions that justified them are gone, and it is a situation people commonly face. Comparing decanalization followed by recanalization with continued canalization now tests whether loosening confident beliefs helps an agent adapt to a changed world.

One design decision was made after seeing data. The first learned policies were trained in the same changing world used for evaluation. They learned to cope with the change, were almost never trapped, and gained nothing from decanalization. Because hypercanalization concerns persistence after changes a habit did not anticipate, we then trained in a stable world and evaluated in the changing one. The paper reports the changing-world result as a boundary condition.

Because of these changes, some of the original comments no longer apply. We note where this is the case below and explain how the underlying concern has been addressed.

## Reviewer 1

> My biggest issue with the paper as it currently exists is that the choice of reward function is not well justified within the paper itself. [...] My recommendation would be to focus on canalization that is connected to the intrinsic dynamics of learning itself. If, however, the focus remains on the design of the reward function, then that choice should be thoroughly justified and defended within the paper. It may also be valuable to design a non-canalization-inducing reward function which can be compared against the canalizing one.

We took this recommendation. Canalization now arises from learning: the agent's confidence in its cognitive map grows with experience and resists revision. The reward functions are standard drive reduction and play no role in producing canalization. Traversal costs remain as a feature of the world but are not part of the account. The "healthy" comparison the reviewer suggests is provided by agents with low-precision beliefs, which track what they currently perceive and are trapped much less often (Results, first subsection).

> Page 3 (Footnote): Deep CANALs is the Juliani et al. (2024) model, while CANAL is the Carhart-Harris et al. (2023) model.

Corrected. The distinction is now made in the main text.

> Page 4: It would be helpful if the Introduction ended with a discussion of the hypothesis being tested in the paper and an allusion to what the findings of the paper are.

The Introduction now ends with two explicit hypotheses: that a temporary decanalization improves the agent's regulation after the intervention, and that an HRL agent benefits more than an NF agent. It also says that we first check that canalization becomes maladaptive, and that the effect of each component and of intensity is explored without a prediction. TODO: the reviewer also asked for an allusion to the findings; the Introduction does not yet preview them.

> Page 4: Why was a 3D environment chosen?

No longer applies. The simulation is now a two-dimensional world in Python.

> Page 5: The PPO algorithm should be properly cited here.

Done.

> Page 5: There is no description of the architecture of the model itself. [...] Please include these details, as well as what parameter choices were used for training.

The policy is a two-layer network with 64 units per layer and separate policy and value outputs, described in Methods; training settings are in the Appendix. TODO: verify the Appendix is complete for the new model.

> Page 7: I am not clear on the action space available to the agent.

No longer applies in this form. Every 0.5 s the policy chooses one of four options (seek remembered food, explore unseen territory, follow the most worn direction, or avoid visible food), each carried out by fixed steering rules (Methods).

> Page 10: It is claimed that it is a normal practice to provide "disproportionally more reward the closer it gets to the target."

The claim has been removed. Both reward functions now reward drive reduction as defined by Keramati and Gutkin (2014).

> Page 10: It is claimed that positive reinforcement is more effective than negative reinforcement.

The claim has been removed.

> Page 11: The choice of the Negative Feedback agent as a baseline should be better justified.

TODO.

> Page 12: It is not clear what "60 seconds" means in this context.

No longer applies. All durations are in simulated seconds, with a fixed tick of 0.05 s.

> Page 12: As currently described, the decanalization intervention feels somewhat arbitrary. [...] It would be valuable to see how adjusting this parameter influences the results of the simulations.

The intervention is no longer a single setting. In an exploratory analysis, we vary its intensity and test each of its two components alone. Each helps on its own, they help most together, and very strong disruption helps less than moderate disruption (Results; all settings in the appendix sensitivity analysis).

> Page 15: The tables are somewhat difficult to interpret. [...] Furthermore, it would be valuable to demonstrate more clearly what kind of policies are learned by agents within the first condition.

TODO: plain-language measures table and simple CDR vs. CCC table. The behavior of undisturbed agents is now shown directly: most become trapped, returning to failing resources (Results, and the movement and trajectory figures).

> Page 16: The authors find differences in the performance of the control conditions which they describe as a "false positive."

No longer applies. Paired trials share the world layout, starting state, and random streams, so the two conditions are identical until the intervention begins.

> Page 19: Having a stronger hypothesis being tested would help make the summary section more clear.

The paper now tests two hypotheses, stated at the end of the Introduction and taken up in turn in the Results and at the start of the Discussion: decanalization improves later regulation, and an HRL agent benefits more than an NF agent. Both held. The other analyses are presented as checks (why agents become trapped) or as exploratory (components and intensity), not as hypotheses.

> A related question is: "why did this need to be simulated at all?"

TODO. Several results were not obvious in advance: NF agents escape their failing patches but barely improve; the two components of the intervention interact; and stronger disruption is not better.

> Page 19: The authors provide "niche-construction" as a motivation for the reward function in the discussion.

No longer applies. Canalization no longer depends on traversal costs or niche construction.

> Page 20: The authors state that the HRL agent did not achieve an optimal policy given the environment.

TODO. A policy trained in the changing world now regulates close to the noise floor, which shows the task can be learned well.

> Page 20: The discussion is a place for engaging with the wider literature [...] It would be valuable to expand it.

TODO.

> Page 28 and 29: These figures are difficult to read. [...] Another suggestion would be to have a single "hero figure".

TODO: describe the new overview, movement, and trajectory figures.

## Reviewer 2

> "Canalization and plasticity in psychopathology" is a highly problematic paper [...] it would be more accurate (even if less satisfying/aggrandizing) to refer to this as the "second principal component" of psychopathology.

TODO. The relevant text was lost in the rewrite and needs to be restored to the paper.

> In discussing altered beliefs under psychedelics, it could be worth mentioning this work which suggests we ought to expect combinations of both directly and indirectly relaxed and strengthened beliefs (ALBUS).

TODO. Restore to the Discussion.

> Another question I had in reading this manuscript was the extent to which these findings could be used to understand the natural/normative functioning of psychedelic-like transformative experiences as described in the excellent work of Ari Brouwer.

TODO. Restore to the Discussion.

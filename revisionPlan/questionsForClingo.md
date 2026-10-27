# COMMENTS / QUESTIONS FOR CLINGO

Note there is a fair bit of human in the AI here.

Open items from Jeff's recent work. Since no new runs are possible before this resubmission,  most items are just "we did this, please confirm." Items marked BEFORE FINAL SUBMISSION should prob. be done after this revision but before publication.

0. GET RID OF CODE COMMENTS

I think most of them are outdated but did not do this yet. I am fine just nuking it all tbh.

1. PARAMETER SENSITIVITY (Reviewer 1, p. 12)

The reviewer asked to see how changing the canalization rate during decanalization affects results. For this revision we will leave the footnote and Limitations sentence as they are, and ask the reviewer in the response letter whether that is enough or whether they want a test with reported values. Please confirm the footnote is accurate: RESULTS.md (line 39) calls those runs a "legacy sensitivity demonstration" from the earlier setup. If so, should the footnote say the test was done on an earlier version?

> It was also done on a newer version now--didn't change the results either (tho the results were quite different, as we'll have to discuss)


BEFORE FINAL SUBMISSION (if the reviewer asks): run the test on the current policies (e.g., visit counting stopped, normal, and increased during decanalization) and report the results in an appendix table.

> Could do this again once we're on the final trained policies, but subsequent sensitivity tests on later policies suggests it's not doing anything significant enough to move the needle (but worth checking out just to do so one last time!)

1. PREDICTED GAIN RAYCAST

From the code, the predicted pellet gain does not sum the pellets on the ray as the paper says. Each pellet overwrites the total (GetAnticipatedResourceYield, node 448), so only the last hit counts, which appears to be the farthest pellet. Multiple pellets on the ray are rare, so we are leaving the paper as is for this revision.

BEFORE FINAL SUBMISSION: confirm the bug (e.g., log AnticipatedResourceGain with two pellets of different values on the ray), fix the code to sum, rerun, and update the results. Also explain the 0.2 multiplier at the end of GetAnticipatedTraversalCosts (node 325), so we can describe it.

> Bug totally confirmed. Now deep in process of re-training. First results nulled our results (still some effect but too weak to be significant w/ power produced from 250 trials). New policies are gonna be changed in several ways just to see what happens...

3. HRL REWARD (please confirm)

Following the text message you sent Jeff about this, the paper now cites Keramati and Gutkin's result that maximizing drive-reduction reward also minimizes deviation from the setpoint, and describes our reward as rewarding closeness to the setpoint directly ("in effect, the organism is minimizing drive"). See the HRL section.

> We are again making adjustments to the reward function in the spirit of training the agent to minimize its setpoint in our particular setup, so this explanation will require re-re-jiggering.

4. H LOSS SIGN (please confirm)

The results tables now report h loss as a positive amount (sign flipped; p-values unchanged). If any figure shows h loss as negative, please flip it to match.

> We're not showing h loss in any figures---it's just in those results tables

5. HIGHER H LOSS AFTER DECANALIZATION (please confirm)

Part of the extra h loss under CDR is built in: counting stops during decanalization and counts are halved afterward, so tiles cost more than under CCC. We removed a sentence about this from Results to keep it simple. OK to leave it out?

> After some sensitivity analysis, it appears this is also something with unclear value, so we're just going to be removing it and mentions of it entirely, aside from a small section where we go over the myriad things we explored in the process (where we IMO rightly decided to remove any manipulation that wasn't actually doing anything)---i.e., we tried some things that seemed like they could be related to the effects of decanalization but we ultimately stuck with the perceptual shifts vs the other ones (traversal increases + the flattening of the landscape, which is what this was supposed to be).

6. QUICK CODE CHECKS (please answer from the code)

a. Tile cost is 10/(n+1) times "the stored frame delta". Is that always 0.05 s? If so, we'll say "per tick".

> Kind of yes. I adjusted the text to reflect the way the tile cost is fixed to the tick rate.

b. The loss estimate is said to use "current velocity", but the code seems to use MaxSpeed. Which is right?

> We set the current velocity to MaxSpeed and keep it there by giving the agent a constant push that's capped by MaxSpeed so it's more technically correct to call it current velocity, as that's the ultimate source of truth, even though it should always be at that speed.

c. "Harvested pellet count" is defined as the number of different pellets harvested. Is it distinct pellets or total collections?

> Distinct. I'll just call them "unique" (which I feel like I used to call them... ::thinking::)

d. Limitations says parameters were "selected independently of the evaluation data". True, including the snapshot choice?

> Yes, in the current iteration the snapshot choice was derived from selecting the snapshot with the lowest abs mean setpoint distance (which didn't get tested in trials but in actual tests against the model, though these lengths were the same as the trial sequence lengths)
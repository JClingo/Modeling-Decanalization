The installed engine and authored Blueprint graphs expose two training-to-evaluation
differences that need measurement before further tuning.

Training calls the native policy's `RunInference()` without an argument; its
declared action-noise default is 1. The manager's inference graph supplies 0,
which samples the mean action. These are different behaviors of the same saved
network. This is a common design choice, not by itself an implementation error.
The staged audit compares both modes on identical initial environments without
changing the primary mean-action evaluation protocol.

Training terminates when absolute h exceeds 100. Fixed-horizon evaluation keeps
recording the trajectory beyond that bound. In the completed earlier screen,
the baseline spent about 7.1% of evaluation time beyond the training boundary;
the unsuccessful combined learning proposal spent about 59.7%. That establishes
a distribution mismatch, but does not establish its cause or an effective fix.
Changing the training failure convention is not bundled into the reward/PPO
screens. The absolute-error reward includes its explicit absorbing-failure cost.

The training and evaluation interactor share the 11-float observation schema.
The scalar homeostatic observation uses scale 100. Native agent resets zero
the recurrent state; buffer-only truncation resets the experience segment,
without that full agent/world reset. In the native engineering trials, both
action modes had a zero recurrent-state norm at the first reporting window
and nonzero norms at the next two windows. Continuous CCC retains h and tile
counts between these windows. The inherited phase-start velocity initialization
remains, so this is not a claim of uninterrupted kinematics.

The matched static-cost control preserves traversal counting. Ordinary-contact
costs stay at the first-entry rate regardless of prior traversal count, and
anticipation uses that same fixed rate. Native validation exercises real collision
raycasts, actual tile-contact callbacks and visit increments. The inherited
decanalization branch leaves tile impact at zero; this behavior is preserved.
The static mechanism control is limited to CCC and is not enabled for CDR.

The three authored graph exports and installed-engine source hashes are retained
here. Native checks and code variants remain in the engineering run folders
listed by `../engineering_verified.json`. Failed harness attempts and the failed
partial audit are preserved. The variable-scope correction in the new traversal
logger changes instrumentation only; it does not change model weights or the
scientific protocol. The corrected audit must complete before its comparison
can be interpreted.

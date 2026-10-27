# What changes at recanalization

Let n be a tile's count immediately before the CDR transition out of
decanalization. Each ordinary entry and each decanalized entry still adds one.
At the transition, apply the chosen transformation once:

| Rule | Transformation | n=1 | n=3 | n=7 |
|---|---|---:|---:|---:|
| Reset | 0 | 0 | 0 | 0 |
| Retain quarter, floor | floor(0.25 n) | 0 | 0 | 1 |
| Retain half, floor (current) | floor(0.5 n) | 0 | 1 | 3 |
| Retain three quarters, floor | floor(0.75 n) | 0 | 2 | 5 |
| Keep | n | 1 | 3 | 7 |
| Retain half, exact | 0.5 n | 0.5 | 1.5 | 3.5 |

These are rule calculations, not empirical performance results. In particular,
flooring removes the entire count history of a tile visited once for any of
the three fractional, floored retention rules. Exact halving preserves half
an entry. Because counts are stored as doubles, fractional counts can be used
by the existing cost and anticipation arithmetic without changing their types.

For an illustrative tile with base impact 10, its cost rate on the next entry
is `10 / (T(n) + 2)`: the entry adds one, and the executed cost denominator
adds another one. Thus a tile with n=1 has next-entry rate 5 under current
floored halving, 4 under exact halving, and approximately 3.333 when all history
is retained. Actual starting-tile timing and phase placement must be considered
separately; this example assumes a subsequent fresh entry.

The comparison between exact and floored halving isolates rounding. The
comparison between different retention fractions varies how much history is
preserved. Neither comparison changes weights or online learning. Lower
traversal costs need not improve performance: loss can move an agent above
its setpoint closer to zero, and the policy can change its path in response
to changed costs and observations.

CCC retains its accumulated counts with ordinary counting throughout and does
not undergo the intervention. CDR-versus-CCC results therefore compare the
whole intervention, including perceptual/physical perturbations and history
changes. Comparing alternative CDR rules directly with current half-floor is
necessary to estimate the effect of changing the recanalization operation.

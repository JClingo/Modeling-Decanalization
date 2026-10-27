# What the traversal factor changes

The factor changes a tile's environmental memory of traversal. It does not
change PPO parameters, update policy weights during evaluation, or count time
spent standing on a tile.

For each actual tile-entry event, the stored count changes by:

```text
ordinary canalization: n <- n + 1
decanalization:        n <- n + factor
recanalization:       n <- floor(n / 2)  [once at the transition]
```

The primary factor-1 experiment therefore retains ordinary counting in every
phase. Factor 0 disables new traversal counting during decanalization;
2, 4 and 7 accelerate it. These other factors are sensitivity conditions.
Pre-existing history remains present during the
intervention and is halved at recanalization for every CDR factor.

At the halving operation, a tile that started phase 2 with count n_C and received
N_D entries during phase 2 has:

```text
n_R = floor((n_C + factor * N_D) / 2)
```

An additional ordinary entry after that operation adds another count. This
ordering matters for cost calculations and for interpreting captured phase-start
counts. The prediction repair accounts separately for the already-entered
starting tile and prospective entries into future tiles.

For example, consider a previously unvisited tile crossed once during phase 2.
Its base impact parameter is 10, as in the experiment. On its next ordinary
entry, the count is n_R+1, and the traversal-cost rate is 10/(n_R+2):

| Decanalized factor | Count after that phase-2 entry | Count immediately after halving | Rate on next ordinary entry |
|---|---:|---:|---:|
| 0 | 0 | 0 | 5.000 |
| 1 | 1 | 0 | 5.000 |
| 2 | 2 | 1 | 3.333 |
| 4 | 4 | 2 | 2.500 |
| 7 | 7 | 3 | 2.000 |

These are illustrative calculations from the counting/cost rules, not measured
performance results. Repeated visits and pre-existing counts change the values.
They show why count-halving makes the manipulation nonlinear and why factor 1
can have the same retained count as factor 0 for a newly visited tile.

Higher factors can make paths crossed during the perturbation cheaper later.
That need not improve setpoint regulation: traversal loss can be useful when h
is positive, and a fixed policy can change its actions in response to the altered
landscape. “Increased plasticity” here names a faster update to environmental
history, not a demonstrated neural mechanism or an assumed performance benefit.

The separate native editor audit invokes the real Blueprint overlap and
canalization handlers on transient actors. All 17 checks passed: one/two entries
at each factor, ordinary counting independent of factor, and rounding down at
recanalization. Its asset hash matches the original corrected factor-0 tile asset.
The scored native runs additionally verify the installed factor on every one of
the 2,500 tiles in each saved phase scene.

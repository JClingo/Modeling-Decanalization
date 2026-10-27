# Proposed recanalization sensitivity additions

These are proposals; the manuscript source is not automatically rewritten. The main half-floor condition remains unchanged.

## Methods / supplement

> We assessed sensitivity to the transformation of traversal history at recanalization while retaining one counted visit per tile entry in every phase. We compared resetting counts to zero, retaining one quarter, one half or three quarters with rounding down, retaining all counts, and retaining one half without rounding. Each condition comprised 250 trials under the same selected fixed HRL policy and corrected anticipatory observations. The current half-floor and CCC batches were reused. We compared phase-3 absolute deviation and received reward with CCC using Welch intervals and Holm adjustment across six conditions and two endpoints. A separate ten-test family compared the five alternatives directly with the current transformation. Baseline-change and paired analyses were sensitivity checks.

## Results

> Across the six CDR transformations, post-intervention mean absolute deviation ranged from 13.753 to 14.874, and mean objective reward ranged from 79.964 to 81.052 per 100-second phase. CCC means were 18.475 and 79.349, respectively.
> No transformation established a post-intervention difference from CCC in either endpoint after the twelve-test Holm adjustment. This does not establish equivalence.
> Direct comparisons with the current half-floor rule did not establish a difference in either endpoint after the separate ten-test adjustment.

## Discussion and figure

Replace the existing limitation that count-halving was not explored with a description of this extension and its actual uncertainty. Describe which alternatives differ directly from the current rule, as well as which differ from CCC. Do not infer a difference between two rules merely because one comparison with CCC is significant and another is not. The paper’s current primary rule remains half-floor. This extension does not establish an optimal transformation or generalization across training seeds.

> Post-intervention HRL performance under six transformations of tile traversal counts at recanalization, with 250 trials per condition. Counting remains one per entry throughout. Points show trial means and bars show unadjusted 95% intervals; the dashed line and band show the CCC mean and interval. Absolute-deviation summaries use recorded event/update samples. Reward is the received total per 100-second phase. The separate contrast figure shows CDR-minus-CCC Welch differences and intervals; multiplicity-adjusted tests are reported in the table.

Use `retention_response.pdf`, `ccc_contrasts.pdf` and `post_table_rows.tex`. All nine descriptive outcomes and the full statistical tables remain available in the CSVs.

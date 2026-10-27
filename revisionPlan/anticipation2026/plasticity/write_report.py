"""Write the factor-sweep report only after all native and statistical checks."""
from pathlib import Path
import csv,json
HERE=Path(__file__).resolve().parent
rows=lambda name:list(csv.DictReader((HERE/name).open()))
verification=json.loads((HERE/'verification.json').read_text());assert verification['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
d=rows('phase_summary.csv');p=rows('primary_contrasts.csv');q=rows('factor_pairwise.csv')
r=rows('relative_bootstrap.csv');s=rows('sensitivity.csv');landscape=rows('landscape_counts.csv')
factors=[0,1,2,4,7]
def summary(c,m,phase=3):return next(x for x in d if x['condition']==c and x['metric']==m and int(x['phase'])==phase)
def mean(c,m,phase=3):return float(summary(c,m,phase)['mean'])
def effect(c,reference,m):return next(x for x in p if x['condition']==c and x['reference']==reference and x['metric']==m and x['phase']=='3')
def interval(row,key='difference'):
 return f"{float(row[key]):.3f} [{float(row['ci95_low']):.3f}, {float(row['ci95_high']):.3f}]"
def percent(c,reference,m):
 if c==reference:return '0 (reference)'
 x=next(x for x in r if x['condition']==c and x['reference']==reference and x['metric']==m)
 return f"{float(x['improvement_percent']):+.1f}% [{float(x['ci95_low']):+.1f}, {float(x['ci95_high']):+.1f}]"
mae='homeostatic-mae';reward='reward-total'
best=min(factors,key=lambda f:mean('CDR-'+str(f),mae))
benefit=[int(x['condition'].split('-')[1]) for x in p if x['phase']=='3' and x['reference']=='CCC' and x['metric']==mae and float(x['difference'])<0 and float(x['p_holm'])<.05]
harm=[int(x['condition'].split('-')[1]) for x in p if x['phase']=='3' and x['reference']=='CCC' and x['metric']==mae and float(x['difference'])>0 and float(x['p_holm'])<.05]
text=['# HRL performance across decanalized traversal factors','',
'This experiment changes environmental traversal counting while holding the selected HRL policy and corrected anticipation fixed. It does not retrain the policy. Each condition contains 250 complete trials with three 100-second phases. Factor 0 and CCC reuse the original corrected reference batches; factors 1, 2, 4 and 7 are new native evaluations.','',
'**Current primary designation:** the author confirmed factor 1 as the originally intended condition after this sweep was reported. Use [the factor-1 HRL analysis](../primary-factor1/RESULTS.md) for primary inference; factors 0, 2, 4 and 7 are sensitivity conditions. The numerical families and CSV names below preserve the original sweep analysis, and “primary” within this sweep means its originally specified 16-test comparison family. See [the design clarification](../PRIMARY_DESIGN_CLARIFICATION.md). The original hashed analysis plan remains unchanged.','',
'## Counting rule','',
'The earlier corrected evaluation used factor 0, so traversal count did not increase during decanalization. The intended primary condition now uses factor 1. The Blueprint directly adds the factor on each tile entry. Factor 1 is ordinary counting, and 2/4/7 accelerate counting to two/four/seven visits per entry. Counts still increase by one in ordinary phases. Recanalization halves counts with rounding down. Thus, factor 1 gives one increment per entry throughout, while retaining the once-only count halving. Factor 0 disables counting during the intervention. Neither removes pre-intervention history.','',
'These factors operationalize environmental plasticity: greater retained counts reduce later traversal costs. Policy weights remain frozen. The count-halving step and integer rounding can make the effective manipulation nonlinear. Performance itself need not improve monotonically as crossing becomes cheaper, because loss can help an agent above its setpoint.','',
'## Post-intervention performance','',
'Means are trial-level phase-3 summaries. MAE is sampled from the existing event/update history; reward is the actual HRL callback total for 2,000 decisions.','',
'| Condition | Mean absolute h | HRL reward | Fraction within ±5 | Median MAE |',
'|---|---:|---:|---:|---:|']
for c in [*['CDR-'+str(f) for f in factors],'CCC']:
 text.append(f"| {c} | {mean(c,mae):.3f} | {mean(c,reward):.3f} | {mean(c,'homeostatic-fraction-within-5'):.4f} | {float(summary(c,mae)['median']):.3f} |")
text+=['',f'Factor {best} has the lowest observed mean phase-3 MAE among the five CDR factors. This ranking is descriptive; these data do not establish an optimal factor.', '']
if benefit:text.append('New factors with lower phase-3 MAE than CCC after the primary 16-test Holm adjustment: '+', '.join(map(str,benefit))+'.')
else:text.append('No new factor establishes lower phase-3 MAE than CCC after the primary 16-test Holm adjustment. This is not evidence that all factors are equivalent.')
if harm:text.append('New factors with higher phase-3 MAE than CCC after that adjustment: '+', '.join(map(str,harm))+'.')
text+=['','The observed factor effects are small: factor 1 lowers mean MAE by 2.3% relative to factor 0, while factor 7 raises it by 2.4%; mean reward changes by less than 0.5% across all five factors. All phase-3 Welch comparisons, all-factor pairwise comparisons, baseline-change and paired/matched sensitivity comparisons have intervals spanning zero and Holm p=1.00. The retained landscape nevertheless changes substantially: mean total counts at phase-3 start rise from 78.512 at factor 0 to 2,218.180 at factor 7. The manipulation worked, but no corresponding performance advantage was established. These results do not demonstrate equivalence.']
text+=['','## Relative performance','',
'Positive percentages mean improvement: reduction in mean MAE or increase in mean reward. Percentages compare group means. Brackets are descriptive trial-bootstrap 95% intervals, using independent condition resampling (10,000 resamples, base R seed 261026), not multiplicity-adjusted hypothesis tests.','',
'| Factor | MAE improvement vs factor 0 | Reward improvement vs factor 0 |',
'|---|---:|---:|']
for f in factors:
 c='CDR-'+str(f);text.append(f'| {f} | {percent(c,"CDR-0",mae)} | {percent(c,"CDR-0",reward)} |')
text+=['','| Factor | MAE improvement vs ordinary counting (factor 1) | Reward improvement vs ordinary counting |',
'|---|---:|---:|']
for f in factors:
 c='CDR-'+str(f);text.append(f'| {f} | {percent(c,"CDR-1",mae)} | {percent(c,"CDR-1",reward)} |')
text+=['','## Primary absolute contrasts','',
'Each new factor is compared with factor 0 and CCC. Differences are factor minus reference. Intervals are unadjusted Welch 95% intervals; Holm adjusts 16 phase-3 tests together (four new factors × two references × MAE/reward). See ANALYSIS_PLAN.md for the separate phase-2 and all-factor pairwise families.','',
'| Factor | Reference | MAE difference [95% CI] | MAE Holm p | Reward difference [95% CI] | Reward Holm p |',
'|---|---|---:|---:|---:|---:|']
for f in factors[1:]:
 for ref in ['CDR-0','CCC']:
  a=effect('CDR-'+str(f),ref,mae);b=effect('CDR-'+str(f),ref,reward)
  text.append(f"| {f} | {ref} | {interval(a)} | {float(a['p_holm']):.4g} | {interval(b)} | {float(b['p_holm']):.4g} |")
text+=['','## Acceleration relative to ordinary counting','',
'These are secondary comparisons with factor 1, drawn from the complete ten-pair CDR comparison table. Their Holm family contains 20 tests (ten factor pairs × two outcomes), so adjusted p values can differ from the primary table for duplicated contrasts.','',
'| Factor | MAE difference vs 1 [95% CI] | Holm p | Reward difference vs 1 [95% CI] | Holm p |',
'|---|---:|---:|---:|---:|']
for f in [2,4,7]:
 a=next(x for x in q if int(x['higher_factor'])==f and x['lower_factor']=='1' and x['phase']=='3' and x['metric']==mae)
 b=next(x for x in q if int(x['higher_factor'])==f and x['lower_factor']=='1' and x['phase']=='3' and x['metric']==reward)
 text.append(f"| {f} | {interval(a)} | {float(a['p_holm']):.4g} | {interval(b)} | {float(b['p_holm']):.4g} |")
text+=['','## Phases and persistent landscape changes','',
'| Condition | MAE pre | MAE during | MAE post | Reward pre | Reward during | Reward post |',
'|---|---:|---:|---:|---:|---:|---:|']
for c in [*['CDR-'+str(f) for f in factors],'CCC']:
 values=[mean(c,m,phase) for m in [mae,reward] for phase in [1,2,3]]
 text.append('| '+c+' | '+' | '.join(f'{v:.3f}' for v in values)+' |')
text+=['','Phase boundaries restore the trial’s initial h. These phase means do not describe uninterrupted homeostatic recovery. All CDR conditions retain the same combined perceptual/physical decanalization and count-halving rule; CCC has no intervention.','',
'| Condition | Mean total tile counts at start of phase 2 | Mean total tile counts at start of phase 3 |',
'|---|---:|---:|']
for c in [*['CDR-'+str(f) for f in factors],'CCC']:
 values=[float(next(x['mean'] for x in landscape if x['condition']==c and int(x['phase'])==phase)) for phase in [2,3]]
 text.append(f'| {c} | {values[0]:.3f} | {values[1]:.3f} |')
text+=['','These are totals across the 2,500 tile counts captured at phase start, not counts of distinct tiles. They audit the retained landscape manipulation, not a causal explanation of every performance difference.','',
'## Matching and sensitivity','',
'| Comparison | Identical baseline MAE trials | Matching recorded initial h / RNG / recurrent memory |',
'|---|---:|---|']
for x in verification['baseline_alignment']:
 fields=x['matching_start_fields']
 text.append(f"| {x['condition']} vs {x['reference']} | {x['identical_baseline_metrics'][mae]}/250 | {fields['initial-homeostatic-state']}/250; {fields['rng-start']}/250; {fields['policy-memory-start']}/250 |")
text+=['','The factor itself differs in recorded scene metadata; complete engine-state identity is not assumed. A few baseline trajectories also differ despite matching recorded start fields. The primary Welch comparison retains all trials. Baseline-change and paired-ID sensitivity analyses are reported separately; a further pretreatment-matched sensitivity retains only IDs with identical phase-1 metrics and captured start fields, as documented in the analysis-plan amendment.','',
'| Factor vs CCC | Method | Trials per condition | MAE difference [95% CI] | Holm p |',
'|---|---|---:|---:|---:|']
for f in factors[1:]:
 for method in ['Welch-change','paired-ID','paired-baseline-matched']:
  x=next(x for x in s if x['condition']=='CDR-'+str(f) and x['reference']=='CCC' and x['phase']=='3' and x['metric']==mae and x['method']==method)
  text.append(f"| {f} | {method} | {x['n_cdr']} | {interval(x)} | {float(x['p_holm']):.4g} |")
text+=['','All trials, including large errors, remain included in the primary comparison. Full standard deviations, medians, minima and maxima are in phase_summary.csv. Independent R checks reproduce all 162 descriptive rows, 32 primary contrasts, 40 all-factor contrasts and 128 sensitivity contrasts.','',
'## Implications for the paper','',
'Use factor-1 CDR versus CCC as the primary HRL experiment, in accordance with the author’s clarified original plan. Present factor 0 and accelerated factors 2, 4 and 7 as sensitivity conditions around ordinary counting. Retain the factor-response curve and comparisons against both factor 0 and factor 1 with uncertainty. The designation follows the stated design intent, not a claim that the observed minimum identifies an optimal factor; document that the author’s clarification followed inspection of the sweep. The available NF CDR batch remains factor 0 and is not a matching factor-1 primary result.','',
'Use these current measurements in place of claims based on the legacy traversal-factor files. The earlier data used different observation code/policies and cannot be pooled. A factor effect is an effect of changing environmental history under this selected policy; it does not establish neural plasticity, online learning, or variation across independent training seeds.','',
'Suggested Results paragraph: “We varied the decanalized traversal factor over 0, 1, 2, 4 and 7 while holding the selected HRL policy fixed. Mean post-intervention absolute deviation ranged from 14.79 to 15.51, and mean objective reward ranged from 79.83 to 80.19 per 100-second phase. Although larger factors left substantially greater traversal counts after recanalization, the planned comparisons did not establish differences in subsequent absolute regulation or reward, or an advantage over uninterrupted canalization. Baseline-change and matched-trial sensitivity analyses retained this uncertainty. These results provide no clear dose-response relationship between this environmental-history parameter and post-intervention performance for the selected policy.”','',
'## Reproduction and evidence','',
'The same selected HRL snapshots were verified in all runs. Native receipts, 3,000 new scene hashes, 12 new loaded inference snapshot files and the requested factor on every tile were checked. Import additionally rechecks 1,500 reference scene hashes for the landscape-count audit. A separate editor audit passed 17 direct native event-handler checks for decanalized increments, ordinary counting and count-halving, with no saved asset changes. These are handler tests, not physical collision tests. All 1,500 trials across six conditions are complete: 4,500 phases and 9,000,000 decisions. Five source-project asset/map hashes were unchanged at native completion.','',
'The frozen compact inputs and their hashes are in inputs/ and source_manifest.json. Full native scene records, matching snapshots, logs and isolated project copies remain under the source run recorded in that manifest. Reproduce using analyze.py, bootstrap_and_plot.R and write_report.py in that order. See README.md for commands.']
(HERE/'RESULTS.md').write_text('\n'.join(text)+'\n')

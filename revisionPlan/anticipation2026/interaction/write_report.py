"""Report direct interactions after native and independent statistical checks."""
from pathlib import Path
import csv,json

HERE=Path(__file__).resolve().parent
rows=lambda name:list(csv.DictReader((HERE/name).open()))
verification=json.loads((HERE/'verification.json').read_text());assert verification['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
d=rows('phase_summary.csv');interactions=rows('interactions.csv');simple=rows('simple_rate_effects.csv')
ccc=rows('ccc_contrasts.csv');sensitivity=rows('sensitivity.csv');counts=rows('landscape_counts.csv')
rules=['zero','half','keep'];labels={'zero':'Reset','half':'Halve and floor','keep':'Keep all'}
metrics=['homeostatic-mae','reward-total']
def mean(c,m,phase=3):return float(next(r['mean'] for r in d if r['condition']==c and r['metric']==m and int(r['phase'])==phase))
def interval(r):return f"{float(r['difference']):+.3f} [{float(r['ci95_low']):.3f}, {float(r['ci95_high']):.3f}]"
def pp(r):return f"{float(r['p_holm']):.4g}"
def get(table,m,**keys):return next(r for r in table if r['phase']=='3' and r['metric']==m and all(r[k]==v for k,v in keys.items()))
significant=[r for r in interactions if r['phase']=='3' and float(r['p_holm'])<.05]
text=['# Does post-decanalization retention change the effect of faster counting?','',
      'This completed 2 × 3 evaluation crosses counting increments of 1 and 7 during decanalization with resetting tile counts, halving and flooring them, or keeping them at recanalization. Pre- and post-intervention counting remains one per entry. The same selected corrected-anticipation HRL policy is fixed in every condition. Each CDR cell and the shared CCC control contains 250 complete trials.','',
      '## Direct answer','']
if significant:
    text.append('At least one direct interaction contrast passes the planned six-test Holm adjustment. The affected endpoint and direction are reported below; this remains an exploratory result for one selected policy.')
    for r in significant:text.append(f"- {r['metric']}: {labels[r['first_rule']]} versus {labels[r['second_rule']]}, interaction {interval(r)}, Holm p={pp(r)}.")
else:
    text.append('The experiment does not establish that the post-decanalization count rule changes the performance effect of increasing counting from 1× to 7×. No direct interaction passes the planned six-test Holm adjustment. This leaves interactions uncertain rather than establishing independence or equivalence.')
text += ['', 'The interaction is a difference of rate effects, not a comparison of which separate p values fall below 0.05. For example, keep-versus-half is (7× keep − 1× keep) − (7× half − 1× half). The same CCC control cancels from this contrast.','',
         '## Post-intervention means and simple counting-rate effects','',
         '| Recanalization rule | 1× MAE | 7× MAE | MAE 7×−1× [95% CI] | Holm p | 1× reward | 7× reward | Reward 7×−1× [95% CI] | Holm p |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for rule in rules:
    a,b=[get(simple,m,rule=rule) for m in metrics]
    text.append(f"| {labels[rule]} | {mean('k1-'+rule,metrics[0]):.3f} | {mean('k7-'+rule,metrics[0]):.3f} | {interval(a)} | {pp(a)} | {mean('k1-'+rule,metrics[1]):.3f} | {mean('k7-'+rule,metrics[1]):.3f} | {interval(b)} | {pp(b)} |")
text += ['', 'Simple effects have their own six-test family (three rules × two endpoints). Negative MAE differences favor faster counting; positive reward differences favor it. MAE uses recorded event/update samples; reward is the actual callback total per 100-second, 2,000-decision phase.','',
         '## Primary interaction contrasts','',
         '| First rule versus second | Change in MAE rate effect [95% CI] | Holm p | Change in reward rate effect [95% CI] | Holm p |',
         '|---|---:|---:|---:|---:|']
tex=['% Primary phase-3 interactions; 250 trials/cell; four-cell Welch-Satterthwaite CIs; Holm family=6.']
for first,second in [('zero','half'),('keep','half'),('keep','zero')]:
    a,b=[get(interactions,m,first_rule=first,second_rule=second) for m in metrics]
    label=labels[first]+' vs '+labels[second]
    text.append(f'| {label} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |')
    tex.append(f'{label} & {interval(a)} & {pp(a)} & {interval(b)} & {pp(b)} '+r'\\')
(HERE/'interaction_table_rows.tex').write_text('\n'.join(tex)+'\n')
text += ['', 'An interaction compares the 7×−1× effect under the first rule with that under the second. A negative MAE interaction means faster counting is more favorable under the first rule; a positive reward interaction has the same favorable interpretation. These are four-cell Welch-Satterthwaite comparisons with unadjusted 95% t intervals. Holm adjusts all three rule contrasts and both endpoints together, six tests. The three pairwise contrasts are dependent; no separate omnibus test is claimed.','',
         'The response figure shows condition means with unadjusted 95% t confidence intervals; the dashed line and gray band show the shared CCC mean and its interval. The interaction figure shows direct interaction estimates and unadjusted 95% intervals, with a dashed zero line.','',
         '## CDR versus the shared CCC control','',
         f'CCC means are MAE {mean("CCC",metrics[0]):.3f} and reward {mean("CCC",metrics[1]):.3f}. These secondary comparisons have a separate 12-test family. They compare the complete CDR intervention with CCC, not the isolated count transformation.','',
         '| CDR cell | MAE difference vs CCC [95% CI] | Holm p | Reward difference vs CCC [95% CI] | Holm p |',
         '|---|---:|---:|---:|---:|']
for k in [1,7]:
    for rule in rules:
        c=f'k{k}-{rule}';a,b=[get(ccc,m,condition=c) for m in metrics]
        text.append(f'| {k}×, {labels[rule]} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |')
text += ['', '## Sensitivity and alignment','',
         '| Rule contrast | Method | Trials per cell | MAE interaction [95% CI] | Holm p | Reward interaction [95% CI] | Holm p |',
         '|---|---|---:|---:|---:|---:|---:|']
for first,second in [('zero','half'),('keep','half'),('keep','zero')]:
    for method in ['Welch-change','paired-ID','paired-ID-change','paired-baseline-matched']:
        a,b=[get(sensitivity,m,first_rule=first,second_rule=second,method=method) for m in metrics]
        text.append(f"| {labels[first]} vs {labels[second]} | {method} | {a['n_per_cell']} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |")
sens_significant=[r for r in sensitivity if r['phase']=='3' and float(r['p_holm'])<.05]
if sens_significant:
    text += ['', 'At least one sensitivity contrast passes its own six-test adjustment. This is method-dependent evidence and must be distinguished from the primary four-cell comparison:']
    for r in sens_significant:
        text.append(f"- {r['method']}, {r['metric']}, {labels[r['first_rule']]} versus {labels[r['second_rule']]}: {interval(r)}, Holm p={pp(r)}.")
else:text += ['', 'No phase-3 interaction sensitivity passes its corresponding six-test Holm adjustment.']
text += ['', 'Each sensitivity method uses its own six-test family per phase. Baseline-change subtracts phase 1 within trial before forming the contrast. Paired methods use same-ID four-cell contrasts. Pretreatment matching uses all nine phase-1 metrics plus recorded initial h, RNG and recurrent memory across all four cells. No trials are excluded from the primary analysis. Recorded start-field agreement does not prove complete engine-state identity.','',
         '| Rate | Rule vs half-floor | Identical phase-1 MAE trials | Identical phase-2 MAE trials | Matching initial h / RNG / memory |',
         '|---|---|---:|---:|---|']
for r in verification['baseline_alignment']:
    f=r['start_fields']
    text.append(f"| {r['factor']}× | {labels[r['rule']]} | {r['phase1_identical'][metrics[0]]}/250 | {r['phase2_identical'][metrics[0]]}/250 | {f['initial-homeostatic-state']}/250; {f['rng-start']}/250; {f['policy-memory-start']}/250 |")
text += ['', '## Environmental history and interpretation','',
         '| Rule | Mean total tile counts, 1× | Mean total tile counts, 7× |',
         '|---|---:|---:|']
for rule in rules:
    values=[float(next(r['mean'] for r in counts if r['condition']==f'k{k}-{rule}' and r['phase']=='3')) for k in [1,7]]
    text.append(f'| {labels[rule]} | {values[0]:.3f} | {values[1]:.3f} |')
text += ['', 'These are summed counts across the 2,500 tiles captured at phase-3 start, not distinct-tile counts. Resetting erases the direct stored tile-count channel, while resource states, recurrent memory and trajectories created during decanalization can still differ. Higher retained counts lower later traversal costs nonlinearly. Lower loss need not improve regulation when h is positive.','',
         'Ordinary physical and predicted losses remain zero during the intervention. Phase boundaries restore initial h, so the evaluation does not represent uninterrupted homeostatic recovery. All fixed-horizon trials, including extreme errors, are retained. The findings concern one selected policy and do not establish robustness across training seeds or changes in neural plasticity.','',
         'Keep k=1/half-floor as the main paper condition. This author-approved factorial extension tests the interaction left unresolved by the earlier two separate sweeps. Do not select a replacement condition or claim an optimal rate/retention rule from these exploratory outcomes.','',
         '## Verification and reproduction','',
         'The two new cells contain 500 trials, 1,500 phases and 3,000,000 decisions. With four reused CDR cells and the shared CCC reference, the factorial package covers 1,750 trials, 5,250 phases and 10,500,000 decisions. Both variants passed 15 real Blueprint handler checks before scoring, including factor 7 during decanalization and ordinary increments of 1. All 1,500 new scene hashes, six loaded inference snapshot files, durable completion receipts and compiled tile hashes were verified. The corrected anticipation and selected weights match the references. Production source hashes are preserved.','',
         (HERE/'r_verification.txt').read_text().strip(),'',
         'Run analyze.py, verify_and_plot.R and write_report.py in order. Frozen input hashes and reference manifests are in source_manifest.json. The native run and local archive preserve raw scenes, model captures, variant assets, logs, protocol and exact source copies. The main report is generated only after native completion and independent statistical verification.']
(HERE/'RESULTS.md').write_text('\n'.join(text)+'\n')
paper=['# Proposed factorial sensitivity addition','',
       'The manuscript source is preserved. Keep the original k=1/half-floor primary condition.','',
       '> To test whether post-decanalization count retention modified the effect of accelerated traversal counting, we crossed increments of one and seven during decanalization with resetting, halving and flooring, or retaining counts at recanalization. Each cell contained 250 trials under the same fixed HRL policy. We compared the 7-minus-1 rate effects between retention rules using four-cell heteroskedastic contrasts and Welch-Satterthwaite intervals. Holm correction covered three rule contrasts and two endpoints. Same-ID and baseline-change contrasts were sensitivity analyses.','']
if not significant:
    paper += ['> The factorial evaluation did not establish an interaction between counting rate and retention rule for post-intervention absolute deviation or received reward after multiplicity correction. This leaves interaction effects uncertain rather than establishing independence or equivalence.']
    a,b=[get(interactions,m,first_rule='keep',second_rule='half') for m in metrics]
    paper += ['',f'> Retaining all counts rather than halving and flooring changed the 7-minus-1 counting-rate effect by {interval(a)} for absolute deviation and {interval(b)} for received reward (95% confidence intervals; Holm p={pp(a)} and {pp(b)}, respectively).']
else:
    for r in significant:
        paper += [f"> For {r['metric']}, the change in the counting-rate effect between {labels[r['first_rule']]} and {labels[r['second_rule']]} was {interval(r)} (Holm p={pp(r)})."]
if sens_significant:
    paper += ['', '> Some sensitivity contrasts passed their corresponding multiplicity adjustments; these method-dependent findings are reported separately from the primary analysis.']
paper += ['', 'Report the full interaction table and uncertainty, plus any sensitivity disagreement. A significant comparison with CCC under one rule and an uncertain comparison under another is not itself an interaction. These are environmental-history manipulations under one trained policy; they do not establish neural plasticity or generalization across training runs.','',
          'Use factorial_response.pdf, interaction_contrasts.pdf and interaction_table_rows.tex for the supplement.']
(HERE/'MANUSCRIPT_ADDITIONS.md').write_text('\n'.join(paper)+'\n')

"""Write interpretations only after native completion and independent R checks."""
from pathlib import Path
import csv,json

HERE=Path(__file__).resolve().parent
read=lambda name:list(csv.DictReader((HERE/name).open()))
verification=json.loads((HERE/'verification.json').read_text())
assert verification['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
summary=read('phase_summary.csv');primary=read('primary_contrasts.csv')
current=read('versus_current.csv');sens=read('sensitivity.csv');landscape=read('landscape_counts.csv')
conditions=['zero','quarter-floor','half-floor','three-quarter-floor','keep','half-exact']
labels={'zero':'0% retained','quarter-floor':'25%, floored','half-floor':'50%, floored (current)',
        'three-quarter-floor':'75%, floored','keep':'100% retained','half-exact':'50%, exact'}
mae='homeostatic-mae';reward='reward-total'
def mean(c,m,phase=3):
    return float(next(r['mean'] for r in summary if r['condition']==c and r['metric']==m and int(r['phase'])==phase))
def effect(table,c,m):return next(r for r in table if r['condition']==c and r['metric']==m and r['phase']=='3')
def interval(r):return f"{float(r['difference']):+.3f} [{float(r['ci95_low']):.3f}, {float(r['ci95_high']):.3f}]"
def pp(r):return f"{float(r['p_holm']):.4g}"
def meaningful(table,m,direction):
    return [r['condition'] for r in table if r['phase']=='3' and r['metric']==m and float(r['p_holm'])<.05 and direction*float(r['difference'])>0]
text=['# HRL performance under different post-decanalization count transformations','',
      'This experiment changes the stored tile counts at the CDR transition out of decanalization. Counting is one visit per actual entry in every phase, and the selected corrected-anticipation HRL policy is fixed. This directly tests a different manipulation from the earlier sweep of counting rates during decanalization.','',
      '## Answer: CDR versus CCC','']
for m,label,direction in [(mae,'lower absolute setpoint error',-1),(reward,'higher received objective reward',1)]:
    wins=meaningful(primary,m,direction);losses=meaningful(primary,m,-direction)
    if wins:text.append('Conditions establishing '+label+' than CCC after the 12-test Holm adjustment: '+', '.join(labels[c] for c in wins)+'.')
    else:text.append('No tested transformation establishes '+label+' than CCC after the 12-test Holm adjustment.')
    if losses:text.append('Conditions with a detectable change in the opposite direction: '+', '.join(labels[c] for c in losses)+'.')
    text.append('')
text += ['The comparisons retain all 250 trials per condition. Differences are CDR minus CCC; negative MAE and positive reward differences favor CDR. Brackets are unadjusted Welch 95% intervals. All six conditions and both endpoints form one 12-test phase-3 Holm family. An interval spanning zero does not establish equivalence.','',
         '| Counts retained at recanalization | CDR MAE | CDR reward | MAE difference vs CCC [95% CI] | MAE Holm p | Reward difference vs CCC [95% CI] | Reward Holm p |',
         '|---|---:|---:|---:|---:|---:|---:|']
for c in conditions:
    a,b=effect(primary,c,mae),effect(primary,c,reward)
    text.append(f'| {labels[c]} | {mean(c,mae):.3f} | {mean(c,reward):.3f} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |')
text += ['',f'CCC means: MAE **{mean("CCC",mae):.3f}**, reward **{mean("CCC",reward):.3f}** per 100-second phase.','',
         '## Does changing the current rule change performance?','',
         'A difference from CCC alone does not show that a new transformation improved on the current implementation. These direct comparisons use half-floor as the reference, with a separate 10-test Holm family (five alternatives × two endpoints).','',
         '| Alternative to half-floor | MAE difference [95% CI] | Holm p | Reward difference [95% CI] | Holm p |',
         '|---|---:|---:|---:|---:|']
for c in conditions:
    if c=='half-floor':continue
    a,b=effect(current,c,mae),effect(current,c,reward)
    text.append(f'| {labels[c]} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |')
rounding=[effect(current,'half-exact',m) for m in [mae,reward]]
if any(float(r['p_holm'])<.05 for r in rounding):
    text += ['','At least one half-exact versus half-floor contrast passes the secondary Holm adjustment; its direction and endpoint are given above. This isolates flooring while retaining the same one-half scaling.']
else:text += ['','The half-exact versus half-floor comparisons do not establish a performance effect of flooring on either endpoint. This leaves rounding effects uncertain rather than proving that rounding is irrelevant.']
text += ['', '## Counts and phase diagnostics','',
         '| Condition | Mean total counts at phase-3 start | MAE pre | MAE during | MAE post | Reward post |',
         '|---|---:|---:|---:|---:|---:|']
for c in [*conditions,'CCC']:
    count=float(next(r['mean'] for r in landscape if r['condition']==c and r['phase']=='3'))
    text.append(f'| {labels.get(c,c)} | {count:.3f} | {mean(c,mae,1):.3f} | {mean(c,mae,2):.3f} | {mean(c,mae):.3f} | {mean(c,reward):.3f} |')
exact_audit=json.loads((HERE/'inputs/half-exact.verified.json').read_text())
fractional_mean=exact_audit['fractional_tile_counts_by_phase']['3']/250
current_counts=float(next(r['mean'] for r in landscape if r['condition']=='half-floor' and r['phase']=='3'))
exact_counts=float(next(r['mean'] for r in landscape if r['condition']=='half-exact' and r['phase']=='3'))
text += ['', f'At phase-3 start, exact halving retains a mean total count of {exact_counts:.3f}, compared with {current_counts:.3f} under current floored halving. Exact halving leaves an average of {fractional_mean:.3f} tiles per trial with fractional counts in the captured scene. A once-visited tile retains 0.5 under exact halving and zero under floored halving. Thus the rounding comparison changes measurable environmental history, even if a performance contrast remains uncertain.']
text += ['','Count totals sum the 2,500 tiles captured at phase start; they are not numbers of distinct visited tiles. Native handler tests verify the exact transformation before scoring. Initial phase placement/overlap ordering may add ordinary entries around the count-transform operation, so a captured phase-3 total need not equal the transformation applied to a phase-2-start total.','',
         'Ordinary physical and predicted loss are still removed during decanalization. Phase boundaries restore the trial’s initial h, so these phase means do not represent uninterrupted homeostatic recovery. The unchanged phase-2 comparisons are diagnostic, not additional evidence of a post-transition effect.','',
         '| CDR condition vs current half-floor | Identical phase-1 MAE trials | Identical phase-2 MAE trials | Matching initial h / RNG / memory |',
         '|---|---:|---:|---|']
for r in verification['baseline_alignment']:
    if r['reference']!='half-floor':continue
    f=r['start_fields']
    text.append(f"| {labels[r['condition']]} | {r['phase1_identical'][mae]}/250 | {r['phase2_identical'][mae]}/250 | {f['initial-homeostatic-state']}/250; {f['rng-start']}/250; {f['policy-memory-start']}/250 |")
text += ['', '## Sensitivity analyses','',
         'Welch baseline-change, paired-ID, paired-ID baseline-change and pretreatment-matched paired analyses are exported in sensitivity.csv. Each keeps the corresponding 12-test CCC or 10-test current-rule family, separately per phase/method. Pretreatment matching uses all nine phase-1 metrics and recorded start fields, not post-intervention outcomes. Exact engine-state identity is not assumed, and all trials remain in the primary Welch analysis.','',
         '| Condition vs CCC | Method | Matched/sample n | MAE difference [95% CI] | Holm p | Reward difference [95% CI] | Holm p |',
         '|---|---|---:|---:|---:|---:|---:|']
for c in conditions:
    for method in ['Welch-change','paired-ID','paired-baseline-matched']:
        a,b=[next(r for r in sens if r['condition']==c and r['reference']=='CCC' and r['phase']=='3'
                 and r['metric']==m and r['method']==method) for m in [mae,reward]]
        text.append(f"| {labels[c]} | {method} | {a['n_cdr']} | {interval(a)} | {pp(a)} | {interval(b)} | {pp(b)} |")
text += ['', '## Interpretation for the paper','',
         'Keep half-floor with a one-count increment throughout as the main condition. Treat this author-approved extension as an exploratory sensitivity analysis, specifying each transformation and both comparison families. Report whether alternatives differ from CCC and whether they differ directly from the current transformation; a significant result in one condition and an uncertain result in another is not itself a significant difference between them.','',
         'Any altered count retention changes environmental history under one selected fixed policy. It does not establish changes in neural plasticity, effects across independently trained policies, or a biological intervention mechanism. Lower traversal costs need not improve regulation when the agent is above its setpoint. Extreme-error trials remain included, and uncertainty must be reported alongside the mean estimates.','',
         '## Verification and reproduction','',
         'Five new CDR batches contain 1,250 scored trials, added to the existing 250-trial current-rule batch and 250-trial CCC batch: 1,750 trials, 5,250 phases and 10,500,000 decisions. A separate one-trial smoke test is excluded from all scored tables. Native receipts, 3,750 new scene hashes, 15 new loaded inference snapshot files and 75 handler checks pass. The corrected anticipation asset and all selected loaded-model hashes match the earlier reference. Each variant’s compiled tile asset is retained and its hash matches the asset recorded by its scored run. Production source assets/maps are unchanged.','',
         'The smoke-test wrapper initially expected its observer’s final callback even though native completion had already saved a complete receipt and exited. This orchestration race was corrected to use the durable native receipt; the completed smoke data and the diagnostic are preserved. It did not change the simulation or generate discarded scored outcomes.','',
         'One concurrent disposable editor stalled during zero-count validation startup, before producing scored trials. Its logs were preserved and that audit was restarted successfully. The recovery kept the three ongoing native batches running and used a fifth independent copy for half-exact after a memory/CPU resource check. This changes concurrency only; simulated timesteps, trials and experimental settings are unchanged. The original dispatcher’s startup failure record and the successful recovery/completion record are retained together.','',
         (HERE/'r_verification.txt').read_text().strip(),'',
         'Reproduce from frozen compact inputs with analyze.py, verify_and_plot.R and write_report.py, in that order. source_manifest.json identifies the raw sources and all frozen file hashes. Full native scenes, model captures, logs, approved protocol and script copies are retained in the experiment run folder and the local reproducibility archive. This report is generated only after all native and independent statistical checks complete.']
(HERE/'RESULTS.md').write_text('\n'.join(text)+'\n')
# A compact supplement-ready table, retaining the two endpoint contrast family.
tex=['% Recanalization sensitivity: 250 trials/condition; phase-3 Welch; Holm family=12 (six conditions x two endpoints).']
for c in conditions:
    a,b=effect(primary,c,mae),effect(primary,c,reward)
    def ti(r):return f"{float(r['difference']):.3f} [{float(r['ci95_low']):.3f}, {float(r['ci95_high']):.3f}]"
    label=labels[c].replace('%',r'\%')
    tex.append(f"{label} & {mean(c,mae):.3f} & {ti(a)} & {pp(a)} & {mean(c,reward):.3f} & {ti(b)} & {pp(b)} "+r'\\')
(HERE/'post_table_rows.tex').write_text('\n'.join(tex)+'\n')

maes=[mean(c,mae) for c in conditions];rewards=[mean(c,reward) for c in conditions]
mae_effects=[effect(primary,c,mae) for c in conditions]
reward_effects=[effect(primary,c,reward) for c in conditions]
any_ccc=any(float(r['p_holm'])<.05 for r in mae_effects+reward_effects)
any_current=any(float(r['p_holm'])<.05 for r in current if r['phase']=='3')
paper=['# Proposed recanalization sensitivity additions','',
       'These are proposals; the manuscript source is not automatically rewritten. The main half-floor condition remains unchanged.','',
       '## Methods / supplement','',
       '> We assessed sensitivity to the transformation of traversal history at recanalization while retaining one counted visit per tile entry in every phase. We compared resetting counts to zero, retaining one quarter, one half or three quarters with rounding down, retaining all counts, and retaining one half without rounding. Each condition comprised 250 trials under the same selected fixed HRL policy and corrected anticipatory observations. The current half-floor and CCC batches were reused. We compared phase-3 absolute deviation and received reward with CCC using Welch intervals and Holm adjustment across six conditions and two endpoints. A separate ten-test family compared the five alternatives directly with the current transformation. Baseline-change and paired analyses were sensitivity checks.','',
       '## Results','',
       f'> Across the six CDR transformations, post-intervention mean absolute deviation ranged from {min(maes):.3f} to {max(maes):.3f}, and mean objective reward ranged from {min(rewards):.3f} to {max(rewards):.3f} per 100-second phase. CCC means were {mean("CCC",mae):.3f} and {mean("CCC",reward):.3f}, respectively.']
if not any_ccc:
    paper += ['> No transformation established a post-intervention difference from CCC in either endpoint after the twelve-test Holm adjustment. This does not establish equivalence.']
else:
    for metric,label in [(mae,'absolute deviation'),(reward,'objective reward')]:
        for c in conditions:
            r=effect(primary,c,metric)
            if float(r['p_holm'])<.05:
                paper += [f'> {labels[c]} changed {label} relative to CCC (difference {interval(r)}, Holm p={pp(r)}).']
if not any_current:
    paper += ['> Direct comparisons with the current half-floor rule did not establish a difference in either endpoint after the separate ten-test adjustment.']
else:
    for r in current:
        if r['phase']=='3' and float(r['p_holm'])<.05:
            label='absolute deviation' if r['metric']==mae else 'objective reward'
            paper += [f"> Relative to the current half-floor rule, {labels[r['condition']]} changed {label} (difference {interval(r)}, Holm p={pp(r)})."]
paper += ['', '## Discussion and figure','',
          'Replace the existing limitation that count-halving was not explored with a description of this extension and its actual uncertainty. Describe which alternatives differ directly from the current rule, as well as which differ from CCC. Do not infer a difference between two rules merely because one comparison with CCC is significant and another is not. The paper’s current primary rule remains half-floor. This extension does not establish an optimal transformation or generalization across training seeds.','',
          '> Post-intervention HRL performance under six transformations of tile traversal counts at recanalization, with 250 trials per condition. Counting remains one per entry throughout. Points show trial means and bars show unadjusted 95% intervals; the dashed line and band show the CCC mean and interval. Absolute-deviation summaries use recorded event/update samples. Reward is the received total per 100-second phase. The separate contrast figure shows CDR-minus-CCC Welch differences and intervals; multiplicity-adjusted tests are reported in the table.','',
          'Use `retention_response.pdf`, `ccc_contrasts.pdf` and `post_table_rows.tex`. All nine descriptive outcomes and the full statistical tables remain available in the CSVs.']
(HERE/'MANUSCRIPT_ADDITIONS.md').write_text('\n'.join(paper)+'\n')

"""Write the current HRL report and paper rows from independently checked CSVs."""
from pathlib import Path
import csv, json

HERE = Path(__file__).resolve().parent
read = lambda name: list(csv.DictReader((HERE / name).open()))
assert json.loads((HERE / 'verification.json').read_text())['passed']
assert (HERE / 'r_verification.txt').read_text().startswith('PASS:')
summary = read('phase_summary.csv')
primary = read('primary_contrasts.csv')
sensitivity = read('sensitivity.csv')
labels = {'homeostatic-mae': 'Mean absolute h', 'setpoint-dev': 'Population SD of h',
          'reward-total': 'Objective reward per phase',
          'homeostatic-fraction-within-5': 'Fraction within ±5',
          'homeostatic-rms': 'RMS h', 'setpoint-avg': 'Signed mean h',
          'loss-total': 'Logged h loss', 'gain-total': 'Logged h gain',
          'gains-harvested': 'Logged harvest count'}


def mean(order, metric, phase=3):
    return float(next(r['mean'] for r in summary if r['condition'] == 'HRL-'+order
                      and int(r['phase']) == phase and r['metric'] == metric))


def interval(row):
    return f"{float(row['difference']):.3f} [{float(row['ci95_low']):.3f}, {float(row['ci95_high']):.3f}]"


text = ['# Primary HRL analysis: traversal factor 1', '',
        'Factor 1 is the primary condition following the author’s clarification of the original design on 26 October 2026. Each actual entry increments the tile count by one in every phase. The existing count-halving operation at recanalization remains. Factors 0, 2, 4 and 7 are sensitivity conditions. See [the design clarification](../PRIMARY_DESIGN_CLARIFICATION.md).', '',
        'The factor-1 batch and CCC each contain 250 completed trials. Policy selection and weights are unchanged: the selected fresh HRL policy has 750,000 training transitions and receives corrected anticipation. Promoting this completed evaluation condition requires no retraining or new HRL trials.', '',
        'Post-intervention MAE and objective-reward contrasts remain uncertain. The MAE point estimate favors CDR, but the interval includes both benefit and harm. These results establish neither improved regulation nor equivalence.', '',
        '## Post-intervention outcomes', '',
        'The estimand is the phase-3 CDR-minus-CCC difference in trial means. Intervals are unadjusted two-sided Welch 95% intervals. Holm adjusts all nine HRL outcomes together within each phase; phase 2 is a separate exploratory family. All 250 trials per condition are retained. The earlier two-objective, 18-test factor-0 analysis is a separate reference and is not this HRL-only family.', '',
        '| Outcome | CDR, factor 1 | CCC | Difference [95% CI] | Holm p |',
        '|---|---:|---:|---:|---:|']
tex = ['% Factor-1 HRL primary analysis; 250 trials per condition; Holm family=9 HRL outcomes.']
for metric, label in labels.items():
    row = next(r for r in primary if r['phase'] == '3' and r['metric'] == metric)
    a, b = mean('CDR', metric), mean('CCC', metric)
    pp = f"{float(row['p_holm']):.4g}"
    text.append(f'| {label} | {a:.3f} | {b:.3f} | {interval(row)} | {pp} |')
    texlabel = label.replace('±', r'$\pm$').replace(' h', ' $h$')
    tex.append(f"{texlabel} & {a:.3f} & {b:.3f} & {float(row['difference']):.3f} & [{float(row['ci95_low']):.3f}, {float(row['ci95_high']):.3f}] & {pp} " + r'\\')
(HERE / 'hrl_post_table_rows.tex').write_text('\n'.join(tex)+'\n')
text += ['', '## Phase means', '',
         '| Condition | MAE pre | MAE during | MAE post | Reward pre | Reward during | Reward post |',
         '|---|---:|---:|---:|---:|---:|---:|']
for order in ['CDR', 'CCC']:
    values = [mean(order, m, p) for m in ['homeostatic-mae', 'reward-total'] for p in [1, 2, 3]]
    text.append('| HRL-'+order+' | '+' | '.join(f'{x:.3f}' for x in values)+' |')
assert mean('CDR', 'loss-total', 2) == 0
text += ['', 'MAE and other homeostatic summaries use the recorded event/update samples. Reward is the actual callback total across 2,000 decisions per 100-second phase. During decanalization, physical and anticipated losses are zero even though traversal counting continues. The trial’s initial h is restored at phase boundaries, so connected phase means do not show uninterrupted recovery.', '',
         '## Matching and sensitivity', '',
         'All 250 trial IDs have matching captured initial h, RNG and recurrent-memory starts; 249 have identical values for all nine phase-1 metrics. One baseline trajectory differs despite matching recorded start fields. The full primary sample is retained. Exact scene hashes are not a useful pairing criterion across factors because the factor itself changes scene metadata. Matching recorded fields does not prove complete engine-state identity.', '',
         '| Outcome | Method | Trials per condition | Difference [95% CI] | Holm p |',
         '|---|---|---:|---:|---:|']
for metric in ['homeostatic-mae', 'reward-total']:
    for method in ['Welch-change', 'paired-ID', 'paired-ID-change', 'paired-baseline-matched']:
        row = next(r for r in sensitivity if r['phase'] == '3' and r['metric'] == metric and r['method'] == method)
        text.append(f"| {labels[metric]} | {method} | {row['n_cdr']} | {interval(row)} | {float(row['p_holm']):.4g} |")
text += ['', 'Each sensitivity method has its own nine-outcome Holm family per phase. Baseline-change contrasts subtract phase-1 outcomes within trial before comparing conditions. All these MAE and reward intervals include zero. The factor-0 bootstrap from the earlier delivery is not reused or relabelled as a factor-1 bootstrap.', '',
         '## Paper interpretation and NF status', '',
         'Use the factor-1 rows and figures here for the primary HRL results. Update the counting description and appendix to an entry increment of 1 in all three phases, retaining floor(n/2) at recanalization. Describe the factor-0 and accelerated-factor runs as sensitivity evidence. Their current [sweep report](../plasticity/RESULTS.md) retains the full numerical comparisons and uncertainty.', '',
         'Suggested HRL Results paragraph: “Using the intended increment of one traversal count per entry in all phases, post-intervention mean absolute deviation was 14.789 under CDR and 18.475 under CCC (difference −3.686, 95% CI [−9.722, 2.349]). Mean objective reward was 79.964 and 79.349, respectively (difference 0.615, 95% CI [−1.796, 3.026]). Both Holm-adjusted p values were 1.0. Baseline-change and paired sensitivity analyses retained this uncertainty. The evaluation therefore did not establish improved post-intervention regulation.”', '',
         '**The available corrected NF CDR data used factor 0.** They are separate reference evidence, not a matching factor-1 primary result. A matched NF evaluation and an explicit joint multiplicity family are needed before reporting both objectives as one factor-1 primary experiment. NF reward/proximity statements from the earlier report must carry their factor-0 qualification. No neural plasticity or generalization across independently trained policies is established by these single-policy evaluations.', '',
         'The author clarified the intended primary factor after the sweep outcomes were available; this is documented rather than presented as preregistration. The designation follows that stated intent and does not establish factor 1 as optimal.', '',
         '## Reproduction and verification', '',
         'Run `analyze.py`, `verify_and_plot.R`, then `write_report.py` as shown in README.md. The Python analysis validates both frozen source manifests, raw JSON/YAML agreement, completion receipts, corrected asset identity and selected loaded-model hashes. Existing native audits checked 750 factor-1 and 750 CCC scene hashes; routine compact-data reproduction does not claim to reread external scene binaries. Independent base R reproduced 54 descriptive rows, 18 Welch comparisons and 72 sensitivity comparisons, including confidence intervals and Holm adjustments. There are 500 trials, 1,500 phases and 3,000,000 decisions.', '',
         'The original factor-0 reports and ZIP bundles remain historical records. `selection.json` identifies the actual primary runs and distinguishes the CCC’s unused stored decanalized factor (0) from its executed ordinary increment (1). `source_manifest.json` records hashes of the source manifests, selection and author clarification.']
(HERE / 'RESULTS.md').write_text('\n'.join(text)+'\n')

"""Reproduce the author-designated factor-1 HRL primary comparison.

Reads the original verified reference inputs and the separately frozen native
factor-1 evaluation. Neither source selection nor frozen sweep plan is edited.
"""
from pathlib import Path
import csv, json, sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / 'plasticity'))
import build_analysis as shared
import analyze as sweep


def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def save(name, rows):
    with (HERE / name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = json.loads((BASE / 'plasticity/source_manifest.json').read_text())
    for name, item in manifest['files'].items():
        assert shared.sha(BASE / 'plasticity' / name) == item['sha256']
    assert shared.sha(BASE / 'source_manifest.json') == manifest['baseline_source_manifest_sha256']
    assert shared.sha(BASE / 'plasticity/ANALYSIS_PLAN.md') == manifest['analysis_plan_sha256']
    original, runs, reference_rows = shared.load_inputs()
    catalog = json.loads((BASE / 'inputs/selected_policy_catalog.json').read_text())
    factor_audit = json.loads((BASE / 'plasticity/inputs/factor-1.verified.json').read_text())
    assert factor_audit['factor'] == 1 and factor_audit['trials'] == 250
    a, ra, factor_rows = sweep.load_factor(1, catalog)
    b, rb = original['HRL-CCC'], runs['HRL-CCC']
    arrays = {'HRL-CDR': a, 'HRL-CCC': b}
    rows = [dict(run=ra['run-id'], family='HRL', order='cdr', factor=1,
                 **{k: v for k, v in r.items() if k not in ['condition', 'factor']})
            for r in factor_rows]
    rows += [dict(**r, factor='') for r in reference_rows
             if r['family'] == 'HRL' and r['order'] == 'ccc']
    # CCC's stored DecanalizationRateFactor is zero, but its decanalized branch
    # never executes; actual entry increments are one throughout the control.
    start_fields = ['rng-start', 'policy-memory-start',
                    'initial-homeostatic-state', 'observed-start-h']
    matched = [i for i in range(250)
               if all(a[i][0][m] == b[i][0][m] for m in shared.METRICS)
               and all(ra['trials'][i]['phases'][0][k] == rb['trials'][i]['phases'][0][k]
                       for k in start_fields)]
    assert len(matched) == 249
    summary, primary, sensitivity = [], [], []
    for condition, data in arrays.items():
        for phase in range(3):
            for metric in shared.METRICS:
                values = [t[phase][metric] for t in data]
                summary.append(dict(condition=condition, phase=phase+1,
                                    metric=metric, **shared.describe(values),
                                    minimum=min(values), maximum=max(values)))
    for phase in [1, 2]:
        for metric in shared.METRICS:
            primary.append(dict(family='HRL', factor=1, phase=phase+1,
                                metric=metric, method='Welch', estimand='CDR minus CCC',
                                **shared.compare([t[phase][metric] for t in a],
                                                 [t[phase][metric] for t in b])))
            for method, change, paired, ids in [
                ('Welch-change', True, False, range(250)),
                ('paired-ID', False, True, range(250)),
                ('paired-ID-change', True, True, range(250)),
                ('paired-baseline-matched', False, True, matched)]:
                x = [a[i][phase][metric] - (a[i][0][metric] if change else 0) for i in ids]
                y = [b[i][phase][metric] - (b[i][0][metric] if change else 0) for i in ids]
                sensitivity.append(dict(family='HRL', factor=1, phase=phase+1,
                                        metric=metric, method=method,
                                        **shared.compare(x, y, paired)))
    for phase in [2, 3]:
        shared.holm([r for r in primary if r['phase'] == phase])
        for method in sorted({r['method'] for r in sensitivity}):
            shared.holm([r for r in sensitivity if r['phase'] == phase and r['method'] == method])
    selection = dict(primary_family='HRL', decanalized_factor=1,
                     actual_entry_increments=dict(pre=1, during=1, post=1),
                     recanalization='floor(n/2), once at transition',
                     conditions={'HRL-CDR': ra['run-id'], 'HRL-CCC': rb['run-id']},
                     control_stored_decanalization_factor=0,
                     control_decanalized_branch_executed=False,
                     selection_reason='Author clarified original intended factor; not optimization on evaluation results',
                     clarification='../PRIMARY_DESIGN_CLARIFICATION.md',
                     sensitivity_factors=[0, 2, 4, 7],
                     nf_status='Available NF CDR is factor 0; excluded from this primary family',
                     holm_tests_per_phase=9)
    dump('selection.json', selection)
    save('trial_metrics.csv', rows)
    save('phase_summary.csv', summary)
    save('primary_contrasts.csv', primary)
    save('sensitivity.csv', sensitivity)
    save('baseline_matched_ids.csv', [dict(trial=i) for i in matched])
    # Protect these dependencies without mutating either earlier input manifest.
    dependencies = [BASE / 'source_manifest.json', BASE / 'plasticity/source_manifest.json',
                    BASE / 'PRIMARY_DESIGN_CLARIFICATION.md', HERE / 'selection.json']
    dump('source_manifest.json', dict(dependencies=[dict(path=str(p.relative_to(BASE)),
         sha256=shared.sha(p)) for p in dependencies],
         raw_data='Hashes and native provenance validated through the two source manifests'))
    dump('verification.json', dict(passed=True, conditions=2, trials=500, phases=1500,
         decisions=3000000, all_source_hashes_verified=True, raw_json_yaml_agreement=True,
         native_factor1_scene_audit='plasticity/inputs/factor-1.verified.json: 750 hashes, 3 loaded model files',
         control_scene_audit='source_audit.json: HRL-CCC 750 hashes',
         baseline_matched_trials=len(matched), excluded_primary_trials=0,
         identical_baseline_metrics={m: sum(t[0][m] == u[0][m] for t, u in zip(a, b))
                                     for m in shared.METRICS},
         matching_start_fields={k: sum(t['phases'][0][k] == u['phases'][0][k]
                                      for t, u in zip(ra['trials'], rb['trials'])) for k in start_fields},
         descriptive_rows=len(summary), primary_contrasts=len(primary),
         sensitivity_contrasts=len(sensitivity), holm_tests_per_phase=9))
    print('PASS: factor-1 HRL primary analysis, 500 trials; 54 summaries, 18 contrasts, 72 sensitivities.')


if __name__ == '__main__':
    main()

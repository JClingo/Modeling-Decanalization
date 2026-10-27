"""Produce a compact, reviewable report from isolated reset comparisons."""
import hashlib
import json
from pathlib import Path

root = Path('Saved/ResetPerformanceAudit')
names = ['legacy_startup', 'legacy_matched', 'current_matched',
         'current_matched_velocity', 'current_startup', 'current_legacy_startup', 'current_matched_velocity_stream']
runs = {name: json.loads((root / (name + '.json')).read_text()) for name in names}
assert all(run['passed'] for run in runs.values())
assert len({run['initial_scene_sha256'] for run in runs.values()}) == 1
for run in runs.values():
    if run['matched_scene']:
        assert run['matched_scene_sha256'] == run['initial_scene_sha256']

def compare(a, b):
    left, right = runs[a], runs[b]
    fields = ['position', 'yaw', 'control_yaw', 'velocity', 'memory', 'homeostatic_state',
              'max_speed', 'max_walk_speed', 'anticipated_gain', 'anticipated_loss',
              'observation', 'action', 'passive_loss', 'decanalized', 'tick']
    differences = []
    field_counts = {f: 0 for f in fields}
    assert len(left['samples']) == len(right['samples'])
    for l, r in zip(left['samples'], right['samples']):
        changed = [f for f in fields if l[f] != r[f]]
        for f in changed: field_counts[f] += 1
        if changed: differences.append({'tick': l['tick'], 'fields': changed})
    return {'left': a, 'right': b, 'samples_compared': len(left['samples']),
            'samples_different': len(differences), 'first_difference': differences[0] if differences else None,
            'different_samples_by_field': field_counts,
            'phase_metrics_identical': left['phases'] == right['phases']}

report = {
    'checkpoint': 'Training_ppo_sharedmemory_2026-10-14_16-11-38_*_6000.bin',
    'fixed_step_seconds': .05,
    'initial_scene_identical_across_processes': True,
    'matched_scene_restoration_verified': True,
    'comparisons': [compare('legacy_matched', 'current_matched'),
                    compare('legacy_startup', 'current_matched_velocity'),
                    compare('legacy_startup', 'current_matched_velocity_stream'),
                    compare('legacy_startup', 'current_legacy_startup'),
                    compare('legacy_startup', 'current_startup')],
    'runs': {name: {'phases': run['phases'], 'wall_seconds': run['wall_seconds'],
                    'initial_velocity': run['before_first_tick']['velocity'],
                    'initial_memory_max': max(map(abs, run['before_first_tick']['memory']))}
             for name, run in runs.items()},
    'limitations': ['One deterministic trial per condition; not a generalization benchmark.',
                    'Matched-scene restoration is an audit intervention, not production behavior.',
                    'Only reset-era assets were compared; older training/reward changes were held fixed.'],
}
report['snapshot_sha256'] = {
    kind: hashlib.sha256((Path('Intermediate/LearningAgents/Snapshots') /
        ('Training_ppo_sharedmemory_2026-10-14_16-11-38_' + kind + '_6000.bin')).read_bytes()).hexdigest()
    for kind in ['encoder', 'policy', 'decoder']}
for comparison in report['comparisons']:
    if comparison['right'] in ['current_matched', 'current_matched_velocity_stream', 'current_legacy_startup']:
        assert comparison['samples_different'] == 0, comparison
        assert comparison['phase_metrics_identical'], comparison
report['phase_boundary_homeostatic_resampling'] = {
    'present_in_legacy_and_current': True,
    'range': [-15.0, 15.0],
    'graph': 'BP_GameMode.RunTrial: clear Setpoints, add RandomFloatInRangeFromStream, broadcast SetpointsChanged',
    'production_behavior_changed_by_audit': False,
    'user_confirmed_intentional': True,
    'implication': 'Post-decanalization phase metrics are not recovery from the preceding homeostatic state.'}
before = json.loads((root / 'production_hashes.before.json').read_text(encoding='utf-8-sig'))
report['production_assets_unchanged'] = all(
    hashlib.sha256(Path(item['Path']).read_bytes()).hexdigest().upper() == item['Hash'] for item in before)
assert report['production_assets_unchanged']
Path('analysis/timing/reset_performance_validation.json').write_text(json.dumps(report, indent=2) + '\n')
for name, run in runs.items():
    print(name, {phase: round(values['mae'], 3) for phase, values in run['phases'].items()})
for comparison in report['comparisons']: print(comparison)

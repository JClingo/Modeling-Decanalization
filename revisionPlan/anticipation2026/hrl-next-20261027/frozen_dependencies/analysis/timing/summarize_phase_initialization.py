import hashlib
import json
from pathlib import Path

root=Path('Saved/PhaseVelocityFix')
checks=json.loads((root/'validation.json').read_text())
natural=json.loads((root/'natural_validation.json').read_text())
first_frame=json.loads((root/'first_frame.json').read_text())
assert checks['passed'] and natural['passed']
assert all(abs(s['speed']-s['max_speed'])<.01 for s in natural['samples'])
preserved=json.loads((root/'preserved.before.json').read_text(encoding='utf-8-sig'))
assert all(hashlib.sha256(Path(p['Path']).read_bytes()).hexdigest().upper()==p['Hash'] for p in preserved)
report={
    'passed':True,
    'velocity':'ActorForwardVector * BaseMaxSpeed; speed cap and cached MaxSpeed initialized together',
    'homeostasis':'One inference draw per trial initialization, reused at every phase start; training starts unchanged',
    'state_preservation':'Phase memory, pose, availability, timers and harvest state preserved; full resets clear memory',
    'checks':[{'label':c['label'],'expected_speed':c['expected_speed'],'actual_speed':c['speed'],
               'homeostatic_state':c['homeostatic_state'],'trial_start':c['trial_start']} for c in checks['checks']],
    'independent_trial_starts':checks['trial_starts'],
    'natural_trial':natural,
    'spawn_placement':'Native collision-checked teleport and walking mode settle the floor before velocity assignment; fresh forward input prevents braking after reset clears previous input.',
    'first_five_frame_speeds':[sum(v*v for v in s['velocity'])**.5 for s in first_frame['ticks']],
    'unchanged_assets':preserved,
    'production_compile_success': 'PHASE_VELOCITY_COMPILED' in (root/'production_compile.log').read_text(),
}
assert report['production_compile_success']
Path('analysis/timing/phase_initialization_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Phase initialization validated:',len(checks['checks']),'checks and one complete natural trial')

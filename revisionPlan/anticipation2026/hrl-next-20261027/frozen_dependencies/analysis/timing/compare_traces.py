"""Compare traces by actual simulation tick, rejecting missing/duplicate steps."""
import json
import math
from pathlib import Path

root=Path('Saved/TimingFix')
def read(name):
    rows=[json.loads(line) for line in (root/(name+'.jsonl')).read_text(encoding='utf-8').splitlines()]
    assert rows[-1].get('reason')=='complete', (name,rows[-1])
    frames=[r for r in rows if 'total_ticks' in r]
    by_tick={r['total_ticks']:r for r in frames}
    assert len(frames)==len(by_tick)==200, (name,len(frames),len(by_tick))
    assert list(by_tick)==list(range(1,201)), (name,list(by_tick)[:5])
    return by_tick

a,b=read('fixed_headless'),read('fixed_visible')
report={'decisions':200, 'comparison':'rendered PIE vs -nullrhi PIE; frozen embedded networks; FixedSeed', 'max_absolute_errors':{}}
for field in ['delta','sim_time','max_walk_speed','yaw','control_yaw','h','period_count']:
    report['max_absolute_errors'][field]=max(abs(a[t][field]-b[t][field]) for t in a)
for field in ['position','velocity','action']:
    report['max_absolute_errors'][field]=max(math.dist(a[t][field],b[t][field]) for t in a)
report['timestep']=sorted(set(r['delta'] for r in a.values()))
report['speed_limit']=sorted(set(r['max_walk_speed'] for r in a.values()))
report['measured_max_speed']=max(math.hypot(*r['velocity'][:2]) for r in a.values())
report['local_player_controller']=all(r['is_local'] and r['controller_class']=='PlayerController' for r in list(a.values())+list(b.values()))
report['mode_flags_consistent']=all(r['run_inference'] and not r['is_training'] for r in list(a.values())+list(b.values()))
report['period_count_at_200']=a[200]['period_count']
report['sim_time_at_200']=a[200]['sim_time']
report['same_initial_state']=a[1]['position']==b[1]['position'] and a[1]['h']==b[1]['h']
report['exact_match']=all(v==0 for v in report['max_absolute_errors'].values())
assert all(abs(dt-.05)<1e-7 for dt in report['timestep'])
assert report['speed_limit']==[1000.0]
assert report['exact_match'], report
(root/'comparison.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

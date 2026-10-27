"""Compare current-project controlled movement traces without speed assumptions."""
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'Saved/MovementAudit'
def read(name):
    rows=[json.loads(x) for x in (root/(name+'.jsonl')).read_text().splitlines()]
    assert rows[-1].get('reason')=='complete', (name,rows[-1])
    samples=[x for x in rows if 'total_ticks' in x]
    assert [x['total_ticks'] for x in samples]==list(range(1,201)), (name,'missing ticks')
    return samples

def summary(s):
    simulated=s[-1]['sim_time']-s[0]['sim_time']
    wall=s[-1]['wall_seconds']-s[0]['wall_seconds']
    distance=sum(math.dist(a['position'],b['position']) for a,b in zip(s,s[1:]))
    return {'decisions':len(s),'delta':sorted(set(x['delta'] for x in s)),
            'base_max_speed':sorted(set(x['base_max_speed'] for x in s)),
            'max_walk_speed':sorted(set(x['max_walk_speed'] for x in s)),
            'max_horizontal_velocity':max(math.hypot(*x['velocity'][:2]) for x in s),
            'distance_cm':distance,'distance_per_sim_second':distance/simulated,
            'sim_seconds':simulated,'wall_seconds':wall,'sim_to_wall_ratio':simulated/wall}

def compare(a,b):
    differences={}
    for k in ['delta','base_max_speed','max_walk_speed','yaw','control_yaw','h','period_count']:
        differences[k]=max(abs(x[k]-y[k]) for x,y in zip(a,b))
    for k in ['position','velocity','action']:
        differences[k]=max(math.dist(x[k],y[k]) for x,y in zip(a,b))
    differences['elapsed_sim_time']=max(abs((x['sim_time']-a[0]['sim_time'])-(y['sim_time']-b[0]['sim_time'])) for x,y in zip(a,b))
    return {'max_absolute_errors':differences,'exact_match':all(v==0 for v in differences.values()),
            'startup_world_time_offset':b[0]['sim_time']-a[0]['sim_time'],
            'same_initial_state':a[0]['position']==b[0]['position'] and a[0]['h']==b[0]['h']}

if __name__=='__main__':
    labels=['rendered_pie','headless_pie','headless_game','headless_game_uncapped']
    traces={k:read(k) for k in labels}
    report={'checkpoint':json.loads((root/'checkpoint.json').read_text()),
            'modes':{k:summary(v) for k,v in traces.items()},
            'comparisons':{k:compare(traces['rendered_pie'],traces[k]) for k in labels[1:]}}
    (root/'comparison.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

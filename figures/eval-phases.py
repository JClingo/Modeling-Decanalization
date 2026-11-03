"""Run against a checkout of github.com/JClingo/decanalization: python3 eval-phases.py <repo> <out.json>, then collapse to phases-inputs.json.
Per-phase CCC vs CDR (boost 1, d 1) outcomes for the four stable-trained seeds per family,
64 paired trials (eval seeds 5000-5063), changing world. Mirrors eval_policies.run."""
import json,sys,os,statistics as st
from multiprocessing import Pool
CODE=sys.argv[1];OUT=sys.argv[2]
sys.path.insert(0,os.path.join(CODE,'model'))
import numpy as np
from mapagent import MapParams
from world import phase_dose
from policy_agent import OptionTrial
from settings import WORLD
TAGS=['_stable','_stable_s1','_stable_s2','_stable_s3']

def run(args):
    family,tag,seed,arm=args
    w=list(np.load(os.path.join(CODE,'results','policies',f'policy_{family}{tag}.npz')).values())
    p=MapParams(**WORLD)
    dose=phase_dose(p,'DOSE',1.,100.) if arm=='CDR' else phase_dose(p,'CCC')
    t=OptionTrial(p,seed,dose,family,w,temp_boost=1. if arm=='CDR' else 0.).run()
    a,b,c=p.phases;bounds=[(0,a),(a,a+b),(a+b,a+b+c)];S=t.log['samples'];H=t.log['harvests']
    ph=lambda lo,hi:[s for s in S if lo<s[0]<=hi]
    r=dict(mae=[float(st.mean(abs(s[3]) for s in ph(*bd))) for bd in bounds],
           mean_h=[float(st.mean(s[3] for s in ph(*bd))) for bd in bounds],
           trapped=[bool(min(s[3] for s in ph(*bd))<=-100) for bd in bounds],
           harvests=[sum(1 for h in H if lo<h[0]<=hi) for lo,hi in bounds],
           rich=[sum(1 for h in H if h[1] in t.rich and lo<h[0]<=hi) for lo,hi in bounds])
    return family,tag,seed,arm,r

if __name__=='__main__':
    os.chdir(os.path.join(CODE,'model'))
    jobs=[(f,tg,s,arm) for f in ('HRL','NF') for tg in TAGS for s in range(5000,5064) for arm in ('CCC','CDR')]
    if len(sys.argv)>3: jobs=jobs[:int(sys.argv[3])]
    with Pool() as pool: done=pool.map(run,jobs)
    json.dump([dict(family=f,tag=tg,seed=s,arm=arm,**r) for f,tg,s,arm,r in done],open(OUT,'w'))
    print('done',len(done))

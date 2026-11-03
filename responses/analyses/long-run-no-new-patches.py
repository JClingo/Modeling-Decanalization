"""Exploratory run (Nov 3, 2026): the degrading world with no new patches, no intervention, 1,200 s.

All four stable-trained HRL policies, 64 trials each (evaluation seeds 5000-5063), plus the seed-0 policy in
the stable world for reference. Records, per 100 s bin, mean h, mean |h|, and min h for each trial.
Output: long-run-no-new-patches.json, a list of [policy tag, degrade (None = changing-world default,
0.0 = stable), evaluation seed, bins]. Summary in responses/notesForClingo.md.

Usage: python3 long-run-no-new-patches.py /path/to/decanalization/model output.json
Belongs eventually in the code repository's results/development/.
"""
import sys,json,os
MODEL=sys.argv[1]; sys.path.insert(0,MODEL); os.chdir(MODEL)
import numpy as np
from multiprocessing import Pool
from mapagent import MapParams
from policy_agent import OptionTrial
from settings import WORLD
from world import phase_dose
POL=os.path.join(MODEL,'..','results','policies')
def job(a):
    tag,world,seed=a
    W=list(np.load(os.path.join(POL,f'policy_HRL{tag}.npz')).values())
    p=MapParams(**dict(WORLD,**world))
    tr=OptionTrial(p,seed,phase_dose(p,'CCC'),'HRL',W).run()
    h=np.array([s[3] for s in tr.log['samples']])  # every 0.5 s
    bins=[(float(h[i:i+200].mean()),float(np.abs(h[i:i+200]).mean()),float(h[i:i+200].min())) for i in range(0,len(h),200)]
    return tag,world.get('degrade',None),seed,bins
if __name__=='__main__':
    deg=dict(rich_patches=0,phases=(300.,100.,800.))
    stab=dict(rich_patches=0,degrade=0.,phases=(300.,100.,800.))
    jobs=[(t,deg,s) for t in ('_stable','_stable_s1','_stable_s2','_stable_s3') for s in range(5000,5064)]+[('_stable',stab,s) for s in range(5000,5064)]
    with Pool(8) as pool: res=pool.map(job,jobs)
    json.dump(res,open(sys.argv[2],'w')); print(len(res))

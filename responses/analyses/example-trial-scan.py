"""Scan for the example trial in Figures 2 and 4 (Nov 3, 2026).

Runs all 64 paired trials (evaluation seeds 5000-5063) of the stable-trained HRL policy, training seed 0,
CCC vs CDR (d = 1, boost 1), and records per-phase mean |h|, mean h, min h, new-patch harvests and total
harvests. Seed 5020 is the trial whose per-phase mean h and new-patch harvests in both conditions are closest
to the averages over all 64 (squared differences, h scaled by 50 and harvests by 10).
Output: example-trial-scan.json, a list of [seed, CCC phases, CDR phases].

Usage: python3 example-trial-scan.py /path/to/decanalization/model output.json
"""
import sys,json,os
MODEL=sys.argv[1]; sys.path.insert(0,MODEL); os.chdir(MODEL)
import numpy as np
from multiprocessing import Pool
from mapagent import MapParams
from policy_agent import OptionTrial
from settings import WORLD
from world import phase_dose
W=list(np.load(os.path.join(MODEL,'..','results','policies','policy_HRL_stable.npz')).values())
B=(0,300,400,700)
def run(seed,arm):
    p=MapParams(**WORLD)
    if arm=='CCC': tr=OptionTrial(p,seed,phase_dose(p,'CCC'),'HRL',W)
    else: tr=OptionTrial(p,seed,phase_dose(p,'DOSE',1.0,100.0),'HRL',W,temp_boost=1.0)
    tr.run()
    out={}
    for ph,(lo,hi) in enumerate(zip(B,B[1:])):
        hs=[s[3] for s in tr.log['samples'] if lo<round(s[0],3)<=hi]
        new=sum(1 for hv in tr.log['harvests'] if lo<=round(hv[0],3)<hi and hv[1] in tr.rich)
        tot=sum(1 for hv in tr.log['harvests'] if lo<=round(hv[0],3)<hi)
        out[ph]=dict(mae=float(np.mean(np.abs(hs))),mh=float(np.mean(hs)),minh=float(min(hs)),new=new,tot=tot)
    return out
def both(seed): return seed,run(seed,'CCC'),run(seed,'CDR')
if __name__=='__main__':
    with Pool(8) as pool: res=pool.map(both,range(5000,5064))
    json.dump(res,open(sys.argv[2],'w'))
    print(len(res))

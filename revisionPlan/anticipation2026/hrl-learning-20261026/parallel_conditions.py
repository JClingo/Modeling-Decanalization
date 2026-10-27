"""Run the last two frozen conditions alongside the sequential controls.

Uses independent native processes and socket ports, not additional AI agents.
No training/reward settings change. The main dispatcher reuses completed
selection receipts when it reaches these conditions.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'learning/hrl'))
import run as native
from profiles import PROFILES
from study import Selector

def condition(name,port):
    protocol=native.read(HERE/'comparison_protocol.json');root=Path(protocol['raw_root'])
    profile=PROFILES[name];initial=[]
    for seed in protocol['training_seeds']:
        label=f'canalization-{name}-{seed}';selection=root/label/'selection.json'
        if selection.exists() and native.read(selection).get('complete'):
            print('REUSE '+label,flush=True);continue
        assert not (root/label).exists(),'Inspect incomplete run before restarting: '+label
        selector=Selector(protocol['minimum_gathers'],protocol['plateau_patience'])
        def callback(checkpoint):
            result=native.evaluate(root,label+'-validation-'+str(checkpoint['gathers']),profile,checkpoint,
                protocol['selection_trials'],protocol['selection_environment_seed'],continuous=True)
            stop=selector.update(result);native.write(selection,selector.record());return stop
        native.train(root,label,profile,seed,100000+seed,
            protocol['maximum_transitions_per_policy']//10000,protocol['checkpoint_every_gathers'],port,callback)
        record={**selector.record(),'complete':True,
                'termination':native.read(root/label/'trainer_complete.json')['reason']}
        assert record['best'];native.write(selection,record)
        initial.append({kind:native.sha(root/label/'initial'/(kind+'.bin')) for kind in ['policy','critic']})
        assert all(len({x[k] for x in initial})==len(initial) for k in ['policy','critic'])
    native.write(root/('parallel-'+name+'-complete.json'),dict(complete=True,condition=name,port=port,
        runner_sha256=native.sha(Path(__file__)),initial_hashes=initial))
    print('PARALLEL_CONDITION_COMPLETE '+name,flush=True)

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs=[executor.submit(condition,name,port) for name,port in [
            ('canalization-persistent',48660),('canalization-aware',48680)]]
        for job in jobs:job.result()

"""Retry the single communication failure; preserve all original evidence.

There is no resumable optimizer/world state. Reinitialize the same seed and
use the frozen training/selection contract, then run the independent comparison.
"""
from pathlib import Path
import os,shutil,subprocess,traceback
import compare
from study import Selector
from profiles import PROFILES

HERE=Path(__file__).resolve().parent

def main():
    native=compare.native;p=compare.protocol();root=Path(p['raw_root'])
    condition='canalization-aware';seed=3401
    original=f'canalization-{condition}-{seed}';label=original+'-retry1'
    assert not (root/label).exists(),'Inspect prior retry before another restart'
    assert not native.read(root/original/'engine_result.json')['passed']
    assert not native.read(root/original/'selection.json').get('complete',False)
    for name,expected in p['source_sha256'].items():
        assert native.sha(native.HERE/name)==expected,'Frozen runner changed: '+name
    archive=HERE/'attempts';archive.mkdir(exist_ok=True)
    for name in ['postprocessing_status.json','postprocessing_process.json']:
        source=HERE/name;target=archive/('initial-'+name)
        if source.exists() and not target.exists():shutil.copy2(source,target)
    native.write(HERE/'recovery.json',dict(
        reason='Unreal reported a communication timeout waiting for the policy at gather 162.',
        root_cause='Not established; no trainer exception receipt was written.',
        original_attempt=str(root/original),original_attempt_preserved=True,
        restart='From initial weights with the same seed; optimizer/world state was not saved.',
        settings_changed=False,execution='Single training workflow with its checkpoint evaluations.',
        run_directory_overrides={f'{condition}:{seed}':label},
        script_sha256=native.sha(Path(__file__))))
    native.write(HERE/'postprocessing_process.json',dict(pid=os.getpid(),recovery_run=label))
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        native.write(HERE/'postprocessing_status.json',dict(status='retrying-training',completed_policies=11,total_policies=12,run=label))
        print('RECOVERY_STARTED '+label+' PID '+str(os.getpid()),flush=True)
        selector=Selector(p['minimum_gathers'],p['plateau_patience']);profile=PROFILES[condition]
        def callback(checkpoint):
            result=native.evaluate(root,label+'-validation-'+str(checkpoint['gathers']),profile,checkpoint,
                p['selection_trials'],p['selection_environment_seed'],continuous=True)
            stop=selector.update(result);native.write(root/label/'selection.json',selector.record());return stop
        native.train(root,label,profile,seed,100000+seed,
            p['maximum_transitions_per_policy']//10000,p['checkpoint_every_gathers'],48700,callback)
        record=dict(**selector.record(),complete=True,termination=native.read(root/label/'trainer_complete.json')['reason'])
        assert record['best'];native.write(root/label/'selection.json',record)
        native.write(HERE/'postprocessing_status.json',dict(status='independent-evaluation'))
        compare.evaluate()
        native.write(HERE/'postprocessing_status.json',dict(status='analyzing'))
        compare.summarize()
        native.write(HERE/'postprocessing_status.json',dict(status='plotting'))
        subprocess.run([str(native.PYTHON_ENV/'bin/python'),str(HERE/'plot.py')],check=True)
        native.write(HERE/'postprocessing_status.json',dict(status='complete',results=str(HERE/'results.json')))
    except BaseException:
        native.write(HERE/'postprocessing_status.json',dict(status='failed',recovery_run=label,error=traceback.format_exc()))
        raise

if __name__=='__main__':main()

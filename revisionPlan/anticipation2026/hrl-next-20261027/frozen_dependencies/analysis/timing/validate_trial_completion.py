"""Exercise real final-trial notification, suppressing desktop test dialogs."""
import json
from pathlib import Path
import runpy
import unreal

baseline=set(Path(unreal.Paths.project_saved_dir()).resolve().joinpath('TrialResults').glob('*.completed.json'))
context=runpy.run_path(str(Path(__file__).with_name('validate_trial_yaml.py')))
result=context['result']
assert result['passed'],result
import trial_notifications
if context['mode']:
    path=Path(result['path']).with_suffix('.completed.json')
    assert path.exists(),'No completion receipt'
    receipt=json.loads(path.read_text())
    assert receipt['status']=='completed' and receipt['results_saved']
    assert receipt['trials_completed']==receipt['trials_requested']==3
    assert receipt['results_file']==result['path']
    before=path.stat().st_mtime_ns
    gm=context['gm'];gm.set_editor_property('IsTrialMode',True,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    trial_notifications.notify_completed_trials()
    assert path.stat().st_mtime_ns==before,'Duplicate completion receipt'
    result['completion']=receipt
else:
    trial_notifications.notify_completed_trials()
    assert set(Path(unreal.Paths.project_saved_dir()).resolve().joinpath('TrialResults').glob('*.completed.json'))==baseline
result['completion_check_passed']=True
(context['root']/'completion_validation.json').write_text(json.dumps(result,indent=2))

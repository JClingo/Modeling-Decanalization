"""Recover the isolated zero-count editor startup; preserve all first-attempt logs.

The original dispatcher's zero worker stops at its failed audit and never
starts its queued half-exact evaluation. Other native children keep running.
"""
from pathlib import Path
import concurrent.futures,json,os,shutil,subprocess,time
import run_experiment as ex

p=ex.RUN/'worker-0/TestProject';dest=ex.RUN/'zero'
process=ex.read(dest/'native_audit_process.json')
pid=process['pid']
assert str(p/'ue_canalization.uproject') in process['arguments']
started=time.monotonic()
while True:
    status=subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
    if status.returncode or status.stdout.strip().startswith('Z'):break
    if time.monotonic()-started>300:raise RuntimeError('Original isolated audit did not stop within its guard')
    time.sleep(2)
assert not any((p/'Saved/TrialResults').iterdir()),'No scored zero trials should exist before recovery'
assert not (dest/'verified.json').exists()
attempt=dest/'startup-attempt-1';attempt.mkdir()
for name in ['native_audit.log','native_audit.stdout','native_audit_process.json']:
    if (dest/name).exists():shutil.move(str(dest/name),attempt/name)
settings=ex.read(p/'evaluation_settings.json')
assert settings['condition']=='zero' and settings['trials']==250
tile=p/'Content/Level/BP_Tile.uasset';tilehash=ex.sha(tile)
assert tilehash==ex.sha(dest/'BP_Tile.compiled.uasset')
ex.write(ex.RUN/'zero_recovery.json',dict(stage='retrying-editor',original_pid=pid,
         reason='Concurrent disposable editor startup stalled before native audit and before scored trials',started_at=ex.stamp()))
ex.native(p,dest,'launch_validation.py','native_audit','audit',240)
report=ex.read(p.parent/'native_validation.json')
assert report['passed'] and report['condition']=='zero' and len(report['tests'])==15
assert ex.sha(tile)==tilehash
report['asset_sha256']=tilehash;report['asset_unchanged_after_audit']=True
ex.write(dest/'native_validation.json',report)
for name in ['live.json','runtime_result.json']:
    path=p.parent/name
    if path.exists():path.unlink()
catalog=ex.read(ex.EXPORT/'selected_policy_catalog.json')
ex.write(ex.RUN/'concurrency_amendment.json',dict(at=ex.stamp(),native_workers=5,
         rationale='Resource check: native games use about 277 MB resident memory each, 36 percent system memory free, ten CPU cores; fifth independent copy avoids serial half-exact batch',
         experimental_settings_unchanged=True))
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
    pending=pool.submit(ex.evaluate,4,'half-exact',catalog)
    print('START recovered zero 250 trials '+ex.stamp(),flush=True)
    ex.native(p,dest,'runtime.py','evaluation')
    if (p.parent/'runtime_result.json').exists():assert ex.read(p.parent/'runtime_result.json')['passed']
    zero=ex.verify_and_archive(p,dest,'zero',catalog,settings)
    half=pending.result()
ex.write(ex.RUN/'zero_recovery.json',dict(stage='complete',zero=zero,half_exact=half,at=ex.stamp()))
reports=[ex.read(ex.RUN/name/'verified.json') for name in ex.CONDITIONS]
assert all(r['passed'] and r['trials']==250 for r in reports)
for path,h in ex.read(ex.RUN/'source_preservation.json').items():assert ex.sha(path)==h
ex.write(ex.RUN/'complete.json',dict(passed=True,conditions=reports,source_preserved=True,
         recovered_startup=True,finished_at=ex.stamp()))
print('RECANALIZATION_COMPLETE_AFTER_STARTUP_RECOVERY',flush=True)

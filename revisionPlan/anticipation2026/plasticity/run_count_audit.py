"""Prepare/run one native count-rule audit, preserving every production worker."""
from pathlib import Path
import os,shutil,signal,subprocess,sys,time
import run_experiment as ex
p=ex.RUN/'count-audit'/'TestProject'
if '--stop-existing-audit' in sys.argv:
 for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
  parts=line.strip().split(None,1)
  if len(parts)==2 and parts[1].startswith(str(ex.EXE)+' ') and str(p/'ue_canalization.uproject') in parts[1]:
   os.kill(int(parts[0]),signal.SIGTERM)
   print('Stopped only the stalled disposable audit editor, PID '+parts[0],flush=True)
 time.sleep(3)
if not p.exists():
 p.mkdir(parents=True);template=ex.OLD/'HRL/TestProject'
 for folder in ['Content','Config','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
  shutil.copytree(template/folder,p/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
 shutil.copy2(template/'ue_canalization.uproject',p/'ue_canalization.uproject')
 (p/'COUNT_RULE_AUDIT_COPY').write_text('Disposable direct-event count-rule audit.\n')
 (p/'Intermediate').mkdir();(p/'Intermediate/PipInstall').symlink_to(ex.OLD/'python-env',target_is_directory=True)
else:
 assert '--retry-editor' in sys.argv and (p/'COUNT_RULE_AUDIT_COPY').exists()
 prefix='attempt-'+str(len(list(p.parent.glob('attempt-*-audit.stdout')))+1)+'-'
 for name in ['audit.log','audit.stdout']:
  path=p.parent/name
  if path.exists():path.rename(p.parent/(prefix+name))
tile=p/'Content/Level/BP_Tile.uasset';before=ex.sha(tile)
shutil.copy2(ex.HERE/'count_rule_native.py',ex.RUN/'count_rule_native.py')
shutil.copy2(ex.HERE/'launch_count_native.py',ex.RUN/'launch_count_native.py')
args=[str(ex.EXE),str(p/'ue_canalization.uproject'),'-ExecCmds=py '+str(ex.RUN/'launch_count_native.py'),'-DisablePipInstall','-nosound','-unattended','-nop4','-stdout','-FullStdOutLogOutput','-abslog='+str(p.parent/'audit.log')]
with (p.parent/'audit.stdout').open('w') as out:result=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT,timeout=240)
text=(p.parent/'audit.stdout').read_text(errors='replace');report=ex.read(p.parent/'count_rule_validation.json')
assert result.returncode==0 and report['passed'] and len(report['tests'])==17,text[-5000:]
assert ex.sha(tile)==before,'Temporary audit edits were saved unexpectedly'
report['asset_sha256']=before;report['asset_unchanged_after_audit']=True
ex.write(p.parent/'count_rule_validation.json',report)
shutil.copy2(p.parent/'count_rule_validation.json',ex.HERE/'count_rule_validation.json')
print('COUNT_RULE_AUDIT_COMPLETE: 17 native event-handler checks passed; original asset bytes preserved.')

"""Observe native completion and factor settings; never change simulated state."""
import json,pathlib,time,traceback,unreal
p=pathlib.Path(unreal.Paths.project_dir()).resolve();assert (p/'PLASTICITY_EVALUATION_COPY').exists()
s=json.loads((p/'evaluation_settings.json').read_text());started=time.monotonic();last=0;done=False
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
def write(name,obj):
 path=p.parent/name;tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2));tmp.replace(path)
def finish(error=None,metrics=None):
 global done
 if done:return
 done=True;write('runtime_result.json',dict(passed=error is None,error=error,metrics=str(metrics) if metrics else None,wall_seconds=time.monotonic()-started))
 unreal.unregister_slate_post_tick_callback(handle);unreal.SystemLibrary.execute_console_command(world,'QUIT')
def tick(dt):
 global last
 try:
  if time.monotonic()-last<2:return
  last=time.monotonic()
  if last-started>14400:raise RuntimeError('Evaluation exceeded four-hour guard')
  paths=list((p/'Saved/TrialResults').glob('*.metrics.json'))
  if not paths:return
  assert len(paths)==1
  path=paths[0];data=json.loads(path.read_text())
  complete=sum(len(t['phases'])==3 and all(x.get('complete') for x in t['phases']) for t in data['trials'])
  write('live.json',dict(factor=s['factor'],complete_trials=complete,trials=s['trials'],status=data['status'],wall_seconds=last-started))
  if data['status']=='failed':raise RuntimeError(data.get('error'))
  receipt=path.with_name(path.name.replace('.metrics.json','.completed.json'))
  if data['status']=='complete' and receipt.exists():
   r=json.loads(receipt.read_text());assert r['results_saved'] and r['trials_completed']==r['trials_requested']==s['trials']
   finish(metrics=path)
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)

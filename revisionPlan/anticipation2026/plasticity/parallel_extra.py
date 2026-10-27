"""Run the two queued conditions in independent copies alongside the first two.

Temporarily pause only the Python queue dispatcher, not its native Unreal
children. On completion resume it; its durable-result checks reuse the finished
factor-4/7 results instead of duplicating them. This changes concurrency only.
"""
from pathlib import Path
import concurrent.futures,json,os,shutil,signal,subprocess,traceback
import run_experiment as ex

def stop_handler(signum,frame):raise SystemExit('Parallel extension interrupted')
signal.signal(signal.SIGTERM,stop_handler)
def main():
 records=[ex.read(ex.RUN/f'factor-{f}/process.json') for f in [1,2]]
 parents=[int(subprocess.check_output(['ps','-p',str(r['pid']),'-o','ppid='],text=True).strip()) for r in records]
 assert parents[0]==parents[1] and parents[0]!=os.getpid()
 parent=parents[0]
 command=subprocess.check_output(['ps','-p',str(parent),'-o','command='],text=True)
 assert 'plasticity/run_experiment.py' in command,command
 catalog=ex.read(ex.EXPORT/'selected_policy_catalog.json')
 ex.write(ex.RUN/'parallel_extension.json',dict(stage='preparing',dispatcher_pid=parent,native_processes_unchanged=[r['pid'] for r in records],started_at=ex.stamp()))
 os.kill(parent,signal.SIGSTOP)
 try:
  for i in [2,3]:
   p=ex.RUN/f'worker-{i}'/'TestProject'
   assert not p.exists(),'Extra worker already exists; inspect its durable records before restarting'
   p.mkdir(parents=True);template=ex.OLD/'HRL/TestProject'
   for folder in ['Content','Config','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
    shutil.copytree(template/folder,p/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
   shutil.copy2(template/'ue_canalization.uproject',p/'ue_canalization.uproject')
   (p/'PLASTICITY_EVALUATION_COPY').write_text('Independent concurrent factor evaluation.\n')
   (p/'Intermediate').mkdir();(p/'Intermediate/PipInstall').symlink_to(ex.OLD/'python-env',target_is_directory=True)
   assert ex.sha(p/'Content/Agent/BP_Agent.uasset')==catalog['anticipation_asset_sha256']
  shutil.copy2(Path(__file__),ex.RUN/'parallel_extra.py')
  ex.write(ex.RUN/'parallel_extension.json',dict(stage='running',dispatcher_pid=parent,native_processes_unchanged=[r['pid'] for r in records],started_at=ex.stamp(),workers=4))
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   jobs=[pool.submit(ex.evaluate,2,4,catalog),pool.submit(ex.evaluate,3,7,catalog)]
   results=[job.result() for job in jobs]
  ex.write(ex.RUN/'parallel_extension.json',dict(stage='complete',dispatcher_pid=parent,results=results,finished_at=ex.stamp()))
 except BaseException:
  ex.write(ex.RUN/'parallel_extension_failure.json',dict(error=traceback.format_exc(),at=ex.stamp()))
  # Preserve failed logs/results before allowing the original dispatcher to
  # retry a queued factor in a different worker.
  for factor in [4,7]:
   dest=ex.RUN/f'factor-{factor}'
   if dest.exists() and not (dest/'verified.json').exists():
    dest.rename(ex.RUN/(f'aborted-extra-factor-{factor}-'+ex.stamp().replace(':','-')))
  raise
 finally:
  os.kill(parent,signal.SIGCONT)
  print('Original dispatcher resumed; existing durable results will be reused.',flush=True)
if __name__=='__main__':main()

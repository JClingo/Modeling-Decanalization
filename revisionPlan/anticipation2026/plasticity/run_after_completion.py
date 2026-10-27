"""Finish analysis after all native conditions have durable verified receipts."""
from pathlib import Path
import json,os,subprocess,sys,time,traceback
HERE=Path(__file__).resolve().parent
RUN=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization/Saved/AnticipationPlasticity20261026')
started=time.monotonic();last_print=0
def write(obj):
 p=HERE/'postprocess_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(p)
try:
 while not (RUN/'complete.json').exists():
  if (RUN/'failure.json').exists():raise RuntimeError((RUN/'failure.json').read_text())
  if time.monotonic()-started>18000:raise RuntimeError('Native completion did not arrive within the five-hour analysis guard')
  progress=[]
  for p in sorted(RUN.glob('worker-*/live.json')):
   x=json.loads(p.read_text());progress.append({k:x[k] for k in ['factor','complete_trials','trials']})
  write(dict(stage='waiting-for-native-completion',progress=progress))
  if time.monotonic()-last_print>300:
   print('Native progress: '+json.dumps(progress),flush=True);last_print=time.monotonic()
  time.sleep(15)
 write(dict(stage='import-and-analysis'))
 subprocess.run([sys.executable,str(HERE/'analyze.py'),'--import-run',str(RUN)],check=True,timeout=900)
 write(dict(stage='independent-verification-bootstrap-and-figures'))
 env=os.environ.copy();cache=Path('/private/tmp/codex-plasticity-font-cache');cache.mkdir(exist_ok=True);env['XDG_CACHE_HOME']=str(cache)
 subprocess.run(['/opt/homebrew/bin/Rscript','--vanilla',str(HERE/'bootstrap_and_plot.R'),str(HERE)],check=True,timeout=600,env=env)
 write(dict(stage='report'))
 subprocess.run([sys.executable,str(HERE/'write_report.py')],check=True,timeout=120)
 write(dict(stage='complete',passed=True,results=str(HERE/'RESULTS.md')))
 print('PLASTICITY_ANALYSIS_COMPLETE '+str(HERE/'RESULTS.md'),flush=True)
except BaseException:
 write(dict(stage='failed',error=traceback.format_exc()));raise

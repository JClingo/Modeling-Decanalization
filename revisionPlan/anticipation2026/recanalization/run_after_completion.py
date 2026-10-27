"""Run authorized dependent analysis after durable native completion exists."""
from pathlib import Path
import json,os,subprocess,sys,time,traceback

HERE=Path(__file__).resolve().parent
RUN=Path('/private/tmp/anticipation-recanalization-20261026')
status=HERE/'postprocess_status.json'
def write(stage,**details):
    tmp=status.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),**details),indent=2)+'\n')
    tmp.replace(status)
def execute(arguments):
    env=dict(os.environ,XDG_CACHE_HOME='/tmp/codex-r-cache')
    with (RUN/'postprocess.log').open('a') as out:
        subprocess.run(arguments,stdout=out,stderr=subprocess.STDOUT,check=True,env=env)
try:
    write('waiting_for_native_completion')
    started=time.monotonic()
    while not (RUN/'complete.json').exists():
        if time.monotonic()-started>14400:raise TimeoutError('Native completion did not arrive within four hours')
        time.sleep(5)
    assert json.loads((RUN/'complete.json').read_text())['passed']
    write('freezing_and_analyzing')
    execute([sys.executable,str(HERE/'analyze.py'),'--import-run',str(RUN)])
    write('independent_R_verification_and_figures')
    execute(['Rscript','--vanilla',str(HERE/'verify_and_plot.R'),str(HERE)])
    write('writing_report')
    execute([sys.executable,str(HERE/'write_report.py')])
    write('ready_for_visual_review',report=str(HERE/'RESULTS.md'))
    print('RECANALIZATION_ANALYSIS_READY_FOR_VISUAL_REVIEW',flush=True)
except Exception:
    write('failed',error=traceback.format_exc())
    raise

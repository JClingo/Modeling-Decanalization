"""One extra native seed workflow; publish only a completed future result.

The live sequential pipeline is unmodified. A completed future seed can be
reused through a directory alias, preserving every original absolute path.
"""
from pathlib import Path
import json,os,re,signal,subprocess,sys,threading,time,traceback
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import pipeline as study
native=study.native
ROOT=study.ROOT
LABEL='parallel-reward-absolute'
SEED=3401
ACTUAL=ROOT/f'next-{LABEL}-{SEED}'
CANONICAL=ROOT/f'next-reward-absolute-{SEED}'
STOP=threading.Event()
PRESSURE_ABORT=threading.Event()

def write_status(stage,**details):
    native.write(HERE/'parallel_status.json',dict(stage=stage,pid=os.getpid(),updated_at=native.stamp(),**details))
    print(stage+' '+json.dumps(details),flush=True)

def memory_free():
    result=subprocess.run(['/usr/bin/memory_pressure','-Q'],capture_output=True,text=True,timeout=10)
    match=re.search(r'System-wide memory free percentage:\s*(\d+)%',result.stdout)
    return int(match.group(1)) if match else None

def safety_watch():
    low=0
    while not STOP.wait(10):
        try:
            free=memory_free()
            primary=native.read(HERE.parent/'status.json')
            progress_path=ROOT/('next-'+primary.get('experiment','unknown')+'-'+str(primary.get('training_seed',0)))/'training_progress.json'
            progress=native.read(progress_path) if progress_path.exists() else None
            with (HERE/'resource_history.jsonl').open('a') as file:
                file.write(json.dumps(dict(time=native.stamp(),memory_free_percent=free,
                    main_stage=primary['stage'],main_training_progress=progress))+'\n')
            low=low+1 if free is not None and free<15 else 0
            if low<2:continue
            PRESSURE_ABORT.set()
            # Terminate only this helper's native children. Partial evidence
            # stays under its distinct prefix and is never published.
            owned=list(ROOT.glob(ACTUAL.name+'*'))+list(ROOT.glob('next-'+ACTUAL.name+'*'))
            listing=subprocess.run(['/bin/ps','-axo','pid=,command='],capture_output=True,text=True,timeout=10)
            for line in listing.stdout.splitlines():
                parts=line.strip().split(None,1)
                if len(parts)!=2:continue
                pid,command=parts
                if any(str(folder/'TestProject') in command for folder in owned):
                    try:os.kill(int(pid),signal.SIGTERM)
                    except ProcessLookupError:pass
            write_status('stopped-for-memory-pressure',memory_free_percent=free,primary_pipeline_untouched=True)
            return
        except Exception as error:
            native.write(HERE/'resource_monitor_warning.json',dict(error=str(error)))

def safe_to_publish():
    state=native.read(HERE.parent/'status.json')
    if state.get('stage')!='training' or state.get('experiment')!='reward-absolute':return False
    if state.get('training_seed')==1201:return True
    if state.get('training_seed')==2301:
        path=ROOT/'next-reward-absolute-2301/training_progress.json'
        # A full remaining gather/validation margin prevents publication while
        # the primary pipeline could be entering the target seed.
        return not path.exists() or native.read(path)['steps']<1500000
    return False

def main():
    p=study.prepare()
    assert not ACTUAL.exists() and not CANONICAL.exists(),'Inspect existing acceleration attempt before retrying'
    free=memory_free()
    assert free is not None and free>=25,'Insufficient memory headroom for an extra workflow'
    assert safe_to_publish(),'Primary pipeline is too close to this future seed'
    native.write(HERE/'parallel_plan.json',dict(
        purpose='Execution-only acceleration requested by the user; no scientific settings change',
        maximum_additional_workflows=1,training_seed=SEED,environment_seed=100000+SEED,
        profile=study.PROFILES['absolute-25'].contract(),protocol_sha256=native.sha(HERE.parent/'protocol.json'),
        script_sha256=native.sha(Path(__file__)),socket_port=48780,actual_run=str(ACTUAL),
        future_alias=str(CANONICAL),model_and_world_resume=False,
        memory_guard='Require at least 25% system memory headroom at launch; stop extra native children after two readings below 15%',
        reuse='Publish a directory symlink only after durable verified completion, while the primary pipeline is still safely ahead of this seed'))
    native.write(HERE/'parallel_process.json',dict(pid=os.getpid(),started_at=native.stamp()))
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    # These changes are confined to this process. The live primary process and
    # frozen source files retain their original status writer and socket port.
    study.status=lambda stage,**details:write_status(stage,**details)
    original_train=native.train
    def extra_train(*args,**kwargs):
        args=list(args);args[7]=48780
        return original_train(*args,**kwargs)
    native.train=extra_train
    watcher=threading.Thread(target=safety_watch,daemon=True);watcher.start()
    try:
        record=study.training(LABEL,study.PROFILES['absolute-25'],SEED,p)
        assert not PRESSURE_ABORT.is_set()
        assert record['complete'] and native.read(ACTUAL/'training_verified.json')['passed']
        assert record['profile']==study.PROFILES['absolute-25'].contract()
        if not CANONICAL.exists() and safe_to_publish():
            CANONICAL.symlink_to(ACTUAL,target_is_directory=True)
            native.write(HERE/'published_alias.json',dict(passed=True,alias=str(CANONICAL),
                actual=str(ACTUAL),absolute_checkpoint_paths_preserved=True,selection_sha256=native.sha(ACTUAL/'selection.json')))
            write_status('complete-and-published',actual_run=str(ACTUAL),alias=str(CANONICAL))
        else:
            write_status('complete-not-published',reason='Primary pipeline reached the target; its own attempt remains authoritative',actual_run=str(ACTUAL))
    except BaseException:
        if not PRESSURE_ABORT.is_set():write_status('failed',error=traceback.format_exc(),primary_pipeline_untouched=True)
        raise
    finally:
        STOP.set();watcher.join(timeout=15)

if __name__=='__main__':main()

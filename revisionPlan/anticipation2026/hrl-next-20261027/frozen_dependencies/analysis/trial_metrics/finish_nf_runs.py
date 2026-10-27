"""Wait for the authorized NF-CDR run, then execute and import NF-CCC.

Status is atomically written under Saved/NFControl20261017. Does not commit:
analysis, editorial review, and publication are completed by the owning chat.
"""
from pathlib import Path
import datetime,json,subprocess,time,traceback,sys
from collect_primary import collect
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT/'Saved/NFControl20261017'
CDR=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'Saved/TrialResults/NF-CDR-46379CD74E30DFBAC6A712BBC252E36A.metrics.json'
EXE=Path('D:/Dev/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')
PROJECT=WORK/'TestProject/ue_canalization.uproject'
status={}
def write(stage,**kw):
    status.update(stage=stage,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw)
    p=WORK/'workflow_status.json';tmp=p.with_suffix('.tmp')
    for attempt in range(20):
        try:tmp.write_text(json.dumps(status,indent=2));tmp.replace(p);break
        except PermissionError:
            if attempt==19:raise
            time.sleep(.1)
try:
    write('waiting-for-cdr',cdr=str(CDR))
    while True:
        d=json.loads(CDR.read_text());complete=sum(len(t['phases'])==3 and all(p.get('complete') for p in t['phases']) for t in d['trials'])
        write('waiting-for-cdr',cdr_trials_complete=complete)
        assert d['status']!='failed',d.get('error')
        if d['status']=='complete' and CDR.with_suffix('').with_suffix('.completed.json').exists():break
        time.sleep(15)
    cdr_id=collect(CDR,'NF','cdr');write('cdr-imported',cdr_run_id=cdr_id)
    results=WORK/'TestProject/Saved/TrialResults';before=set(results.glob('*.metrics.json'))
    args=[str(EXE),str(PROJECT),'/Game/Level/Landscape','-game','-EnablePlugins=PythonScriptPlugin','-DisablePipInstall','-UseFixedTimeStep','-FPS=20','-NoVSync','-NoTrialCompletionDialog','-nullrhi','-nosound','-unattended','-nop4','-abslog='+str(WORK/'ccc.log')]
    with (WORK/'ccc.stdout.log').open('w') as out:
        process=subprocess.Popen(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        write('running-ccc',ccc_pid=process.pid,arguments=args)
        while process.poll() is None:
            files=set(results.glob('*.metrics.json'))-before
            if len(files)==1:
                file=next(iter(files));d=json.loads(file.read_text());record=d['provenance'].get('matched-training-record')
                assert record and record['reward-family']=='NF' and record['snapshot-update-label']==5000
                assert d['provenance']['environment']['TrialSequenceOrder']=='ccc'
                assert d['provenance']['environment']['TrialsToRun']==250
                write('running-ccc',ccc_metrics=str(file),ccc_trials_complete=sum(len(t['phases'])==3 and all(p.get('complete') for p in t['phases']) for t in d['trials']))
            time.sleep(15)
    assert process.returncode==0,process.returncode
    files=set(results.glob('*.metrics.json'))-before;assert len(files)==1
    ccc_id=collect(next(iter(files)),'NF','ccc')
    selection={'HRL-CDR':'HRL-CDR-6C224C4240886C1BAEB3EF9EFCE7DE7E','HRL-CCC':'HRL-CCC-A137EBFA4FB0CC61D2F3D6AD20FCE332','NF-CDR':cdr_id,'NF-CCC':ccc_id}
    (ROOT/'analysis/paper-update-2026-10-17-reruns/selection.json').write_text(json.dumps(selection,indent=2))
    write('ready-for-analysis',ccc_run_id=ccc_id,ccc_trials_complete=250)
except Exception:
    write('failed',error=traceback.format_exc());raise

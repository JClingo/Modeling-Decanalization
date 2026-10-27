"""Reproducible opt-in HRL preparation, native checks, training and evaluation."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,math,os,shutil,subprocess,sys,time
from dataclasses import replace
from profiles import PROFILES,STAGES,load_profile
from landscape import summarize_counts

HERE=Path(__file__).resolve().parent
SOURCE=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization')
OLD=SOURCE/'Saved/AnticipationRetrain20261025'
PYTHON_ENV=Path(os.environ.get('HRL_PYTHON_ENV',str(OLD/'python-env')))
EXE=Path('/Users/Shared/Epic Games/UE_5.5/Engine/Binaries/Mac/UnrealEditor-Cmd')
DOTNET=EXE.parents[2]/'Binaries/ThirdParty/DotNet/8.0.300/mac-arm64/dotnet'
ASSETCLI=Path('/private/tmp/anticipation-fix/bin/AssetAudit.dll')
KINDS=['encoder','policy','decoder','critic']

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def copy_code(project):
    dest=project/'analysis/hrl_learning';dest.mkdir(parents=True,exist_ok=True)
    for path in HERE.glob('*.py'):shutil.copy2(path,dest/path.name)
def asset(root,*args):
    env=dict(os.environ,DOTNET_CLI_HOME=str(root/'dotnet-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
    subprocess.run([str(DOTNET),str(ASSETCLI),*map(str,args)],env=env,check=True,stdout=subprocess.DEVNULL)
def source_files():
    paths=[SOURCE/p for p in ['Content/Agent/BP_Agent.uasset','Content/Agent/BP_GameMode.uasset',
           'Content/Learning/BP_AgentManager.uasset','Content/Learning/BP_AgentTrainingEnv.uasset',
           'Content/Level/BP_Tile.uasset','Content/Level/Landscape.umap']]
    paths += [SOURCE/'analysis/anticipation-retrained-2026-10-25/policies/HRL'/(k+'.bin') for k in KINDS]
    return {str(p):sha(p) for p in paths}
def native(project,script,label,mode='compile',timeout=360,on_progress=None):
    root=project.parent
    if mode=='compile':flags=['-run=pythonscript','-script='+str(project/'analysis/hrl_learning'/script)]
    elif mode=='audit':flags=['-ExecCmds=py '+str(project/'analysis/hrl_learning'/script)]
    else:flags=['/Game/Level/Landscape','-game','-ExecCmds=py '+str(project/'analysis/hrl_learning'/script),'-EnablePlugins=PythonScriptPlugin']
    args=[str(EXE),str(project/'ue_canalization.uproject'),*flags,'-DisablePipInstall','-UseFixedTimeStep','-FPS=20',
          '-FixedSeed','-NoVSync','-NoTrialCompletionDialog','-nullrhi','-nosound','-unattended','-nop4',
          '-stdout','-FullStdOutLogOutput','-abslog='+str(root/(label+'.log'))]
    with (root/(label+'.stdout')).open('w') as out:
        process=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        write(root/(label+'_process.json'),dict(pid=process.pid,arguments=args,started_at=stamp()))
        try:
            if on_progress is None:code=process.wait(timeout=timeout)
            else:
                deadline=time.monotonic()+timeout
                while process.poll() is None:
                    if time.monotonic()>deadline:raise subprocess.TimeoutExpired(args,timeout)
                    on_progress()
                    try:process.wait(timeout=1)
                    except subprocess.TimeoutExpired:pass
                code=process.returncode
                on_progress()
        except BaseException:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=15)
            raise
    output=(root/(label+'.stdout')).read_text(errors='replace')
    if code or 'LogBlueprint: Error:' in output or 'LogPython: Error:' in output:
        raise RuntimeError(label+' failed:\n'+output[-6000:])
    return output

def baseline_snapshots():
    folder=SOURCE/'analysis/anticipation-retrained-2026-10-25/policies/HRL'
    return {kind:dict(path=str(folder/(kind+'.bin')),sha256=sha(folder/(kind+'.bin'))) for kind in KINDS}
def selected_reference():
    return dict(snapshots=baseline_snapshots(),steps=750000,gathers=75,profile=PROFILES['baseline'].contract(),
                policy_seed=1234,environment_seed=1,kind='preserved selected HRL policy; fixed benchmark, not a new training replicate')
def contract(profile,mode='train',**kwargs):
    return dict(profile=profile.contract(),mode=mode,policy_seed=1234,environment_seed=701,
                evaluation_seed=41001,trials=1,order='ccc',port=48620,max_gathers=2,checkpoint_every=1,
                engine_guard_seconds=1200,continuous_homeostasis=False,**kwargs)
def settings(profile,mode='train',**kwargs):
    result=contract(profile,mode);result.update(kwargs)
    if mode=='evaluate':result.setdefault('snapshots',baseline_snapshots())
    return result

def prepare(root):
    root.mkdir(parents=True,exist_ok=True)
    receipt=root/'prepared.json'
    if receipt.exists():
        assert read(root/'source_preservation.json')==source_files(),'Production baseline changed since preparation'
        return root/'template/TestProject'
    assert not (root/'template').exists(),'Incomplete preparation exists; inspect it before retrying in a fresh root'
    if shutil.disk_usage(root).free<2*1024**3:raise RuntimeError('Need at least 2 GiB free for isolated native copies')
    write(root/'source_preservation.json',source_files())
    project=root/'template/TestProject';project.mkdir(parents=True)
    bundle=HERE/'assets/manifest.json'
    template=SOURCE if bundle.exists() else OLD/'HRL/TestProject'
    for folder in ['Content','Config','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
        shutil.copytree(template/folder,project/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
    shutil.copy2(template/'ue_canalization.uproject',project/'ue_canalization.uproject')
    (project/'HRL_LEARNING_COPY').write_text('Opt-in HRL learning experiment.\n')
    (project/'ANTICIPATION_RETRAIN_COPY').write_text('Isolated HRL learning copy.\n')
    assert (PYTHON_ENV/'bin/python').is_file(),'Set HRL_PYTHON_ENV to the validated Python/Torch environment'
    (project/'Intermediate').mkdir();(project/'Intermediate/PipInstall').symlink_to(PYTHON_ENV,target_is_directory=True)
    copy_code(project)
    # Only this disposable metrics module receives the opt-in extension.
    with (project/'Content/Python/trial_metrics.py').open('a') as file:
        file.write("\n# Opt-in uniform native decision metrics.\nimport sys as _hrl_sys\n_hrl_sys.path.insert(0,str(Path(unreal.Paths.project_dir()).resolve()/'analysis/hrl_learning'))\nfrom trial_metrics_extension import install as _hrl_install\n_hrl_install(globals())\n")
    if bundle.exists():
        manifest=read(bundle)
        for path,expected in manifest['prerequisites'].items():assert sha(SOURCE/path)==expected,path
        for name,expected in manifest['assets'].items():
            path=HERE/'assets'/name;assert sha(path)==expected,name
            shutil.copy2(path,project/'Content/Learning'/name)
    else:
        native(project,'add_variables.py','add_variables')
        from patch_asset import patch
        from patch_manager import patch as patch_manager
        for name,function in [('BP_AgentTrainingEnv',patch),('BP_AgentManager',patch_manager)]:
            source=root/(name+'.variables.json');target=root/(name+'.patched.json')
            destination=project/'Content/Learning'/(name+'.uasset')
            asset(root,'export',destination,source)
            function(source,target,SOURCE/'analysis/timing')
            asset(root,'import',target,destination)
    write(project/'run_settings.json',settings(PROFILES['baseline'],'evaluate'))
    native(project,'configure.py','compile_authored_graphs')
    assert read(root/'source_preservation.json')==source_files()
    write(receipt,dict(passed=True,prepared_at=stamp(),source_hashes_preserved=True,
        template=str(project),code={p.name:sha(p) for p in HERE.glob('*.py')}))
    print('PREPARED '+str(project),flush=True)
    return project

def clone(root,name):
    template=prepare(root);project=root/name/'TestProject'
    assert not project.exists(),'Refusing to overwrite a prior run: '+str(project)
    project.mkdir(parents=True)
    for folder in ['Content','Config','analysis']:
        shutil.copytree(template/folder,project/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
    for name in ['ue_canalization.uproject','HRL_LEARNING_COPY','ANTICIPATION_RETRAIN_COPY']:
        shutil.copy2(template/name,project/name)
    (project/'Intermediate').mkdir();(project/'Intermediate/PipInstall').symlink_to(PYTHON_ENV,target_is_directory=True)
    copy_code(project)
    return project

def configure(project,profile,mode,**kwargs):
    data=settings(profile,mode,**kwargs);write(project/'run_settings.json',data)
    if 'inference_action_noise' in data or data.get('static_tile_costs'):
        from audit_variants import patch_variants
        patch_variants(project,data,asset,SOURCE/'analysis/timing')
    output=native(project,'configure.py','configure')
    assert 'HRL_LEARNING_CONFIGURED' in output
    write(project.parent/'code_manifest.json',{p.name:sha(p) for p in (project/'analysis/hrl_learning').glob('*.py')})
    return data

def validate(root):
    existing=sorted(root.glob('native-validation*/native_validation.json'))
    for path in existing:
        if read(path)['passed'] and sha(path.parent/'TestProject/analysis/hrl_learning/validate_native.py')==sha(HERE/'validate_native.py'):
            return read(path)
    name='native-validation' if not (root/'native-validation').exists() else 'native-validation-attempt-'+str(len(existing)+1)
    project=clone(root,name)
    configure(project,PROFILES['baseline'],'evaluate')
    native(project,'validate_native.py','native_validation','audit',240)
    receipt=read(project.parent/'native_validation.json');assert receipt['passed'],receipt
    print('NATIVE_VALIDATION_PASS '+str(len(receipt['cases']))+' cases',flush=True)
    return receipt

def train(root,name,profile,policy_seed=1234,environment_seed=701,max_gathers=200,checkpoint_every=10,port=48620,on_checkpoint=None,**overrides):
    project=clone(root,name)
    configure(project,profile,'train',policy_seed=policy_seed,environment_seed=environment_seed,
              max_gathers=max_gathers,checkpoint_every=checkpoint_every,port=port,engine_guard_seconds=8*3600,**overrides)
    seen=set()
    def progress():
        if (project.parent/'STOP').exists():return
        if on_checkpoint:
            for path in sorted((project.parent/'checkpoints').glob('*/checkpoint.json')):
                if path in seen:continue
                checkpoint=read(path)
                should_stop=on_checkpoint(checkpoint)
                seen.add(path)
                if should_stop:
                    write(project.parent/'STOP',dict(reason='held-out MAE plateau',gathers=checkpoint['gathers']))
                    break
    native(project,'runtime.py','training','game',8*3600+60,progress if on_checkpoint else None)
    receipt=read(project.parent/'engine_result.json');assert receipt['passed'],receipt
    completion=read(project.parent/'trainer_complete.json');assert completion['gathers']==max_gathers or (project.parent/'STOP').exists()
    assert read(project.parent/'native_environment.json')['passed']
    checkpoints=list((project.parent/'checkpoints').glob('*/checkpoint.json'));assert checkpoints
    last=read(sorted(checkpoints)[-1])
    initial=project.parent/'initial/policy.bin'
    assert last['snapshots']['policy']['sha256']!=sha(initial),'No native policy update'
    assert read(root/'source_preservation.json')==source_files()
    write(project.parent/'training_verified.json',dict(passed=True,completion=completion,policy_updated=True,
        initial_policy_sha256=sha(initial),checkpoints=len(checkpoints),last_checkpoint=str(sorted(checkpoints)[-1])))
    print('TRAINING_PASS '+name+' '+str(completion['steps'])+' transitions',flush=True)
    return last

def compact_evaluation(project):
    """Keep scored evidence and variant assets; remove only this finished copy."""
    destination=project.parent
    assert (project/'HRL_LEARNING_COPY').exists()
    assert not (destination/'TrialResults').exists()
    shutil.move(str(project/'Saved/TrialResults'),str(destination/'TrialResults'))
    for folder in ['analysis/hrl_learning','Config']:
        shutil.copytree(project/folder,destination/('code' if folder.startswith('analysis') else 'Config'),
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['run_settings.json','configured.json','ue_canalization.uproject']:
        shutil.copy2(project/name,destination/name)
    for name in ['Agent/BP_Agent.uasset','Agent/BP_GameMode.uasset','Learning/BP_AgentManager.uasset','Learning/BP_AgentTrainingEnv.uasset',
                 'Level/BP_Tile.uasset','Level/Landscape.umap']:
        target=destination/'native_assets'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(project/'Content'/name,target)
    shutil.rmtree(project)
    write(destination/'compacted.json',dict(passed=True,reason='Completed evaluation; raw scenes, loaded models, code, settings and variant assets retained'))

def evaluate(root,name,profile,checkpoint,trials=8,seed=41001,order='ccc',continuous=False,**overrides):
    if continuous and order!='ccc':raise ValueError('Continuous selection supports CCC only')
    if overrides.get('static_tile_costs') and order!='ccc':raise ValueError('Static-cost mechanism control is validated for CCC only')
    project=clone(root,name)
    for item in checkpoint['snapshots'].values():assert sha(item['path'])==item['sha256']
    configure(project,profile,'evaluate',snapshots=checkpoint['snapshots'],trials=trials,evaluation_seed=seed,order=order,
              policy_seed=checkpoint.get('policy_seed',1234),environment_seed=checkpoint.get('environment_seed',701),
              continuous_homeostasis=continuous,**overrides)
    native_record=dict(**{'reward-family':'HRL','snapshot-update-label':checkpoint.get('gathers',0)*profile.updates,
        'snapshot-sha256':{k:checkpoint['snapshots'][k]['sha256'] for k in ['encoder','policy','decoder']},
        'trainer':'hrl_learning','training-transitions':checkpoint.get('steps',750000)},
        hrl_learning_profile=profile.contract())
    if checkpoint.get('kind','').startswith('preserved selected'):
        native_record=read(SOURCE/'analysis/anticipation-retrained-2026-10-25/policies/HRL/training_manifest.json')
        native_record.pop('held_out_selection',None)
        native_record['hrl-learning-evaluation-profile']=profile.contract()
        assert native_record['snapshot-sha256']=={k:checkpoint['snapshots'][k]['sha256'] for k in ['encoder','policy','decoder']}
    write(project/'Content/Python/trial_training_manifests.json',[native_record])
    native(project,'runtime.py','evaluation','game',max(900,trials*40))
    return verify_evaluation(project,profile,checkpoint,trials,seed,order,continuous)

def verify_evaluation(project,profile,checkpoint,trials,seed,order,continuous=False):
    root=project.parent.parent
    candidates=list((project/'Saved/TrialResults').glob('*.metrics.json'));assert len(candidates)==1
    path=candidates[0];data=read(path)
    receipt=read(path.with_name(path.name.replace('.metrics.json','.completed.json')))
    assert data['status']=='complete' and receipt['results_saved'] and receipt['trials_completed']==trials
    assert len(data['trials'])==trials
    provenance=data['provenance'];assert provenance['environment']['TrialSequenceOrder']==order
    settings=read(project/'run_settings.json')
    assert provenance['inference-action-noise']==settings.get('inference_action_noise',0.)
    assert provenance['environment']['TrialEnvironmentSeed']==seed
    for kind,item in provenance['snapshots'].items():
        assert item['loaded-sha256']==checkpoint['snapshots'][kind]['sha256']
        assert sha(path.parent/item['loaded-snapshot'])==item['loaded-sha256']
    results=[]
    for trial in data['trials']:
        assert len(trial['phases'])==3
        phases=[]
        for phase in trial['phases']:
            assert phase['complete'] and phase['decision-ticks']==2000
            uniform=phase['uniform-decision-metrics'];assert uniform['decision_samples']==2000
            blob=gzip.decompress((path.parent/phase['scene-file']).read_bytes())
            assert hashlib.sha256(blob).hexdigest()==phase['scene-sha256']
            scene=json.loads(blob);assert len(scene['tiles'])==2500
            assert all(tile['DecanalizationRateFactor']==1 for tile in scene['tiles'])
            traversal_blob=gzip.decompress((path.parent/phase['traversal-file']).read_bytes())
            assert hashlib.sha256(traversal_blob).hexdigest()==phase['traversal-sha256']
            traversal=json.loads(traversal_blob)
            assert traversal['tile_names']==[tile['name'] for tile in scene['tiles']]
            assert traversal['start']==[tile['OverlapCount'] for tile in scene['tiles']]
            assert phase['traversal-metrics']==traversal['metrics']
            recomputed=summarize_counts(traversal['end'],traversal['start'],static_tile_costs=settings.get('static_tile_costs',False))
            assert recomputed.keys()==traversal['metrics'].keys()
            for key,value in recomputed.items():
                actual=traversal['metrics'][key]
                assert actual is None if value is None else math.isclose(value,actual,rel_tol=1e-12,abs_tol=1e-12),(key,value,actual)
            phases.append(uniform)
        if continuous:
            assert data['hrl-learning-contract']['continuous_homeostasis']
            assert 'continuous CCC' in data['homeostatic-boundary-protocol']
            for previous,current in zip(trial['phases'],trial['phases'][1:]):
                assert math.isclose(current['initial-homeostatic-state'],previous['end-homeostatic-state'],rel_tol=1e-6,abs_tol=1e-5)
        results.append(dict(trial=trial['id'],time_mae=sum(p['time_mae'] for p in phases)/3,
                            fraction_within_5=sum(p['fraction_within_5'] for p in phases)/3,phases=phases))
    metric_name=path.name
    compact_evaluation(project)
    summary=dict(passed=True,trials=results,mean_time_mae=sum(t['time_mae'] for t in results)/trials,
                 mean_fraction_within_5=sum(t['fraction_within_5'] for t in results)/trials,
                 evaluation_seed=seed,order=order,checkpoint=checkpoint,metrics=str(project.parent/'TrialResults'/metric_name),profile=profile.contract())
    summary['continuous_homeostasis']=continuous
    summary['inference_action_noise']=settings.get('inference_action_noise',0.)
    summary['static_tile_costs']=settings.get('static_tile_costs',False)
    write(project.parent/'summary.json',summary)
    assert read(root/'source_preservation.json')==source_files()
    print('EVALUATION_PASS '+project.parent.name+' time MAE='+str(summary['mean_time_mae']),flush=True)
    return summary

def smoke(root):
    prepare(root);checks=validate(root)
    runs=[]
    cases=[('baseline',1234),('quality-10',1234),('absolute-25',1234),('guarded-log',1234),
           ('guarded-ratio',1234),('guarded-annealed',1234),('canalization-aware',1234),('canalization-aware',2301)]
    for index,(name,seed) in enumerate(cases):
        label='smoke-'+name+'-'+str(seed)
        checkpoint=train(root,label,PROFILES[name],policy_seed=seed,max_gathers=2,checkpoint_every=1,port=48620+index)
        runs.append(dict(name=label,checkpoint=checkpoint))
    initial=[read(root/f'smoke-canalization-aware-{seed}/training_verified.json')['initial_policy_sha256'] for seed in [1234,2301]]
    assert initial[0]!=initial[1],'Native constructor seeds did not change initialized weights'
    # Exercise both unchanged and absolute reward graphs over full trial phases.
    evaluations=[]
    for name in ['baseline','absolute-25','canalization-aware']:
        checkpoint=next(r['checkpoint'] for r in runs if r['name']=='smoke-'+name+'-1234')
        evaluations.append(evaluate(root,'evaluate-'+name,PROFILES[name],checkpoint,trials=1,seed=71001))
    write(root/'smoke_verified.json',dict(passed=True,native_cases=len(checks['cases']),training_runs=len(runs),
        native_initialization_seeds_verified=True,full_trial_evaluations=len(evaluations),uniform_decisions=18000,
        evaluations=evaluations,source_hashes_preserved=read(root/'source_preservation.json')==source_files()))
    print('HRL_LEARNING_SMOKE_COMPLETE',flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','validate','smoke','train','evaluate','reference','list'])
    parser.add_argument('--root',type=Path,default=Path('/private/tmp/hrl-learning-20261026'))
    parser.add_argument('--profile',choices=PROFILES,default='canalization-aware')
    parser.add_argument('--profile-json',type=Path);parser.add_argument('--reward-from',choices=STAGES['reward'])
    parser.add_argument('--name');parser.add_argument('--seed',type=int,default=1234);parser.add_argument('--environment-seed',type=int,default=701)
    parser.add_argument('--gathers',type=int,default=200);parser.add_argument('--checkpoint-every',type=int,default=10)
    parser.add_argument('--checkpoint',type=Path);parser.add_argument('--trials',type=int,default=8)
    parser.add_argument('--evaluation-seed',type=int,default=41001);parser.add_argument('--order',choices=['ccc','cdr'],default='ccc')
    parser.add_argument('--continuous',action='store_true',help='Carry h across CCC reporting windows')
    args=parser.parse_args();root=args.root.resolve()
    if args.command=='list':
        print(json.dumps(dict(stages=STAGES,profiles={k:v.contract() for k,v in PROFILES.items()}),indent=2));return
    profile=load_profile(read(args.profile_json)) if args.profile_json else PROFILES[args.profile]
    if args.reward_from:
        reward=PROFILES[args.reward_from];profile=replace(profile,reward=reward.reward,distance_scale=reward.distance_scale).validate()
    if args.command=='prepare':prepare(root)
    elif args.command=='validate':validate(root)
    elif args.command=='smoke':smoke(root)
    elif args.command=='train':
        if args.gathers<1 or args.checkpoint_every<1:parser.error('Training counts must be positive')
        train(root,args.name or 'train-'+profile.name+'-'+str(args.seed),profile,args.seed,args.environment_seed,args.gathers,args.checkpoint_every)
    elif args.command=='reference':
        evaluate(root,args.name or 'selected-reference-'+str(args.evaluation_seed),PROFILES['baseline'],selected_reference(),
                 args.trials,args.evaluation_seed,args.order,args.continuous)
    else:
        if args.checkpoint is None:parser.error('--checkpoint is required')
        if args.trials<1:parser.error('--trials must be positive')
        checkpoint=read(args.checkpoint)
        if args.profile_json is None:profile=load_profile(checkpoint['profile'])
        evaluate(root,args.name or 'eval-'+profile.name,profile,checkpoint,args.trials,args.evaluation_seed,args.order,args.continuous)

if __name__=='__main__':main()

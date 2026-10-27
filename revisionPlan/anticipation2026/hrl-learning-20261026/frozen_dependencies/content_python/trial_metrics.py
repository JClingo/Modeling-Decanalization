"""Versioned fixed-horizon trial metrics and reproducibility records.

Blueprints compute reward through TrainingEnv.GatherAgentReward at every decision.
Python runs only at phase boundaries and YAML checkpoints, never per decision.
"""
import datetime,gzip,hashlib,json,math,os,struct,subprocess,time
from pathlib import Path
import unreal

SCHEMA_VERSION=2
_runs={}
def get(o,name):return o.get_editor_property(name)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def packed(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def atomic(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    payload=json.dumps(value,indent=2,allow_nan=False)
    # Windows readers/antivirus can briefly prevent replacing an open file.
    # Retry only access conflicts; a persistent failure still aborts the run.
    for attempt in range(20):
        try:
            tmp.write_text(payload,encoding='utf-8');os.replace(tmp,path)
            return
        except PermissionError:
            if attempt==19:raise
            time.sleep(min(.05 * 2**attempt,.5))
def actors(world,folder,name):
    return unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,f'/Game/{folder}/{name}.{name}_C'))
def context():
    world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
    if not world or not unreal.GameplayStatics.get_game_mode(world):
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    gm=unreal.GameplayStatics.get_game_mode(world)
    if not gm or not get(gm,'IsTrialMode'):return None
    managers=actors(world,'Learning','BP_AgentManager')
    if not managers or not get(managers[0],'Run Inference'):return None
    name=get(gm,'TrialFileName')
    if not name:return None
    path=Path(unreal.Paths.convert_relative_path_to_full(name))
    return world,gm,managers[0],path
def values(obj,names):return {n:get(obj,n) for n in names}
def vector(v):return [float(v.x),float(v.y),float(v.z)]
def pose(a):
    rot=a.get_actor_rotation()
    return dict(position=vector(a.get_actor_location()),rotation=[rot.pitch,rot.yaw,rot.roll])
def rng_state(gm):
    # UE exposes InitialSeed but not the mutable Seed to Python. Recover the
    # full uint32 state from three draws on a COPY; the live stream never advances.
    # FRandomStream::GetFraction in UE 5.5 uses (Seed >> 9) after its LCG update.
    stream=get(gm,'RandomStream').copy()
    first=float(unreal.MathLibrary.random_float_from_stream(stream))
    # One native call is essential: Python marshals const struct arguments by value.
    rot=unreal.MathLibrary.random_rotator_from_stream(stream,True)
    f32=lambda v:struct.unpack('f',struct.pack('f',v))[0]
    high=round(first*(1<<23));a,c,mask=196314165,907633515,(1<<32)-1
    candidates=[]
    for low in range(512):
        s1=(high<<9)|low;s2=(a*s1+c)&mask;s3=(a*s2+c)&mask
        if f32((s2>>9)/(1<<23)*360)==rot.pitch and f32((s3>>9)/(1<<23)*360)==rot.roll:
            candidates.append((pow(a,-1,1<<32)*(s1-c))&mask)
    assert len(candidates)==1,'Could not recover unambiguous UE random stream state'
    check=get(gm,'RandomStream').copy()
    assert float(unreal.MathLibrary.random_float_from_stream(check))==first,'RNG capture advanced live state'
    return {'initial-seed':get(stream,'initial_seed'),'current-seed-uint32':candidates[0],
            'validation-first-fraction':first,'validation-rotation':[rot.yaw,rot.pitch,rot.roll],
            'capture':'UE5.5 LCG recovered from a copied stream; live RNG unchanged'}

def state(ctx):
    _,gm,_,path=ctx
    key=str(path)
    if key not in _runs:
        _runs[key]={'schema-version':SCHEMA_VERSION,'run-id':path.stem,'created-at-utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'status':'initializing','results-file':path.name,'trials':[],'definitions':{
                        'duration':'simulation seconds; 2000 decisions at dt=0.05 per phase',
                        'reward-total':'sum of actual TrainingEnv.GatherAgentReward outputs, once per inference decision',
                        'evaluation-boundary':'fixed horizon: no training terminal penalty/cutoff; reset transitions excluded from NF progress',
                        'setpoint-dev':'population standard deviation sqrt(sum((h-mean(h))^2)/N)',
                        'homeostasis-sampling':'GameMode.Setpoints history, including seeded state and event/update samples; not a uniformly timed decision trajectory',
                        'policy-replication':'repeated evaluations of selected policies, not independent training replicates'}}
    return _runs[key]
def metadata(ctx):
    world,gm,m,path=ctx;run=state(ctx)
    if 'provenance' in run:return
    project=Path(unreal.Paths.project_dir()).resolve();artifact=path.with_suffix('.provenance');artifact.mkdir(exist_ok=True)
    snapshots={}
    for kind,field in [('encoder','EncoderSnapshot'),('policy','PolicySnapshot'),('decoder','Decoder Snapshot')]:
        declared=get(get(m,field),'file_path')
        candidates=[Path(unreal.Paths.convert_relative_path_to_full(declared)),(project/declared).resolve()]
        # UE FilePath is commonly relative to the engine executable working directory.
        resolved=next((p for p in candidates if p.is_file()),None)
        destination=artifact/(kind+'.bin')
        network=unreal.load_asset('/Game/Learning/DA_Agent'+kind.title())
        network.save_network_to_snapshot(unreal.FilePath(file_path=str(destination)))
        assert destination.is_file(),f'Failed to capture loaded {kind}'
        snapshots[kind]={'declared-path':declared,'resolved-path':str(resolved) if resolved else None,
                         'declared-file-sha256':digest(resolved) if resolved else None,
                         'loaded-snapshot':str(destination.relative_to(path.parent)), 'loaded-sha256':digest(destination)}
    manifests=json.loads((Path(__file__).parent/'trial_training_manifests.json').read_text(encoding='utf-8'))
    matches=[entry for entry in manifests if all(entry['snapshot-sha256'][k]==snapshots[k]['loaded-sha256'] for k in snapshots)]
    agent=actors(world,'Agent','BP_Agent')[0]
    env=get(m,'TrainingEnv')
    assert get(env,'UseHomeostaticReward'),'Trial schema 2 requires the current HRL/NF objective'
    assetpaths=['Agent/BP_Agent','Agent/BP_GameMode','Learning/BP_AgentManager','Learning/BP_AgentInteractor',
                'Learning/BP_AgentTrainingEnv','Libraries/BFL_Common','Level/BP_Tile','Resource/BP_Resource','Resource/BP_ResourceSpawner']
    assets={a:digest(project/'Content'/(a+'.uasset')) for a in assetpaths}
    helpers={n:digest(Path(__file__).parent/n) for n in ['trial_metrics.py','trial_training_manifests.json']}
    try:commit=subprocess.check_output(['git','-c','core.fsmonitor=false','rev-parse','HEAD'],cwd=project,text=True,stderr=subprocess.DEVNULL,creationflags=0x08000000).strip()
    except Exception:commit=None
    run['provenance']={'engine-version':unreal.SystemLibrary.get_engine_version(),'project-git-commit':commit,
        'asset-sha256':assets,'logger-sha256':helpers,'snapshots':snapshots,
        'matched-training-record':matches[0] if len(matches)==1 else None,'training-record-match-count':len(matches),
        'environment':values(gm,['IsHRL','TrialSequenceOrder','TrialsToRun','TrainingEnvironmentSeed','TrialEnvironmentSeed','ActiveEnvironmentSeed','BasePassiveLossRate','PeriodTickLength','SpawnerGridWidth','SpawnerGridSpacing']),
        'agent':values(agent,['BaseMaxSpeed']),
        'reward-settings':values(env,['UseHomeostaticReward','RewardDistanceScale','HomeostaticRewardRate','HomeostaticFailureReward','Max Setpoint Distance','Max Time']),
        'phase-decision-ticks':2000,'simulation-dt-seconds':0.05,'phase-simulation-seconds':100,
        'runtime-manager-training-settings':str(get(m,'Trainer Training Settings')),
        'runtime-manager-process-settings':str(get(m,'Trainer Process Settings')),
        'inference-action-noise':0.0}
    run['status']='running'
def begin_phase():
    ctx=context()
    if not ctx:return
    try:
        world,gm,m,path=ctx;run=state(ctx);metadata(ctx)
        dt=unreal.GameplayStatics.get_world_delta_seconds(world)
        assert math.isclose(dt,.05,abs_tol=1e-7),f'Unexpected trial dt: {dt}'
        trial_id=int(get(gm,'TrialsRun'));env=get(m,'TrainingEnv');steps=int(get(env,'Episode Steps'))
        phase=steps//2000+1;assert phase in [1,2,3]
        trial=next((t for t in run['trials'] if t['id']==trial_id),None)
        if trial is None:
            assert phase==1,'Missing trial-start capture'
            trial={'id':trial_id,'reward-function':'HRL' if get(gm,'IsHRL') else 'NF','sequence-order':get(gm,'TrialSequenceOrder'),'phases':[]};run['trials'].append(trial)
        assert not any(p['sequence-idx']==phase for p in trial['phases']),'Duplicate phase start'
        agent=actors(world,'Agent','BP_Agent')[0];la=get(m,'LearningAgentsManager');aid=la.get_agent_id(agent)
        tiles=actors(world,'Level','BP_Tile');resources=actors(world,'Resource','BP_Resource')
        # Stable actor-name sorting makes each captured scene digest deterministic.
        scene={'agent':dict(**pose(agent),velocity=vector(agent.get_velocity())),
               'tiles':[dict(name=a.get_name(),**pose(a),**values(a,['OverlapCount','HomeostaticImpact','BaseHomeostaticImpact','DecanalizationRateFactor'])) for a in sorted(tiles,key=lambda x:x.get_name())],
               'resources':[dict(name=a.get_name(),**pose(a),**values(a,['BaseHomeostaticImpact','MaxHomeostaticImpact','RespawnRate','OverlapCount','HomeostaticImpact']),collision=a.get_actor_enable_collision(),hidden=get(a,'hidden'),respawn_timer_active=unreal.SystemLibrary.is_timer_active(a,'Respawn'),respawn_timer_remaining=unreal.SystemLibrary.get_timer_remaining_time(a,'Respawn')) for a in sorted(resources,key=lambda x:x.get_name())]}
        blob=packed(scene);scene_path=path.with_suffix('.provenance')/f'trial-{trial_id:04d}-phase-{phase}.scene.json.gz'
        scene_path.write_bytes(gzip.compress(blob,mtime=0))
        trial['phases'].append({'sequence-idx':phase,'start-decision-counter':int(get(gm,'TotalTickCount')),
            'start-reward-step':steps,'initial-homeostatic-state':get(gm,'TrialStartingHomeostaticState'),
            'observed-start-h':list(get(gm,'Setpoints'))[-1],'rng-start':rng_state(gm),
            'policy-memory-start':list(get(m,'Policy').get_memory_state(aid)),
            'scene-file':str(scene_path.relative_to(path.parent)),'scene-sha256':hashlib.sha256(blob).hexdigest(),
            'environment-tile-count':len(tiles),'environment-pellet-count':len(resources)})
        atomic(path.with_suffix('.metrics.json'),run)
    except Exception as error:fail(ctx,error)
def capture_phase():
    ctx=context()
    if not ctx:return
    try:
        _,gm,m,path=ctx;run=state(ctx);trial=next(t for t in run['trials'] if t['id']==int(get(gm,'TrialsRun')));phase=trial['phases'][-1]
        assert 'complete' not in phase,'Duplicate phase completion'
        h=[float(x) for x in get(gm,'Setpoints')];assert h and all(math.isfinite(x) for x in h)
        steps=int(get(get(m,'TrainingEnv'),'Episode Steps'))-phase['start-reward-step'];assert steps==2000,steps
        mean=sum(h)/len(h);sd=math.sqrt(sum((x-mean)**2 for x in h)/len(h))
        actual=float(get(gm,'TotalRewards'));assert math.isfinite(actual)
        phase.update({'complete':True,'decision-ticks':steps,'duration-seconds':steps*.05,'homeostatic-sample-count':len(h),
            'setpoint-avg':mean,'setpoint-dev':sd,'homeostatic-mae':sum(abs(x) for x in h)/len(h),
            'homeostatic-rms':math.sqrt(sum(x*x for x in h)/len(h)),
            'homeostatic-fraction-within-5':sum(abs(x)<=5 for x in h)/len(h),'reward-total':actual,
            'rng-end':rng_state(gm),'end-decision-counter':int(get(gm,'TotalTickCount'))})
        if len(run['trials'])==get(gm,'TrialsToRun') and all(len(t['phases'])==3 and all(p.get('complete') for p in t['phases']) for t in run['trials']):run['status']='complete'
        atomic(path.with_suffix('.metrics.json'),run)
    except Exception as error:fail(ctx,error)
def checkpoint():
    ctx=context()
    if not ctx:return
    try:
        _,_,_,path=ctx;run=state(ctx);atomic(path.with_suffix('.metrics.json'),run)
        # The native writer rewrites TrialYML first. Append top-level schema metadata,
        # keeping the existing trials/sequences schema compatible with YAML readers.
        with path.open('a',encoding='utf-8') as f:
            f.write(metadata_suffix(path))
    except Exception as error:fail(ctx,error)
def metadata_suffix(path):
    return ('\nschema-version: 2\nduration-unit: simulation-seconds\n'
            'reward-source: TrainingEnv.GatherAgentReward\nsetpoint-dev-definition: population-standard-deviation\n'
            'metadata-file: '+json.dumps(path.with_suffix('.metrics.json').name)+'\n')
def fail(ctx,error):
    world,_,_,path=ctx;run=state(ctx);run.update(status='failed',error=str(error));atomic(path.with_suffix('.metrics.json'),run)
    unreal.log_error('TRIAL_METRICS_FAILED: '+str(error));unreal.SystemLibrary.execute_console_command(world,'QUIT')
    raise error

# Opt-in uniform native decision metrics.
import sys as _hrl_sys
_hrl_sys.path.insert(0,str(Path(unreal.Paths.project_dir()).resolve()/'analysis/hrl_learning'))
from trial_metrics_extension import install as _hrl_install
_hrl_install(globals())

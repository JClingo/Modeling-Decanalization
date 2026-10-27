"""Attach uniform decision metrics to existing native phase receipts."""
import gzip,hashlib,json,math
from pathlib import Path
from metrics import COUNTERS, summarize
from landscape import summarize_counts

def install(namespace):
    import unreal
    settings_path=Path(unreal.Paths.project_dir()).resolve()/'run_settings.json'
    settings=json.loads(settings_path.read_text())
    continuous=settings.get('continuous_homeostasis',False)
    if continuous and settings.get('order','ccc')!='ccc':
        raise ValueError('Continuous learning selection is defined for CCC only')
    original_begin,original_capture=namespace['begin_phase'],namespace['capture_phase']
    original_metadata=namespace['metadata']
    def metadata(ctx):
        original_metadata(ctx)
        namespace['state'](ctx)['provenance']['inference-action-noise']=settings.get('inference_action_noise',0.)
        namespace['state'](ctx)['provenance']['static-tile-costs']=settings.get('static_tile_costs',False)
    namespace['metadata']=metadata
    starts={}
    def begin():
        original_begin()
        ctx=namespace['context']()
        if not ctx:return
        try:
            world,gm,manager,_=ctx
            run=namespace['state'](ctx)
            trial=next(t for t in run['trials'] if t['id']==int(gm.get_editor_property('TrialsRun')))
            phase=trial['phases'][-1]
            policy=manager.get_editor_property('Policy')
            memory=list(policy.get_memory_state(0))
            phase['policy-memory-at-window-start']=dict(size=len(memory),squared_norm=sum(float(x)**2 for x in memory))
            trial.setdefault('initial-homeostatic-state',phase['initial-homeostatic-state'])
            env=manager.get_editor_property('TrainingEnv')
            excursion=float(env.get_editor_property('DecisionOutOfBandTime')) if continuous and phase['sequence-idx']>1 else 0.
            for name in COUNTERS:env.set_editor_property(name,0.)
            env.set_editor_property('DecisionOutOfBandTime',excursion)
            env.set_editor_property('RecordDecisionHomeostasis',True)
            tiles=sorted(namespace['actors'](world,'Level','BP_Tile'),key=lambda a:a.get_name())
            starts.clear()
            starts['names']=[a.get_name() for a in tiles]
            starts['counts']=[float(a.get_editor_property('OverlapCount')) for a in tiles]
        except Exception as error:namespace['fail'](ctx,error)
    def capture():
        original_capture()
        ctx=namespace['context']()
        if not ctx:return
        try:
            world,gm,manager,path=ctx;run=namespace['state'](ctx)
            if run['status']=='failed':return
            trial=next(t for t in run['trials'] if t['id']==int(gm.get_editor_property('TrialsRun')))
            phase=trial['phases'][-1];env=manager.get_editor_property('TrainingEnv')
            counters={name:float(env.get_editor_property(name)) for name in COUNTERS}
            result=summarize(counters)
            assert result['decision_samples']==phase['decision-ticks']==2000,result
            assert abs(result['duration_seconds']-100.)<1e-4,result
            phase['uniform-decision-metrics']=result
            end_h=float(list(gm.get_editor_property('Setpoints'))[-1])
            phase['end-homeostatic-state']=end_h
            tiles=sorted(namespace['actors'](world,'Level','BP_Tile'),key=lambda a:a.get_name())
            assert starts['names']==[a.get_name() for a in tiles]
            end=[float(a.get_editor_property('OverlapCount')) for a in tiles]
            traversal=summarize_counts(end,starts['counts'],static_tile_costs=settings.get('static_tile_costs',False))
            payload=dict(tile_names=starts['names'],start=starts['counts'],end=end,metrics=traversal)
            blob=namespace['packed'](payload)
            target=path.with_suffix('.provenance')/f"trial-{trial['id']:04d}-phase-{phase['sequence-idx']}.traversal.json.gz"
            target.write_bytes(gzip.compress(blob,mtime=0))
            phase['traversal-metrics']=traversal
            phase['traversal-file']=str(target.relative_to(path.parent))
            phase['traversal-sha256']=hashlib.sha256(blob).hexdigest()
            run['uniform-decision-metric-definition']='Post-update h recorded inside every native reward callback; dt-weighted, including out-of-bounds inference decisions.'
            contract_path=Path(unreal.Paths.project_dir()).resolve()/'run_settings.json'
            run['hrl-learning-contract']=json.loads(contract_path.read_text())
            if continuous:
                # The existing native phase-boundary code seeds its new h
                # history from this anchor. Updating it before that native
                # step preserves h while retaining per-window event histories.
                # This explicit opt-in is confined to the new learning protocol.
                # set_editor_property sends editor change notifications, which
                # reconstruct this live GameMode and erase its trial context.
                # The engine's object-scoped SETNOPEC updates only the anchor,
                # without Pre/PostEditChange. Verify the live value immediately.
                command=f'SETNOPEC {gm.get_path_name()} TrialStartingHomeostaticState {end_h:.17g}'
                unreal.SystemLibrary.execute_console_command(world,command)
                assert math.isclose(float(gm.get_editor_property('TrialStartingHomeostaticState')),end_h,rel_tol=1e-12,abs_tol=1e-12)
                run['homeostatic-boundary-protocol']='continuous CCC; prior end h seeds the next reporting window'
            namespace['atomic'](path.with_suffix('.metrics.json'),run)
        except Exception as error:namespace['fail'](ctx,error)
    namespace['begin_phase'],namespace['capture_phase']=begin,capture

"""Bounded native checks before the staged study; not performance evidence."""
from pathlib import Path
import json,shutil,sys
from dataclasses import replace
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'learning/hrl_next'))
import run as native
from profiles import PROFILES
ROOT=Path('/private/tmp/hrl-canalization-study-20261026')
sys.path.insert(0,str(HERE.parent/'hrl-learning-20261026'))
import share_scratch_storage as storage

def main():
    cases=[]
    for noise in [1.,0.]:
        name='next-engineering-noise'+str(int(noise))+'-20261027'
        receipt=ROOT/name/'summary.json'
        result=native.read(receipt) if receipt.exists() else native.evaluate(ROOT,name,PROFILES['baseline'],native.selected_reference(),
            trials=1,seed=43001,continuous=True,inference_action_noise=noise)
        assert result['passed'] and result['inference_action_noise']==noise
        cases.append(dict(name=name,passed=True))
    name='next-engineering-ratio-20261027';folder=ROOT/name
    if not (folder/'training_verified.json').exists():
        native.train(ROOT,name,PROFILES['ratio-only'],policy_seed=9231,environment_seed=109231,max_gathers=2,checkpoint_every=1,port=48740)
    assert native.read(folder/'training_verified.json')['passed']
    assert native.read(folder/'effective_config.json')['HRLLearning']['objective']=='ratio'
    cases.append(dict(name=name,passed=True))
    storage.main()
    name='next-engineering-curriculum-20261027';folder=ROOT/name
    if folder.exists() and not (folder/'training_verified.json').exists():
        assert (folder/'engine_result.json').exists() and not native.read(folder/'engine_result.json')['passed']
        name+='-retry1';folder=ROOT/name
    if not (folder/'training_verified.json').exists():
        native.train(ROOT,name,replace(PROFILES['baseline'],name='curriculum-engineering',episode_seconds=300.),
            policy_seed=9231,environment_seed=109231,max_gathers=2,checkpoint_every=1,port=48740,training_curriculum=True)
    assert native.read(folder/'training_verified.json')['passed']
    history=[json.loads(line) for line in (folder/'curriculum_history.jsonl').read_text().splitlines()]
    assert history[0]['stage']==0 and history[0]['seconds']==100.
    cases.append(dict(name=name,passed=True,initial_duration=history[0]['seconds']))
    storage.main()
    name='next-engineering-static-20261027';folder=ROOT/name
    prior=native.read(folder/'static_validation.json') if (folder/'static_validation.json').exists() else {}
    if not prior.get('passed') or not any(t['name'].startswith('physical static cost') for t in prior.get('tests',[])):
        project=folder/'TestProject'
        if not project.exists():
            project=native.clone(ROOT,name)
            native.configure(project,PROFILES['baseline'],'evaluate',static_tile_costs=True)
        else:
            assert (project/'HRL_LEARNING_COPY').exists()
            assert native.read(project/'configured.json')['static_tile_costs']
            attempts=folder/'harness_attempts';attempts.mkdir(exist_ok=True)
            number=len(list(attempts.glob('attempt-*')))+1;attempt=attempts/f'attempt-{number}';attempt.mkdir()
            for item in ['static_validation.json','static_validation.log','static_validation.stdout']:
                if (folder/item).exists():shutil.copy2(folder/item,attempt/item)
            # Preserve the failed commandlet harness; the actor-placement
            # subsystem requires a fully initialized editor session.
            for suffix in ['log','stdout']:
                old=folder/('static_validation.'+suffix)
                archive=folder/('static_validation.commandlet-failure.'+suffix)
                if old.exists() and not archive.exists():shutil.copy2(old,archive)
                elif old.exists():
                    archive=folder/('static_validation.editor-placement-failure.'+suffix)
                    if not archive.exists():shutil.copy2(old,archive)
        source=Path('/private/tmp/anticipation-fix/validate_anticipation.py').read_text()
        source=source.replace("OUT=pathlib.Path('/tmp/anticipation-fix/runtime_validation.json')", "OUT=pathlib.Path("+repr(str(folder/'static_validation.json'))+")")
        source=source.replace('denominator=count+(1 if enter<=1e-9 else 2)','denominator=2.')
        source=source.replace("['BaseHomeostaticImpact','OverlapCount']","['BaseHomeostaticImpact','OverlapCount','HomeostaticImpact','BP Game Mode']")
        source=source.replace("['PeriodTickLength','Setpoints','AnticipatedNets']","['PeriodTickLength','Setpoints','AnticipatedNets','IsDecanalized','Delta Seconds']")
        source=source.replace('actor=subsystem.spawn_actor_from_class(cls,v(location));assert actor is not None,path',
            "transform=unreal.Transform(location=v(location))\n  library=unreal.get_default_object(unreal.GameplayStatics)\n  actor=library.call_method('BeginDeferredActorSpawnFromClass',(world,cls,transform,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))\n  assert actor is not None,path\n  actor=library.call_method('FinishSpawningActor',(actor,transform,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))")
        physical=""" gm.set_editor_property('Delta Seconds',.05)
 for decanalized in [False,True]:
  gm.set_editor_property('IsDecanalized',decanalized)
  for count in [0.,3.,15.]:
   tile=spawn('/Game/Level/BP_Tile.BP_Tile',(10000+count*100,10000,0))
   tile.set_editor_property('BP Game Mode',gm)
   tile.set_editor_property('BaseHomeostaticImpact',10.)
   tile.set_editor_property('OverlapCount',count)
   tile.call_method('ReceiveActorBeginOverlap',(agent,))
   expected=0. if decanalized else .25
   check('physical static cost: decanalized='+str(decanalized)+' initial_count='+str(count),tile.get_editor_property('HomeostaticImpact'),expected)
   check('visit counter preserved: decanalized='+str(decanalized)+' initial_count='+str(count),tile.get_editor_property('OverlapCount'),count+1.)
"""
        source=source.replace(" assert all(t['passed']",physical+" assert all(t['passed']")
        (project/'analysis/hrl_learning/static_validation.py').write_text(source)
        launcher="""import unreal,time
started=time.monotonic()
def validate(delta):
    if time.monotonic()-started<2:return
    unreal.unregister_slate_post_tick_callback(handle)
    try:
        exec(compile(open(SOURCE).read(),SOURCE,'exec'),globals())
    finally:
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SystemLibrary.execute_console_command(world,'QUIT_EDITOR')
handle=unreal.register_slate_post_tick_callback(validate)
""".replace('SOURCE',repr(str(project/'analysis/hrl_learning/static_validation.py')))
        (project/'analysis/hrl_learning/launch_static_validation.py').write_text(launcher)
        native.native(project,'launch_static_validation.py','static_validation','audit',240)
    result=native.read(folder/'static_validation.json');assert result['passed']
    cases.append(dict(name=name,passed=True,checks=len(result['tests'])))
    name='next-engineering-static-trial-20261027';receipt=ROOT/name/'summary.json'
    result=native.read(receipt) if receipt.exists() else native.evaluate(ROOT,name,PROFILES['baseline'],native.selected_reference(),
        trials=1,seed=43001,continuous=True,inference_action_noise=0.,static_tile_costs=True)
    assert result['passed'] and result['static_tile_costs']
    cases.append(dict(name=name,passed=True))
    native.write(HERE/'engineering_verified.json',dict(passed=True,cases=cases,production_preserved=native.source_files()==native.read(ROOT/'source_preservation.json')))
    print('NEXT_ENGINEERING_PASS',flush=True)

if __name__=='__main__':main()

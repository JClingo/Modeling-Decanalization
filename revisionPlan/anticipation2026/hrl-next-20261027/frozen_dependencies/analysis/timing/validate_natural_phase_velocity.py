"""Run one complete real trial with production-default staged assets."""
import json
from pathlib import Path
import time
import traceback
import unreal
root=Path(unreal.Paths.project_dir()).resolve().parent
assert root.name=='PhaseVelocityFix'
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
gm=unreal.GameplayStatics.get_game_mode(world)
agent=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,'/Game/Agent/BP_Agent.BP_Agent_C'))[0]
result={'passed':False,'samples':[]};started=time.monotonic();last=None;done=False
def finish(error=None):
    global done
    if done:return
    done=True;result.update(passed=error is None,error=error,wall_seconds=time.monotonic()-started)
    (root/'natural_validation.json').write_text(json.dumps(result,indent=2))
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(world,'QUIT')
def tick(dt):
    global last
    try:
        if time.monotonic()-started>150:raise RuntimeError('Natural trial timed out')
        if gm.get_editor_property('TrialsRun')>=1:
            assert {s['phase'] for s in result['samples']}=={0,1,2}
            assert len({s['trial_start'] for s in result['samples']})==1
            finish();return
        count=gm.get_editor_property('TotalTickCount')
        phase=0 if count<6000 else (1 if count<12000 else 2)
        if phase!=last:
            last=phase
            result['samples'].append({'phase':phase,'tick':count,'speed':agent.get_velocity().length(),
                                      'max_speed':agent.get_editor_property('BaseMaxSpeed'),
                                      'trial_start':gm.get_editor_property('TrialStartingHomeostaticState'),
                                      'first_homeostatic_value':gm.get_editor_property('Setpoints')[0]})
            assert result['samples'][-1]['first_homeostatic_value']==result['samples'][-1]['trial_start']
            assert abs(result['samples'][-1]['speed']-result['samples'][-1]['max_speed'])<.01
            (root/'natural_validation.json').write_text(json.dumps(result,indent=2))
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)

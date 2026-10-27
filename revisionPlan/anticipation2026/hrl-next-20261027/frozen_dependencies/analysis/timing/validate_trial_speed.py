"""Measure actual frozen-policy trial time and compare decision trajectories."""
import json
from pathlib import Path
import time
import traceback
import unreal

project=Path(unreal.Paths.project_dir()).resolve()
assert project.name=='TestProject' and project.parent.name=='TrialSpeedFix'
args=unreal.SystemLibrary.get_command_line().split()
label=next(a.split('=',1)[1] for a in args if a.startswith('-SpeedLabel='))
full='-FullTrial' in args
root=project.parent
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
gm=unreal.GameplayStatics.get_game_mode(world)
manager_class=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class=unreal.load_class(None,'/Game/Agent/BP_Agent.BP_Agent_C')
manager=unreal.GameplayStatics.get_all_actors_of_class(world,manager_class)[0]
agent=unreal.GameplayStatics.get_all_actors_of_class(world,agent_class)[0]
assert manager.get_editor_property('Run Inference') and gm.get_editor_property('IsTrialMode')
started=time.monotonic();start_sim=unreal.GameplayStatics.get_time_seconds(world)
result={'label':label,'full_trial':full,'samples':[]};done=False
path=Path(unreal.Paths.convert_relative_path_to_full(gm.get_editor_property('TrialFileName')))
receipt=path.with_suffix('.completed.json')

def vec(v):return [v.x,v.y,v.z]
def finish(error=None):
 global done
 if done:return
 done=True
 elapsed=time.monotonic()-started
 simulated=unreal.GameplayStatics.get_time_seconds(world)-start_sim
 result.update(passed=error is None,error=error,wall_seconds=elapsed,simulated_seconds=simulated,speedup=simulated/elapsed)
 if receipt.exists():result['completion']=json.loads(receipt.read_text())
 (root/(label+'.json')).write_text(json.dumps(result,indent=2))
 unreal.unregister_slate_post_tick_callback(handle)
 unreal.SystemLibrary.execute_console_command(world,'QUIT')

def tick(dt):
 try:
  if time.monotonic()-started>90:raise RuntimeError('Trial speed test timeout')
  aid=manager.get_editor_property('LearningAgentsManager').get_agent_id(agent)
  action,_=manager.get_editor_property('Interactor').get_action_vector(aid)
  points=gm.get_editor_property('Setpoints')
  if len(result['samples'])<200:
   result['samples'].append({'delta':unreal.GameplayStatics.get_world_delta_seconds(world),
    'position':vec(agent.get_actor_location()),'velocity':vec(agent.get_velocity()),
    'yaw':agent.get_actor_rotation().yaw,'action':list(action),'homeostatic_state':points[-1] if points else None,
    'max_walk_speed':agent.get_editor_property('character_movement').get_editor_property('max_walk_speed')})
  if full:
   if receipt.exists():finish()
  elif len(result['samples'])>=200:finish()
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)

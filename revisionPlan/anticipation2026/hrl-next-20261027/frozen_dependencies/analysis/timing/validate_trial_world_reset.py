"""Validate dirty world state over repeated real trial and phase callbacks in a copy."""
import json
from pathlib import Path
import time
import traceback
import unreal

project=Path(unreal.Paths.project_dir()).resolve()
assert project.name=='TestProject' and project.parent.name=='TrialWorldResetFix'
root=project.parent
started=time.monotonic();done=False;ran=False
result={'passed':False,'trials':[]}
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
gm=unreal.GameplayStatics.get_game_mode(world)
def prop(o,n):return o.get_editor_property(n)
def actors(path):return unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,path))
def finish(error=None):
 global done
 if done:return
 done=True;result['passed']=error is None;result['error']=error
 (root/'validation.json').write_text(json.dumps(result,indent=2))
 unreal.unregister_slate_post_tick_callback(handle)
 unreal.SystemLibrary.execute_console_command(world,'QUIT')

def tick(dt):
 global ran
 try:
  if time.monotonic()-started>30:raise RuntimeError('Reset validator timeout')
  if prop(gm,'Delta Seconds')<=0:return
  manager=actors('/Game/Learning/BP_AgentManager.BP_AgentManager_C')[0]
  agent=actors('/Game/Agent/BP_Agent.BP_Agent_C')[0]
  resources=actors('/Game/Resource/BP_Resource.BP_Resource_C')
  tiles=actors('/Game/Level/BP_Tile.BP_Tile_C')
  la=prop(manager,'LearningAgentsManager');policy=prop(manager,'Policy');aid=la.get_agent_id(agent)
  if ran:
   assert all(not unreal.SystemLibrary.is_timer_active(r,'Respawn') for r in resources)
   assert all(not prop(r,'hidden') for r in resources)
   result['next_frame_clean']=True;finish();return
  ran=True
  manager.set_actor_tick_enabled(False);gm.set_actor_tick_enabled(False)
  def world_state():
   touching=set(agent.get_overlapping_actors(class_filter=unreal.load_class(None,'/Game/Level/BP_Tile.BP_Tile_C')))
   return {'tick_count':prop(gm,'TotalTickCount'),'trials_run':prop(gm,'TrialsRun'),
    'spawn_touching_tiles':len(touching),
    'nonzero_tile_impacts':sum(prop(t,'HomeostaticImpact')!=0 for t in tiles if t not in touching),
    'nonzero_tile_visits':sum(prop(t,'OverlapCount')!=0 for t in tiles if t not in touching),
    'hidden_pellets':sum(prop(r,'hidden') for r in resources),
    'collision_disabled_pellets':sum(not r.get_actor_enable_collision() for r in resources),
    'overlap_disabled_pellets':sum(not prop(prop(r,'Cylinder'),'generate_overlap_events') for r in resources),
    'active_respawn_timers':sum(unreal.SystemLibrary.is_timer_active(r,'Respawn') for r in resources),
    'nonzero_pellet_counts':sum(prop(r,'OverlapCount')!=0 for r in resources),
    'memory_max':max(abs(v) for v in policy.get_memory_state(aid)),
    'velocity':[agent.get_velocity().x,agent.get_velocity().y,agent.get_velocity().z],
    'setpoints':list(prop(gm,'Setpoints'))}
  result['world_counts']={'tiles':len(tiles),'pellets':len(resources)}
  for n in range(6):
   resource=resources[n];tile=tiles[n]
   tile.call_method('ReceiveActorBeginOverlap',args=(agent,))
   resource.call_method('ReceiveActorBeginOverlap',args=(agent,))
   resource.call_method('ReceiveActorEndOverlap',args=(agent,))
   policy.set_memory_state(aid,[.75]*policy.get_memory_state_size())
   assert prop(tile,'HomeostaticImpact')!=0
   assert prop(resource,'hidden') and unreal.SystemLibrary.is_timer_active(resource,'Respawn')
   case={'is_cdr':bool(n%2),'dirty':world_state(),'phase_checks':[]}
   # Natural phase transitions are allowed to change canalization effects;
   # they must retain pellet harvest state, timer and recurrent memory.
   for count in (6000,12000,18000):
    gm.set_editor_property('TotalTickCount',count,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    gm.call_method('RunTrial',args=(prop(gm,'TrialFileName'),bool(n%2)))
    assert prop(resource,'hidden')
    assert unreal.SystemLibrary.is_timer_active(resource,'Respawn')
    assert max(abs(v) for v in policy.get_memory_state(aid))==.75
    case['phase_checks'].append({'boundary':count,'state_preserved':True})
   # Also exercise recovery of disabled availability flags at full reset.
   resource.set_actor_enable_collision(False)
   prop(resource,'Cylinder').set_editor_property('generate_overlap_events',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
   gm.set_editor_property('TotalTickCount',18002,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
   gm.call_method('RunTrial',args=(prop(gm,'TrialFileName'),bool(n%2)))
   after=world_state();case['after']=after;result['trials'].append(case)
   for field in ['nonzero_tile_impacts','nonzero_tile_visits','hidden_pellets','collision_disabled_pellets','overlap_disabled_pellets','active_respawn_timers','nonzero_pellet_counts','memory_max','tick_count']:
    assert after[field]==0,(field,after)
   assert after['trials_run']==n+1
   # Full resets clear old motion, then initialize the new phase at maximum
   # forward speed (the phase-velocity requirement supersedes stationary starts).
   expected=agent.get_actor_forward_vector()*prop(agent,'BaseMaxSpeed')
   assert (agent.get_velocity()-expected).length()<.01
   assert len(after['setpoints'])==1
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)

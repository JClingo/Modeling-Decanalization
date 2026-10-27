"""Trace frozen-policy movement in isolated PIE or standalone game mode."""
import json
import pathlib
import time
import traceback
import unreal

project = pathlib.Path(unreal.Paths.project_dir()).resolve()
assert project.name == 'TestProject' and project.parent.name == 'MovementAudit'
root = project.parent
args = unreal.SystemLibrary.get_command_line()
label = next(x.split('=',1)[1] for x in args.split() if x.startswith('-MovementLabel='))
standalone = '-game' in args.split()
stream = (root/(label+'.jsonl')).open('w')
started = time.monotonic()
last_tick = None
frames = 0
done = False
manager_class = unreal.load_class(None, '/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class = unreal.load_class(None, '/Game/Agent/BP_Agent.BP_Agent_C')
if not standalone:
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    levels.load_level('/Game/Level/Landscape')

def emit(x):
    stream.write(json.dumps(x)+'\n')
    stream.flush()
def prop(o,n): return o.get_editor_property(n)
def vec(v): return [v.x,v.y,v.z]
def world_now():
    if standalone: return unreal.find_object(None, '/Game/Level/Landscape.Landscape')
    return editor.get_game_world()
def finish(reason, error=None):
    global done
    if done: return
    done = True
    emit({'event':'end','reason':reason,'error':error,'frames':frames,
          'wall_seconds':time.monotonic()-started})
    stream.close()
    unreal.unregister_slate_post_tick_callback(handle)
    world = world_now()
    if not standalone:
        levels.editor_request_end_play()
        world = editor.get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'QUIT' if standalone else 'QUIT_EDITOR')

def tick(dt):
    global last_tick, frames
    try:
        if time.monotonic()-started > 150:
            finish('timeout'); return
        world = world_now()
        if not world: return
        gm = unreal.GameplayStatics.get_game_mode(world)
        managers = unreal.GameplayStatics.get_all_actors_of_class(world, manager_class)
        agents = unreal.GameplayStatics.get_all_actors_of_class(world, agent_class)
        if not gm or not managers or not agents: return
        manager,agent = managers[0],agents[0]
        t = prop(gm,'TotalTickCount')
        if t<=0 or t==last_tick: return
        last_tick=t
        aid=prop(manager,'LearningAgentsManager').get_agent_id(agent)
        action,h=prop(manager,'Interactor').get_action_vector(aid)
        ctrl=agent.get_controller()
        points=prop(gm,'Setpoints')
        emit({'total_ticks':t,'sim_time':unreal.GameplayStatics.get_time_seconds(world),
              'delta':unreal.GameplayStatics.get_world_delta_seconds(world),
              'wall_seconds':time.monotonic()-started,'slate_delta':dt,
              'base_max_speed':prop(agent,'BaseMaxSpeed'),
              'max_walk_speed':prop(agent,'character_movement').get_editor_property('max_walk_speed'),
              'position':vec(agent.get_actor_location()),'velocity':vec(agent.get_velocity()),
              'yaw':agent.get_actor_rotation().yaw,
              'control_yaw':ctrl.get_control_rotation().yaw if ctrl else None,
              'action':list(action),'h':points[-1] if points else None,
              'period_count':prop(gm,'HomeostaticPeriodsElapsed'),
              'run_inference':prop(manager,'Run Inference'),'is_training':prop(gm,'IsTraining')})
        frames+=1
        if frames>=200: finish('complete')
    except Exception:
        finish('error',traceback.format_exc())

emit({'event':'start','label':label,'standalone':standalone,'command':args})
handle=unreal.register_slate_post_tick_callback(tick)
if not standalone: levels.editor_request_begin_play()

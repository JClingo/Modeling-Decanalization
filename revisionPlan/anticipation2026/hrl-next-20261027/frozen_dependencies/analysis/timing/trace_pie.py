"""Capture actual PIE simulation state; launch the editor with -ExecutePythonScript.

Use -TimingLabel=baseline_visible / baseline_headless / fixed_visible / fixed_headless.
Seed is controlled by -FixedSeed. Source assets/maps are never saved by this script.
"""
import json
import pathlib
import time
import traceback
import unreal

root = pathlib.Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())) / 'TimingFix'
args = unreal.SystemLibrary.get_command_line()
label = next((x.split('=', 1)[1] for x in args.split() if x.startswith('-TimingLabel=')), 'trace')
stream = (root / (label + '.jsonl')).open('w', encoding='utf-8')
started = time.monotonic()
frames = 0
last_tick = None
finishing = False

def emit(item):
    stream.write(json.dumps(item) + '\n')
    stream.flush()

def prop(obj, name):
    return obj.get_editor_property(name) if obj else None

def vec(v): return [v.x, v.y, v.z]

editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
manager_class = unreal.load_class(None, '/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class = unreal.load_class(None, '/Game/Agent/BP_Agent.BP_Agent_C')
cdo = unreal.get_default_object(manager_class)
cdo.set_editor_property('Run Inference', True)
for kind, field in [('encoder','EncoderSnapshot'), ('policy','PolicySnapshot'), ('decoder','Decoder Snapshot'), ('critic','Critic Snapshot')]:
    path = root / ('embedded_' + kind + '.bin')
    if not path.exists():
        raise RuntimeError('Missing frozen embedded snapshot: ' + str(path))
    cdo.set_editor_property(field, unreal.FilePath(file_path=str(path)))
levels.load_level('/Game/Level/Landscape')

def stop(reason):
    global finishing
    if finishing: return
    finishing = True
    emit({'event': 'end', 'reason': reason, 'frames': frames})
    stream.close()
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), 'QUIT_EDITOR')

def tick(slate_delta):
    global frames, last_tick
    try:
        if time.monotonic() - started > 180:
            stop('timeout')
            return
        world = editor.get_game_world()
        if world is None: return
        gm = unreal.GameplayStatics.get_game_mode(world)
        managers = unreal.GameplayStatics.get_all_actors_of_class(world, manager_class)
        agents = unreal.GameplayStatics.get_all_actors_of_class(world, agent_class)
        if not managers or not agents or gm is None: return
        manager, agent = managers[0], agents[0]
        total_ticks = prop(gm, 'TotalTickCount')
        if total_ticks <= 0 or total_ticks == last_tick: return
        last_tick = total_ticks
        controller = agent.get_controller()
        movement = agent.get_editor_property('character_movement')
        interactor = prop(manager, 'Interactor')
        aid = prop(manager, 'LearningAgentsManager').get_agent_id(agent)
        action, action_hash = interactor.get_action_vector(aid) if interactor is not None else ([], None)
        points = prop(gm, 'Setpoints')
        item = {'decision_index': frames, 'sim_time': unreal.GameplayStatics.get_time_seconds(world),
                'delta': unreal.GameplayStatics.get_world_delta_seconds(world),
                'slate_delta': slate_delta, 'is_training': prop(gm, 'IsTraining'),
                'run_inference': prop(manager, 'Run Inference'),
                'max_walk_speed': movement.get_editor_property('max_walk_speed'),
                'velocity': vec(agent.get_velocity()), 'position': vec(agent.get_actor_location()),
                'yaw': agent.get_actor_rotation().yaw,
                'control_yaw': controller.get_control_rotation().yaw if controller else None,
                'controller_class': controller.get_class().get_name() if controller else None,
                'is_local': controller.is_local_controller() if controller else None,
                'action': list(action), 'action_hash': action_hash, 'h': points[-1] if points else None,
                'total_ticks': total_ticks,
                'period_count': prop(gm, 'HomeostaticPeriodsElapsed' if 'fixed_' in label else 'SecondsElapsed')}
        emit(item)
        frames += 1
        if frames >= 200: stop('complete')
    except Exception:
        emit({'event':'error','traceback':traceback.format_exc()})
        stop('error')

emit({'event':'start','label':label,'command_line':args,'source':'embedded networks; original snapshot unavailable'})
handle = unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

"""Run 30 actual training decisions in PIE; back up network assets first."""
import json
import pathlib
import time
import traceback
import unreal

root = pathlib.Path(unreal.Paths.project_saved_dir()).resolve() / 'PythonRuntimeFix'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
manager_class = unreal.load_class(None, '/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class = unreal.load_class(None, '/Game/Agent/BP_Agent.BP_Agent_C')
levels.load_level('/Game/Level/Landscape')
started = time.monotonic()
samples = []
done = False
last_tick = None
trainer = None

def prop(o, n): return o.get_editor_property(n)
def vec(v): return [v.x, v.y, v.z]

def finish(error=None):
    global done
    if done: return
    done = True
    (root / 'training_smoke.json').write_text(json.dumps(
        {'passed': error is None, 'error': error, 'samples': samples}, indent=2))
    if trainer and trainer.is_training(): trainer.end_training()
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), 'QUIT_EDITOR')

def tick(dt):
    global last_tick, trainer
    try:
        if time.monotonic() - started > 120: raise RuntimeError('Training smoke test timed out')
        world = editor.get_game_world()
        if not world: return
        managers = unreal.GameplayStatics.get_all_actors_of_class(world, manager_class)
        agents = unreal.GameplayStatics.get_all_actors_of_class(world, agent_class)
        gm = unreal.GameplayStatics.get_game_mode(world)
        if not managers or not agents or not gm: return
        manager, agent = managers[0], agents[0]
        if prop(manager, 'Run Inference'): raise RuntimeError('Current manager is set to inference mode')
        trainer = prop(manager, 'PPOTrainer')
        if not trainer: return
        if trainer.has_training_failed(): raise RuntimeError('PPO training failed')
        ticks = prop(gm, 'TotalTickCount')
        if ticks <= 0 or ticks == last_tick: return
        last_tick = ticks
        aid = prop(manager, 'LearningAgentsManager').get_agent_id(agent)
        action, action_hash = prop(manager, 'Interactor').get_action_vector(aid)
        samples.append({'tick': ticks, 'is_training': trainer.is_training(),
                        'action': list(action), 'position': vec(agent.get_actor_location()),
                        'velocity': vec(agent.get_velocity()),
                        'max_walk_speed': prop(agent, 'character_movement').get_editor_property('max_walk_speed')})
        if len(samples) >= 30:
            assert all(s['is_training'] for s in samples), 'Trainer is not active'
            assert any(any(abs(v) > 1e-6 for v in s['action']) for s in samples), 'No sampled actions'
            assert any(s['position'] != samples[0]['position'] for s in samples), 'Pawn did not move'
            finish()
    except Exception:
        finish(traceback.format_exc())

handle = unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

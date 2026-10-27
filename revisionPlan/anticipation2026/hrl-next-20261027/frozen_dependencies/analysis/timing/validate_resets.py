"""Exercise actual manager reset callbacks in PIE without starting an optimizer."""
import json
import pathlib
import time
import traceback
import unreal

root = pathlib.Path(unreal.Paths.project_saved_dir()).resolve() / 'ResetFix'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
manager_class = unreal.load_class(None, '/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class = unreal.load_class(None, '/Game/Agent/BP_Agent.BP_Agent_C')
cdo = unreal.get_default_object(manager_class)
cdo.set_editor_property('Run Inference', True)
for kind, field in [('encoder','EncoderSnapshot'), ('policy','PolicySnapshot'), ('decoder','Decoder Snapshot'), ('critic','Critic Snapshot')]:
    cdo.set_editor_property(field, unreal.FilePath(file_path=str(root.parent / 'TimingFix' / ('embedded_' + kind + '.bin'))))
levels.load_level('/Game/Level/Landscape')
started = time.monotonic()
results = []
done = False

def vec(v): return [v.x, v.y, v.z]
def prop(o, n): return o.get_editor_property(n)
def finish(error=None):
    global done
    if done: return
    done = True
    (root / 'validation.json').write_text(json.dumps({'passed': error is None, 'error': error, 'cases': results}, indent=2))
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), 'QUIT_EDITOR')

def tick(dt):
    try:
        if time.monotonic() - started > 120:
            raise RuntimeError('PIE reset test timed out')
        world = editor.get_game_world()
        if world is None: return
        managers = unreal.GameplayStatics.get_all_actors_of_class(world, manager_class)
        agents = unreal.GameplayStatics.get_all_actors_of_class(world, agent_class)
        if not managers or not agents: return
        gm = unreal.GameplayStatics.get_game_mode(world)
        if prop(gm, 'TotalTickCount') < 3: return
        manager, agent = managers[0], agents[0]
        la = prop(manager, 'LearningAgentsManager')
        aid = la.get_agent_id(agent)
        policy = prop(manager, 'Policy')
        env = prop(manager, 'TrainingEnv')
        if env is None:
            raise RuntimeError('Missing TrainingEnvironment under ' + la.get_path_name())
        unreal.log('RESET_TEST env=' + env.get_path_name() + ' gm=' + str(prop(env, 'GameMode')))
        controller = agent.get_controller()
        movement = prop(agent, 'character_movement')
        for steps, yaw in [(0, 120.0), (1, -120.0), (20, 80.0), (0, -80.0)]:
            for _ in range(steps):
                env.gather_rewards()
            actual_steps = prop(env, 'Episode Steps')
            movement.set_editor_property('velocity', unreal.Vector(100, 200, 300))
            agent.add_movement_input(unreal.Vector(1, 0, 0), 1.0)
            agent.jump()
            agent.launch_character(unreal.Vector(0, 0, 1000), True, True)
            controller.set_control_rotation(unreal.Rotator(20, yaw, 30))
            policy.set_memory_state(aid, [1.0] * policy.get_memory_state_size())
            la.reset_agents([aid])
            case = {'steps_before': actual_steps, 'velocity': vec(agent.get_velocity()),
                    'pending_input': vec(agent.get_pending_movement_input_vector()),
                    'last_input': vec(agent.get_last_movement_input_vector()),
                    'steps': prop(env, 'Episode Steps'), 'reward': prop(env, 'TotalReward'),
                    'terminated': prop(env, 'ShouldTerminate'),
                    'memory': list(policy.get_memory_state(aid)),
                    'rotation': str(controller.get_control_rotation()),
                    'actor_rotation': str(agent.get_actor_rotation()),
                    'tick_count': prop(gm, 'TotalTickCount'),
                    'last_resource_cleared': prop(env, 'LastCollidingResource') is None}
            results.append(case)
            assert case['velocity'] == [0,0,0] and case['pending_input'] == [0,0,0] and case['last_input'] == [0,0,0], case
            assert case['steps'] == 0 and case['reward'] == 0 and not case['terminated'] and case['last_resource_cleared'], case
            assert all(v == 0 for v in case['memory']), case
            r = controller.get_control_rotation()
            assert abs(r.pitch) < 0.001 and abs(r.roll) < 0.001, case
            ar = agent.get_actor_rotation()
            assert all(abs((getattr(ar,k)-getattr(r,k)+180)%360-180) < 0.001 for k in ['pitch','yaw','roll']), case
            assert case['tick_count'] == 0, case
        finish()
    except Exception:
        finish(traceback.format_exc())

handle = unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

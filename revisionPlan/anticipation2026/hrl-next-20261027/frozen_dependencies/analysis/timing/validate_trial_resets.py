"""Exercise RunTrial phase and full-trial boundaries in PIE, without an optimizer."""
import json
import pathlib
import time
import traceback
import unreal

root = pathlib.Path(unreal.Paths.project_saved_dir()).resolve() / 'TrialResetFix'
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
manager_class = unreal.load_class(None, '/Game/Learning/BP_AgentManager.BP_AgentManager_C')
agent_class = unreal.load_class(None, '/Game/Agent/BP_Agent.BP_Agent_C')
gm_class = unreal.load_class(None, '/Game/Agent/BP_GameMode.BP_GameMode_C')
cdo = unreal.get_default_object(manager_class)
cdo.set_editor_property('Run Inference', True)
for kind, field in [('encoder','EncoderSnapshot'), ('policy','PolicySnapshot'), ('decoder','Decoder Snapshot'), ('critic','Critic Snapshot')]:
    cdo.set_editor_property(field, unreal.FilePath(file_path=str(root.parent / 'TimingFix' / ('embedded_' + kind + '.bin'))))
gm_cdo = unreal.get_default_object(gm_class)
gm_cdo.set_editor_property('IsTrialMode', False)
gm_cdo.set_editor_property('TrialFileName', str(root / 'test_trials.csv'))
levels.load_level('/Game/Level/Landscape')
started = time.monotonic()
results = []
done = False

def vec(v): return [v.x, v.y, v.z]
def rot(r): return [r.pitch, r.yaw, r.roll]
def prop(o, n): return o.get_editor_property(n)

def finish(error=None):
    global done
    if done: return
    done = True
    (root / 'validation.json').write_text(json.dumps({'passed': error is None, 'error': error, 'cases': results}, indent=2))
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), 'QUIT_EDITOR')

def set_tick(world, gm, count):
    # The test-only package permits setting this counter on instances. Restore
    # the compiled production package immediately after this test process exits.
    gm.set_editor_property('TotalTickCount', count)
    assert prop(gm, 'TotalTickCount') == count, 'Cannot seed trial boundary tick'

def tick(dt):
    try:
        if time.monotonic() - started > 120: raise RuntimeError('PIE test timed out')
        world = editor.get_game_world()
        if world is None: return
        managers = unreal.GameplayStatics.get_all_actors_of_class(world, manager_class)
        agents = unreal.GameplayStatics.get_all_actors_of_class(world, agent_class)
        if not managers or not agents: return
        gm = unreal.GameplayStatics.get_game_mode(world)
        if prop(gm, 'TotalTickCount') < 3: return
        manager, agent = managers[0], agents[0]
        la = prop(manager, 'LearningAgentsManager')
        policy = prop(manager, 'Policy')
        env = prop(manager, 'TrainingEnv')
        controller = agent.get_controller()
        movement = prop(agent, 'character_movement')
        aid = la.get_agent_id(agent)
        for trial in range(2):
            for count in [6000,12000,18000,18002]:
                set_tick(world, gm, count)
                movement.set_editor_property('velocity', unreal.Vector(100,200,300))
                agent.add_movement_input(unreal.Vector(1,0,0),1.0)
                controller.set_control_rotation(unreal.Rotator(pitch=20,yaw=120,roll=30))
                memory = [0.75] * policy.get_memory_state_size()
                policy.set_memory_state(aid, memory)
                before = {'position':vec(agent.get_actor_location()),
                          'rotation':rot(controller.get_control_rotation()),
                          'pending_input':vec(agent.get_pending_movement_input_vector()),
                          'trials_run':prop(gm,'TrialsRun')}
                gm.call_method('RunTrial', args=(str(root / 'test_trials.csv'), bool(trial)))
                after_memory = list(policy.get_memory_state(aid))
                case = {'trial':trial,'boundary_tick':count,'before':before,
                        'position':vec(agent.get_actor_location()),
                        'rotation':rot(controller.get_control_rotation()),
                        'actor_rotation':rot(agent.get_actor_rotation()),
                        'velocity':vec(agent.get_velocity()),
                        'pending_input':vec(agent.get_pending_movement_input_vector()),
                        'tick_count':prop(gm,'TotalTickCount'),
                        'trials_run':prop(gm,'TrialsRun'),
                        'sequence_count':prop(gm,'SequenceCount'),
                        'episode_steps':prop(env,'Episode Steps'),
                        'memory_max_absolute':max(abs(v) for v in after_memory)}
                results.append(case)
                if count <= 18000:
                    assert case['position']==before['position'] and case['rotation']==before['rotation'],case
                    assert case['velocity']==[100,200,300] and case['pending_input']==before['pending_input'],case
                    assert after_memory==memory and case['trials_run']==before['trials_run'],case
                else:
                    assert case['trials_run']==before['trials_run']+1,case
                    assert case['tick_count']==0 and case['sequence_count']==0 and case['episode_steps']==0,case
                    assert case['velocity']==[0,0,0] and case['pending_input']==[0,0,0],case
                    assert case['memory_max_absolute']==0,case
                    assert case['position']!=before['position'],case
                    r=case['rotation']; ar=case['actor_rotation']
                    assert abs(r[0])<0.001 and abs(r[2])<0.001,case
                    assert all(abs((a-b+180)%360-180)<0.001 for a,b in zip(r,ar)),case
        finish()
    except Exception:
        finish(traceback.format_exc())

handle = unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

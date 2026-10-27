"""Validate real Blueprint reward callbacks in isolated PIE; no optimizer."""
import json
import math
import pathlib
import time
import traceback
import unreal

root=pathlib.Path(__file__).resolve().parents[2]/'Saved/NFRewardFix'
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
bp=unreal.load_asset('/Game/Agent/BP_GameMode')
for field in ['Setpoints','AnticipatedNets','IsHRL']:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
levels.load_level('/Game/Level/Landscape')
editor_world=editor.get_editor_world()
manager_class=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
started=time.monotonic(); done=False; cases=[]
def prop(o,n):return o.get_editor_property(n)
def finish(error=None):
    global done
    if done:return
    done=True
    (root/'nf_reward_validation.json').write_text(json.dumps({'passed':error is None,'error':error,'cases':cases},indent=2))
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor_world,'QUIT_EDITOR')
def tick(dt):
    try:
        if time.monotonic()-started>90:raise RuntimeError('Reward validation timed out')
        w=editor.get_game_world()
        if not w:return
        ms=unreal.GameplayStatics.get_all_actors_of_class(w,manager_class)
        gm=unreal.GameplayStatics.get_game_mode(w)
        if not ms or not gm or prop(gm,'TotalTickCount')<3:return
        m=ms[0];la=prop(m,'LearningAgentsManager');env=prop(m,'TrainingEnv')
        aid=0
        for mode in [False,True]:
            for previous,current in [(-40,-20),(-20,-40),(-10,30),(-10,0),(5,-2),(50,50),(-50,-50),(0,0),(0,101),(0,-101)]:
                la.reset_agents([aid])
                gm.set_editor_property('IsHRL',mode)
                gm.set_editor_property('Setpoints',[float(previous),float(current)])
                gm.set_editor_property('AnticipatedNets',[1.0,1.0])
                interactor=m.get_editor_property('Interactor')
                interactor.gather_observations()
                observation,_=interactor.get_observation_vector(aid)
                observed=float(observation[-1])*100.0
                assert math.isclose(observed,current,rel_tol=1e-5,abs_tol=1e-5),(current,list(observation))
                env.gather_rewards()
                reward=env.get_reward(aid)
                delta=unreal.GameplayStatics.get_world_delta_seconds(w)
                expected=(-1.0 if abs(current)>100 else delta/(1+(current/25.0)**2)) if mode else (max(abs(previous)-abs(current),0)/25.0 if current<0 and abs(current)<=100 else 0.0)
                case={'mode':mode,'previous':previous,'current':current,'reward':reward,
                      'observed_homeostasis':observed,
                      'expected':expected,'steps':prop(env,'Episode Steps'),
                      'terminated':prop(env,'ShouldTerminate'),'total':prop(env,'TotalReward')}
                cases.append(case)
                assert math.isclose(reward,expected,rel_tol=1e-5,abs_tol=1e-7),case
                assert case['steps']==1 and case['terminated']==(abs(current)>100),case
                if abs(current)<=100:
                    env.gather_rewards()
                    assert math.isclose(env.get_reward(aid),expected if mode else 0.0,rel_tol=1e-5,abs_tol=1e-7),case
                    assert prop(env,'Episode Steps')==2,case
                else:
                    env.gather_rewards()
                    assert env.get_reward(aid)==0,case
                la.reset_agents([aid])
                assert prop(env,'TotalReward')==0 and prop(env,'Episode Steps')==0 and not prop(env,'ShouldTerminate')
        # Carry the decision cache across a phase switch; history may still span a whole homeostatic period.
        la.reset_agents([aid])
        gm.set_editor_property('IsHRL',True)
        gm.set_editor_property('Setpoints',[-40.0,-20.0])
        env.gather_rewards()
        gm.set_editor_property('IsHRL',False)
        gm.set_editor_property('Setpoints',[-40.0,-10.0])
        env.gather_rewards()
        value=env.get_reward(aid)
        assert math.isclose(value,0.4,rel_tol=1e-5),value
        cases.append({'phase_switch':'HRL -> NF','reward':value,'expected':0.4})
        la.reset_agents([aid])
        assert not prop(env,'HasPreviousRewardState') and prop(env,'PreviousRewardState')==0
        gm.set_editor_property('Setpoints',[-25.0,-20.0])
        env.gather_rewards()
        assert math.isclose(env.get_reward(aid),0.2,rel_tol=1e-5)
        cases.append({'trial_reset':'cache invalidated','reward':env.get_reward(aid),'expected':0.2})
        finish()
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

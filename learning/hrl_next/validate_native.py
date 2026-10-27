"""Real Blueprint reward, sampling and reset regression tests in isolated PIE."""
from pathlib import Path
import json,math,sys,time,traceback
import unreal
project=Path(unreal.Paths.project_dir()).resolve();assert (project/'HRL_LEARNING_COPY').exists()
sys.path.insert(0,str(project/'analysis/hrl_learning'))
from metrics import COUNTERS,summarize
from profiles import PROFILES
root=project.parent;cases=[];done=False;started=time.monotonic()
bp=unreal.load_asset('/Game/Learning/BP_AgentTrainingEnv')
for field in ['UseAbsoluteErrorReward','RewardDistanceScale','HomeostaticFailureReward','Max Setpoint Distance']:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
bp=unreal.load_asset('/Game/Agent/BP_GameMode')
for field in ['Setpoints','IsHRL','IsTrialMode']:
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level('/Game/Level/Landscape');editor_world=editor.get_editor_world()
manager_class=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')

def finish(error=None):
    global done
    if done:return
    done=True
    (root/'native_validation.json').write_text(json.dumps(dict(passed=error is None,error=error,cases=cases),indent=2))
    levels.editor_request_end_play();unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor_world,'QUIT_EDITOR')

def close(a,b):assert math.isclose(a,b,rel_tol=2e-5,abs_tol=2e-6),(a,b)

def tick(delta):
    try:
        if time.monotonic()-started>120:raise TimeoutError('Native reward validation')
        world=editor.get_game_world()
        if not world:return
        managers=unreal.GameplayStatics.get_all_actors_of_class(world,manager_class)
        gm=unreal.GameplayStatics.get_game_mode(world)
        if not managers or not gm or gm.get_editor_property('TotalTickCount')<3:return
        m=managers[0];m.set_actor_tick_enabled(False)
        m.set_editor_property('Run Inference',False)
        # The existing trial instrumentation bypasses termination by design.
        # Direct reward tests exercise the training branch instead.
        gm.set_editor_property('IsTrialMode',False)
        env=m.get_editor_property('TrainingEnv');la=m.get_editor_property('LearningAgentsManager')
        # Fixed-horizon inference intentionally raises the runtime failure bound.
        # Restore the training bound for these direct termination callback tests.
        env.set_editor_property('Max Setpoint Distance',100.)
        dt=unreal.GameplayStatics.get_world_delta_seconds(world)
        for profile_name in ['baseline','quality-10','absolute-25']:
            p=PROFILES[profile_name]
            env.set_editor_property('UseAbsoluteErrorReward',p.reward=='absolute')
            env.set_editor_property('RewardDistanceScale',p.distance_scale)
            env.set_editor_property('HomeostaticFailureReward',p.terminal_reward())
            for h in [-101.,-100.,-25.,-5.,0.,5.,25.,100.,101.]:
                la.reset_agents([0]);gm.set_editor_property('IsHRL',True)
                env.set_editor_property('Max Setpoint Distance',100.)
                assert env.get_editor_property('Max Setpoint Distance')==100.
                gm.set_editor_property('Setpoints',[h,h])
                for key in COUNTERS:env.set_editor_property(key,0.)
                env.set_editor_property('RecordDecisionHomeostasis',True)
                env.gather_rewards();value=env.get_reward(0)
                expected=p.terminal_reward() if abs(h)>100 else (-dt*abs(h)/p.distance_scale if p.reward=='absolute' else dt/(1+(h/p.distance_scale)**2))
                close(value,expected)
                env.gather_rewards();close(env.get_reward(0),0. if abs(h)>100 else expected)
                counters={k:float(env.get_editor_property(k)) for k in COUNTERS};summary=summarize(counters)
                assert summary['decision_samples']==2,summary
                close(summary['time_mae'],abs(h));close(summary['duration_seconds'],2*dt)
                close(summary['fraction_within_5'],float(abs(h)<=5));close(summary['fraction_above_100'],float(abs(h)>100))
                cases.append(dict(profile=profile_name,h=h,reward=value,expected=expected,metrics=summary))
        # Sampling must survive a terminal reward guard and include all decisions.
        la.reset_agents([0]);env.set_editor_property('RecordDecisionHomeostasis',True)
        for key in COUNTERS:env.set_editor_property(key,0.)
        path=[12.,8.,4.,0.,-6.,-3.,120.,-120.]
        for h in path:
            gm.set_editor_property('Setpoints',[h,h]);env.gather_rewards()
        summary=summarize({k:float(env.get_editor_property(k)) for k in COUNTERS})
        close(summary['time_mae'],sum(abs(h) for h in path)/len(path))
        close(summary['time_rmse'],math.sqrt(sum(h*h for h in path)/len(path)))
        close(summary['time_mean_signed'],sum(path)/len(path));close(summary['fraction_above_100'],.25)
        assert summary['completed_recoveries']==2,summary
        close(summary['mean_completed_excursion_seconds'],1.5*dt)
        close(summary['censored_excursion_seconds'],2*dt)
        cases.append(dict(trajectory=path,metrics=summary))
        env.set_editor_property('RecordDecisionHomeostasis',False)
        env.gather_rewards();assert env.get_editor_property('DecisionSampleCount')==len(path)
        cases.append(dict(disabled_sampling_preserves_count=True))
        # HRL options must not alter the NF branch.
        la.reset_agents([0]);gm.set_editor_property('IsHRL',False)
        gm.set_editor_property('Setpoints',[-40.,-20.]);env.gather_rewards();close(env.get_reward(0),.8)
        env.gather_rewards();close(env.get_reward(0),0.)
        cases.append(dict(nf_reward_unchanged=True))
        finish()
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

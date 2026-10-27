"""Native watcher: success requires durable training or full phase receipts."""
from pathlib import Path
import json,sys,time,traceback
import unreal
project=Path(unreal.Paths.project_dir()).resolve();assert (project/'HRL_LEARNING_COPY').exists()
sys.path.insert(0,str(project/'analysis/hrl_learning'))
from landscape import summarize_counts
root=project.parent;settings=json.loads((project/'run_settings.json').read_text());started=time.monotonic();done=False
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
manager_class=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
trainer=None
last_step=None;episode_index=0;last_landscape_step=-100;tiles=None

def finish(error=None):
    global done
    if done:return
    done=True
    (root/'engine_result.json').write_text(json.dumps(dict(passed=error is None,error=error,wall_seconds=time.monotonic()-started),indent=2))
    if trainer and trainer.is_training():trainer.end_training()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(world,'QUIT')

def tick(delta):
    global trainer,last_step,episode_index,last_landscape_step,tiles
    try:
        if time.monotonic()-started>settings['engine_guard_seconds']:raise TimeoutError('HRL native process guard')
        if (root/'trainer_error.json').exists():raise RuntimeError((root/'trainer_error.json').read_text())
        if settings['mode']=='evaluate':
            return # Native trial completion saves its own receipt and quits.
        actors=unreal.GameplayStatics.get_all_actors_of_class(world,manager_class)
        if not actors:return
        trainer=actors[0].get_editor_property('PPOTrainer')
        if trainer and trainer.has_training_failed():raise RuntimeError('Unreal PPO training failed')
        env=actors[0].get_editor_property('TrainingEnv')
        if env:
            if not (root/'native_environment.json').exists():
                profile=settings['profile']
                actual=dict(world_episode_limit=float(env.get_editor_property('Max Time')),
                    experience_segment_limit=actors[0].get_editor_property('Trainer Settings').get_editor_property('MaxEpisodeStepNum'),
                    reset_world_on_update=actors[0].get_editor_property('ResetWorldOnPolicyUpdate'),
                    initialization_seed=actors[0].get_editor_property('InitializationSeed'),
                    failure_boundary=float(env.get_editor_property('Max Setpoint Distance')))
                assert actual['world_episode_limit']==profile['episode_seconds'],actual
                assert actual['experience_segment_limit']==profile['segment_steps'],actual
                assert actual['reset_world_on_update']==profile['reset_world_on_update'],actual
                assert actual['initialization_seed']==settings['policy_seed'],actual
                assert actual['failure_boundary']==profile['failure_boundary'],actual
                (root/'native_environment.json').write_text(json.dumps(dict(passed=True,**actual),indent=2))
            step=int(env.get_editor_property('Episode Steps'))
            if last_step is not None and step<last_step:
                episode_index+=1;last_landscape_step=-100
            if step-last_landscape_step>=100:
                if tiles is None:
                    tile_cls=unreal.load_class(None,'/Game/Level/BP_Tile.BP_Tile_C')
                    tiles=unreal.GameplayStatics.get_all_actors_of_class(world,tile_cls)
                counts=[float(tile.get_editor_property('OverlapCount')) for tile in tiles]
                row=dict(observed_episode=episode_index,episode_decisions=step,episode_seconds=step*.05,
                         **summarize_counts(counts),sampling='every 100 decisions and first observation after a reset')
                with (root/'landscape_history.jsonl').open('a') as file:file.write(json.dumps(row)+'\n')
                last_landscape_step=step
            last_step=step
        if (root/'trainer_complete.json').exists():
            assert list((root/'checkpoints').glob('*/checkpoint.json')),'No updated checkpoint'
            finish()
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
unreal.log('HRL_LEARNING_WATCH_STARTED')

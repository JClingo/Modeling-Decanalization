"""Native watcher: success requires durable training or full phase receipts."""
from pathlib import Path
import json,sys,time,traceback
import unreal
project=Path(unreal.Paths.project_dir()).resolve();assert (project/'HRL_LEARNING_COPY').exists()
sys.path.insert(0,str(project/'analysis/hrl_learning'))
from landscape import summarize_counts
from curriculum import next_stage
root=project.parent;settings=json.loads((project/'run_settings.json').read_text());started=time.monotonic();done=False
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
manager_class=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
trainer=None
last_step=None;episode_index=0;last_landscape_step=-100;tiles=None
curriculum_stage=-1;recent_training=[];last_gather=-1

def finish(error=None):
    global done
    if done:return
    done=True
    (root/'engine_result.json').write_text(json.dumps(dict(passed=error is None,error=error,wall_seconds=time.monotonic()-started),indent=2))
    if trainer and trainer.is_training():trainer.end_training()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(world,'QUIT')

def tick(delta):
    global trainer,last_step,episode_index,last_landscape_step,tiles,curriculum_stage,last_gather
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
            if settings.get('training_curriculum'):
                # The physical world changes duration only after a reset.
                progress=root/'training_progress.json'
                if progress.exists():
                    data=json.loads(progress.read_text())
                    if data['gathers']!=last_gather:
                        recent_training.append(data);del recent_training[:-10];last_gather=data['gathers']
                step_now=int(env.get_editor_property('Episode Steps'))
                if curriculum_stage<0:
                    curriculum_stage=0
                    env.set_editor_property('Max Time',100.)
                    with (root/'curriculum_history.jsonl').open('a') as file:
                        file.write(json.dumps(dict(stage=0,seconds=100.,steps=0))+'\n')
                elif last_step is not None and step_now<last_step and curriculum_stage<2 and len(recent_training)==10:
                    steps=recent_training[-1]['steps']
                    proposed=next_stage(curriculum_stage,recent_training,True)
                    if proposed>curriculum_stage:
                        curriculum_stage=proposed;seconds=[100.,200.,300.][curriculum_stage]
                        env.set_editor_property('Max Time',seconds)
                        with (root/'curriculum_history.jsonl').open('a') as file:
                            file.write(json.dumps(dict(stage=curriculum_stage,seconds=seconds,steps=steps,
                                recent_mean_time_mae=sum(x['training_time_mae'] for x in recent_training)/10))+'\n')
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

"""Validate production training through one PPO update, then stop gracefully.

Back up network/external-actor packages first; restore after editor shutdown.
"""
import json
import pathlib
import time
import traceback
import unreal

root=pathlib.Path(unreal.Paths.project_saved_dir()).resolve()/'HomeostaticFix'
logs=pathlib.Path(unreal.Paths.project_intermediate_dir()).resolve()/'LearningAgents/TensorBoard/runs'
old_runs=set(logs.glob('*'))
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cls=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
unreal.get_default_object(cls).set_editor_property('Run Inference',False)
levels.load_level('/Game/Level/Landscape')
editor_world=editor.get_editor_world()
started=time.monotonic();done=False;trainer=None;decisions=0;last_tick=None;last_poll=0
def finish(error=None,events=None):
    global done
    if done:return
    done=True
    (root/'training_validation.json').write_text(json.dumps({
        'passed':error is None,'error':error,'decisions':decisions,
        'event_files':events or [],'wall_seconds':time.monotonic()-started},indent=2))
    if trainer and trainer.is_training():trainer.end_training()
    levels.editor_request_end_play()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(editor_world,'QUIT_EDITOR')
def tick(dt):
    global trainer,decisions,last_tick,last_poll
    try:
        if time.monotonic()-started>180:raise RuntimeError('Training validation timed out')
        w=editor.get_game_world()
        if not w:return
        managers=unreal.GameplayStatics.get_all_actors_of_class(w,cls)
        if not managers:return
        m=managers[0];trainer=m.get_editor_property('PPOTrainer')
        if not trainer:return
        if trainer.has_training_failed():raise RuntimeError('PPO training failed')
        gm=unreal.GameplayStatics.get_game_mode(w)
        t=gm.get_editor_property('TotalTickCount')
        if t!=last_tick:decisions+=1;last_tick=t
        # A first completed optimizer update is confirmed by the original trainer log.
        log=root/'training_validation.log'
        now=time.monotonic()
        if now-last_poll<1:return
        last_poll=now
        if log.exists() and 'Subprocess: Iter:' in log.read_text(errors='replace'):
            events=[str(f) for d in set(logs.glob('*'))-old_runs for f in d.glob('events*')]
            assert events,'No TensorBoard run was created'
            finish(events=events)
    except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()

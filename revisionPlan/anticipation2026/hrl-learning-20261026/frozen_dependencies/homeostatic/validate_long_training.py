"""Monitor a standalone isolated run past the reported optimizer failure point."""
import json
import pathlib
import re
import time
import traceback
import unreal

project=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert project.parent.name=='TrainingCrashFix' and project.name=='TestProject'
root=project.parent
log=root/'training.log'
cls=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
started=time.monotonic();last_poll=0;done=False
def tick(dt):
    global last_poll,done
    if done or time.monotonic()-last_poll<1:return
    last_poll=time.monotonic()
    try:
        world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
        if not world:return
        managers=unreal.GameplayStatics.get_all_actors_of_class(world,cls)
        if not managers:return
        trainer=managers[0].get_editor_property('PPOTrainer')
        if not trainer:return
        text=log.read_text(errors='replace') if log.exists() else ''
        iterations=re.findall(r'Subprocess: Iter:\s+(\d+)',text)
        iteration=int(iterations[-1]) if iterations else -1
        if trainer.has_training_failed():raise RuntimeError('Trainer failed; see training.log')
        if time.monotonic()-started>1200:raise RuntimeError('Long validation timed out')
        if iteration<1280:return
        result={'passed':True,'last_reported_iteration':iteration,
                'wall_seconds':time.monotonic()-started}
    except Exception:
        result={'passed':False,'error':traceback.format_exc(),'wall_seconds':time.monotonic()-started}
    done=True
    (root/'validation.json').write_text(json.dumps(result,indent=2))
    if trainer.is_training():trainer.end_training()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(world,'QUIT')
handle=unreal.register_slate_post_tick_callback(tick)

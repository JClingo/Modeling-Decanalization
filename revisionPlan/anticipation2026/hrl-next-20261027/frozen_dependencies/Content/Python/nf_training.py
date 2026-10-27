"""Choose the NF trainer from the actual runtime mode before spawning Python."""
from pathlib import Path

def configure_nf_training():
    import unreal
    worlds=[]
    try: worlds.append(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    except Exception: pass
    worlds.append(unreal.find_object(None,'/Game/Level/Landscape.Landscape'))
    world=next((w for w in worlds if w and unreal.GameplayStatics.get_game_mode(w)),None)
    if not world: raise RuntimeError('NF trainer routing could not find the game world')
    gm=unreal.GameplayStatics.get_game_mode(world)
    if gm.get_editor_property('IsHRL'): raise RuntimeError('NF trainer routing was invoked in HRL mode')
    cls=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
    managers=unreal.GameplayStatics.get_all_actors_of_class(world,cls)
    assert len(managers)==1,'NF routing requires exactly one AgentManager'
    manager=managers[0]
    if manager.get_editor_property('Run Inference'): return
    # Unreal struct wrappers refer to the live value. Mutate only these fields;
    # preserve every engine/intermediate path and the HRL class defaults.
    settings=manager.get_editor_property('Trainer Process Settings')
    settings.set_editor_property('TrainerFileName','nf_ppo',notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    path=str(Path(unreal.Paths.project_dir()).resolve()/'analysis'/'homeostatic')
    settings.set_editor_property('CustomTrainerModulePath',unreal.DirectoryPath(path=path),notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
    check=manager.get_editor_property('Trainer Process Settings')
    assert check.get_editor_property('TrainerFileName')=='nf_ppo','NF trainer settings did not update'
    unreal.log('NF_TRAINER_SELECTED: nf_ppo; HRL defaults unchanged')

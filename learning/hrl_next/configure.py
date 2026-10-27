"""Configure opt-in training/evaluation, including placed actor overrides."""
from pathlib import Path
import json,sys
import unreal
project=Path(unreal.Paths.project_dir()).resolve()
assert (project/'HRL_LEARNING_COPY').exists()
sys.path.insert(0,str(project/'analysis/hrl_learning'))
from profiles import load_profile
s=json.loads((project/'run_settings.json').read_text());p=load_profile(s['profile'])
if s.get('static_tile_costs'):
    agent_bp=unreal.load_asset('/Game/Agent/BP_Agent')
    unreal.BlueprintEditorLibrary.compile_blueprint(agent_bp)
    assert unreal.EditorAssetLibrary.save_asset('/Game/Agent/BP_Agent',False)
def default(path):
    bp=unreal.load_asset(path);return bp,unreal.get_default_object(bp.generated_class())
def save(bp,path):
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert unreal.EditorAssetLibrary.save_asset(path,False)
# Compile authored graph before reading its generated defaults.
bp,c=default('/Game/Learning/BP_AgentTrainingEnv')
if s.get('training_curriculum'):
    unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'Max Time',True)
save(bp,'/Game/Learning/BP_AgentTrainingEnv')
c=unreal.get_default_object(bp.generated_class())
for name,value in [('UseHomeostaticReward',True),('UseAbsoluteErrorReward',p.reward=='absolute'),
                   ('RewardDistanceScale',p.distance_scale),('HomeostaticRewardRate',1.),
                   ('HomeostaticFailureReward',p.terminal_reward()),('RecordDecisionHomeostasis',False)]:
    c.set_editor_property(name,value)
c.set_editor_property('Max Time',p.episode_seconds)
c.set_editor_property('Max Setpoint Distance',p.failure_boundary)
save(bp,'/Game/Learning/BP_AgentTrainingEnv')
evaluation=s['mode']=='evaluate'
bp,c=default('/Game/Agent/BP_GameMode')
for name,value in [('IsTrialMode',evaluation),('IsTraining',not evaluation),('IsHRL',True),
                   ('TrainingEnvironmentSeed',s['environment_seed']),('TrialEnvironmentSeed',s['evaluation_seed']),
                   ('TrialsToRun',s['trials']),('TrialSequenceOrder',s.get('order','ccc'))]:c.set_editor_property(name,value)
save(bp,'/Game/Agent/BP_GameMode')
bp,c=default('/Game/Level/BP_Tile');c.set_editor_property('DecanalizationRateFactor',1.)
save(bp,'/Game/Level/BP_Tile')
bp,c=default('/Game/Learning/BP_AgentManager')
fields=['ResetWorldOnPolicyUpdate','InitializationSeed','Run Inference','Trainer Process Settings','Socket Settings','Trainer Settings','Trainer Training Settings',
        'EncoderSnapshot','PolicySnapshot','Decoder Snapshot','Critic Snapshot']
for field in fields:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
save(bp,'/Game/Learning/BP_AgentManager');c=unreal.get_default_object(bp.generated_class())
c.set_editor_property('Run Inference',evaluation)
c.set_editor_property('InitializationSeed',s['policy_seed'])
c.set_editor_property('ResetWorldOnPolicyUpdate',p.reset_world_on_update)
trainer_settings=c.get_editor_property('Trainer Settings')
trainer_settings.set_editor_property('max_episode_step_num',p.segment_steps)
trainer_settings.set_editor_property('maximum_recorded_steps_per_iteration',10000)
c.set_editor_property('Trainer Settings',trainer_settings)
process=c.get_editor_property('Trainer Process Settings')
engine='/Users/Shared/Epic Games/UE_5.5/Engine/'
for name,value in [('editor_engine_relative_path',unreal.DirectoryPath(path=engine)),('non_editor_engine_relative_path',engine),
                   ('editor_intermediate_relative_path',unreal.DirectoryPath(path=str(project/'Intermediate'))),
                   ('non_editor_intermediate_relative_path',str(project/'Intermediate')),
                   ('custom_trainer_module_path',unreal.DirectoryPath(path=str(project/'analysis/hrl_learning'))),
                   ('trainer_file_name','native_trainer')]:process.set_editor_property(name,value)
c.set_editor_property('Trainer Process Settings',process)
socket=c.get_editor_property('Socket Settings')
for name,value in [('ip_address','127.0.0.1'),('port',s['port']),('timeout',120.)]:socket.set_editor_property(name,value)
c.set_editor_property('Socket Settings',socket)
train=c.get_editor_property('Trainer Training Settings')
properties={'LearningRatePolicy':'learning_rate_policy','LearningRateCritic':'learning_rate_critic',
            'PolicyBatchSize':'policy_batch_size','CriticBatchSize':'critic_batch_size','PolicyWindow':'policy_window_size',
            'IterationsPerGather':'iterations_per_gather','DiscountFactor':'discount_factor','GaeLambda':'gae_lambda',
            'ActionEntropyWeight':'action_entropy_weight','EpsilonClip':'epsilon_clip','UseGradNormMaxClipping':'use_grad_norm_max_clipping',
            'GradNormMax':'grad_norm_max','AdvantageNormalization':'advantage_normalization','AdvantageMin':'minimum_advantage',
            'AdvantageMax':'maximum_advantage','TrimEpisodeStartStepNum':'number_of_steps_to_trim_at_start_of_episode',
            'TrimEpisodeEndStepNum':'number_of_steps_to_trim_at_end_of_episode','LearningRateDecay':'learning_rate_decay',
            'CriticWarmupIterations':'critic_warmup_iterations'}
for key,value in p.ppo_settings().items():train.set_editor_property(properties[key],value)
train.set_editor_property('device',unreal.LearningAgentsTrainingDevice.CPU)
train.set_editor_property('random_seed',s['policy_seed']);c.set_editor_property('Trainer Training Settings',train)
for field,kind in [('EncoderSnapshot','encoder'),('PolicySnapshot','policy'),('Decoder Snapshot','decoder'),('Critic Snapshot','critic')]:
    c.set_editor_property(field,unreal.FilePath(file_path=s['snapshots'][kind]['path'] if evaluation else ''))
save(bp,'/Game/Learning/BP_AgentManager')
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Level/Landscape')
cls=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
for actor in unreal.GameplayStatics.get_all_actors_of_class(world,cls):
    for field in fields:actor.set_editor_property(field,c.get_editor_property(field))
# Tile placed overrides can supersede the class default.
tile_cls=unreal.load_class(None,'/Game/Level/BP_Tile.BP_Tile_C')
for actor in unreal.GameplayStatics.get_all_actors_of_class(world,tile_cls):actor.set_editor_property('DecanalizationRateFactor',1.)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(project/'configured.json').write_text(json.dumps(s,indent=2))
unreal.log('HRL_LEARNING_CONFIGURED '+s['mode']+' '+p.name)

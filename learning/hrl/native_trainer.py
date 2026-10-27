"""UE trainer entry point, effective settings, checkpoints and task diagnostics."""
from pathlib import Path
import sys
PROJECT=Path(__file__).resolve().parents[2]
assert (PROJECT/'HRL_LEARNING_COPY').exists(),'The trainer entry point requires a marked isolated project'
sys.path.insert(0,str(PROJECT/'analysis/homeostatic'))
import copy,hashlib,json,math,time,traceback
import numpy as np
import train_ppo as epic
from train_common import UE_RESPONSE_SUCCESS,UE_RESPONSE_STOPPED
from homeostatic_ppo import HomeostaticPPOTrainer,TelemetryCommunicator,setpoint_column
from profiles import load_profile
from trainer import GuardedTrainer
ROOT=PROJECT.parent
SETTINGS=json.loads((PROJECT/'run_settings.json').read_text())
PROFILE=load_profile(SETTINGS['profile'])
KINDS={0:'policy',1:'critic',2:'encoder',3:'decoder'}
def write(name,data):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)

class Recorder:
    def __init__(self,comm,config):
        self.comm,self.config=comm,config
        self.steps=self.gathers=0;self.started=time.monotonic();self.networks={};self.metrics={}
        self.column=setpoint_column(config)
    def __getattr__(self,name):return getattr(self.comm,name)
    def receive_network(self,index,network):
        response=self.comm.receive_network(index,network)
        if response==UE_RESPONSE_SUCCESS:
            self.networks[index]=network
            target=ROOT/'initial'/(KINDS[index]+'.bin');target.parent.mkdir(exist_ok=True)
            epic.save_snapshot_to_file(network,str(target))
        return response
    def receive_experience(self,*args,**kwargs):
        if (ROOT/'STOP').exists() or self.gathers>=SETTINGS['max_gathers']:
            self.comm.send_complete()
            write('trainer_complete.json',dict(reason='stop-request' if (ROOT/'STOP').exists() else 'gather-budget',
                steps=self.steps,gathers=self.gathers,wall_seconds=time.monotonic()-self.started))
            return UE_RESPONSE_STOPPED,None,None
        response,buffer,stats=self.comm.receive_experience(*args,**kwargs)
        if response==UE_RESPONSE_SUCCESS:
            self.steps+=len(buffer['obs'][0]);self.gathers+=1
            h=np.asarray(buffer['obs_next'][0][:,self.column],dtype=np.float64)*100.
            reward=np.asarray(buffer['rew'][0],dtype=np.float64).reshape(-1)
            if not np.isfinite(h).all() or not np.isfinite(reward).all():raise FloatingPointError('Invalid experience')
            self.metrics=dict(steps=self.steps,gathers=self.gathers,
                training_time_mae=float(np.abs(h).mean()),training_time_rmse=float(np.sqrt(np.square(h).mean())),
                training_fraction_within_5=float((np.abs(h)<=5).mean()),
                training_fraction_above_100=float((np.abs(h)>100).mean()),
                terminated_transitions=int(buffer['terminated'].sum()),
                truncated_transitions=int(buffer['truncated'].sum()),
                native_reward_mean=float(reward.mean()),wall_seconds=time.monotonic()-self.started)
            write('training_progress.json',self.metrics)
        return response,buffer,stats
    def send_network(self,index,network):
        self.networks[index]=network
        response=self.comm.send_network(index,network)
        if response==UE_RESPONSE_SUCCESS and index==3:
            if self.gathers==1 or self.gathers%SETTINGS['checkpoint_every']==0 or self.gathers==SETTINGS['max_gathers']:
                folder=ROOT/'checkpoints'/f'gather-{self.gathers:05d}';folder.mkdir(parents=True,exist_ok=True)
                snapshots={}
                for key,value in self.networks.items():
                    path=folder/(KINDS[key]+'.bin');epic.save_snapshot_to_file(value,str(path))
                    snapshots[KINDS[key]]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                write(str(folder.relative_to(ROOT)/'checkpoint.json'),dict(**self.metrics,snapshots=snapshots,
                    profile=PROFILE.contract(),policy_seed=SETTINGS['policy_seed'],environment_seed=SETTINGS['environment_seed']))
        return response

def train(config,communicator):
    from torch.utils import tensorboard
    settings=copy.deepcopy(config)
    for key,expected in PROFILE.ppo_settings().items():
        actual=settings['PPOSettings'][key]
        assert math.isclose(actual,expected,rel_tol=2e-6,abs_tol=1e-9),(key,actual,expected)
    assert settings['PPOSettings']['Seed']==SETTINGS['policy_seed']
    assert settings['Schemas']['Observations'][0]['Schema']['VectorSize']==11
    settings['HRLLearning']=PROFILE.contract()
    write('effective_config.json',settings)
    original_writer,original_trainer=tensorboard.SummaryWriter,epic.PPOTrainer
    writers=[]
    class Writer(original_writer):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);writers.append(self)
    def diagnostics(data):
        write('optimizer_diagnostics.json',data)
        with (ROOT/'optimizer_history.jsonl').open('a') as file:file.write(json.dumps(data,allow_nan=False)+'\n')
        if writers:
            for name,value in data.items():
                if isinstance(value,(float,int)) and math.isfinite(value):writers[-1].add_scalar('hrl/'+name,value,data['steps'])
    def factory(*args,**kwargs):
        if PROFILE.guarded:return GuardedTrainer(*args,profile=PROFILE,record=diagnostics,**kwargs)
        return HomeostaticPPOTrainer(*args,**kwargs)
    tensorboard.SummaryWriter,epic.PPOTrainer=Writer,factory
    try:
        recorder=Recorder(communicator,settings)
        proxy=TelemetryCommunicator(recorder,settings,lambda:writers[-1] if writers else None)
        epic.train(settings,proxy)
    except Exception:
        write('trainer_error.json',dict(error=traceback.format_exc()));raise
    finally:
        for writer in writers:writer.close()
        tensorboard.SummaryWriter,epic.PPOTrainer=original_writer,original_trainer

(ROOT/'trainer_import_ready').write_text('HRL trainer imports complete.\n')

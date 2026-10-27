"""NF stability, native serialization and HRL isolation regressions."""
import copy
import math
import pathlib
import sys
import unittest
import numpy as np
import torch
engine=pathlib.Path('D:/Dev/UE_5.5/Engine/Plugins/Experimental')
sys.path.extend([str(engine/'LearningAgents/Content/Python'),str(engine/'NNERuntimeBasicCpu/Content/Python')])
from nf_ppo import NFTrainer, ACTION_STD, stable_config, clipped_surrogate, gradient_norm
from nne_runtime_basic_cpu_pytorch import NeuralNetwork, Concat, Denormalize
from train_common import schema_log_prob

torch.set_num_threads(1)

def trainer():
    torch.manual_seed(31)
    encoder=torch.nn.Linear(2,2)
    policy=torch.nn.Linear(2,2);policy.device='cpu'
    critic=torch.nn.Linear(2,1)
    decoder=NeuralNetwork('cpu');decoder.model=Concat(np.array([2],dtype=np.uint32),np.array([2],dtype=np.uint32),[Denormalize(2,'cpu')])
    actor=list(encoder.parameters())+list(policy.parameters())+list(decoder.parameters())
    return NFTrainer({}, {'Type':'Continuous','VectorSize':1,'DistributionSize':2,'EncodedSize':2},
        policy,critic,encoder,decoder,torch.optim.AdamW(actor,lr=.001,weight_decay=.1),
        torch.optim.AdamW(list(critic.parameters())+list(encoder.parameters()),lr=.001),
        eps_clip=.1,advantage_min=-10.,grad_norm_max=.25)

def batch(t):
    obs=torch.randn(128,1,2);mem=torch.zeros(128,1,0)
    with torch.no_grad():
        dist=t.decoder(t.policy(t.encoder(obs[:,0])))
        act=dist[:,:1]+torch.randn(128,1)*ACTION_STD
        logp=schema_log_prob(t.action_schema,dist,act)[:,None]
    return torch.ones(128,1),obs,act[:,None],mem,torch.randn(128,1),logp,1

class NFTests(unittest.TestCase):
    def test_signed_ppo_clipping(self):
        ratio=torch.tensor([math.log(1.3),math.log(.7),0.,0.],requires_grad=True)
        result=clipped_surrogate(ratio,torch.tensor([1.,-1.,1.,-1.]),.1)
        (-result.sum()).backward()
        torch.testing.assert_close(result,torch.tensor([1.1,-.9,1.,-1.]))
        torch.testing.assert_close(ratio.grad,torch.tensor([0.,0.,-1.,1.]))

    def test_nf_config_does_not_mutate_hrl_config(self):
        original={'TaskName':'Training','Schemas':{'Actions':[{'Schema':{'Type':'And','Elements':{
            'Turn':{'Type':'Continuous','VectorSize':1,'DistributionSize':2}}}}]},
            'PPOSettings':{'LearningRatePolicy':.001,'LearningRateCritic':.001,
                'IterationsPerGather':32,'EpsilonClip':.2,'GradNormMax':.5}}
        before=copy.deepcopy(original);result=stable_config(original)
        self.assertEqual(original,before)
        self.assertEqual(result['PPOSettings']['ActionRegularizationWeight'],0.)
        self.assertEqual(result['PPOSettings']['IterationsPerGather'],8)

    def test_decoder_roundtrip_preserves_native_layout_and_std(self):
        t=trainer();size=t.decoder_bytes
        data=np.zeros(size,dtype=np.uint8);t.decoder.save_to_filedata(data)
        restored=NeuralNetwork('cpu');restored.load_from_filedata(data)
        self.assertEqual(restored.get_filedata_size(),size)
        x=torch.tensor([[.4,1e20],[-.4,-1e20]])
        torch.testing.assert_close(restored(x)[:,1].exp(),torch.full((2,),ACTION_STD))
        torch.testing.assert_close(restored(x)[:,0],x[:,0])

    def test_kl_guard_prevents_actor_mutation(self):
        t=trainer();args=list(batch(t));args[5]=args[5]-1.
        before=[p.detach().clone() for g in t.optim_policy.param_groups for p in g['params']]
        t.train_policy(*args)
        self.assertEqual(t.skipped_kl,1)
        for p,b in zip([p for g in t.optim_policy.param_groups for p in g['params']],before):
            self.assertTrue(torch.equal(p,b))

    def test_actor_mean_learns_without_variance_drift(self):
        t=trainer()
        with torch.no_grad():t.policy.weight.zero_();t.policy.bias.zero_()
        for _ in range(1000):
            args=list(batch(t))
            # A simple directional task: positive steering is advantageous.
            args[4]=args[2][...,0].detach()/ACTION_STD
            t.train_policy(*args)
        with torch.no_grad():mean=t.decoder(t.policy(t.encoder(torch.zeros(1,2))))[0,0].item()
        self.assertGreater(mean,.1)
        self.assertEqual(t.accepted,1000)
        self.assertAlmostEqual(t.nf_layer.mean[1].item(),math.log(ACTION_STD),places=6)
        self.assertEqual(t.nf_layer.std[1].item(),0.)

    def test_critic_does_not_change_actor_encoder(self):
        t=trainer();before=[p.clone() for p in t.encoder.parameters()]
        ids={id(p) for g in t.optim_critic.param_groups for p in g['params']}
        self.assertFalse(any(id(p) in ids for p in t.encoder.parameters()))
        t.train_critic(torch.randn(32,2),torch.zeros(32,0),torch.ones(32))
        for p,b in zip(t.encoder.parameters(),before):self.assertTrue(torch.equal(p,b))

    def test_bootstrap_discards_all_legacy_data(self):
        t=trainer()
        parameters=[p for network in [t.policy,t.critic,t.encoder,t.decoder] for p in network.parameters()]
        before=[p.clone() for p in parameters]
        stats=t.train({},256,256,8,16)
        self.assertEqual(stats['loss/policy'],[0.]*8)
        self.assertFalse(t.bootstrap_pending)
        for p,b in zip(parameters,before):self.assertTrue(torch.equal(p,b))

    def test_finite_large_gradient_norm_does_not_overflow(self):
        p=torch.nn.Parameter(torch.ones(20));p.grad=torch.full_like(p,1e20)
        self.assertTrue(math.isfinite(gradient_norm([p])))

if __name__=='__main__':unittest.main()

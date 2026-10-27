"""Regression tests for final-transition GAE and episode boundaries."""
import pathlib
import sys
import unittest
from types import SimpleNamespace
import numpy as np
import torch

engine=pathlib.Path('D:/Dev/UE_5.5/Engine/Plugins/Experimental')
sys.path.extend([str(engine/'LearningAgents/Content/Python'),str(engine/'NNERuntimeBasicCpu/Content/Python')])
from homeostatic_ppo import gae, setpoint_column, HomeostaticPPOTrainer, clipped_log_surrogate, require_finite

class AdvantagesTests(unittest.TestCase):
    def make_trainer(self):
        policy=torch.nn.Linear(2,3);policy.device='cpu'
        critic=torch.nn.Linear(2,1)
        return HomeostaticPPOTrainer({},
            {'Type':'Continuous','VectorSize':1,'DistributionSize':2,'EncodedSize':2},
            policy,critic,torch.nn.Identity(),torch.nn.Identity(),
            torch.optim.Adam(policy.parameters(),lr=1e-4),
            torch.optim.Adam(critic.parameters(),lr=1e-3),
            advantage_min=-10.,use_grad_norm_max_clipping=True)

    def test_recurrent_policy_update_with_mixed_advantages_stays_finite(self):
        t=self.make_trainer()
        result=t.train_policy(torch.ones(3,2),torch.zeros(3,2,1),torch.zeros(3,2,1),
            torch.zeros(3,2,1),torch.tensor([[1.,1.],[-1.,-1.],[.5,-.5]]),torch.zeros(3,2),2)
        self.assertTrue(np.isfinite(result).all())
        self.assertTrue(all(torch.isfinite(p).all() for p in t.policy.parameters()))

    def test_critic_optimizer_rejects_bad_gradient_before_mutating_weights(self):
        t=self.make_trainer()
        parameters=list(t.critic.parameters())
        before=[p.detach().clone() for p in parameters]
        for p in parameters:p.grad=torch.full_like(p,float('nan'))
        with self.assertRaises(FloatingPointError):t.optim_critic.step()
        for p,previous in zip(parameters,before):self.assertTrue(torch.equal(p,previous))

    def test_clipping_stops_decreasing_bad_action_probability_past_limit(self):
        ratio=torch.tensor([-5.0],requires_grad=True)
        loss=-clipped_log_surrogate(ratio,torch.tensor([-1.]),-.2,.2).sum()
        loss.backward()
        self.assertAlmostEqual(loss.item(),-.2,places=6)
        self.assertEqual(ratio.grad.item(),0.0)

    def test_clipping_stops_increasing_good_action_probability_past_limit(self):
        ratio=torch.tensor([5.0],requires_grad=True)
        loss=-clipped_log_surrogate(ratio,torch.tensor([1.]),-.2,.2).sum()
        loss.backward()
        self.assertAlmostEqual(loss.item(),-.2,places=6)
        self.assertEqual(ratio.grad.item(),0.0)

    def test_bad_action_still_has_correct_gradient_inside_clip(self):
        ratio=torch.tensor([0.0],requires_grad=True)
        (-clipped_log_surrogate(ratio,torch.tensor([-1.]),-.2,.2).sum()).backward()
        self.assertEqual(ratio.grad.item(),1.0)

    def test_nonfinite_weights_are_rejected(self):
        with self.assertRaises(FloatingPointError):require_finite('test',torch.tensor([float('nan')]))
    def test_single_terminal_transition_keeps_reward(self):
        a,r=gae(np.array([-1.]),np.array([0.]),np.array([20.]),
                np.array([True]),np.array([False]),.99,.95)
        np.testing.assert_allclose(a,[-1.]);np.testing.assert_allclose(r,[-1.])

    def test_last_nonterminal_transition_bootstraps(self):
        a,r=gae(np.array([1.]),np.array([2.]),np.array([4.]),
                np.array([False]),np.array([False]),.5,1.)
        np.testing.assert_allclose(a,[1.]);np.testing.assert_allclose(r,[3.])

    def test_truncation_bootstraps_but_does_not_cross_episode(self):
        a,r=gae(np.array([1.,100.]),np.array([0.,0.]),np.array([4.,0.]),
                np.array([False,True]),np.array([True,False]),.5,1.)
        np.testing.assert_allclose(a,[3.,100.])

    def test_recursion_includes_final_transition(self):
        a,r=gae(np.array([1.,2.]),np.zeros(2),np.zeros(2),
                np.array([False,True]),np.array([False,False]),.5,1.)
        np.testing.assert_allclose(a,[2.,2.])

    def test_schema_column_uses_indices_not_dictionary_order(self):
        c={'Schemas':{'Observations':[{'Schema':{'Type':'And','Elements':{
            'SetpointDistance':{'Index':1,'VectorSize':1},'Rays':{'Index':0,'VectorSize':7}}}}]}}
        self.assertEqual(setpoint_column(c),7)

    def test_normalized_advantages_preserve_negative_feedback(self):
        trainer=HomeostaticPPOTrainer.__new__(HomeostaticPPOTrainer)
        trainer.encoder=lambda x:x
        trainer.critic=lambda x:torch.zeros((len(x),1))
        trainer.policy=SimpleNamespace(device='cpu')
        trainer.discount_factor=.99;trainer.gae_lambda=.95
        trainer.adv_norm=True;trainer.adv_min=-10.;trainer.adv_max=10.
        obs=torch.zeros((2,1));mem=torch.zeros((2,0))
        adv,returns,_=trainer.compute_advantages_and_returns(
            obs,obs,mem,mem,np.array([1.,-1.]),np.ones(2,dtype=bool),np.zeros(2,dtype=bool))
        np.testing.assert_allclose(adv.numpy(),[1.,-1.])
        np.testing.assert_allclose(returns.numpy(),[1.,-1.])

if __name__=='__main__':unittest.main()

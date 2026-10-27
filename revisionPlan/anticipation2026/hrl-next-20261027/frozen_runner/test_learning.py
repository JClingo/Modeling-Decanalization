"""Behavioral regression tests for learning safety and objective accounting."""
from pathlib import Path
import copy,math,os,sys,unittest
import numpy as np
import torch
from dataclasses import replace
engine=Path(os.environ.get('HRL_ENGINE_DIR','/Users/Shared/Epic Games/UE_5.5/Engine'))
sys.path[:0]=[str(engine/'Plugins/Experimental/LearningAgents/Content/Python'),
              str(engine/'Plugins/Experimental/NNERuntimeBasicCpu/Content/Python'),
              '/Users/jingo/Work/PhD/Dissertation Project/decanalization/analysis/homeostatic']
from profiles import PROFILES,Profile,schedule
from metrics import COUNTERS,summarize
from trainer import GuardedTrainer,recurrent_windows,surrogate
from train_common import schema_log_prob
from study import Selector,resolve_profiles
from landscape import summarize_counts
from objective import ratio_surrogate
from curriculum import next_stage

class LearningTests(unittest.TestCase):
    def test_static_control_records_revisits_without_claiming_cost_reduction(self):
        active=summarize_counts([9.,0.],[7.,0.])
        static=summarize_counts([9.,0.],[7.,0.],static_tile_costs=True)
        self.assertEqual(static['window_entries'],2.)
        self.assertEqual(static['window_fraction_entries_revisiting'],1.)
        self.assertEqual(static['mean_visited_next_cost_fraction_of_first'],1.)
        self.assertAlmostEqual(active['mean_visited_next_cost_fraction_of_first'],2/11)
    def test_curriculum_requires_stability_budget_and_a_physical_reset(self):
        rows=[dict(training_time_mae=20.,terminated_transitions=10,steps=500000)]*10
        self.assertEqual(next_stage(0,rows,True),1)
        self.assertEqual(next_stage(0,rows,False),0)
        self.assertEqual(next_stage(0,rows[:9],True),0)
        self.assertEqual(next_stage(1,rows,True),1)
        self.assertEqual(next_stage(0,[dict(x,training_time_mae=30.) for x in rows],True),0)
        self.assertEqual(next_stage(0,[dict(x,terminated_transitions=30) for x in rows],True),0)
        rows=[dict(x,steps=1000000) for x in rows]
        self.assertEqual(next_stage(1,rows,True),2)
        self.assertEqual(next_stage(2,rows,True),2)
    def test_ratio_only_retains_original_optimizer_and_recurrent_settings(self):
        a,b=PROFILES['baseline'].contract(),PROFILES['ratio-only'].contract()
        self.assertEqual({k for k in a if a[k]!=b[k]},{'name','objective'})
        self.assertFalse(PROFILES['ratio-only'].guarded)

    def test_ratio_only_surrogate_has_standard_values_and_clipped_gradients(self):
        values=torch.tensor([math.log(1.5),math.log(.5),math.log(1.1),math.log(.9)],requires_grad=True)
        advantages=torch.tensor([1.,-1.,1.,-1.])
        result=ratio_surrogate(values,advantages,math.log(.8),math.log(1.2))
        torch.testing.assert_close(result,torch.tensor([1.2,-.8,1.1,-.9]))
        result.sum().backward()
        torch.testing.assert_close(values.grad,torch.tensor([0.,0.,1.1,-.9]))

    def make(self,lr=1e-4,target=.015):
        torch.manual_seed(27)
        encoder=torch.nn.Linear(1,1);policy=torch.nn.Linear(2,3);policy.device='cpu'
        critic=torch.nn.Linear(2,1);decoder=torch.nn.Identity()
        profile=replace(PROFILES['guarded-ratio'],policy_lr=lr,target_kl=target)
        return GuardedTrainer({},dict(Type='Continuous',VectorSize=1,DistributionSize=2,EncodedSize=2),
            policy,critic,encoder,decoder,
            torch.optim.AdamW(list(policy.parameters())+list(encoder.parameters()),lr=lr),
            torch.optim.AdamW(list(critic.parameters())+list(encoder.parameters()),lr=1e-3),
            profile=profile,advantage_min=-10.,use_grad_norm_max_clipping=True)

    def test_both_objectives_stop_good_and_bad_actions_at_the_correct_clip_side(self):
        for objective in ['log','ratio']:
            log_ratio=torch.tensor([math.log(1.5),math.log(.5)],requires_grad=True)
            loss=-surrogate(log_ratio,torch.tensor([1.,-1.]),.2,objective).sum()
            loss.backward();torch.testing.assert_close(log_ratio.grad,torch.zeros(2))

    def test_ratio_surrogate_matches_probability_ratio_not_log_ratio(self):
        x=torch.tensor([math.log(1.1)])
        self.assertAlmostEqual(float(surrogate(x,torch.ones(1),.2,'ratio')),1.1,places=6)

    def test_last_transition_and_short_episode_receive_training_coverage(self):
        indices,mask=recurrent_windows([False,True,True],[False]*3,16)
        self.assertEqual(indices.shape,(3,16))
        self.assertEqual(mask.sum(axis=1).tolist(),[2,1,1])
        self.assertEqual(indices[-1,0],2)
        self.assertTrue(mask[-1,0])

    def test_truncation_masks_next_episode_without_dropping_boundary(self):
        _,mask=recurrent_windows([False]*4,[False,True,False,True],3)
        self.assertEqual(mask.sum(axis=1).tolist(),[2,1,2,1])

    def test_post_update_kl_rejection_restores_weights_and_optimizer_state(self):
        trainer=self.make(lr=1.,target=1e-6)
        obs=torch.tensor([[[.1],[.2]],[[.4],[.5]]]);mem=torch.zeros(2,2,1)
        actions=torch.zeros(2,2,1);mask=torch.ones(2,2,dtype=torch.bool)
        with torch.no_grad():
            distributions=trainer.distribution(obs,mem,2)
            old=torch.stack([schema_log_prob(trainer.action_schema,d,actions[:,i]) for i,d in enumerate(distributions)],dim=1)
        parameters=list(trainer.encoder.parameters())+list(trainer.policy.parameters())
        before=[p.detach().clone() for p in parameters]
        state=copy.deepcopy(trainer.optim_policy.state_dict())
        trainer.train_policy(mask,obs,actions,mem,torch.tensor([[1.,-1.],[1.,-1.]]),old,2)
        self.assertEqual(trainer.rejected,1);self.assertEqual(trainer.accepted,0)
        for p,expected in zip(parameters,before):torch.testing.assert_close(p,expected,rtol=0,atol=0)
        self.assertEqual(trainer.optim_policy.state_dict(),state)

    def test_critic_cannot_change_actor_encoder(self):
        trainer=self.make();before=[p.detach().clone() for p in trainer.encoder.parameters()]
        trainer.train_critic(torch.ones(4,1),torch.zeros(4,1),torch.full((4,),2.))
        for p,expected in zip(trainer.encoder.parameters(),before):torch.testing.assert_close(p,expected,rtol=0,atol=0)

    def test_guarded_training_handles_buffer_shorter_than_window(self):
        trainer=self.make();buffer=dict(obs=np.zeros((2,1),dtype=np.float32),obs_next=np.ones((2,1),dtype=np.float32),
            act=np.zeros((2,1),dtype=np.float32),mem=np.zeros((2,1),dtype=np.float32),mem_next=np.zeros((2,1),dtype=np.float32),
            rew=np.array([.01,-.1],dtype=np.float32),terminated=np.array([False,True]),truncated=np.array([False,False]))
        stats=trainer.train(buffer,2,2,2,16)
        self.assertTrue(np.isfinite(stats['loss/policy']).all())
        self.assertEqual(trainer.diagnostics['recurrent_starts'],2)
        self.assertEqual(trainer.diagnostics['recurrent_valid_steps'],3)

    def test_absorbing_failure_cannot_escape_a_stream_of_valid_error_costs(self):
        for gamma in [.99,.995,.9975]:
            p=replace(PROFILES['absolute-25'],discount=gamma)
            step=-p.dt*p.failure_boundary/p.distance_scale
            terminal=p.terminal_reward()
            self.assertAlmostEqual(terminal,step/(1-gamma))
            # Waiting k steps at the worst valid error and then failing has
            # exactly the same discounted cost as immediate failure.
            for k in [1,20,2000]:
                later=step*(1-gamma**k)/(1-gamma)+gamma**k*terminal
                self.assertAlmostEqual(terminal,later,places=9)

    def test_profile_rejects_unstable_or_silent_settings(self):
        for changes in [dict(discount=1.),dict(window=0),dict(policy_lr=float('nan')),
                        dict(entropy_end=.0001),dict(objective='unknown'),dict(reset_world_on_update='false'),
                        dict(segment_steps=10001),dict(episode_seconds=0.)]:
            with self.assertRaises(ValueError):replace(Profile(),**changes).validate()

    def test_schedule_has_explicit_endpoints_and_does_not_overshoot(self):
        p=PROFILES['guarded-annealed']
        self.assertEqual(schedule(p,0)['entropy'],.001)
        self.assertAlmostEqual(schedule(p,p.anneal_steps*2)['entropy'],.0001)
        self.assertAlmostEqual(schedule(p,p.anneal_steps*2)['lr_fraction'],.1)

    def test_time_metrics_reject_empty_data(self):
        with self.assertRaises(ValueError):summarize({k:0. for k in COUNTERS})

    def test_masked_padding_cannot_poison_kl(self):
        trainer=self.make()
        value=trainer.approximate_kl(torch.tensor([[0.,1000.]]),torch.tensor([[1.,0.]]))
        self.assertEqual(value,0.)

    def test_checkpoint_selection_uses_time_mae_and_waits_for_minimum(self):
        selector=Selector(minimum=50,patience=2)
        def result(mae,gather,reward):return dict(mean_time_mae=mae,reward=reward,checkpoint=dict(gathers=gather))
        self.assertFalse(selector.update(result(10.,1,0.)))
        self.assertFalse(selector.update(result(11.,10,100.)))
        self.assertFalse(selector.update(result(10.5,20,200.)))
        self.assertTrue(selector.update(result(10.2,50,300.)))
        self.assertEqual(selector.best['mean_time_mae'],10.)

    def test_small_improvement_is_retained_without_resetting_plateau(self):
        selector=Selector(minimum=0,patience=2)
        selector.update(dict(mean_time_mae=10.,checkpoint=dict(gathers=1)))
        selector.update(dict(mean_time_mae=9.99,checkpoint=dict(gathers=2)))
        self.assertEqual(selector.best['mean_time_mae'],9.99)
        self.assertEqual(selector.stale,1)

    def test_world_duration_is_independent_of_experience_segment_length(self):
        baseline=PROFILES['baseline'];long=PROFILES['canalization-300s'];segment=PROFILES['segment-100s']
        self.assertEqual(baseline.episode_seconds,100.)
        self.assertEqual(long.segment_steps,baseline.segment_steps)
        self.assertEqual(long.episode_seconds,300.)
        self.assertEqual(segment.episode_seconds,baseline.episode_seconds)
        self.assertEqual(segment.segment_steps,2000)

    def test_rollbacks_also_restore_existing_adam_momentum(self):
        trainer=self.make();obs=torch.tensor([[[.1],[.2]],[[.4],[.5]]]);mem=torch.zeros(2,2,1)
        actions=torch.zeros(2,2,1);mask=torch.ones(2,2,dtype=torch.bool);advantages=torch.tensor([[1.,-1.],[1.,-1.]])
        def old_logp():
            with torch.no_grad():
                distributions=trainer.distribution(obs,mem,2)
                return torch.stack([schema_log_prob(trainer.action_schema,d,actions[:,i]) for i,d in enumerate(distributions)],dim=1)
        trainer.train_policy(mask,obs,actions,mem,advantages,old_logp(),2)
        self.assertEqual(trainer.accepted,1)
        trainer.profile=replace(trainer.profile,target_kl=1e-9)
        for group in trainer.optim_policy.param_groups:group['lr']=1.
        before=copy.deepcopy(trainer.optim_policy.state_dict())
        trainer.train_policy(mask,obs,actions,mem,advantages,old_logp(),2)
        self.assertEqual(trainer.rejected,1)
        after=trainer.optim_policy.state_dict()
        self.assertEqual(before['param_groups'],after['param_groups'])
        for key,values in before['state'].items():
            for field,value in values.items():
                if torch.is_tensor(value):torch.testing.assert_close(value,after['state'][key][field],rtol=0,atol=0)
                else:self.assertEqual(value,after['state'][key][field])

    def test_route_reuse_is_measured_relative_to_the_start_of_each_phase(self):
        result=summarize_counts([3,1,2],[1,0,2])
        self.assertEqual(result['window_entries'],3)
        self.assertEqual(result['window_first_visits'],1)
        self.assertEqual(result['window_distinct_tiles'],2)
        self.assertAlmostEqual(result['window_fraction_entries_revisiting'],2/3)

    def test_route_entropy_distinguishes_uniform_and_concentrated_visitation(self):
        equal=summarize_counts([5,5]);focused=summarize_counts([9,1])
        self.assertAlmostEqual(equal['effective_visited_tiles'],2.)
        self.assertLess(focused['effective_visited_tiles'],equal['effective_visited_tiles'])

    def test_count_resets_cannot_be_misreported_as_route_entries(self):
        with self.assertRaises(ValueError):summarize_counts([0,1],[2,1])

    def test_learning_comparisons_hold_reward_and_canalizing_environment_fixed(self):
        profiles,context=resolve_profiles(['baseline','horizon-32'],'horizon','quality-10')
        self.assertEqual(context,'canalization-persistent')
        for profile in profiles.values():
            self.assertEqual(profile.episode_seconds,300.)
            self.assertFalse(profile.reset_world_on_update)
            self.assertEqual(profile.distance_scale,10.)
        self.assertEqual(profiles['baseline'].window,16)
        self.assertEqual(profiles['horizon-32'].window,32)

    def test_world_history_stage_preserves_the_original_control(self):
        profiles,context=resolve_profiles(['baseline','canalization-300s','canalization-persistent'],'canalization')
        self.assertIsNone(context)
        self.assertEqual(profiles['baseline'].episode_seconds,100.)
        self.assertTrue(profiles['baseline'].reset_world_on_update)
        self.assertEqual(profiles['canalization-300s'].episode_seconds,300.)
        self.assertTrue(profiles['canalization-300s'].reset_world_on_update)
        self.assertFalse(profiles['canalization-persistent'].reset_world_on_update)

if __name__=='__main__':unittest.main()

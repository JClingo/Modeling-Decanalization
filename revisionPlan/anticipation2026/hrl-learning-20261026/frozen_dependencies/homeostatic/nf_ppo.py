"""NF-only PPO stabilization. HRL continues to use homeostatic_ppo unchanged.

Fixed exploration variance is encoded in the existing native decoder parameters,
so training, shared-memory inference and saved snapshots use the same network.
The first legacy-variance rollout is discarded before any actor update.
"""
import copy
import math
import numpy as np
import torch
from homeostatic_ppo import HomeostaticPPOTrainer, TelemetryCommunicator, require_finite, setpoint_column
import train_ppo as epic
from train_common import schema_log_prob
from nne_runtime_basic_cpu_pytorch import Concat, Denormalize

ACTION_STD = 0.15
TARGET_KL = 0.015
VERSION = 'NFStable1'


def stable_config(config):
    result = copy.deepcopy(config)
    schema = result['Schemas']['Actions'][0]['Schema']
    assert schema['Type'] == 'And' and len(schema['Elements']) == 1, 'NF trainer expects one scalar steering action'
    action = next(iter(schema['Elements'].values()))
    assert action['Type'] == 'Continuous' and action['VectorSize'] == 1 and action['DistributionSize'] == 2
    settings = result['PPOSettings']
    for key, cap in [('LearningRatePolicy', 3e-5), ('LearningRateCritic', 3e-4),
                     ('IterationsPerGather', 8), ('EpsilonClip', .1), ('GradNormMax', .25)]:
        settings[key] = min(settings[key], cap)
        assert settings[key] > 0, key
    settings.update(ActionEntropyWeight=0., ActionRegularizationWeight=0.,
                    UseGradNormMaxClipping=True, CriticWarmupIterations=0)
    result['TaskName'] += '_' + VERSION
    result['NFStability'] = {'Version': VERSION, 'ActionStd': ACTION_STD, 'TargetKL': TARGET_KL,
                             'DiscardInitialActorRollout': True, 'CriticUpdatesEncoder': False}
    return result


def fixed_variance_decoder(decoder):
    """Validate the project's native scalar decoder; preserve its byte layout."""
    model = decoder.model
    assert isinstance(model, Concat) and len(model.layers) == 1, 'Unexpected NF decoder layout'
    layer = model.layers[0]
    assert isinstance(layer, Denormalize) and tuple(layer.mean.shape) == (2,)
    assert tuple(layer.std.shape) == (2,)
    return layer


def enforce_variance(layer):
    with torch.no_grad():
        layer.mean[1] = math.log(ACTION_STD)
        layer.std[1] = 0.


def clipped_surrogate(log_ratio, advantage, epsilon):
    ratio = torch.exp(log_ratio.clamp(-20., 20.))
    return torch.minimum(ratio * advantage, ratio.clamp(1.-epsilon, 1.+epsilon) * advantage)


def gradient_norm(parameters):
    norms = []
    for p in parameters:
        if p.grad is not None:
            require_finite('NF actor gradient', p.grad)
            norms.append(torch.linalg.vector_norm(p.grad.detach().to(torch.float64)))
    return float(torch.linalg.vector_norm(torch.stack(norms))) if norms else 0.


class NFTrainer(HomeostaticPPOTrainer):
    def __init__(self, *args, writer_getter=lambda: None, **kwargs):
        super().__init__(*args, **kwargs)
        self.writer_getter = writer_getter
        self.nf_updates = 0
        self.skipped_kl = 0
        self.accepted = 0
        self.bootstrap_pending = True
        self.nf_column = None
        self.nf_layer = fixed_variance_decoder(self.decoder)
        self.decoder_bytes = self.decoder.get_filedata_size()
        enforce_variance(self.nf_layer)
        # AdamW's decay/momentum can move zero-gradient coordinates too. Mask
        # their gradients, then restore the fixed coordinates after each step.
        def mask_log_std(gradient):
            result = gradient.clone(); result[1] = 0.; return result
        self.nf_layer.mean.register_hook(mask_log_std)
        self.nf_layer.std.register_hook(mask_log_std)
        # A critic step must not change the policy's shared encoder behind the
        # actor KL check. NF gives encoder ownership solely to the actor.
        encoder_ids = {id(p) for p in self.encoder.parameters()}
        for group in self.optim_critic.param_groups:
            group['params'] = [p for p in group['params'] if id(p) not in encoder_ids]
        assert self.decoder.get_filedata_size() == self.decoder_bytes

    def log(self, values):
        writer = self.writer_getter()
        if writer:
            for name, value in values.items(): writer.add_scalar('nf/' + name, float(value), self.nf_updates)

    def train(self, buffer, policy_batch_size, critic_batch_size, iterations, policy_window, update_func=None):
        if self.bootstrap_pending:
            self.bootstrap_pending = False
            self.log({'bootstrap_rollout_discarded': 1., 'action_std': ACTION_STD})
            print('[NF_STABLE] Initial legacy-variance rollout discarded; bounded decoder published before learning.', flush=True)
            names = ['grads/encoder', 'grads/decoder', 'grads/policy', 'grads/critic',
                     'loss/critic_ret', 'loss/critic_reg', 'loss/critic', 'loss/policy_surr',
                     'loss/policy_ent', 'loss/policy_reg', 'loss/policy']
            return {**{name: [0.] * iterations for name in names}, 'experience/avg_return': 0.}
        if self.nf_column is not None:
            # A diagnostic on replay observations and their stored memory,
            # not a held-out deterministic evaluation or a trial score.
            with torch.no_grad():
                obs = torch.as_tensor(buffer['obs'][::max(1, len(buffer['obs'])//512)], device=self.policy.device)
                mem = torch.as_tensor(buffer['mem'][::max(1, len(buffer['obs'])//512)], device=self.policy.device)
                output = self.policy(torch.cat([self.encoder(obs), mem], dim=-1))
                distribution = self.decoder(output[:, :self.act_enc_num])
                negative = obs[:, self.nf_column] < 0
                values = {'action_std': ACTION_STD, 'log_std_max': distribution[:, 1].max().item(),
                          'mean_action_abs': distribution[:, 0].abs().mean().item()}
                if negative.any():
                    means = distribution[negative, 0].abs()
                    values.update(mean_action_abs_negative=means.mean().item(),
                                  fraction_small_mean_negative=(means < .01).float().mean().item())
                self.log(values)
        return super().train(buffer, policy_batch_size, critic_batch_size, iterations, policy_window, update_func)

    def train_policy(self, mask, obs, act, mem, adv, logp, policy_window):
        self.optim_policy.zero_grad()
        enforce_variance(self.nf_layer)
        policy_mem = mem[:, 0]
        log_ratios = []
        for index in range(policy_window):
            output = self.policy(torch.cat([self.encoder(obs[:, index]), policy_mem], dim=-1))
            encoded, policy_mem = output[:, :self.act_enc_num], output[:, self.act_enc_num:]
            distribution = self.decoder(encoded)
            require_finite('NF distribution', distribution)
            log_ratios.append(schema_log_prob(self.action_schema, distribution, act[:, index]) - logp[:, index])
        log_ratio = torch.stack(log_ratios, dim=1)
        require_finite('NF log probability ratio', log_ratio)
        weights = mask.to(log_ratio.dtype)
        count = weights.sum().clamp_min(1.)
        epsilon = math.exp(self.eps_clip_log_max) - 1.
        loss = -(weights * clipped_surrogate(log_ratio, adv, epsilon)).sum() / count * self.action_surr_weight / self.act_num
        require_finite('NF policy loss', loss)
        with torch.no_grad():
            kl = float((weights * (torch.exp(log_ratio.clamp(-20., 20.)) - 1. - log_ratio)).sum() / count)
            large_ratio = bool(((log_ratio.abs() > 20.) & (weights > 0)).any())
        self.nf_updates += 1
        if large_ratio or kl > TARGET_KL:
            self.skipped_kl += 1
            self.log({'approx_kl': kl, 'skipped_kl_updates': self.skipped_kl, 'accepted_actor_updates': self.accepted})
            return (0., 0., 0., float(loss.detach()), 0., 0., float(loss.detach()))
        loss.backward()
        groups = [list(self.encoder.parameters()), list(self.decoder.parameters()), list(self.policy.parameters())]
        norms = [gradient_norm(group) for group in groups]
        total = math.sqrt(sum(value*value for value in norms))
        scale = min(1., self.grad_norm_max / (total + 1e-12))
        with torch.no_grad():
            for group in groups:
                for parameter in group:
                    if parameter.grad is not None: parameter.grad.mul_(scale)
        self.optim_policy.step()
        enforce_variance(self.nf_layer)
        for network in [self.encoder, self.decoder, self.policy]:
            for p in network.parameters(): require_finite('NF updated parameter', p)
        self.accepted += 1
        self.log({'approx_kl': kl, 'actor_gradient_norm_before_clip': total,
                  'accepted_actor_updates': self.accepted, 'skipped_kl_updates': self.skipped_kl})
        return (*norms, float(loss.detach()), 0., 0., float(loss.detach()))

    def train_critic(self, obs, mem, returns):
        self.optim_critic.zero_grad()
        with torch.no_grad():
            features = self.encoder(obs)
        prediction = self.critic(torch.cat([features, mem], dim=-1))[..., 0]
        loss_ret = (returns - prediction).abs().mean()
        loss_reg = self.return_reg_weight * prediction.abs().mean()
        loss = loss_ret + loss_reg
        require_finite('NF critic loss', loss)
        loss.backward()
        parameters = list(self.critic.parameters())
        norm = gradient_norm(parameters)
        scale = min(1., self.grad_norm_max / (norm + 1e-12))
        with torch.no_grad():
            for parameter in parameters:
                if parameter.grad is not None: parameter.grad.mul_(scale)
        self.optim_critic.step()
        for p in parameters: require_finite('NF updated critic', p)
        return (0., norm, float(loss_ret.detach()), float(loss_reg.detach()), float(loss.detach()))


def train(config, communicator):
    from torch.utils import tensorboard
    settings = stable_config(config)
    original_writer, original_trainer = tensorboard.SummaryWriter, epic.PPOTrainer
    writers = []
    class NFWriter(original_writer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); writers.append(self)
    def make_trainer(*args, **kwargs):
        trainer = NFTrainer(*args, writer_getter=lambda: writers[-1] if writers else None, **kwargs)
        trainer.nf_column = setpoint_column(settings)
        return trainer
    tensorboard.SummaryWriter, epic.PPOTrainer = NFWriter, make_trainer
    print('[NF_STABLE] NFStable1: fixed serialized std=0.15, conservative PPO, target KL=0.015. HRL trainer untouched.', flush=True)
    try:
        proxy = TelemetryCommunicator(communicator, settings, lambda: writers[-1] if writers else None)
        epic.train(settings, proxy)
    finally:
        for writer in writers: writer.close()
        tensorboard.SummaryWriter, epic.PPOTrainer = original_writer, original_trainer

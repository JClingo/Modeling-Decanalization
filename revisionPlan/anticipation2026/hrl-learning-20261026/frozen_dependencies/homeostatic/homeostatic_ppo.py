"""UE 5.5 PPO adapter: complete GAE, centered advantages and task telemetry.

Configure the manager's custom module directory to this folder, trainer filename
homeostatic_ppo. The engine modules remain unchanged.
"""
import time
import numpy as np
import torch
import train_ppo as epic
from ppo import PPOTrainer
from train_common import UE_RESPONSE_SUCCESS, schema_log_prob, schema_entropy, schema_regularization


def clipped_log_surrogate(log_ratio, advantages, clip_min, clip_max):
    """Keep UE's log surrogate but clip on the correct side for each sign."""
    return torch.minimum(log_ratio * advantages,
                         log_ratio.clamp(clip_min, clip_max) * advantages)


def require_finite(name, value):
    if not torch.isfinite(value).all():
        raise FloatingPointError('Non-finite ' + name + '; refusing to publish invalid network weights')


def checked_gradient_norm(parameters, maximum):
    parameters = [p for p in parameters if p.grad is not None]
    if not parameters:
        return 0.0
    norm = torch.nn.utils.clip_grad_norm_(parameters, maximum, error_if_nonfinite=True)
    return float(norm)


def gae(rewards, values, next_values, terminated, truncated, gamma, lam):
    """Bootstrap time limits, stop recursion at either episode boundary."""
    delta = rewards + (~terminated) * gamma * next_values - values
    continuation = (~(terminated | truncated)) * gamma * lam
    advantages = np.empty_like(delta)
    following = 0.0
    for index in range(len(delta) - 1, -1, -1):
        following = delta[index] + continuation[index] * following
        advantages[index] = following
    return advantages, advantages + values


class HomeostaticPPOTrainer(PPOTrainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Also guard the engine's critic optimizer before it can mutate weights.
        def check_step(optimizer, args, kwargs):
            for group in optimizer.param_groups:
                for parameter in group['params']:
                    if parameter.grad is not None:
                        require_finite('optimizer gradient', parameter.grad)
        self.optim_critic.register_step_pre_hook(check_step)
        self.optim_policy.register_step_pre_hook(check_step)

    def train_policy(self, mask, obs, act, mem, adv, logp, policy_window):
        self.optim_policy.zero_grad()
        loss_surr = loss_ent = loss_reg = 0.0
        policy_mem = mem[:, 0]
        for index in range(policy_window):
            output = self.policy(torch.cat([self.encoder(obs[:, index]), policy_mem], dim=-1))
            encoded, policy_mem = output[:, :self.act_enc_num], output[:, self.act_enc_num:]
            distribution = self.decoder(encoded)
            require_finite('policy distribution', distribution)
            ratio = schema_log_prob(self.action_schema, distribution, act[:, index]) - logp[:, index]
            require_finite('policy log probability ratio', ratio)
            surrogate = clipped_log_surrogate(ratio, adv[:, index],
                                             self.eps_clip_log_min, self.eps_clip_log_max)
            loss_surr += self.action_surr_weight * (mask[:, index] * -surrogate / self.act_num).mean() / policy_window
            loss_ent += self.action_ent_weight * (mask[:, index] * -schema_entropy(self.action_schema, distribution) / self.act_num).mean() / policy_window
            loss_reg += self.action_reg_weight * (mask[:, index] * schema_regularization(self.action_schema, distribution) / self.act_num).mean() / policy_window
        loss = loss_surr + loss_ent + loss_reg
        require_finite('policy loss', loss)
        loss.backward()
        groups = [list(self.encoder.parameters()), list(self.decoder.parameters()), list(self.policy.parameters())]
        maximum = self.grad_norm_max if self.use_grad_norm_max_clipping else float('inf')
        norms = [checked_gradient_norm(group, maximum) for group in groups]
        self.optim_policy.step()
        for name, network in [('encoder', self.encoder), ('decoder', self.decoder), ('policy', self.policy)]:
            for parameter in network.parameters(): require_finite(name + ' parameters', parameter)
        return (*norms, loss_surr.item(), loss_ent.item(), loss_reg.item(), loss.item())

    def compute_advantages_and_returns(self, obs, obs_next, mem, mem_next,
                                      rew, terminated, truncated,
                                      warn_about_advantages=True):
        with torch.no_grad():
            values = self.critic(torch.cat([self.encoder(obs), mem], dim=-1))[..., 0].cpu().numpy()
            next_values = self.critic(torch.cat([self.encoder(obs_next), mem_next], dim=-1))[..., 0].cpu().numpy()
        advantages, returns = gae(rew, values, next_values, terminated, truncated,
                                 self.discount_factor, self.gae_lambda)
        if self.adv_norm:
            advantages = (advantages - advantages.mean()) / max(advantages.std(), 1e-8)
        advantages = np.clip(advantages, self.adv_min, self.adv_max)
        return (torch.as_tensor(advantages, device=self.policy.device),
                torch.as_tensor(returns, device=self.policy.device), returns.mean())


def setpoint_column(config):
    schema = config['Schemas']['Observations'][0]['Schema']
    elements = schema.get('Elements', {})
    field = elements.get('SetpointDistance')
    if schema.get('Type') != 'And' or not field or field['VectorSize'] != 1:
        raise ValueError('Expected scalar SetpointDistance in the observation schema')
    return sum(x['VectorSize'] for x in elements.values() if x['Index'] < field['Index'])


class TelemetryCommunicator:
    def __init__(self, communicator, config, writer_getter):
        self.communicator = communicator
        self.writer_getter = writer_getter
        self.column = setpoint_column(config)
        self.steps = 0
        self.started = time.monotonic()

    def __getattr__(self, name):
        return getattr(self.communicator, name)

    def send_network(self, network_id, network):
        for parameter in network.parameters():
            require_finite('outgoing network ' + str(network_id), parameter)
        return self.communicator.send_network(network_id, network)

    def receive_experience(self, *args, **kwargs):
        start = time.monotonic()
        result = self.communicator.receive_experience(*args, **kwargs)
        response, buffer, stats = result
        if response == UE_RESPONSE_SUCCESS:
            observations = buffer['obs'][0]
            count = len(observations)
            self.steps += count
            writer = self.writer_getter()
            if writer is not None and count:
                # SpecifyFloatObservation uses FloatScale=100 in BP_AgentInteractor.
                homeostasis = observations[:, self.column] * 100.0
                for tag, value in {
                    'homeostasis/mean_absolute_error': np.abs(homeostasis).mean(),
                    'homeostasis/root_mean_square_error': np.sqrt(np.square(homeostasis).mean()),
                    'homeostasis/fraction_within_5': (np.abs(homeostasis) <= 5.0).mean(),
                    'homeostasis/mean_signed_value': homeostasis.mean(),
                    'throughput/collected_steps': self.steps,
                    'throughput/steps_per_second': self.steps / max(time.monotonic()-self.started, 1e-6),
                    'throughput/collection_seconds': time.monotonic()-start,
                }.items():
                    writer.add_scalar(tag, float(value), self.steps)
                writer.flush()
        return result


def train(config, communicator):
    from torch.utils import tensorboard
    original_writer = tensorboard.SummaryWriter
    original_trainer = epic.PPOTrainer
    writers = []

    class TaskWriter(original_writer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            writers.append(self)

    tensorboard.SummaryWriter = TaskWriter
    epic.PPOTrainer = HomeostaticPPOTrainer
    try:
        proxy = TelemetryCommunicator(communicator, config, lambda: writers[-1] if writers else None)
        epic.train(config, proxy)
    finally:
        for writer in writers:
            writer.close()
        tensorboard.SummaryWriter = original_writer
        epic.PPOTrainer = original_trainer

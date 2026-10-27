"""Opt-in HRL PPO with bounded updates, recurrent coverage and diagnostics."""
import copy
import math
import numpy as np
import torch
from homeostatic_ppo import HomeostaticPPOTrainer, require_finite
from train_common import schema_log_prob, schema_entropy, schema_regularization
from profiles import schedule


def recurrent_windows(terminated, truncated, width):
    """Include every possible start, including the last transition; mask padding."""
    done = np.asarray(terminated, dtype=bool) | np.asarray(truncated, dtype=bool)
    if not len(done) or width < 1:
        raise ValueError('Empty experience or invalid recurrent width')
    raw = np.arange(len(done))[:, None] + np.arange(width)[None, :]
    indices = np.minimum(raw, len(done)-1)
    ends = done[indices]
    prior_ends = np.concatenate([np.zeros((len(done),1),dtype=int), np.cumsum(ends[:,:-1],axis=1)],axis=1)
    return indices, (raw < len(done)) & (prior_ends == 0)


def surrogate(log_ratio, advantage, epsilon, objective):
    if objective == 'log':
        return torch.minimum(log_ratio*advantage,
                             log_ratio.clamp(math.log1p(-epsilon),math.log1p(epsilon))*advantage)
    if objective != 'ratio':
        raise ValueError(objective)
    ratio = log_ratio.exp()
    return torch.minimum(ratio*advantage, ratio.clamp(1-epsilon,1+epsilon)*advantage)


def norm(parameters):
    values = []
    for p in parameters:
        if p.grad is not None:
            require_finite('gradient',p.grad)
            values.append(torch.linalg.vector_norm(p.grad.detach().to(torch.float64)))
    return float(torch.linalg.vector_norm(torch.stack(values))) if values else 0.


class GuardedTrainer(HomeostaticPPOTrainer):
    def __init__(self, *args, profile, record=lambda data: None, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile, self.record = profile, record
        self.steps = self.accepted = self.rejected = 0
        self.actor_stopped = False
        self.diagnostics = {}
        self.base_lrs = [g['lr'] for g in self.optim_policy.param_groups]
        self.base_critic_lrs = [g['lr'] for g in self.optim_critic.param_groups]
        # Critic updates cannot bypass the actor's KL limit through shared features.
        encoder_ids = {id(p) for p in self.encoder.parameters()}
        for group in self.optim_critic.param_groups:
            group['params'] = [p for p in group['params'] if id(p) not in encoder_ids]

    def distribution(self, obs, mem, width):
        state = mem[:,0]
        distributions = []
        for i in range(width):
            output = self.policy(torch.cat([self.encoder(obs[:,i]), state],dim=-1))
            encoded, state = output[:,:self.act_enc_num], output[:,self.act_enc_num:]
            distributions.append(self.decoder(encoded))
        return distributions

    def log_ratios(self, distributions, act, logp):
        return torch.stack([schema_log_prob(self.action_schema,d,act[:,i])-logp[:,i]
                            for i,d in enumerate(distributions)],dim=1)

    def approximate_kl(self, log_ratio, weights):
        # Abort before exponentiation if ratios would become numerically extreme.
        valid = log_ratio[weights.bool()]
        if not torch.isfinite(valid).all() or (valid.abs()>20).any():
            return float('inf')
        safe = torch.where(weights.bool(),log_ratio,torch.zeros_like(log_ratio))
        return float((weights * (safe.exp()-1-safe)).sum()/weights.sum().clamp_min(1))

    def train_policy(self, mask, obs, act, mem, adv, logp, policy_window):
        if self.actor_stopped:
            return (0.,)*7
        self.optim_policy.zero_grad()
        weights = mask.to(obs.dtype)
        count = weights.sum().clamp_min(1)
        distributions = self.distribution(obs,mem,policy_window)
        log_ratio = self.log_ratios(distributions,act,logp)
        log_ratio = torch.where(mask.bool(),log_ratio,torch.zeros_like(log_ratio))
        before_kl = self.approximate_kl(log_ratio.detach(),weights)
        self.diagnostics['approx_kl_before'] = before_kl if math.isfinite(before_kl) else None
        if before_kl > self.profile.target_kl:
            self.rejected += 1
            self.actor_stopped = True
            return (0.,)*7
        epsilon = self.profile.clip
        surr = -(weights*surrogate(log_ratio,adv,epsilon,self.profile.objective)).sum()/count*self.action_surr_weight/self.act_num
        entropy = torch.stack([schema_entropy(self.action_schema,d) for d in distributions],dim=1)
        regularization = torch.stack([schema_regularization(self.action_schema,d) for d in distributions],dim=1)
        ent = -(weights*entropy).sum()/count*self.action_ent_weight/self.act_num
        reg = (weights*regularization).sum()/count*self.action_reg_weight/self.act_num
        loss = surr+ent+reg
        require_finite('HRL policy loss',loss)
        loss.backward()
        groups = [list(self.encoder.parameters()),list(self.decoder.parameters()),list(self.policy.parameters())]
        norms = [norm(group) for group in groups]
        parameters = [p for group in groups for p in group]
        torch.nn.utils.clip_grad_norm_(parameters,self.profile.grad_norm,error_if_nonfinite=True)
        previous = [p.detach().clone() for p in parameters]
        optimizer_state = copy.deepcopy(self.optim_policy.state_dict())
        self.optim_policy.step()
        with torch.no_grad():
            new_ratio = self.log_ratios(self.distribution(obs,mem,policy_window),act,logp)
            after_kl = self.approximate_kl(new_ratio,weights)
        self.diagnostics.update(approx_kl_after=after_kl if math.isfinite(after_kl) else None,
            clip_fraction=float((weights*(log_ratio.exp().sub(1).abs()>epsilon)).sum()/count),
            actor_gradient_norm=math.sqrt(sum(x*x for x in norms)))
        if after_kl > self.profile.target_kl:
            with torch.no_grad():
                for p, old in zip(parameters,previous):p.copy_(old)
            self.optim_policy.load_state_dict(optimizer_state)
            self.rejected += 1
            self.actor_stopped = True
            self.diagnostics['rolled_back'] = True
        else:
            self.accepted += 1
            self.diagnostics['rolled_back'] = False
        for parameter in parameters:require_finite('updated HRL policy',parameter)
        return (*norms,float(surr.detach()),float(ent.detach()),float(reg.detach()),float(loss.detach()))

    def train_critic(self, obs, mem, returns):
        self.optim_critic.zero_grad()
        with torch.no_grad():features = self.encoder(obs)
        prediction = self.critic(torch.cat([features,mem],dim=-1))[...,0]
        # Preserve UE's absolute-error critic objective; isolate ownership/guard changes.
        loss_ret = (prediction-returns).abs().mean()
        loss_reg = self.return_reg_weight*prediction.abs().mean()
        loss = loss_ret+loss_reg
        require_finite('HRL critic loss',loss)
        loss.backward()
        parameters = list(self.critic.parameters())
        magnitude = norm(parameters)
        torch.nn.utils.clip_grad_norm_(parameters,self.profile.grad_norm,error_if_nonfinite=True)
        self.optim_critic.step()
        for parameter in parameters:require_finite('updated HRL critic',parameter)
        self.diagnostics['critic_gradient_norm'] = magnitude
        return (0.,magnitude,float(loss_ret.detach()),float(loss_reg.detach()),float(loss.detach()))

    def train(self, buffer, policy_batch_size, critic_batch_size, iterations, policy_window, update_func=None):
        obs,obs_next,act,mem,mem_next,rew,terminated,truncated = self.extract_from_buffer(buffer)
        self.steps += len(obs)
        current = schedule(self.profile,self.steps)
        self.action_ent_weight = current['entropy']
        for group,base in zip(self.optim_policy.param_groups,self.base_lrs):group['lr']=base*current['lr_fraction']
        for group,base in zip(self.optim_critic.param_groups,self.base_critic_lrs):group['lr']=base*current['lr_fraction']
        self.actor_stopped = False
        self.diagnostics = dict(steps=self.steps,entropy_weight=self.action_ent_weight,
                                policy_lr=self.optim_policy.param_groups[0]['lr'])
        adv,returns,return_mean = self.compute_advantages_and_returns(obs,obs_next,mem,mem_next,rew,terminated,truncated)
        with torch.no_grad():
            prediction = self.critic(torch.cat([self.encoder(obs),mem],dim=-1))[...,0]
            variance = float(torch.var(returns,unbiased=False))
            self.diagnostics['explained_variance'] = 1-float(torch.var(returns-prediction,unbiased=False))/variance if variance>1e-12 else None
        old_logp = self.compute_old_logp(obs,mem,act)
        index,mask = recurrent_windows(terminated,truncated,policy_window)
        index = torch.as_tensor(index,device=self.policy.device,dtype=torch.long)
        mask = torch.as_tensor(mask,device=self.policy.device)
        keys = ['grads/encoder','grads/decoder','grads/policy','grads/critic','loss/critic_ret',
                'loss/critic_reg','loss/critic','loss/policy_surr','loss/policy_ent','loss/policy_reg','loss/policy']
        stats = {key:[] for key in keys}
        for _ in range(iterations):
            ci = torch.randint(len(obs),(critic_batch_size,),device=self.policy.device)
            ce,cg,cr,creg,cl = self.train_critic(obs[ci],mem[ci],returns[ci])
            pi = torch.randint(len(index),(policy_batch_size,),device=self.policy.device)
            ix = index[pi]
            pe,dg,pg,ps,pen,pr,pl = self.train_policy(mask[pi],obs[ix],act[ix],mem[ix],adv[ix],old_logp[ix],policy_window)
            values = [(ce+pe)/2,dg,pg,cg,cr,creg,cl,ps,pen,pr,pl]
            for key,value in zip(keys,values):stats[key].append(value)
            if update_func:update_func()
        self.diagnostics.update(accepted_actor_updates=self.accepted,rejected_actor_updates=self.rejected,
                                actor_stopped_this_gather=self.actor_stopped,
                                recurrent_starts=len(index),recurrent_valid_steps=int(mask.sum()))
        self.record(self.diagnostics)
        return {**stats,'experience/avg_return':return_mean}

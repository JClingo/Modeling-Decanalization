"""Explicit HRL experiments; each profile is a hypothesis, not a selected winner."""
from dataclasses import asdict, dataclass, replace
import math

@dataclass(frozen=True)
class Profile:
    name: str = 'baseline'
    reward: str = 'quality'
    distance_scale: float = 25.
    discount: float = .99
    gae_lambda: float = .95
    window: int = 16
    policy_batch: int = 2056
    critic_batch: int = 4096
    updates: int = 32
    policy_lr: float = 1e-4
    critic_lr: float = 1e-3
    entropy_start: float = .001
    entropy_end: float = .001
    anneal_steps: int = 2000000
    lr_end_fraction: float = 1.
    guarded: bool = False
    objective: str = 'log'
    target_kl: float = .015
    clip: float = .2
    grad_norm: float = .5
    dt: float = .05
    failure_boundary: float = 100.
    failure_reward: float = -1.
    segment_steps: int = 1028
    episode_seconds: float = 100.
    reset_world_on_update: bool = True

    def validate(self):
        for key, value in asdict(self).items():
            if isinstance(value, (float, int)) and not math.isfinite(value):
                raise ValueError(key + ' must be finite')
        if self.reward not in ('quality', 'absolute') or self.objective not in ('log', 'ratio'):
            raise ValueError('Unknown reward or policy objective')
        if not 0 < self.discount < 1 or not 0 <= self.gae_lambda <= 1:
            raise ValueError('Invalid discount/GAE')
        if not 0 < self.clip < 1 or self.distance_scale < .001 or self.dt <= 0 or self.failure_boundary <= 0:
            raise ValueError('Invalid reward/clip scale')
        if self.dt != .05 or self.failure_boundary != 100.:
            raise ValueError('This native runner requires dt=.05 and the existing training failure boundary of 100')
        for key in ('window', 'policy_batch', 'critic_batch', 'updates', 'anneal_steps'):
            if not isinstance(getattr(self, key), int) or getattr(self, key) < 1:
                raise ValueError(key + ' must be a positive integer')
        if not isinstance(self.segment_steps,int) or not 1 <= self.segment_steps <= 10000:
            raise ValueError('Experience segment must fit the 10,000-transition native replay buffer')
        if self.episode_seconds <= 0:
            raise ValueError('World episode duration must be positive')
        if not isinstance(self.reset_world_on_update,bool):
            raise ValueError('World reset control must be boolean')
        if min(self.policy_lr, self.critic_lr, self.grad_norm, self.target_kl) <= 0:
            raise ValueError('Learning/update limits must be positive')
        if min(self.entropy_start, self.entropy_end) < 0 or not 0 < self.lr_end_fraction <= 1:
            raise ValueError('Invalid annealing schedule')
        if not self.guarded and (self.entropy_start != self.entropy_end or self.lr_end_fraction != 1):
            raise ValueError('Schedules require guarded trainer')
        return self

    def terminal_reward(self):
        if self.reward == 'absolute':
            # Continuing discounted absorbing failure state at the boundary.
            # This includes the failing transition and prevents escape from costs.
            return -self.dt * self.failure_boundary / self.distance_scale / (1-self.discount)
        return self.failure_reward

    def ppo_settings(self):
        return dict(LearningRatePolicy=self.policy_lr, LearningRateCritic=self.critic_lr,
                    PolicyBatchSize=self.policy_batch, CriticBatchSize=self.critic_batch,
                    PolicyWindow=self.window, IterationsPerGather=self.updates,
                    DiscountFactor=self.discount, GaeLambda=self.gae_lambda,
                    ActionEntropyWeight=self.entropy_start, EpsilonClip=self.clip,
                    UseGradNormMaxClipping=True, GradNormMax=self.grad_norm,
                    AdvantageNormalization=True, AdvantageMin=-10., AdvantageMax=10.,
                    TrimEpisodeStartStepNum=0, TrimEpisodeEndStepNum=0,
                    LearningRateDecay=1., CriticWarmupIterations=8)

    def contract(self):
        return {**asdict(self.validate()), 'terminal_reward': self.terminal_reward(),
                'failure_accounting': 'discounted-absorbing-boundary' if self.reward == 'absolute' else 'native-terminal-penalty'}

BASE = Profile()
PROFILES = {p.name: p.validate() for p in [
    BASE,
    replace(BASE, name='quality-10', distance_scale=10.),
    replace(BASE, name='absolute-25', reward='absolute'),
    replace(BASE, name='ratio-only', objective='ratio'),
    replace(BASE, name='horizon-32', discount=.995, window=32, policy_batch=1024),
    replace(BASE, name='horizon-64', discount=.9975, window=64, policy_batch=512),
    replace(BASE, name='credit-64', discount=.9975, gae_lambda=.97, window=64, policy_batch=512),
    replace(BASE, name='guarded-log', guarded=True, updates=16, clip=.1),
    replace(BASE, name='guarded-ratio', guarded=True, objective='ratio', updates=16, clip=.1),
    replace(BASE, name='guarded-annealed', guarded=True, objective='ratio', updates=8,
            policy_lr=3e-5, critic_lr=3e-4, entropy_end=.0001, lr_end_fraction=.1, clip=.1),
    replace(BASE, name='segment-100s', segment_steps=2000),
    replace(BASE, name='canalization-300s', episode_seconds=300.),
    replace(BASE, name='canalization-persistent', episode_seconds=300., reset_world_on_update=False),
    replace(BASE, name='canalization-aware', episode_seconds=300., segment_steps=6000, reset_world_on_update=False, discount=.9975, gae_lambda=.97,
            window=64, policy_batch=512, guarded=True, objective='ratio', updates=8,
            policy_lr=3e-5, critic_lr=3e-4, entropy_end=.0001, lr_end_fraction=.1, clip=.1),
]}
STAGES = {'reward': ['baseline', 'quality-10', 'absolute-25'],
          'horizon': ['baseline', 'horizon-32', 'horizon-64', 'credit-64'],
          'stability': ['baseline', 'guarded-log', 'guarded-ratio', 'guarded-annealed'],
          'canalization': ['baseline','canalization-300s','canalization-persistent'],
          'canalization-learning': ['baseline','canalization-aware']}

def load_profile(data):
    return Profile(**{k:v for k,v in data.items() if k in Profile.__dataclass_fields__}).validate()

def schedule(profile, steps):
    fraction = min(max(steps / profile.anneal_steps, 0.), 1.)
    return dict(entropy=profile.entropy_start + fraction*(profile.entropy_end-profile.entropy_start),
                lr_fraction=1. + fraction*(profile.lr_end_fraction-1.))

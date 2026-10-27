"""Standard probability-ratio PPO surrogate, with the existing clip bounds."""
import math
import torch

def ratio_surrogate(log_ratio,advantages,clip_min,clip_max):
    ratio=log_ratio.exp()
    return torch.minimum(ratio*advantages,
        ratio.clamp(math.exp(clip_min),math.exp(clip_max))*advantages)

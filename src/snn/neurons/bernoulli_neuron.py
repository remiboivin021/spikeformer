"""Bernoulli Neuron Layer (BNL) implementation.

Reference: Xpikeformer paper, Section II-B
Stateless (unlike LIF) - used for spike generation in SSA.
Input real value x ∈ [0,1] → spike s[t] ~ Bern(x)
"""

import torch
import torch.nn as nn
from typing import Optional


class BernoulliNeuron(nn.Module):
    """Bernoulli Neuron for spike generation.
    
    Generates spikes according to Bernoulli distribution:
        P(spike = 1) = x
        P(spike = 0) = 1 - x
    
    Used in the Stochastic Spiking Attention (SSA) engine.
    Unlike LIF, this neuron is stateless - each timestep
    is independent given the input probability.
    """
    
    def __init__(
        self,
        threshold: float = 0.5,
        batch_first: bool = True,
    ):
        """Initialize Bernoulli neuron.
        
        Args:
            threshold: Threshold for hard thresholding. Default: 0.5
            batch_first: If True, expects input shape (batch, ...). Default: True
        """
        super().__init__()
        self.threshold = threshold
        self.batch_first = batch_first
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Generate Bernoulli spikes.
        
        Args:
            x: Input tensor of probabilities in [0, 1]
               Shape: (batch, ...) if batch_first=True
        
        Returns:
            Binary spike tensor {0, 1} with same shape as input
        """
        # Clamp input to [0, 1] for valid probabilities
        p = torch.clamp(x, min=0.0, max=1.0)
        
        # Bernoulli sampling: spike ~ Bern(p)
        spike = torch.bernoulli(p)
        
        # Optional hard thresholding
        if self.threshold > 0:
            spike = (spike >= self.threshold).float()
        
        return spike


def bernoulli_sample(p: torch.Tensor) -> torch.Tensor:
    """Bernoulli sampling (functional version).
    
    Args:
        p: Probability tensor in [0, 1]
    
    Returns:
        Binary spike tensor {0, 1}
    """
    p_clamped = torch.clamp(p, min=0.0, max=1.0)
    return torch.bernoulli(p_clamped)


def rate_to_spike_batch(
    rates: torch.Tensor,
    T: int,
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """Convert rate tensor to spike trains over T timesteps.
    
    Args:
        rates: Rate tensor (batch, n_neurons) in [0, 1]
        T: Number of timesteps
        device: Target device
    
    Returns:
        Spike tensor (batch, n_neurons, T)
    """
    batch_size, n_neurons = rates.shape
    p = torch.clamp(rates, min=0.0, max=1.0)
    
    # Expand for T timesteps
    p_expanded = p.unsqueeze(-1).expand(batch_size, n_neurons, T)
    
    # Bernoulli sampling for each timestep
    spikes = torch.bernoulli(p_expanded)
    
    return spikes


class RateNormalizer(nn.Module):
    """Normalizes input to [0, 1] range for Bernoulli encoding."""
    
    def __init__(
        self,
        method: str = "sigmoid",
        learn_gamma: bool = False,
    ):
        """Initialize rate normalizer.
        
        Args:
            method: Normalization method. Options: 'sigmoid', 'linear', 'relu'
            learn_gamma: If True, gamma is learnable. Default: False
        """
        super().__init__()
        self.method = method
        
        if learn_gamma:
            self.gamma = nn.Parameter(torch.tensor(1.0))
        else:
            self.gamma = 1.0
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Normalize input to [0, 1].
        
        Args:
            x: Input tensor
        
        Returns:
            Normalized tensor in [0, 1]
        """
        if self.method == "sigmoid":
            return torch.sigmoid(x / self.gamma)
        elif self.method == "relu":
            return torch.clamp(x / self.gamma, min=0.0, max=1.0)
        elif self.method == "linear":
            # Linear scaling to [0, 1]
            x_min = x.min(dim=-1, keepdim=True)[0]
            x_max = x.max(dim=-1, keepdim=True)[0]
            return (x - x_min) / (x_max - x_min + 1e-8)
        else:
            return torch.clamp(x / self.gamma, min=0.0, max=1.0)
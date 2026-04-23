"""Bernoulli Encoder for spike encoding.

Reference: Xpikeformer paper, Section II-B
Converts real values x ∈ [0,1] to spike trains s[t] ~ Bern(x)
over T timesteps. Spike rate converges to x as T → ∞.
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple


class BernoulliEncoder(nn.Module):
    """Bernoulli spike encoder.
    
    Converts input values to spike trains using Bernoulli sampling.
    Each timestep samples independently from Bern(x) where x is the
    input probability.
    
    For T timesteps, the empirical spike rate converges to x:
        E[spike_rate] ≈ x for large T
    """
    
    def __init__(
        self,
        T: int = 8,
        batch_first: bool = True,
    ):
        """Initialize Bernoulli encoder.
        
        Args:
            T: Number of timesteps for spike encoding. Default: 8
            batch_first: If True, expects input shape (batch, features).
                         Default: True
        """
        super().__init__()
        self.T = T
        self.batch_first = batch_first
    
    def forward(
        self,
        x: torch.Tensor,
        T: Optional[int] = None,
    ) -> torch.Tensor:
        """Encode input to spike trains.
        
        Args:
            x: Input tensor of values in [0, 1]
               Shape: (batch, features) if batch_first=True
            T: Override number of timesteps (optional)
        
        Returns:
            Spike tensor (batch, features, T) or (batch, T, features)
               depending on batch_first setting
        """
        T_actual = T if T is not None else self.T
        
        # Clamp to valid probability range
        p = torch.clamp(x, min=0.0, max=1.0)
        
        # Expand for T timesteps
        if self.batch_first:
            # (batch, features) -> (batch, features, T)
            p_expanded = p.unsqueeze(-1).expand(*p.shape, T_actual)
        else:
            # (features, batch) -> (T, features, batch)
            p_expanded = p.unsqueeze(0).expand(T_actual, *p.shape)
        
        # Bernoulli sampling per timestep
        spikes = torch.bernoulli(p_expanded)
        
        return spikes
    
    def encode(
        self,
        x: torch.Tensor,
        T: Optional[int] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode with spike rate statistics.
        
        Args:
            x: Input tensor
            T: Override timesteps
        
        Returns:
            Tuple of (spike_train, spike_rate)
                spike_train: (batch, features, T)
                spike_rate: (batch, features) empirical rate
        """
        spikes = self.forward(x, T)
        spike_rate = spikes.float().mean(dim=-1 if self.batch_first else -3)
        return spikes, spike_rate


def encode_bernoulli(
    x: torch.Tensor,
    T: int = 8,
    batch_first: bool = True,
) -> torch.Tensor:
    """Bernoulli spike encoding (functional version).
    
    Args:
        x: Input tensor in [0, 1]
        T: Number of timesteps. Default: 8
        batch_first: Input format. Default: True
    
    Returns:
        Spike train tensor
    """
    encoder = BernoulliEncoder(T=T, batch_first=batch_first)
    return encoder(x)


def compute_spike_rate(spikes: torch.Tensor, T: int) -> torch.Tensor:
    """Compute empirical spike rate from spike trains.
    
    Args:
        spikes: Spike tensor (..., T)
        T: Number of timesteps
    
    Returns:
        Spike rate tensor (excluding T dimension)
    """
    return spikes.float().sum(dim=-1) / T


def validate_rate_convergence(
    x: torch.Tensor,
    T: int,
    atol: float = 0.02,
) -> bool:
    """Validate that spike rate converges to input probability.
    
    Args:
        x: Input probabilities in [0, 1]
        T: Number of timesteps
        atol: Absolute tolerance. Default: 0.02
    
    Returns:
        True if |empirical_rate - x| <= atol for all inputs
    """
    batch_size = x.shape[0]
    
    # Generate spike trains
    p = torch.clamp(x, min=0.0, max=1.0)
    p_expanded = p.unsqueeze(-1).expand(batch_size, x.shape[-1], T)
    spikes = torch.bernoulli(p_expanded)
    
    # Compute empirical rates
    empirical_rate = spikes.float().mean(dim=-1)
    
    # Check convergence
    return torch.allclose(empirical_rate, x, atol=atol)
"""Leaky Integrate-and-Fire (LIF) neuron implementation.

Reference: Xpikeformer paper, Equation (2)
V_t = β · V_{t-1} + I_t
Reset on spike: V_t = 0 if V_t >= V_thresh
"""

import torch
import torch.nn as nn
from typing import Tuple


class LeakyIntegrateAndFire(nn.Module):
    """Leaky Integrate-and-Fire neuron.
    
    Implements the membrane dynamics from Equation (2) of the Xpikeformer paper:
    
        V[t] = β · V[t-1] + I[t]
    
    where:
        - V is the membrane potential
        - β is the decay factor (leak)
        - I is the input current
        - spikes are emitted when V >= V_thresh
        - V is reset to 0 after spike emission
    """
    
    def __init__(
        self,
        beta: float = 0.95,
        threshold: float = 1.0,
        spike_reset: bool = True,
    ):
        """Initialize LIF neuron.
        
        Args:
            beta: Decay factor (leak). Default: 0.95
            threshold: Spike threshold. Default: 1.0
            spike_reset: If True, reset membrane to 0 after spike. Default: True
        """
        super().__init__()
        self.beta = beta
        self.threshold = threshold
        self.spike_reset = spike_reset
    
    def forward(
        self,
        x: torch.Tensor,
        mem: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute LIF update.
        
        Args:
            x: Input tensor (batch, ...)
            mem: Previous membrane potential (batch, ...)
        
        Returns:
            spk: Spike tensor (batch, ...) - binary {0, 1}
            mem: Updated membrane potential (batch, ...)
        """
        # Membrane dynamics: V_t = β · V_{t-1} + I_t
        mem = self.beta * mem + x
        
        # Spike generation: spike if V >= V_thresh
        spk = (mem >= self.threshold).float()
        
        # Reset membrane on spike
        if self.spike_reset:
            mem = mem * (1.0 - spk)
        
        return spk, mem
    
    def init_mem(self, *shape, batch_size=None, device=None, dtype=torch.float32):
        """Initialize membrane potential to zero.
        
        Args:
            *shape: Spatial dimensions (if batch_size not provided)
            batch_size: Number of samples in batch (alternative to *shape)
            device: torch device
            dtype: torch data type
        
        Returns:
            Membrane potential tensor initialized to 0
        """
        if batch_size is not None:
            # batch_size was passed as first positional arg
            return torch.zeros(batch_size, *shape, device=device, dtype=dtype)
        else:
            # shape was passed directly
            return torch.zeros(*shape, device=device, dtype=dtype)


class SurrogateGradientFastSigmoid(nn.Module):
    """Fast sigmoid surrogate gradient.
    
    Used for backpropagation through the non-differentiable spike function.
    The surrogate gradient approximates d spike / d V using a fast sigmoid.
    """
    
    def __init__(self, alpha: float = 1.0):
        """Initialize surrogate gradient.
        
        Args:
            alpha: Steepness parameter. Default: 1.0
        """
        super().__init__()
        self.alpha = alpha
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Compute surrogate gradient.
        
        Args:
            x: Membrane potential
        
        Returns:
            Surrogate gradient approximation
        """
        return torch.sigmoid(self.alpha * x)


def fast_sigmoid(x: torch.Tensor, alpha: float = 1.0) -> torch.Tensor:
    """Fast sigmoid surrogate gradient (functional version).
    
    Args:
        x: Membrane potential tensor
        alpha: Steepness parameter. Default: 1.0
    
    Returns:
        Surrogate gradient d_spike/d_V
    """
    return torch.sigmoid(alpha * x)


def lif_step(
    x: torch.Tensor,
    mem: torch.Tensor,
    beta: float = 0.95,
    threshold: float = 1.0,
    spike_reset: bool = True,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """LIF step (functional version).
    
    Args:
        x: Input current
        mem: Membrane potential
        beta: Decay factor
        threshold: Spike threshold
        spike_reset: Reset membrane after spike
    
    Returns:
        Tuple of (spike, membrane potential)
    """
    # Membrane dynamics
    mem = beta * mem + x
    
    # Spike
    spk = (mem >= threshold).float()
    
    # Reset
    if spike_reset:
        mem = mem * (1.0 - spk)
    
    return spk, mem
"""Spike Sweep Architecture (SSA) modules for SpikeFormer.

Reference: Xpikeformer paper, Section II-C
Spike Sweep layer replaces rate coding with temporal spike coding.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class TemporalConvolver(nn.Module):
    """Temporal Convolver (TC) - Depthwise 3x3 convolution.
    
    Applies depthwise 3x3 convolution over spike time dimension.
    Input: (batch, channels, T) → Output: (batch, channels, T)
    
    The convolution kernel operates only on the temporal dimension (T),
    while each channel is processed independently.
    """
    
    def __init__(
        self,
        channels: int,
        kernel_size: int = 3,
    ):
        """Initialize Temporal Convolver.
        
        Args:
            channels: Number of spike channels
            kernel_size: Convolution kernel size (default: 3)
        """
        super().__init__()
        self.channels = channels
        self.kernel_size = kernel_size
        self.padding = kernel_size // 2
        
        # Each channel gets its own 1D conv kernel
        # Weight shape: (channels, 1, kernel_size)
        self.weight = nn.Parameter(
            torch.ones(channels, 1, kernel_size) / kernel_size
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply temporal convolution.
        
        Args:
            x: Input tensor (batch, channels, T)
        
        Returns:
            Convolved tensor (batch, channels, T)
        """
        # Depthwise conv: each channel processed independently
        # Using F.conv1d with grouped conv
        batch, channels, T = x.shape
        
        # Reshape for grouped conv: (batch, 1, T) per channel
        output = torch.zeros_like(x)
        
        for c in range(channels):
            # Apply 1D conv per channel
            output[:, c:c+1, :] = F.conv1d(
                x[:, c:c+1, :],
                self.weight[c:c+1, :, :],
                padding=self.padding,
                groups=1,
            )
        
        return output


class BNFBlock(nn.Module):
    """BNF Block: BatchNorm + Dropout + Linear (Feed-forward).
    
    Per paper Section II-C: BNF = BN → Dropout → FC
    Transforms channel dimensions while normalizing and regularizing.
    """
    
    def __init__(
        self,
        channels: int,
        dropout: float = 0.1,
        activation: str = "gelu",
    ):
        """Initialize BNF Block.
        
        Args:
            channels: Number of channels
            dropout: Dropout probability (default: 0.1)
            activation: Activation function (default: "gelu")
        """
        super().__init__()
        self.channels = channels
        self.dropout = dropout
        
        # LayerNorm over channel dimension (simpler than BatchNorm for this use case)
        # LayerNorm normalizes over (channels,) for each (batch, T) position
        self.norm = nn.LayerNorm(channels)
        
        # Dropout
        self.dropout_layer = nn.Dropout(p=dropout)
        
        # Linear transform (identity in paper - channels → channels)
        self.fc = nn.Linear(channels, channels)
        
        # Activation
        if activation == "gelu":
            self.activation = nn.GELU()
        elif activation == "relu":
            self.activation = nn.ReLU()
        else:
            self.activation = nn.Identity()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply BNF transform.
        
        Args:
            x: Input tensor (batch, channels, T)
        
        Returns:
            Transformed tensor (batch, channels, T)
        """
        # Apply norm per timestep: (batch, channels, T) → (batch, T, channels)
        x = x.transpose(1, 2)
        
        # Apply norm (over channel dimension)
        x = self.norm(x)
        
        # Apply dropout
        x = self.dropout_layer(x)
        
        # Apply FC per timestep
        x = self.fc(x)
        
        # Apply activation
        x = self.activation(x)
        
        # Transpose back to (batch, channels, T)
        x = x.transpose(1, 2)
        
        return x


class SSAModule(nn.Module):
    """Spike Sweep Architecture (SSA) Module.
    
    Per paper Section II-C:
    SSA = TC + BNF + BNL
    
    Combines:
    1. Temporal Convolver (TC) - depthwise 3x3 conv
    2. BNF Block - BN → Dropout → FC
    3. Bernoulli Neuron Layer (BNL) - spike generation
    4. LIF dynamics (integrated via BNL)
    
    Input: (batch, channels, T) - spike probabilities
    Output: (batch, channels, T) - binary spikes
    """
    
    def __init__(
        self,
        channels: int,
        kernel_size: int = 3,
        dropout: float = 0.1,
        use_bn: bool = True,
    ):
        """Initialize SSA Module.
        
        Args:
            channels: Number of spike channels
            kernel_size: TC kernel size (default: 3)
            dropout: BNF dropout probability (default: 0.1)
            use_bn: Use BatchNorm (default: True)
        """
        super().__init__()
        self.channels = channels
        
        # Temporal Convolver
        self.tc = TemporalConvolver(
            channels=channels,
            kernel_size=kernel_size,
        )
        
        # BNF Block
        self.bnf = BNFBlock(
            channels=channels,
            dropout=dropout if use_bn else 0.0,
        )
        
        # BNL is applied via the encoding layer externally
        # SSA outputs probabilities that get encoded by BernoulliEncoder
    
    def forward(
        self,
        x: torch.Tensor,
        temperature: float = 1.0,
    ) -> torch.Tensor:
        """Apply SSA transformation.
        
        Args:
            x: Input tensor (batch, channels, T) - spike probabilities
            temperature: Sampling temperature for BNL
        
        Returns:
            Output tensor (batch, channels, T) - transformed probabilities
        """
        # Apply temporal convolution
        x = self.tc(x)
        
        # Apply BNF
        x = self.bnf(x)
        
        # Return probabilities for BNL encoding
        return x


def create_ssa_module(
    channels: int,
    kernel_size: int = 3,
    dropout: float = 0.1,
) -> SSAModule:
    """Factory function to create SSA module.
    
    Args:
        channels: Number of channels
        kernel_size: TC kernel size
        dropout: Dropout probability
    
    Returns:
        Configured SSAModule
    """
    return SSAModule(
        channels=channels,
        kernel_size=kernel_size,
        dropout=dropout,
    )
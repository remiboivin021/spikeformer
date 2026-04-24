"""Multi-Head Self-Attention (MHSA) for SpikeFormer.

Reference: Xpikeformer paper, Section II-C
MHSA replaces standard self-attention with spike-based attention.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional


class SpikeMHSA(nn.Module):
    """Multi-Head Self-Attention for spike sequences.
    
    Per paper Section II-C:
    MHSA = MH (Multi-Head) + SA (Self-Attention)
    
    Uses spike trains as queries/keys/values,
    applies attention over temporal dimension.
    
    Input: (batch, channels, T)
    Output: (batch, channels, T)
    """
    
    def __init__(
        self,
        channels: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        bias: bool = True,
    ):
        """Initialize MHSA.
        
        Args:
            channels: Number of input channels
            num_heads: Number of attention heads
            dropout: Dropout probability
            bias: Use bias in QKV projection
        """
        super().__init__()
        self.channels = channels
        self.num_heads = num_heads
        self.head_dim = channels // num_heads
        
        assert self.head_dim * num_heads == channels, \
            f"channels {channels} must be divisible by num_heads {num_heads}"
        
        # Q, K, V projections
        self.qkv = nn.Linear(channels, channels * 3, bias=bias)
        
        # Output projection
        self.proj = nn.Linear(channels, channels, bias=bias)
        
        # Dropout
        self.dropout = nn.Dropout(p=dropout)
        
        # Scale factor
        self.scale = math.sqrt(self.head_dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply MHSA.
        
        Args:
            x: Input tensor (batch, channels, T)
        
        Returns:
            Output tensor (batch, channels, T)
        """
        batch, channels, T = x.shape
        
        # Transpose to (batch, T, channels) for linear projection
        x = x.transpose(1, 2)  # (batch, T, channels)
        
        # QKV projection: (batch, T, channels) -> (batch, T, channels*3)
        qkv = self.qkv(x)
        
        # Reshape: (batch, T, channels*3) -> (batch, T, num_heads, head_dim*3)
        qkv = qkv.reshape(batch, T, self.num_heads, 3, self.head_dim)
        
        # Transpose: (batch, T, num_heads, 3, head_dim) -> (3, batch, num_heads, T, head_dim)
        qkv = qkv.permute(3, 0, 2, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # Attention scores: (batch, num_heads, T, T)
        attn = (q @ k.transpose(-2, -1)) / self.scale
        
        # Softmax over temporal dimension
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        
        # Apply attention to values: (batch, num_heads, T, head_dim)
        out = attn @ v
        
        # Reshape: (batch, num_heads, T, head_dim) -> (batch, T, channels)
        out = out.transpose(1, 2).contiguous()
        out = out.reshape(batch, T, channels)
        
        # Output projection
        out = self.proj(out)
        
        # Transpose back: (batch, T, channels) -> (batch, channels, T)
        out = out.transpose(1, 2)
        
        return out


class MultiHeadAttention(nn.Module):
    """Standard Multi-Head Attention (for hybrid models).
    
    This is the classic transformer attention.
    Used in Hybrid phase for ANN↔SNN conversion.
    """
    
    def __init__(
        self,
        channels: int,
        num_heads: int = 4,
        dropout: float = 0.1,
        bias: bool = True,
    ):
        """Initialize MHA."""
        super().__init__()
        self.channels = channels
        self.num_heads = num_heads
        self.head_dim = channels // num_heads
        
        self.q_proj = nn.Linear(channels, channels, bias=bias)
        self.k_proj = nn.Linear(channels, channels, bias=bias)
        self.v_proj = nn.Linear(channels, channels, bias=bias)
        self.out_proj = nn.Linear(channels, channels, bias=bias)
        
        self.dropout = nn.Dropout(p=dropout)
        self.scale = math.sqrt(self.head_dim)
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input (batch, channels, T) or (batch, T, channels)
            mask: Optional attention mask
        
        Returns:
            Output tensor same shape
        """
        # Ensure (batch, T, channels)
        if x.dim() == 3 and x.shape[1] != x.shape[-1]:
            x = x.transpose(1, 2)
        
        batch, T, channels = x.shape
        
        # QKV
        q = self.q_proj(x).reshape(batch, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).reshape(batch, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).reshape(batch, T, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention
        attn = (q @ k.transpose(-2, -1)) / self.scale
        
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        
        # Apply
        out = attn @ v
        out = out.transpose(1, 2).reshape(batch, T, channels)
        out = self.out_proj(out)
        
        return out


def create_mhsa(
    channels: int,
    num_heads: int = 4,
    spike_based: bool = True,
    dropout: float = 0.1,
) -> nn.Module:
    """Factory to create MHSA module.
    
    Args:
        channels: Number of channels
        num_heads: Number of attention heads
        spike_based: Use spike-based attention (True) or standard (False)
        dropout: Dropout probability
    
    Returns:
        MHSA module
    """
    if spike_based:
        return SpikeMHSA(channels=channels, num_heads=num_heads, dropout=dropout)
    else:
        return MultiHeadAttention(channels=channels, num_heads=num_heads, dropout=dropout)
"""SpikeFormer: Full SNN Transformer Model.

Reference: Xpikeformer paper (arXiv:2408.08794v2)
Implements the complete SpikeFormer architecture:
- Input → BernoulliEncoder → [SSA + LIF] × N → Output

Architecture per paper Section II-C and V:
- LIF: Leaky Integrate-and-Fire neuron
- SSA: Spike Sweep Architecture (TC + BNF + BNL)
- MHSA: Multi-Head Self-Attention (optional)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, List

from src.snn.neurons.lif import LeakyIntegrateAndFire
from src.snn.encoding import BernoulliEncoder
from src.snn.architecture import SSAModule


class SpikeFormerLayer(nn.Module):
    """Single SpikeFormer layer.
    
    Combines SSA (Spike Sweep Architecture) with LIF dynamics.
    Per paper: Each layer consists of SSA followed by LIF neuron.
    
    Args:
        channels: Number of channels/features
        num_heads: Number of attention heads (default: 8)
        kernel_size: TC kernel size (default: 3)
        dropout: Dropout probability (default: 0.1)
        T: Number of timesteps for spike encoding
        use_mhsa: Include MHSA in layer (default: False)
    """
    
    def __init__(
        self,
        channels: int,
        num_heads: int = 8,
        kernel_size: int = 3,
        dropout: float = 0.1,
        T: int = 8,
        use_mhsa: bool = False,
    ):
        super().__init__()
        self.channels = channels
        self.T = T
        self.use_mhsa = use_mhsa
        
        # SSA Module per paper Section II-C
        self.ssa = SSAModule(
            channels=channels,
            kernel_size=kernel_size,
            dropout=dropout,
        )
        
        # LIF Neuron per paper Section II-A
        self.lif = LeakyIntegrateAndFire(
            beta=0.95,
            threshold=1.0,
        )
        
        # Optional MHSA (not in initial paper but added for completeness)
        if use_mhsa:
            from src.snn.attention import MultiHeadAttention
            self.mhsa = MultiHeadAttention(
                channels=channels,
                num_heads=num_heads,
                dropout=dropout,
            )
    
    def forward(
        self,
        x: torch.Tensor,
        mem: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through one SpikeFormer layer.
        
        Args:
            x: Input tensor (batch, channels, T)
            mem: Previous membrane potential (batch, channels, T), or None to init
        
        Returns:
            Tuple of (output, spike_history)
                - output: (batch, channels, T)
                - spike_history: membrane potentials for analysis
        """
        # Initialize membrane if not provided
        if mem is None:
            mem = torch.zeros_like(x)
        
        # Apply SSA transformation
        x = self.ssa(x)
        
        # Apply LIF dynamics
        spike_out, mem = self.lif(x, mem)
        
        return spike_out, mem


class SpikeFormerEncoder(nn.Module):
    """SpikeFormer encoder with multiple layers.
    
    Stacks N SpikeFormer layers as described in paper Section II-C.
    
    Args:
        num_layers: Number of encoder layers
        channels: Feature dimension
        num_heads: Attention heads (if using MHSA)
        kernel_size: TC kernel size
        dropout: Dropout probability
        T: Number of timesteps
        use_mhsa: Use MHSA in each layer
    """
    
    def __init__(
        self,
        num_layers: int = 4,
        channels: int = 256,
        num_heads: int = 8,
        kernel_size: int = 3,
        dropout: float = 0.1,
        T: int = 8,
        use_mhsa: bool = False,
    ):
        super().__init__()
        self.num_layers = num_layers
        self.channels = channels
        self.T = T
        
        # Stack of SpikeFormer layers
        self.layers = nn.ModuleList([
            SpikeFormerLayer(
                channels=channels,
                num_heads=num_heads,
                kernel_size=kernel_size,
                dropout=dropout,
                T=T,
                use_mhsa=use_mhsa,
            )
            for _ in range(num_layers)
        ])
        
        # Final layer norm
        self.norm = nn.LayerNorm(channels)
    
    def forward(
        self,
        x: torch.Tensor,
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """Forward pass through all layers.
        
        Args:
            x: Input tensor (batch, channels, T)
        
        Returns:
            Tuple of (output, spike_histories)
        """
        spike_histories = []
        
        for layer in self.layers:
            x, mem = layer(x)
            spike_histories.append(mem)
        
        # Final normalization
        # Transpose: (batch, channels, T) -> (batch, T, channels)
        x = x.transpose(1, 2)
        x = self.norm(x)
        x = x.transpose(1, 2)
        
        return x, spike_histories


class SpikeFormer(nn.Module):
    """SpikeFormer: Full SNN Transformer Model.
    
    Complete implementation of Xpikeformer paper architecture.
    
    Architecture:
        1. Input encoding (image → spike probabilities)
        2. Patch embedding (convolutional projection)
        3. N × SpikeFormerLayer (SSA + LIF)
        4. Classification head
        
    Args:
        image_size: Input image size (default: 224 for ImageNet)
        patch_size: Patch size for embedding (default: 16)
        channels: Feature dimension (default: 256)
        num_layers: Number of encoder layers (default: 4)
        num_heads: Attention heads (default: 8)
        num_classes: Output classes (default: 1000 for ImageNet)
        T: Number of timesteps (default: 8)
        dropout: Dropout probability (default: 0.1)
        kernel_size: TC kernel size (default: 3)
        use_mhsa: Include MHSA in layers (default: False)
    """
    
    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        channels: int = 256,
        num_layers: int = 4,
        num_heads: int = 8,
        num_classes: int = 1000,
        T: int = 8,
        dropout: float = 0.1,
        kernel_size: int = 3,
        use_mhsa: bool = False,
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.channels = channels
        self.num_layers = num_layers
        self.num_classes = num_classes
        self.T = T
        
        # Calculate number of patches
        num_patches = (image_size // patch_size) ** 2
        
        # Patch embedding: Conv stem
        self.patch_embed = nn.Sequential(
            nn.Conv2d(
                in_channels=3,
                out_channels=channels,
                kernel_size=patch_size,
                stride=patch_size,
            ),
            nn.Flatten(2),  # (batch, channels, num_patches)
        )
        
        # Learnable CLS token (optional, for classification)
        self.cls_token = nn.Parameter(torch.randn(1, 1, channels))
        
        # Learnable positional embedding
        self.pos_embed = nn.Parameter(
            torch.randn(1, num_patches + 1, channels)
        )
        
        # Bernoulli encoder for spike encoding
        self.encoder = BernoulliEncoder(T=T, batch_first=True)
        
        # SpikeFormer encoder
        self.encoder_layers = SpikeFormerEncoder(
            num_layers=num_layers,
            channels=channels,
            num_heads=num_heads,
            kernel_size=kernel_size,
            dropout=dropout,
            T=T,
            use_mhsa=use_mhsa,
        )
        
        # Classification head
        self.head = nn.Sequential(
            nn.LayerNorm(channels),
            nn.Dropout(dropout),
            nn.Linear(channels, num_classes),
        )
    
    def forward(
        self,
        x: torch.Tensor,
        return_spikes: bool = False,
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input image (batch, 3, H, W)
            return_spikes: Return spike statistics (default: False)
        
        Returns:
            logits (batch, num_classes) or (logits, spike_stats)
        """
        batch_size = x.shape[0]
        
        # Patch embedding: (batch, 3, H, W) -> (batch, channels, h, w)
        x = self.patch_embed(x)
        
        # Flatten spatial: (batch, channels, h, w) -> (batch, channels, num_patches)
        x = x.flatten(2)  # (batch, channels, num_patches)
        
        # Transpose: (batch, channels, num_patches) -> (batch, num_patches, channels)
        x = x.transpose(1, 2)
        
        # Add CLS token: (batch, num_patches + 1, channels)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        # Add positional embedding
        x = x + self.pos_embed
        
        # Transpose for temporal processing: (batch, num_patches, channels) -> (batch, channels, num_patches)
        x = x.transpose(1, 2)
        
        # Bernoulli encoding: convert to probabilities first
        # Sigmoid to ensure values in [0, 1]
        probs = torch.sigmoid(x)
        
        # Encode to spikes: (batch, channels, num_patches, T)
        spikes = self.encoder(probs)
        
        # Process temporal
        outputs = []
        for t in range(self.T):
            spike_t = spikes[..., t]  # (batch, channels, num_patches)
            
            # Pass through encoder layers
            out_t, _ = self.encoder_layers(spike_t)
            outputs.append(out_t)
        
        # Average over time: (batch, channels, num_patches)
        x = torch.stack(outputs, dim=-1).mean(dim=-1)
        
        # Take CLS token: (batch, channels)
        cls_out = x[:, :, 0]
        
        # Classification: (batch, num_classes)
        logits = self.head(cls_out)
        
        if return_spikes:
            return logits, spikes.mean(dim=-1)
        return logits


class CIFAR10SpikeFormer(SpikeFormer):
    """SpikeFormer adapted for CIFAR-10 (32x32 images).
    
    Smaller model for CIFAR-10 experiments.
    Uses patch_size=4 to get 8x8=64 patches.
    """
    
    def __init__(
        self,
        channels: int = 128,
        num_layers: int = 4,
        num_heads: int = 8,
        num_classes: int = 10,
        T: int = 8,
        dropout: float = 0.1,
        kernel_size: int = 3,
        use_mhsa: bool = False,
    ):
        super().__init__(
            image_size=32,  # CIFAR-10
            patch_size=4,  # 8x8 = 64 patches
            channels=channels,
            num_layers=num_layers,
            num_heads=num_heads,
            num_classes=num_classes,
            T=T,
            dropout=dropout,
            kernel_size=kernel_size,
            use_mhsa=use_mhsa,
        )
    
    def forward(
        self,
        x: torch.Tensor,
        return_spikes: bool = False,
    ) -> torch.Tensor:
        """Forward pass with 32x32 input support."""
        batch_size = x.shape[0]
        
        # Patch embedding: (batch, 3, 32, 32) -> (batch, channels, 8, 8)
        x = self.patch_embed(x)
        
        # Flatten spatial: (batch, channels, 8, 8) -> (batch, channels, 64)
        x = x.flatten(2)
        
        # Transpose: (batch, channels, 64) -> (batch, 64, channels)
        x = x.transpose(1, 2)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        # Add positional embedding (truncated for 64 patches + 1 CLS = 65)
        x = x + self.pos_embed[:, :65, :]
        
        # Transpose: (batch, 65, channels) -> (batch, channels, 65)
        x = x.transpose(1, 2)
        
        # Spike encoding
        probs = torch.sigmoid(x)
        spikes = self.encoder(probs)
        
        # Process temporal
        outputs = []
        for t in range(self.T):
            spike_t = spikes[..., t]  # (batch, channels, 65)
            out_t, _ = self.encoder_layers(spike_t)
            outputs.append(out_t)
        
        # Average over time
        x = torch.stack(outputs, dim=-1).mean(dim=-1)
        
        # Take CLS token: (batch, channels)
        cls_out = x[:, :, 0]
        
        # Classification
        logits = self.head(cls_out)
        
        if return_spikes:
            return logits, spikes.mean(dim=-1)
        return logits


def create_spikeformer(
    model_name: str = "base",
    num_classes: int = 10,
    T: int = 8,
    use_mhsa: bool = False,
) -> nn.Module:
    """Factory to create SpikeFormer models.
    
    Args:
        model_name: 'tiny', 'small', 'base', 'large', 'cifar10'
        num_classes: Output classes
        T: Number of timesteps
        use_mhsa: Include MHSA
    
    Returns:
        Configured SpikeFormer model
    """
    configs = {
        "tiny": dict(channels=64, num_layers=2, num_heads=4),
        "small": dict(channels=128, num_layers=4, num_heads=8),
        "base": dict(channels=256, num_layers=6, num_heads=8),
        "large": dict(channels=512, num_layers=12, num_heads=16),
        "cifar10": dict(channels=128, num_layers=4, num_heads=8),
    }
    
    if model_name not in configs:
        raise ValueError(f"Unknown model: {model_name}")
    
    config = configs[model_name]
    
    if model_name == "cifar10":
        return CIFAR10SpikeFormer(
            channels=config["channels"],
            num_layers=config["num_layers"],
            num_heads=config["num_heads"],
            num_classes=num_classes,
            T=T,
            use_mhsa=use_mhsa,
        )
    
    return SpikeFormer(
        channels=config["channels"],
        num_layers=config["num_layers"],
        num_heads=config["num_heads"],
        num_classes=num_classes,
        T=T,
        use_mhsa=use_mhsa,
    )
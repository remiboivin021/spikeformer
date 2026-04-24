"""ANN Transformer Model (Equivalent to SpikeFormer).

This is the ANN (Artificial Neural Network) baseline for comparison
with the SNN SpikeFormer model.

Architecture mirrors SpikeFormer but uses standard ANN components:
- Conv2d patch embedding (same as SNN)
- Standard MultiHeadAttention
- LayerNorm + MLP feed-forward
- No spike encoding, no temporal processing

Comparison metrics:
- Accuracy on CIFAR-10
- Inference latency
- Energy consumption (estimated FLOPs)

Reference: Xpikeformer paper comparison baseline
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, List


class ANNAttention(nn.Module):
    """Standard Multi-Head Attention for ANN Transformer.
    
    Equivalent to MHSA in SpikeFormer but without spike constraints.
    Used as baseline comparison.
    """
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int = 8,
        dropout: float = 0.1,
        bias: bool = True,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5
        
        assert self.head_dim * num_heads == embed_dim
        
        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input (batch, seq_len, embed_dim)
            mask: Optional attention mask
        
        Returns:
            Output (batch, seq_len, embed_dim)
        """
        batch_size, seq_len, embed_dim = x.shape
        
        # Project Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        
        # Apply attention to values
        out = (attn @ v).transpose(1, 2).contiguous().view(batch_size, seq_len, embed_dim)
        out = self.out_proj(out)
        
        return out


class ANNTransformerLayer(nn.Module):
    """Single ANN Transformer layer.
    
    Equivalent to SpikeFormerLayer but with standard ANN components.
    
    Architecture:
        - LayerNorm → MultiHeadAttention → Residual
        - LayerNorm → MLP → Residual
    """
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        drop_path: float = 0.0,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        
        # Self-attention block
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = ANNAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=dropout,
        )
        
        # MLP block
        self.norm2 = nn.LayerNorm(embed_dim)
        mlp_hidden_dim = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_hidden_dim, embed_dim),
            nn.Dropout(dropout),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input (batch, seq_len, embed_dim)
        
        Returns:
            Output (batch, seq_len, embed_dim)
        """
        # Self-attention with residual
        x = x + self.attn(self.norm1(x))
        
        # MLP with residual
        x = x + self.mlp(self.norm2(x))
        
        return x


class ANNTransformerEncoder(nn.Module):
    """ANN Transformer encoder.
    
    Stacks N transformer layers.
    """
    
    def __init__(
        self,
        num_layers: int = 4,
        embed_dim: int = 256,
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.num_layers = num_layers
        self.embed_dim = embed_dim
        
        self.layers = nn.ModuleList([
            ANNTransformerLayer(
                embed_dim=embed_dim,
                num_heads=num_heads,
                mlp_ratio=mlp_ratio,
                dropout=dropout,
            )
            for _ in range(num_layers)
        ])
        
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input (batch, seq_len, embed_dim)
        
        Returns:
            Output (batch, seq_len, embed_dim)
        """
        for layer in self.layers:
            x = layer(x)
        
        return self.norm(x)


class ANNTransformer(nn.Module):
    """ANN Transformer Model.
    
    Equivalent architecture to SpikeFormer but using standard ANN components.
    This is the baseline for comparison.
    
    Architecture:
        1. Patch embedding (Conv2d)
        2. CLS token + positional embedding
        3. N × Transformer layers
        4. Classification head
    
    Args:
        image_size: Input image size
        patch_size: Patch size
        embed_dim: Embedding dimension
        num_layers: Number of transformer layers
        num_heads: Number of attention heads
        num_classes: Output classes
        mlp_ratio: MLP expansion ratio
        dropout: Dropout probability
    """
    
    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        embed_dim: int = 256,
        num_layers: int = 4,
        num_heads: int = 8,
        num_classes: int = 1000,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.embed_dim = embed_dim
        self.num_layers = num_layers
        self.num_classes = num_classes
        
        # Calculate patches
        self.num_patches = (image_size // patch_size) ** 2
        
        # Patch embedding: Conv2d (same as SpikeFormer)
        self.patch_embed = nn.Sequential(
            nn.Conv2d(
                in_channels=3,
                out_channels=embed_dim,
                kernel_size=patch_size,
                stride=patch_size,
            ),
            nn.Flatten(2),
        )
        
        # CLS token
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim))
        
        # Positional embedding
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches + 1, embed_dim))
        
        # Transformer encoder
        self.encoder = ANNTransformerEncoder(
            num_layers=num_layers,
            embed_dim=embed_dim,
            num_heads=num_heads,
            mlp_ratio=mlp_ratio,
            dropout=dropout,
        )
        
        # Classification head
        self.head = nn.Sequential(
            nn.LayerNorm(embed_dim),
            nn.Dropout(dropout),
            nn.Linear(embed_dim, num_classes),
        )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights."""
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        self.apply(self._init_module)
    
    def _init_module(self, m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.LayerNorm):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input image (batch, 3, H, W)
        
        Returns:
            logits (batch, num_classes)
        """
        batch_size = x.shape[0]
        
        # Patch embedding: (batch, 3, H, W) -> (batch, embed_dim, num_patches_h, num_patches_w)
        x = self.patch_embed(x)
        
        # Flatten: (batch, embed_dim, h, w) -> (batch, embed_dim, num_patches)
        x = x.flatten(2)
        
        # Transpose: (batch, embed_dim, num_patches) -> (batch, num_patches, embed_dim)
        x = x.transpose(1, 2)
        
        # Add CLS token: (batch, num_patches + 1, embed_dim)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        # Add positional embedding
        x = x + self.pos_embed
        
        # Transformer encoder
        x = self.encoder(x)
        
        # Take CLS token
        cls_out = x[:, 0]  # (batch, embed_dim)
        
        # Classification
        return self.head(cls_out)


class CIFAR10ANNTransformer(ANNTransformer):
    """ANN Transformer adapted for CIFAR-10 (32x32 images).
    
    Same as ANNTransformer but optimized for CIFAR-10.
    Uses patch_size=4 to get 8x8=64 patches.
    """
    
    def __init__(
        self,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 8,
        num_classes: int = 10,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        super().__init__(
            image_size=32,
            patch_size=4,
            embed_dim=embed_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            num_classes=num_classes,
            mlp_ratio=mlp_ratio,
            dropout=dropout,
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with 32x32 input support."""
        batch_size = x.shape[0]
        
        # Patch embedding
        x = self.patch_embed(x)  # (batch, embed_dim, 8, 8)
        
        # Flatten: (batch, embed_dim, 8, 8) -> (batch, embed_dim, 64)
        x = x.flatten(2)
        
        # Transpose: (batch, embed_dim, 64) -> (batch, 64, embed_dim)
        x = x.transpose(1, 2)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        # Add positional embedding (truncated for 64 patches + 1 CLS = 65)
        x = x + self.pos_embed[:, :65, :]
        
        # Transformer
        x = self.encoder(x)
        
        # CLS token
        cls_out = x[:, 0]
        
        return self.head(cls_out)


def create_ann_transformer(
    model_name: str = "base",
    num_classes: int = 10,
) -> nn.Module:
    """Factory to create ANN Transformer models.
    
    Args:
        model_name: 'tiny', 'small', 'base', 'large', 'cifar10'
        num_classes: Output classes
    
    Returns:
        Configured ANN Transformer model
    """
    configs = {
        "tiny": dict(embed_dim=64, num_layers=2, num_heads=4),
        "small": dict(embed_dim=128, num_layers=4, num_heads=8),
        "base": dict(embed_dim=256, num_layers=6, num_heads=8),
        "large": dict(embed_dim=512, num_layers=12, num_heads=16),
        "cifar10": dict(embed_dim=128, num_layers=4, num_heads=8),
    }
    
    if model_name not in configs:
        raise ValueError(f"Unknown model: {model_name}")
    
    config = configs[model_name]
    
    if model_name == "cifar10":
        return CIFAR10ANNTransformer(
            embed_dim=config["embed_dim"],
            num_layers=config["num_layers"],
            num_heads=config["num_heads"],
            num_classes=num_classes,
        )
    
    return ANNTransformer(
        embed_dim=config["embed_dim"],
        num_layers=config["num_layers"],
        num_heads=config["num_heads"],
        num_classes=num_classes,
    )
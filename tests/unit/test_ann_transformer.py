"""Tests for ANN Transformer model."""

import pytest
import torch
import torch.nn as nn

from src.ann.transformer import (
    ANNTransformer,
    CIFAR10ANNTransformer,
    ANNTransformerLayer,
    ANNTransformerEncoder,
    ANNAttention,
    create_ann_transformer,
)


class TestANNAttention:
    """Test ANN Attention module."""
    
    def test_init(self):
        """Test attention initialization."""
        attn = ANNAttention(embed_dim=128, num_heads=8)
        assert attn.embed_dim == 128
        assert attn.num_heads == 8
    
    def test_forward_shape(self):
        """Test attention forward shape."""
        attn = ANNAttention(embed_dim=64, num_heads=4)
        x = torch.rand(2, 16, 64)  # (batch, seq_len, embed_dim)
        out = attn(x)
        
        assert out.shape == (2, 16, 64)


class TestANNTransformerLayer:
    """Test ANN Transformer layer."""
    
    def test_init(self):
        """Test layer initialization."""
        layer = ANNTransformerLayer(embed_dim=128)
        assert layer.embed_dim == 128
    
    def test_forward_shape(self):
        """Test layer forward shape."""
        layer = ANNTransformerLayer(embed_dim=64)
        x = torch.rand(2, 16, 64)  # (batch, seq_len, embed_dim)
        out = layer(x)
        
        assert out.shape == (2, 16, 64)


class TestANNTransformerEncoder:
    """Test ANN Transformer encoder."""
    
    def test_init(self):
        """Test encoder initialization."""
        encoder = ANNTransformerEncoder(num_layers=4, embed_dim=128)
        assert encoder.num_layers == 4
        assert encoder.embed_dim == 128
    
    def test_forward_shape(self):
        """Test encoder forward shape."""
        encoder = ANNTransformerEncoder(num_layers=2, embed_dim=64)
        x = torch.rand(2, 16, 64)
        out = encoder(x)
        
        assert out.shape == (2, 16, 64)


class TestANNTransformer:
    """Test full ANN Transformer model."""
    
    def test_init(self):
        """Test model initialization."""
        model = ANNTransformer(num_classes=10)
        assert model.num_classes == 10
    
    def test_forward_cifar10(self):
        """Test forward pass with CIFAR-10 size input."""
        model = CIFAR10ANNTransformer(embed_dim=64)
        x = torch.rand(2, 3, 32, 32)
        out = model(x)
        
        assert out.shape == (2, 10)
    
    def test_forward_imagenet(self):
        """Test forward pass with ImageNet size input."""
        model = ANNTransformer(num_classes=1000, image_size=224, embed_dim=256)
        x = torch.rand(1, 3, 224, 224)
        out = model(x)
        
        assert out.shape == (1, 1000)
    
    def test_gradient_flow(self):
        """Test gradient flow through model."""
        model = CIFAR10ANNTransformer()
        x = torch.rand(2, 3, 32, 32, requires_grad=True)
        out = model(x)
        loss = out.sum()
        loss.backward()
        
        assert x.grad is not None
        assert model.patch_embed[0].weight.grad is not None


class TestFactory:
    """Test factory function."""
    
    def test_create_ann_transformer_cifar10(self):
        """Test CIFAR-10 model creation."""
        model = create_ann_transformer("cifar10", num_classes=10)
        assert isinstance(model, CIFAR10ANNTransformer)
    
    def test_create_ann_transformer_tiny(self):
        """Test tiny model creation."""
        model = create_ann_transformer("tiny", num_classes=100)
        assert isinstance(model, ANNTransformer)
        assert model.embed_dim == 64
    
    def test_create_ann_transformer_invalid(self):
        """Test invalid model name."""
        with pytest.raises(ValueError):
            create_ann_transformer("invalid_model")


class TestEdgeCases:
    """Edge case tests."""
    
    def test_single_image(self):
        """Test with batch_size=1."""
        model = CIFAR10ANNTransformer()
        x = torch.rand(1, 3, 32, 32)
        out = model(x)
        
        assert out.shape == (1, 10)
    
    def test_different_sizes(self):
        """Test with different configurations."""
        configs = [
            dict(embed_dim=64, num_layers=2, num_heads=4),
            dict(embed_dim=128, num_layers=4, num_heads=8),
        ]
        
        for config in configs:
            model = CIFAR10ANNTransformer(**config)
            x = torch.rand(2, 3, 32, 32)
            out = model(x)
            assert out.shape == (2, 10)


class TestANNvsSNNComparison:
    """Tests for ANN vs SNN comparison setup."""
    
    def test_equivalent_shapes(self):
        """Test that ANN and SNN produce equivalent output shapes."""
        from src.snn.spikeformer import CIFAR10SpikeFormer
        
        ann_model = CIFAR10ANNTransformer(embed_dim=128, num_layers=4)
        snn_model = CIFAR10SpikeFormer(channels=128, num_layers=4, T=8)
        
        x = torch.rand(2, 3, 32, 32)
        
        ann_out = ann_model(x)
        snn_out = snn_model(x)
        
        # Both should produce same output shape
        assert ann_out.shape == snn_out.shape == (2, 10)
    
    def test_param_count_comparison(self):
        """Test parameter count comparison.
        
        Note: ANN typically has MORE parameters than SNN for equivalent
        architecture because:
        1. SNN uses sparse binary representations
        2. SNN's temporal processing is more efficient
        3. SNN doesn't need separate time dimension weights
        """
        from src.snn.spikeformer import CIFAR10SpikeFormer
        
        ann_model = CIFAR10ANNTransformer(embed_dim=128, num_layers=4)
        snn_model = CIFAR10SpikeFormer(channels=128, num_layers=4, T=8)
        
        ann_params = sum(p.numel() for p in ann_model.parameters())
        snn_params = sum(p.numel() for p in snn_model.parameters())
        
        print(f"ANN params: {ann_params:,}")
        print(f"SNN params: {snn_params:,}")
        print(f"ANN/SNN ratio: {ann_params / snn_params:.2f}x")
        
        # ANN should have MORE parameters (expected ~5-15x more)
        # due to SNN's sparse binary representation efficiency
        ratio = ann_params / snn_params
        assert ratio > 1.0  # ANN has more params (expected)
        assert ratio < 20.0  # But not absurdly more
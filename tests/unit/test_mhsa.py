"""Tests for MHSA (Multi-Head Self-Attention)."""

import pytest
import torch

from src.snn.attention import SpikeMHSA, MultiHeadAttention, create_mhsa


class TestSpikeMHSA:
    """Test Spike-based MHSA."""
    
    def test_init_default(self):
        """Test MHSA initialization."""
        mhsa = SpikeMHSA(channels=128)
        assert mhsa.channels == 128
        assert mhsa.num_heads == 4
        assert mhsa.head_dim == 32
    
    def test_init_custom_heads(self):
        """Test with custom num_heads."""
        mhsa = SpikeMHSA(channels=128, num_heads=8)
        assert mhsa.num_heads == 8
        assert mhsa.head_dim == 16
    
    def test_forward_shape(self):
        """Test output shape matches input."""
        mhsa = SpikeMHSA(channels=128)
        x = torch.rand(4, 128, 16)  # (batch, channels, T)
        out = mhsa(x)
        
        assert out.shape == (4, 128, 16)
    
    def test_forward_values(self):
        """Test output values are valid."""
        mhsa = SpikeMHSA(channels=64)
        x = torch.rand(2, 64, 8)
        out = mhsa(x)
        
        assert torch.isfinite(out).all()
        assert not torch.isnan(out).any()
    
    def test_different_heads(self):
        """Test with different head configurations."""
        for num_heads in [1, 2, 4, 8]:
            channels = 64
            mhsa = SpikeMHSA(channels=channels, num_heads=num_heads)
            x = torch.rand(2, channels, 8)
            out = mhsa(x)
            assert out.shape == x.shape


class TestMultiHeadAttention:
    """Test standard MHA."""
    
    def test_init(self):
        """Test MHA initialization."""
        mha = MultiHeadAttention(channels=128)
        assert mha.channels == 128
        assert mha.num_heads == 4
    
    def test_forward_shape(self):
        """Test output shape."""
        mha = MultiHeadAttention(channels=128)
        x = torch.rand(4, 128, 16)
        out = mha(x)
        
        # Output is (batch, T, channels) for standard MHA
        assert out.shape[0] == 4
        assert out.shape[2] == 128


class TestFactory:
    """Test factory function."""
    
    def test_create_mhsa_spike(self):
        """Test create_mhsa with spike_based=True."""
        mhsa = create_mhsa(channels=128, spike_based=True)
        assert isinstance(mhsa, SpikeMHSA)
    
    def test_create_mhsa_standard(self):
        """Test create_mhsa with spike_based=False."""
        mhsa = create_mhsa(channels=128, spike_based=False)
        assert isinstance(mhsa, MultiHeadAttention)


class TestEdgeCases:
    """Edge case tests."""
    
    def test_single_channel(self):
        """Test with single channel."""
        mhsa = SpikeMHSA(channels=4, num_heads=1)
        x = torch.rand(2, 4, 4)
        out = mhsa(x)
        
        assert out.shape == (2, 4, 4)
    
    def test_single_timestep(self):
        """Test with T=1."""
        mhsa = SpikeMHSA(channels=16, num_heads=2)
        x = torch.rand(2, 16, 1)
        out = mhsa(x)
        
        assert out.shape == (2, 16, 1)
    
    def test_single_batch(self):
        """Test with batch=1."""
        mhsa = SpikeMHSA(channels=32, num_heads=4)
        x = torch.rand(1, 32, 8)
        out = mhsa(x)
        
        assert out.shape == (1, 32, 8)
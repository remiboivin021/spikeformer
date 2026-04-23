"""Tests for P2: Spike Sweep Architecture."""

import pytest
import torch


class TestTemporalConvolver:
    """Test Temporal Convolver (TC) component."""
    
    def test_init_default(self):
        """Test TC initialization."""
        from src.snn.architecture import TemporalConvolver
        
        tc = TemporalConvolver(channels=128)
        assert tc.channels == 128
        assert tc.kernel_size == 3
    
    def test_init_custom(self):
        """Test TC with custom params."""
        from src.snn.architecture import TemporalConvolver
        
        tc = TemporalConvolver(channels=64, kernel_size=5)
        assert tc.channels == 64
        assert tc.kernel_size == 5
    
    def test_forward_shape(self):
        """Test output shape matches input."""
        from src.snn.architecture import TemporalConvolver
        
        tc = TemporalConvolver(channels=128)
        x = torch.rand(4, 128, 16)  # (batch, channels, T)
        out = tc(x)
        
        assert out.shape == (4, 128, 16)
    
    def test_forward_deterministic(self):
        """Test output is deterministic with same input."""
        from src.snn.architecture import TemporalConvolver
        
        tc = TemporalConvolver(channels=8, kernel_size=3)
        x = torch.zeros(1, 8, 8)
        x[0, 0, :] = 1.0  # Spike in first channel
        
        out1 = tc(x)
        out2 = tc(x)
        
        assert torch.equal(out1, out2)


class TestBNFBlock:
    """Test BNF Block component."""
    
    def test_init_default(self):
        """Test BNF initialization."""
        from src.snn.architecture import BNFBlock
        
        bnf = BNFBlock(channels=128)
        assert bnf.channels == 128
        assert bnf.dropout == 0.1
    
    def test_init_custom(self):
        """Test BNF with custom params."""
        from src.snn.architecture import BNFBlock
        
        bnf = BNFBlock(channels=64, dropout=0.2, activation="relu")
        assert bnf.channels == 64
        assert bnf.dropout == 0.2
    
    def test_forward_shape(self):
        """Test output shape matches input."""
        from src.snn.architecture import BNFBlock
        
        bnf = BNFBlock(channels=128, dropout=0.0)  # No dropout for deterministic test
        x = torch.rand(4, 128, 16)
        out = bnf(x)
        
        assert out.shape == (4, 128, 16)
    
    def test_forward_no_dropout(self):
        """Test with dropout disabled."""
        from src.snn.architecture import BNFBlock
        
        bnf = BNFBlock(channels=128, dropout=0.0)
        x = torch.rand(4, 128, 16)
        out = bnf(x)
        
        # Shape preserved
        assert out.shape == x.shape


class TestSSAModule:
    """Test SSA Module (full SSA)."""
    
    def test_init_default(self):
        """Test SSA initialization."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=128)
        assert ssa.channels == 128
        assert ssa.tc is not None
        assert ssa.bnf is not None
    
    def test_init_custom(self):
        """Test SSA with custom params."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=64, kernel_size=5, dropout=0.2)
        assert ssa.channels == 64
        assert ssa.tc.kernel_size == 5
        assert ssa.bnf.dropout == 0.2
    
    def test_forward_shape(self):
        """Test output shape matches input."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=128)
        x = torch.rand(4, 128, 16)  # Probabilities
        out = ssa(x)
        
        assert out.shape == (4, 128, 16)
    
    def test_forward_probability_output(self):
        """Test output is valid probabilities."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=64)
        x = torch.rand(2, 64, 8)
        out = ssa(x)
        
        # Output should be valid (not NaN/Inf)
        assert torch.isfinite(out).all()
    
    def test_forward_positive_values(self):
        """Test output values are reasonable."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=64)
        x = torch.rand(2, 64, 8)  # [0, 1] probabilities
        out = ssa(x)
        
        # Values should be bounded
        assert out.abs().max().item() < float('inf')
    
    def test_backward_pass(self):
        """Test gradients flow."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=64)
        x = torch.rand(2, 64, 8, requires_grad=True)
        out = ssa(x)
        loss = out.sum()
        loss.backward()
        
        # Gradients should exist
        assert x.grad is not None


class TestFactory:
    """Test factory functions."""
    
    def test_create_ssa_module(self):
        """Test create_ssa_module factory."""
        from src.snn.architecture import create_ssa_module
        
        ssa = create_ssa_module(channels=128)
        
        assert ssa.channels == 128


class TestIntegration:
    """Integration tests with Phase 1 components."""
    
    def test_ssa_output_shapes(self):
        """Test SSA output shapes work with encoding."""
        from src.snn.architecture import SSAModule
        from src.snn.encoding import BernoulliEncoder
        
        ssa = SSAModule(channels=64)
        encoder = BernoulliEncoder(T=8)
        
        # SSA takes (batch, channels, T)
        x = torch.rand(4, 64)  # (batch, features)
        
        # Encode first to add time dimension
        probs = encoder(x)  # (batch, features, T)
        
        # SSA transforms
        out = ssa(probs)
        
        assert out.shape == (4, 64, 8)


class TestEdgeCases:
    """Edge case tests."""
    
    def test_single_channel(self):
        """Test with single channel."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=1)
        x = torch.rand(2, 1, 8)
        out = ssa(x)
        
        assert out.shape == (2, 1, 8)
    
    def test_single_timestep(self):
        """Test with T=1 (edge case)."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=32)
        x = torch.rand(2, 32, 1)
        out = ssa(x)
        
        assert out.shape == (2, 32, 1)
    
    def test_single_batch(self):
        """Test with batch=1."""
        from src.snn.architecture import SSAModule
        
        ssa = SSAModule(channels=32)
        x = torch.rand(1, 32, 8)
        out = ssa(x)
        
        assert out.shape == (1, 32, 8)
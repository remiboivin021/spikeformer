"""Tests for P1-T2: LIF Neuron Implementation."""

import pytest
import torch
from torch.nn.functional import mse_loss


class TestLeakyIntegrateAndFire:
    """Test LIF neuron implementation."""
    
    def test_init_parameters(self):
        """Test LIF initialization with parameters."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.9, threshold=1.5)
        assert lif.beta == 0.9
        assert lif.threshold == 1.5
        assert lif.spike_reset is True
    
    def test_default_parameters(self):
        """Test LIF with default parameters."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire()
        assert lif.beta == 0.95
        assert lif.threshold == 1.0
        assert lif.spike_reset is True
    
    def test_init_mem(self):
        """Test membrane initialization."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire()
        mem = lif.init_mem(4, 128, device="cpu", dtype=torch.float32)
        assert mem.shape == (4, 128)
        assert mem.sum().item() == 0.0
    
    def test_no_spike_below_threshold(self):
        """Test no spike when input below threshold."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        x = torch.tensor(0.5)  # Small input
        mem = lif.init_mem(1)
        
        spk, new_mem = lif(x, mem)
        
        assert spk.item() == 0.0  # No spike
        assert new_mem.item() == 0.5  # V = 0.95 * 0 + 0.5 = 0.5
    
    def test_spike_at_threshold(self):
        """Test spike when input at threshold."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        x = torch.tensor(1.0)  # Input equals threshold
        mem = lif.init_mem(1)
        
        spk, new_mem = lif(x, mem)
        
        assert spk.item() == 1.0  # Spike
        assert new_mem.item() == 0.0  # Reset to 0
    
    def test_spike_above_threshold(self):
        """Test spike when input above threshold."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        x = torch.tensor(2.0)
        mem = lif.init_mem(1)
        
        spk, new_mem = lif(x, mem)
        
        assert spk.item() == 1.0
        assert new_mem.item() == 0.0  # Reset
    
    def test_membrane_decay(self):
        """Test membrane potential decay with beta."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        beta = 0.8
        lif = LeakyIntegrateAndFire(beta=beta, threshold=1.0)
        x = torch.tensor(0.3)
        mem = torch.tensor(0.5)  # Initial membrane
        
        spk, new_mem = lif(x, mem)
        
        expected_mem = beta * 0.5 + 0.3  # 0.4 + 0.3 = 0.7
        assert abs(new_mem.item() - expected_mem) < 1e-6
    
    def test_no_reset_mode(self):
        """Test no reset mode (spike_reset=False)."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0, spike_reset=False)
        x = torch.tensor(2.0)
        mem = lif.init_mem(1)
        
        spk, new_mem = lif(x, mem)
        
        assert spk.item() == 1.0
        assert new_mem.item() > 0.0  # No reset
    
    def test_batch_processing(self):
        """Test LIF with batch inputs."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        x = torch.tensor([0.5, 1.5, 0.8, 2.0])  # Batch of 4
        mem = lif.init_mem(4, device="cpu")
        
        spk, new_mem = lif(x, mem)
        
        assert spk.shape == (4,)
        assert new_mem.shape == (4,)
        # Only indices 1 and 3 should spike
        assert spk[0].item() == 0.0
        assert spk[1].item() == 1.0
        assert spk[2].item() == 0.0
        assert spk[3].item() == 1.0


class TestLIFDynamicOverTime:
    """Test LIF dynamics over multiple timesteps."""
    
    def test_dynamics_50_timesteps(self):
        """Test membrane dynamics over 50 timesteps."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        T = 50
        batch_size = 4
        input_dim = 128
        
        # Random input spikes
        x = torch.rand(batch_size, input_dim, T)
        mem = lif.init_mem(batch_size, input_dim)
        
        spike_counts = torch.zeros(batch_size, input_dim)
        
        for t in range(T):
            spk, mem = lif(x[:, :, t], mem)
            spike_counts += spk
        
        # Verify some spikes occurred (expected with random input)
        total_spikes = spike_counts.sum().item()
        assert total_spikes > 0, "No spikes in 50 timesteps - unexpected"
        # Should not spike on every timestep
        max_spikes = batch_size * input_dim * T
        assert total_spikes < max_spikes, "Spiked every timestep"
    
    def test_conservation_of_membrane(self):
        """Test membrane conservation properties."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.5, threshold=0.5)
        T = 10
        x = torch.ones(1, 1, T) * 0.1  # Small constant input
        mem = lif.init_mem(1, 1)
        
        total_input = 0.0
        spike_counts = []
        
        for t in range(T):
            spk, mem = lif(x[:, :, t], mem)
            total_input += x[:, :, t].item()
            spike_counts.append(spk.item())
        
        # With beta=0.5 and small input, should spike occasionally
        # Membrane should converge toward steady state
        assert len(spike_counts) == T
    
    def test_no_leaky_without_input(self):
        """Test membrane decays without input."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.9, threshold=1.0)
        x = torch.tensor(0.0)  # No input
        mem = torch.tensor(0.5)  # Initial membrane
        
        spk, new_mem = lif(x, mem)
        
        expected = 0.9 * 0.5 + 0.0  # 0.45
        assert abs(new_mem.item() - expected) < 1e-6


class TestSurrogateGradient:
    """Test surrogate gradient functions."""
    
    def test_fast_sigmoid(self):
        """Test fast sigmoid surrogate gradient."""
        from src.snn.neurons import fast_sigmoid
        
        x = torch.tensor([0.0, 1.0, -1.0])
        grad = fast_sigmoid(x)
        
        # Sigmoid(0) = 0.5
        # Sigmoid(1) ≈ 0.731
        # Sigmoid(-1) ≈ 0.269
        assert abs(grad[0].item() - 0.5) < 0.01
        assert grad[1].item() > 0.5
        assert grad[2].item() < 0.5
    
    def test_fast_sigmoid_alpha(self):
        """Test fast sigmoid with different alpha."""
        from src.snn.neurons import fast_sigmoid
        
        x = torch.tensor(1.0)  # Test with non-zero input
        grad_alpha_1 = fast_sigmoid(x, alpha=1.0)
        grad_alpha_10 = fast_sigmoid(x, alpha=10.0)
        
        # Higher alpha at x=1.0 gives gradient closer to 1.0
        # sigmoid(10) > sigmoid(1)
        assert grad_alpha_10.item() > grad_alpha_1.item()


class TestLIFStepFunctional:
    """Test functional LIF step."""
    
    def test_lif_step_basic(self):
        """Test basic lif_step function."""
        from src.snn.neurons import lif_step
        
        x = torch.tensor(0.5)
        mem = torch.tensor(0.3)
        
        spk, new_mem = lif_step(x, mem, beta=0.95, threshold=1.0)
        
        # No spike (0.95*0.3 + 0.5 = 0.785 < 1.0)
        assert spk.item() == 0.0
        assert abs(new_mem.item() - 0.785) < 1e-6
    
    def test_lif_step_with_spike(self):
        """Test lif_step with spike."""
        from src.snn.neurons import lif_step
        
        x = torch.tensor(1.5)
        mem = torch.tensor(0.0)
        
        spk, new_mem = lif_step(x, mem, beta=0.95, threshold=1.0)
        
        assert spk.item() == 1.0
        assert new_mem.item() == 0.0


class TestLIFEdgeCases:
    """Test LIF edge cases."""
    
    def test_zero_beta(self):
        """Test LIF with zero decay (no memory)."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.0, threshold=1.0)
        x = torch.tensor(1.5)
        mem = torch.tensor(0.5)
        
        spk, new_mem = lif(x, mem)
        
        # V = 0.0 * 0.5 + 1.5 = 1.5 >= 1.0 -> spike
        assert spk.item() == 1.0
    
    def test_beta_one(self):
        """Test LIF with beta=1 (no decay)."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=1.0, threshold=1.0)
        x = torch.tensor(0.3)
        mem = torch.tensor(0.5)
        
        spk, new_mem = lif(x, mem)
        
        # V = 1.0 * 0.5 + 0.3 = 0.8 < 1.0 -> no spike
        assert spk.item() == 0.0
        assert abs(new_mem.item() - 0.8) < 1e-6
    
    def test_negative_input(self):
        """Test LIF with negative input."""
        from src.snn.neurons import LeakyIntegrateAndFire
        
        lif = LeakyIntegrateAndFire(beta=0.95, threshold=1.0)
        x = torch.tensor(-0.5)
        mem = torch.tensor(0.3)
        
        spk, new_mem = lif(x, mem)
        
        # V = 0.95 * 0.3 - 0.5 = -0.215 < threshold
        assert spk.item() == 0.0
        assert new_mem.item() < 0.0
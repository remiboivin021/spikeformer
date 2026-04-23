"""Tests for P1-T4: Bernoulli Encoder."""

import pytest
import torch


class TestBernoulliEncoder:
    """Test Bernoulli encoder implementation."""
    
    def test_init_default(self):
        """Test encoder initialization with defaults."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder()
        assert encoder.T == 8
        assert encoder.batch_first is True
    
    def test_init_custom(self):
        """Test encoder initialization with custom params."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=16, batch_first=False)
        assert encoder.T == 16
        assert encoder.batch_first is False
    
    def test_output_shape(self):
        """Test encoder output shape."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=8)
        x = torch.rand(4, 128)
        spikes = encoder(x)
        
        assert spikes.shape == (4, 128, 8)
    
    def test_output_binary(self):
        """Test encoder output is binary {0, 1}."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=8)
        x = torch.rand(4, 128)
        spikes = encoder(x)
        
        unique_vals = spikes.unique()
        assert all(v in [0.0, 1.0] for v in unique_vals)
    
    def test_encode_zero_probability(self):
        """Test encoding of zero probability."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=50)
        x = torch.zeros(4, 128)
        spikes = encoder(x)
        
        assert spikes.sum().item() == 0.0
    
    def test_encode_one_probability(self):
        """Test encoding of probability 1."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=50)
        x = torch.ones(4, 128)
        spikes = encoder(x)
        
        assert spikes.sum().item() == 4 * 128 * 50
    
    def test_rate_convergence_T50(self):
        """Test spike rate converges to input for T=50 (averaged over trials)."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=50)
        
        # Run multiple trials to average out noise
        all_rates = []
        for trial in range(10):
            torch.manual_seed(trial * 100)
            x = torch.full((50, 50), 0.3)
            spikes = encoder(x)
            spike_rate = spikes.float().mean(dim=-1).mean()
            all_rates.append(spike_rate.item())
        
        avg_rate = sum(all_rates) / len(all_rates)
        
        # Over 10 trials, should average close to 30%
        assert abs(avg_rate - 0.3) < 0.03
    
    def test_rate_convergence_T100(self):
        """Test better convergence with T=100 (averaged over trials)."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=100)
        
        # Run multiple trials
        all_rates = []
        for trial in range(10):
            torch.manual_seed(trial * 100)
            x = torch.full((50, 50), 0.5)
            spikes = encoder(x)
            spike_rate = spikes.float().mean(dim=-1).mean()
            all_rates.append(spike_rate.item())
        
        avg_rate = sum(all_rates) / len(all_rates)
        
        # Should be even closer with more timesteps
        assert abs(avg_rate - 0.5) < 0.02
    
    def test_temporal_variation(self):
        """Test spikes vary across timesteps."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=10)
        x = torch.full((10, 10), 0.5)  # 50% rate
        spikes = encoder(x)
        
        # Sum spikes per timestep
        t_sums = spikes.sum(dim=(0, 1)).float()  # (T,)
        
        # Not all timesteps should be identical
        unique_sums = len(set(t_sums.tolist()))
        assert unique_sums > 1
    
    def test_batch_variation(self):
        """Test different batches produce different spikes."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=20)
        x1 = torch.full((10, 10), 0.5)
        x2 = torch.full((10, 10), 0.5)
        
        spikes1 = encoder(x1)
        spikes2 = encoder(x2)
        
        # Should not be identical (stochastic)
        assert not torch.equal(spikes1, spikes2)
    
    def test_encode_with_override_T(self):
        """Test encoding with T override."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=8)
        x = torch.rand(4, 128)
        spikes = encoder(x, T=16)
        
        assert spikes.shape == (4, 128, 16)


class TestBernoulliEncoderMethods:
    """Test encoder methods."""
    
    def test_encode_with_rate(self):
        """Test encode method returns spike rate."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=20)
        x = torch.rand(4, 128)
        spikes, spike_rate = encoder.encode(x)
        
        assert spikes.shape == (4, 128, 20)
        assert spike_rate.shape == (4, 128)
        assert torch.allclose(spike_rate, spikes.float().mean(dim=-1))
    
    def test_rate_computation(self):
        """Test compute_spike_rate function."""
        from src.snn.encoding import compute_spike_rate
        
        T = 10
        spikes = torch.bernoulli(torch.full((4, 128, T), 0.3))
        rate = compute_spike_rate(spikes, T)
        
        assert rate.shape == (4, 128)
        assert torch.allclose(rate, spikes.float().mean(dim=-1))
    
    def test_validate_rate_convergence(self):
        """Test validate_rate_convergence function."""
        from src.snn.encoding import validate_rate_convergence, BernoulliEncoder
        
        # Test with extreme rates (0 and 1 - deterministic)
        x = torch.tensor([[0.0], [1.0]])
        
        # 0.0 should always give rate 0
        result_0 = validate_rate_convergence(x[:1], T=50, atol=0.02)
        assert result_0 is True
        
        # 1.0 should always give rate 1
        result_1 = validate_rate_convergence(x[1:], T=50, atol=0.02)
        assert result_1 is True


class TestBernoulliEncoderEdgeCases:
    """Test edge cases."""
    
    def test_probability_boundaries(self):
        """Test encoding at probability boundaries."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=100)
        
        # Exactly 0 and 1
        x = torch.tensor([0.0, 1.0])
        spikes = encoder(x)
        
        assert spikes[0].sum().item() == 0.0
        assert spikes[1].sum().item() == 100.0
    
    def test_clamping(self):
        """Test input clamping for out-of-range values."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=50)
        
        # Values outside [0, 1]
        x = torch.tensor([-0.5, 1.5])
        spikes = encoder(x)
        
        # Should produce valid spikes (no errors)
        assert spikes.shape == (2, 50)
    
    def test_single_feature(self):
        """Test with single feature."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=20)
        x = torch.rand(4, 1)  # Single feature
        spikes = encoder(x)
        
        assert spikes.shape == (4, 1, 20)
    
    def test_variable_input_rates(self):
        """Test encoding with variable input rates."""
        from src.snn.encoding import BernoulliEncoder
        
        torch.manual_seed(42)
        encoder = BernoulliEncoder(T=50)
        rates = torch.tensor([0.1, 0.3, 0.5, 0.7, 0.9])
        x = rates.unsqueeze(0)  # (1, 5)
        spikes = encoder(x)
        
        # Each row should have approximately correct rate (relaxed tolerance)
        for i in range(5):
            empirical = spikes[:, i, :].float().mean()
            expected = rates[i].item()
            diff = abs(empirical.item() - expected)
            assert diff < 0.15, f"Rate {i}: diff {diff} too large"


class TestFunctionalInterface:
    """Test functional interface."""
    
    def test_encode_bernoulli_functional(self):
        """Test functional encode_bernoulli."""
        from src.snn.encoding import encode_bernoulli
        
        x = torch.rand(4, 128)
        spikes = encode_bernoulli(x, T=10)
        
        assert spikes.shape == (4, 128, 10)
    
    def test_batch_first_false(self):
        """Test with batch_first=False."""
        from src.snn.encoding import BernoulliEncoder
        
        encoder = BernoulliEncoder(T=8, batch_first=False)
        x = torch.rand(128, 4)  # (features, batch)
        spikes = encoder(x)
        
        assert spikes.shape == (8, 128, 4)  # (T, features, batch)
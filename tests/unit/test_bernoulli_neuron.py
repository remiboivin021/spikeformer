"""Tests for P1-T3: Bernoulli Neuron Layer (BNL)."""

import pytest
import torch


class TestBernoulliNeuron:
    """Test Bernoulli neuron implementation."""
    
    def test_init_default(self):
        """Test BNL initialization with defaults."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        assert bnl.threshold == 0.5
        assert bnl.batch_first is True
    
    def test_init_custom(self):
        """Test BNL initialization with custom params."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron(threshold=0.3, batch_first=False)
        assert bnl.threshold == 0.3
        assert bnl.batch_first is False
    
    def test_output_binary(self):
        """Test BNL output is binary {0, 1}."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.rand(4, 128)  # Random probabilities
        spikes = bnl(x)
        
        # Output must be binary
        unique_vals = spikes.unique()
        assert len(unique_vals) <= 2
        assert all(v in [0.0, 1.0] for v in unique_vals)
    
    def test_probability_zero(self):
        """Test no spikes when probability is 0."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.zeros(4, 128)
        spikes = bnl(x)
        
        # All zeros expected
        assert spikes.sum().item() == 0.0
    
    def test_probability_one(self):
        """Test all spikes when probability is 1."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.ones(4, 128)
        spikes = bnl(x)
        
        # All ones expected (Bernoulli(1) = 1 always)
        assert spikes.sum().item() == 4 * 128
    
    def test_probability_half(self):
        """Test ~50% spikes when probability is 0.5."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.full((100, 100), 0.5)
        spikes = bnl(x)
        
        # Should be approximately 50% (law of large numbers)
        spike_rate = spikes.mean().item()
        assert 0.4 < spike_rate < 0.6  # Allow some variance
    
    def test_stochastic_output(self):
        """Test that output is stochastic (varies between calls)."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.full((100, 100), 0.5)
        
        # Run multiple times
        results = [bnl(x).sum().item() for _ in range(10)]
        
        # Not all results should be identical (stochastic)
        unique_counts = len(set(int(r) for r in results))
        assert unique_counts > 1
    
    def test_batch_processing(self):
        """Test BNL with batch inputs."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.rand(8, 64)  # Batch of 8
        spikes = bnl(x)
        
        assert spikes.shape == (8, 64)
    
    def test_clamping_negative(self):
        """Test clamping of negative inputs."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.tensor(-0.5)  # Negative
        spikes = bnl(x)
        
        # Should be clamped to 0
        assert spikes.item() == 0.0
    
    def test_clamping_above_one(self):
        """Test clamping of inputs above 1."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.tensor(1.5)  # Above 1
        spikes = bnl(x)
        
        # Should be clamped to 1
        assert spikes.item() == 1.0


class TestBernoulliSampleFunctional:
    """Test functional bernoulli_sample."""
    
    def test_basic(self):
        """Test basic bernoulli_sample function."""
        from src.snn.neurons import bernoulli_sample
        
        p = torch.tensor(0.7)
        spike = bernoulli_sample(p)
        
        assert spike.item() in [0.0, 1.0]
    
    def test_tensor_input(self):
        """Test with tensor input."""
        from src.snn.neurons import bernoulli_sample
        
        p = torch.tensor([0.3, 0.5, 0.7])
        spike = bernoulli_sample(p)
        
        assert spike.shape == (3,)
        assert spike.min().item() >= 0.0
        assert spike.max().item() <= 1.0


class TestRateToSpikeBatch:
    """Test rate to spike batch conversion."""
    
    def test_output_shape(self):
        """Test output shape (batch, neurons, T)."""
        from src.snn.neurons import rate_to_spike_batch
        
        batch_size = 4
        n_neurons = 128
        T = 10
        
        rates = torch.rand(batch_size, n_neurons)
        spikes = rate_to_spike_batch(rates, T)
        
        assert spikes.shape == (batch_size, n_neurons, T)
    
    def test_rate_half(self):
        """Test spike rate approximately equals input rate."""
        from src.snn.neurons import rate_to_spike_batch
        
        T = 100
        batch_size = 4
        n_neurons = 128
        
        rates = torch.full((batch_size, n_neurons), 0.3)
        spikes = rate_to_spike_batch(rates, T)
        
        # Compute empirical spike rate
        spike_rate = spikes.mean().item()
        
        # Should be approximately 30%
        assert 0.25 < spike_rate < 0.35
    
    def test_rate_zero(self):
        """Test no spikes for zero rate."""
        from src.snn.neurons import rate_to_spike_batch
        
        T = 50
        rates = torch.zeros(4, 128)
        spikes = rate_to_spike_batch(rates, T)
        
        assert spikes.sum().item() == 0.0
    
    def test_rate_one(self):
        """Test all spikes for rate 1."""
        from src.snn.neurons import rate_to_spike_batch
        
        T = 50
        rates = torch.ones(4, 128)
        spikes = rate_to_spike_batch(rates, T)
        
        # All spikes should be 1
        assert spikes.sum().item() == 4 * 128 * T


class TestRateNormalizer:
    """Test rate normalizer."""
    
    def test_sigmoid_method(self):
        """Test sigmoid normalization."""
        from src.snn.neurons import RateNormalizer
        
        normalizer = RateNormalizer(method="sigmoid")
        x = torch.tensor(0.0)
        norm = normalizer(x)
        
        # sigmoid(0) = 0.5
        assert abs(norm.item() - 0.5) < 0.01
    
    def test_relu_method(self):
        """Test ReLU normalization."""
        from src.snn.neurons import RateNormalizer
        
        normalizer = RateNormalizer(method="relu")
        x = torch.tensor(2.0)
        norm = normalizer(x)
        
        # relu(2) clamped to [0,1] = 1
        assert norm.item() == 1.0
    
    def test_relu_negative(self):
        """Test ReLU clamps negative values."""
        from src.snn.neurons import RateNormalizer
        
        normalizer = RateNormalizer(method="relu")
        x = torch.tensor(-1.0)
        norm = normalizer(x)
        
        assert norm.item() == 0.0


class TestBernoulliEdgeCases:
    """Test edge cases."""
    
    def test_exact_threshold(self):
        """Test behavior at exact threshold."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron(threshold=0.5)
        x = torch.tensor(0.5)
        spikes = bnl(x)
        
        assert spikes.item() in [0.0, 1.0]
    
    def test_very_small_probability(self):
        """Test very small probability (close to 0)."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.tensor(0.001)
        spikes = bnl(x)
        
        # Should still work (mostly 0)
        assert spikes.item() in [0.0, 1.0]
    
    def test_very_large_probability(self):
        """Test very large probability (close to 1)."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.tensor(0.999)
        spikes = bnl(x)
        
        # Should still work (mostly 1)
        assert spikes.item() in [0.0, 1.0]
    
    def test_multidim_tensor(self):
        """Test with multi-dimensional tensor."""
        from src.snn.neurons import BernoulliNeuron
        
        bnl = BernoulliNeuron()
        x = torch.rand(2, 4, 8, 16)  # (B, C, H, W)
        spikes = bnl(x)
        
        assert spikes.shape == (2, 4, 8, 16)
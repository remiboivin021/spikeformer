"""Tests for SpikeFormer benchmark module."""

import pytest
import torch
import torch.nn as nn

from src.snn.benchmark import (
    SpikeFormerBenchmark,
    EnergyEstimates,
    BenchmarkResult,
    format_benchmark_result,
    compare_models,
)
from src.snn.spikeformer import CIFAR10SpikeFormer, create_spikeformer


class TestEnergyEstimates:
    """Test energy estimation."""
    
    def test_defaults(self):
        """Test default energy values."""
        energy = EnergyEstimates()
        
        assert energy.ENERGY_MAC_32b > 0
        assert energy.ENERGY_SPIKE < energy.ENERGY_MAC_32b
        assert energy.SPARSE_ACTIVATION_FACTOR < 1.0
        assert energy.EVENT_DRIVEN_FACTOR < 1.0
    
    def test_snn_energy_reduction(self):
        """Test that SNN operations are more efficient."""
        energy = EnergyEstimates()
        
        # Spike operations should be cheaper than MAC
        assert energy.ENERGY_SPIKE < energy.ENERGY_MAC_16b


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""
    
    def test_creation(self):
        """Test creating a benchmark result."""
        result = BenchmarkResult(
            model_name="test",
            batch_size=4,
            num_samples=100,
        )
        
        assert result.model_name == "test"
        assert result.batch_size == 4
        assert result.num_samples == 100
    
    def test_defaults(self):
        """Test default values."""
        result = BenchmarkResult(
            model_name="test",
            batch_size=1,
            num_samples=0,
        )
        
        assert result.accuracy == 0.0
        assert result.latency_mean == 0.0
        assert result.estimated_energy_per_sample == 0.0


class TestSpikeFormerBenchmark:
    """Test SpikeFormerBenchmark class."""
    
    def test_init(self):
        """Test benchmark initialization."""
        model = CIFAR10SpikeFormer(num_classes=10)
        benchmark = SpikeFormerBenchmark(model, "test_model", device="cpu")
        
        assert benchmark.model_name == "test_model"
        assert benchmark.device == "cpu"
        assert benchmark.num_parameters > 0
    
    def test_model_stats(self):
        """Test model statistics."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=64, num_layers=2)
        benchmark = SpikeFormerBenchmark(model, "tiny_model", device="cpu")
        
        assert benchmark.num_parameters > 0
        assert benchmark.model_size_mb > 0
        assert benchmark.model_size_mb < 50  # Should be small
    
    def test_flops_estimation(self):
        """Test FLOPs estimation."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=64, num_layers=2)
        benchmark = SpikeFormerBenchmark(model, "flops_test", device="cpu")
        
        flops = benchmark.estimate_flops((1, 3, 32, 32))
        
        assert flops > 0
        assert flops < 1e9  # Reasonable upper bound
        print(f"Estimated FLOPs: {flops:.0f}")
    
    def test_energy_estimation(self):
        """Test energy estimation."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=64, num_layers=2)
        benchmark = SpikeFormerBenchmark(model, "energy_test", device="cpu")
        
        flops = benchmark.estimate_flops((1, 3, 32, 32))
        energy = benchmark.estimate_energy(flops)
        
        assert energy > 0
        assert energy < 1e-3  # Should be in mJ range at most
        print(f"Estimated energy: {energy:.6e} J = {energy * 1e6:.4f} µJ")
    
    def test_latency_measurement(self):
        """Test latency measurement."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=32, num_layers=1, T=4)
        benchmark = SpikeFormerBenchmark(model, "latency_test", device="cpu")
        
        latencies, mean = benchmark.measure_latency(
            batch_size=1,
            num_warmup=2,
            num_runs=10,
        )
        
        assert len(latencies) == 10
        assert mean > 0
        print(f"Latency: {mean:.2f} ms ± {max(latencies) - min(latencies):.2f} ms")
    
    def test_full_benchmark(self):
        """Test full benchmark run."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=32, num_layers=1, T=4)
        benchmark = SpikeFormerBenchmark(model, "full_test", device="cpu")
        
        result = benchmark.run(
            batch_size=2,
            num_latency_runs=10,
        )
        
        assert result.model_name == "full_test"
        assert result.batch_size == 2
        assert result.num_parameters > 0
        assert result.latency_mean > 0
        assert result.estimated_flops_per_sample > 0
        assert result.estimated_energy_per_sample > 0


class TestCompareModels:
    """Test model comparison."""
    
    def test_compare_two_models(self):
        """Test comparing two models."""
        models = {
            "tiny_cifar": CIFAR10SpikeFormer(num_classes=10, channels=64, num_layers=2, T=4),
            "base_cifar": CIFAR10SpikeFormer(num_classes=10, channels=128, num_layers=4, T=4),
        }
        
        results = compare_models(
            models,
            batch_size=1,
            num_runs=5,
        )
        
        assert len(results) == 2
        assert "tiny_cifar" in results
        assert "base_cifar" in results
        
        # Base should have more params than tiny
        assert results["base_cifar"].num_parameters > results["tiny_cifar"].num_parameters


class TestFormatResult:
    """Test result formatting."""
    
    def test_format(self):
        """Test formatting a benchmark result."""
        result = BenchmarkResult(
            model_name="test_model",
            batch_size=1,
            num_samples=100,
            accuracy=85.5,
            top5_accuracy=99.0,
            latency_mean=10.5,
            latency_std=2.1,
            num_parameters=1000000,
            model_size_mb=4.0,
        )
        
        formatted = format_benchmark_result(result)
        
        assert "test_model" in formatted
        assert "85.50" in formatted or "85.5" in formatted
        assert "10.50" in formatted or "10.5" in formatted
        assert "1,000,000" in formatted or "1000000" in formatted


class TestEdgeCases:
    """Edge case tests."""
    
    def test_large_batch(self):
        """Test with large batch size."""
        model = CIFAR10SpikeFormer(num_classes=10, channels=32, num_layers=1, T=4)
        benchmark = SpikeFormerBenchmark(model, "large_batch", device="cpu")
        
        result = benchmark.run(batch_size=16, num_latency_runs=5)
        
        assert result.batch_size == 16
        assert result.throughput_samples_per_sec > 0
        
        # Latency should scale roughly linearly with batch
        # but throughput should be higher
        print(f"Throughput: {result.throughput_samples_per_sec:.1f} samples/sec")
    
    def test_snn_vs_ann_params(self):
        """Test that SNN and ANN models have similar parameter counts."""
        # Note: For fair comparison, we'd need an equivalent ANN model
        # Here we just verify our SNN model has reasonable size
        model = CIFAR10SpikeFormer(num_classes=10, channels=128, num_layers=4)
        benchmark = SpikeFormerBenchmark(model, "params_test", device="cpu")
        
        # Model should have < 50M params
        assert benchmark.num_parameters < 50_000_000
        print(f"Total params: {benchmark.num_parameters:,}")
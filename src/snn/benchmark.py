"""Benchmark module for SpikeFormer model evaluation.

Measures:
- Accuracy on CIFAR-10
- Inference latency (mean, std, percentiles)
- Estimated energy consumption (FLOPs-based approximation)

Reference: Xpikeformer paper metrics comparison
"""

import torch
import torch.nn as nn
import time
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager

from src.snn.spikeformer import CIFAR10SpikeFormer, SpikeFormer


@dataclass
class BenchmarkResult:
    """Results from benchmark run."""
    model_name: str
    batch_size: int
    num_samples: int
    
    # Accuracy metrics
    accuracy: float = 0.0
    top5_accuracy: float = 0.0
    
    # Latency metrics (in milliseconds)
    latency_mean: float = 0.0
    latency_std: float = 0.0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    latency_min: float = 0.0
    latency_max: float = 0.0
    
    # Throughput
    throughput_samples_per_sec: float = 0.0
    
    # Energy estimation (in Joules)
    estimated_energy_per_sample: float = 0.0
    estimated_flops_per_sample: float = 0.0
    
    # Model stats
    num_parameters: int = 0
    model_size_mb: float = 0.0


@dataclass 
class EnergyEstimates:
    """Energy consumption estimates per component type.
    
    Based on approximate能耗 per operation (pJ = picojoules)
    From: Horowitz, "1.1 Computing's Energy Problem", ISSCC 2014
    
    Operations are categorized by type:
    - MAC (Multiply-Accumulate): ~4.6 pJ for 28nm
    - ADD: ~0.9 pJ
    - Memory access: ~1-4 pJ per 32-bit
    """
    # Energy per operation type (picojoules)
    ENERGY_MAC_32b: float = 4.6  # 32-bit multiply-accumulate
    ENERGY_MAC_16b: float = 1.9  # 16-bit multiply-accumulate (SNN spikes are 1-bit)
    ENERGY_ADD_32b: float = 0.9  # 32-bit addition
    ENERGY_SPIKE: float = 0.03   # Spike event (very efficient)
    ENERGY_MEMORY_ACCESS: float = 1.4  # 32-bit memory access
    
    # SNN-specific energy reduction factors
    SPARSE_ACTIVATION_FACTOR: float = 0.3  # Spikes are sparse (~30% activation)
    EVENT_DRIVEN_FACTOR: float = 0.1  # Event-driven saves vs clock-driven


class SpikeFormerBenchmark:
    """Benchmark runner for SpikeFormer models."""
    
    def __init__(
        self,
        model: nn.Module,
        model_name: str = "SpikeFormer",
        device: str = "cpu",
        T: int = 8,
    ):
        self.model = model
        self.model_name = model_name
        self.device = device
        self.T = T
        self.energy = EnergyEstimates()
        
        # Move model to device
        self.model.eval()
        self.model.to(device)
        
        # Compute model stats
        self._compute_model_stats()
    
    def _compute_model_stats(self):
        """Compute model statistics."""
        total_params = sum(p.numel() for p in self.model.parameters())
        self.num_parameters = total_params
        
        # Model size in MB (assuming 4 bytes per float)
        self.model_size_mb = total_params * 4 / (1024 * 1024)
    
    def estimate_flops(self, input_shape: Tuple[int, int, int, int]) -> float:
        """Estimate FLOPs for a forward pass.
        
        Based on model architecture analysis.
        
        Args:
            input_shape: (batch, channels, height, width)
        
        Returns:
            Estimated FLOPs per sample
        """
        batch, channels, h, w = input_shape
        flops = 0.0
        
        # Patch embedding: Conv2d (batch, 3, 32, 32) -> (batch, channels, 8, 8)
        patch_size = 4  # CIFAR-10
        flops += batch * channels * 3 * patch_size * patch_size * 8 * 8
        flops += batch * channels * 8 * 8  # LayerNorm approx
        
        # Encoder layers
        num_layers = self.model.num_layers if hasattr(self.model, 'num_layers') else 4
        
        # Each layer: SSA + LIF
        for _ in range(num_layers):
            # SSA: TC + BNF
            # Temporal Convolver: depthwise conv per channel
            spatial_tokens = 65  # 64 patches + CLS token (CIFAR)
            flops += batch * channels * spatial_tokens * 3  # 3x1 conv approx
            
            # BNF: LayerNorm + Linear + Dropout
            flops += batch * spatial_tokens * channels * channels  # Linear
            flops += batch * spatial_tokens * channels * 2  # LayerNorm approx
            
            # LIF: threshold comparison (negligible)
            flops += batch * channels * spatial_tokens
        
        # Classification head: Linear
        flops += batch * channels * self.model.num_classes
        
        # Spike encoding overhead (Bernoulli sampling is ~0 cost)
        flops += batch * channels * spatial_tokens * self.T * 2  # sigmoid + sample
        
        return flops
    
    def estimate_energy(self, flops: float) -> float:
        """Estimate energy consumption in Joules.
        
        Based on FLOPs and operation type analysis.
        SNN spikes are 1-bit, reducing energy significantly.
        
        Args:
            flops: Number of FLOPs per sample
        
        Returns:
            Estimated energy in Joules
        """
        # Convert to MAC energy (1 MAC ≈ 4.6 pJ for 32b)
        # But SNN operations are more efficient:
        # - Spikes are 1-bit (weight is 0 or 1)
        # - Sparse activations (only ~30% of neurons fire)
        # - Event-driven computation (no clock switching)
        
        energy_pj = 0.0
        
        # Patch embedding: Conv2d (32-bit MACs)
        energy_pj += flops * self.energy.ENERGY_MAC_32b
        
        # Apply SNN efficiency factors
        # 1. Sparse activation (only ~30% spikes active)
        energy_pj *= self.energy.SPARSE_ACTIVATION_FACTOR
        
        # 2. Event-driven savings (no static power for inactive neurons)
        energy_pj *= self.energy.EVENT_DRIVEN_FACTOR
        
        # 3. 1-bit vs 32-bit computation (spikes are binary)
        energy_pj /= 32  # 1-bit vs 32-bit efficiency
        
        # Convert from pJ to Joules
        energy_joules = energy_pj * 1e-12
        
        return energy_joules
    
    def measure_latency(
        self,
        batch_size: int = 1,
        num_warmup: int = 10,
        num_runs: int = 100,
    ) -> Tuple[List[float], float]:
        """Measure inference latency.
        
        Args:
            batch_size: Batch size for inference
            num_warmup: Number of warmup iterations
            num_runs: Number of timing runs
        
        Returns:
            Tuple of (latencies in ms, mean latency)
        """
        # Create dummy input
        dummy_input = torch.randn(
            batch_size, 3, 32, 32,
            device=self.device
        )
        
        # Warmup
        with torch.no_grad():
            for _ in range(num_warmup):
                _ = self.model(dummy_input)
        
        # Synchronize before timing
        if self.device == "cuda":
            torch.cuda.synchronize()
        
        # Time runs
        latencies = []
        with torch.no_grad():
            for _ in range(num_runs):
                start = time.perf_counter()
                _ = self.model(dummy_input)
                
                if self.device == "cuda":
                    torch.cuda.synchronize()
                
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
        
        return latencies, statistics.mean(latencies)
    
    def evaluate_accuracy(
        self,
        dataloader,
        device: Optional[str] = None,
    ) -> Tuple[float, float]:
        """Evaluate model accuracy on dataset.
        
        Args:
            dataloader: PyTorch DataLoader
            device: Override device
        
        Returns:
            Tuple of (accuracy, top5_accuracy)
        """
        device = device or self.device
        self.model.eval()
        
        correct = 0
        correct_top5 = 0
        total = 0
        
        with torch.no_grad():
            for inputs, targets in dataloader:
                inputs = inputs.to(device)
                targets = targets.to(device)
                
                outputs = self.model(inputs)
                
                # Top-1
                _, predicted = outputs.max(1)
                correct += predicted.eq(targets).sum().item()
                
                # Top-5
                _, predicted_top5 = outputs.topk(5, 1, True, True)
                correct_top5 += predicted_top5.eq(
                    targets.view(-1, 1).expand_as(predicted_top5)
                ).sum().item()
                
                total += targets.size(0)
        
        accuracy = 100.0 * correct / total
        top5_accuracy = 100.0 * correct_top5 / total
        
        return accuracy, top5_accuracy
    
    def run(
        self,
        batch_size: int = 1,
        num_latency_runs: int = 100,
        dataloader = None,
        device: Optional[str] = None,
    ) -> BenchmarkResult:
        """Run full benchmark.
        
        Args:
            batch_size: Batch size for inference
            num_latency_runs: Number of runs for latency measurement
            dataloader: Optional DataLoader for accuracy evaluation
            device: Device override
        
        Returns:
            BenchmarkResult with all metrics
        """
        device = device or self.device
        
        result = BenchmarkResult(
            model_name=self.model_name,
            batch_size=batch_size,
            num_samples=0,
        )
        
        result.num_parameters = self.num_parameters
        result.model_size_mb = self.model_size_mb
        
        # Estimate FLOPs
        input_shape = (batch_size, 3, 32, 32)
        flops = self.estimate_flops(input_shape)
        result.estimated_flops_per_sample = flops
        
        # Estimate energy
        result.estimated_energy_per_sample = self.estimate_energy(flops)
        
        # Measure latency
        latencies, mean_latency = self.measure_latency(
            batch_size=batch_size,
            num_warmup=10,
            num_runs=num_latency_runs,
        )
        
        result.latency_mean = mean_latency
        result.latency_std = statistics.stdev(latencies) if len(latencies) > 1 else 0
        result.latency_min = min(latencies)
        result.latency_max = max(latencies)
        
        sorted_latencies = sorted(latencies)
        result.latency_p50 = sorted_latencies[len(sorted_latencies) // 2]
        result.latency_p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        result.latency_p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        # Throughput
        result.throughput_samples_per_sec = (batch_size / (mean_latency / 1000))
        
        # Accuracy if dataloader provided
        if dataloader is not None:
            accuracy, top5_accuracy = self.evaluate_accuracy(dataloader, device)
            result.accuracy = accuracy
            result.top5_accuracy = top5_accuracy
            result.num_samples = len(dataloader.dataset)
        
        return result


def format_benchmark_result(result: BenchmarkResult) -> str:
    """Format benchmark result as a readable string."""
    # Format energy with appropriate unit
    energy_j = result.estimated_energy_per_sample
    if energy_j < 1e-9:
        energy_str = f"{energy_j * 1e12:.2f} pJ"
    elif energy_j < 1e-6:
        energy_str = f"{energy_j * 1e9:.2f} nJ"
    elif energy_j < 1e-3:
        energy_str = f"{energy_j * 1e6:.2f} µJ"
    else:
        energy_str = f"{energy_j * 1e3:.2f} mJ"
    
    lines = [
        "=" * 60,
        f"Benchmark Results: {result.model_name}",
        "=" * 60,
        "",
        "Model Statistics:",
        f"  Parameters: {result.num_parameters:,}",
        f"  Model Size: {result.model_size_mb:.2f} MB",
        "",
        "Latency (ms):",
        f"  Mean:     {result.latency_mean:.2f} ± {result.latency_std:.2f}",
        f"  Min:      {result.latency_min:.2f}",
        f"  Max:      {result.latency_max:.2f}",
        f"  P50:      {result.latency_p50:.2f}",
        f"  P95:      {result.latency_p95:.2f}",
        f"  P99:      {result.latency_p99:.2f}",
        "",
        "Throughput:",
        f"  {result.throughput_samples_per_sec:.1f} samples/sec",
        "",
        "Energy (estimated):",
        f"  FLOPs/sample: {result.estimated_flops_per_sample:.0f}",
        f"  Energy/sample: {energy_str}",
        "  Note: Simplified estimate based on FLOPs",
        "  Real energy requires hardware measurement",
        "",
    ]
    
    if result.num_samples > 0:
        lines.extend([
            "Accuracy:",
            f"  Top-1:  {result.accuracy:.2f}%",
            f"  Top-5:  {result.top5_accuracy:.2f}%",
            f"  Samples: {result.num_samples}",
        ])
    
    lines.append("=" * 60)
    return "\n".join(lines)


def compare_models(
    models: Dict[str, nn.Module],
    batch_size: int = 1,
    num_runs: int = 100,
    dataloader = None,
    device: str = "cpu",
) -> Dict[str, BenchmarkResult]:
    """Benchmark multiple models for comparison.
    
    Args:
        models: Dict of model_name -> model
        batch_size: Batch size
        num_runs: Number of timing runs
        dataloader: Optional DataLoader
        device: Device to run on
    
    Returns:
        Dict of model_name -> BenchmarkResult
    """
    results = {}
    
    for name, model in models.items():
        print(f"\nBenchmarking {name}...")
        
        benchmark = SpikeFormerBenchmark(
            model=model,
            model_name=name,
            device=device,
        )
        
        result = benchmark.run(
            batch_size=batch_size,
            num_latency_runs=num_runs,
            dataloader=dataloader,
        )
        
        results[name] = result
        print(format_benchmark_result(result))
    
    return results


def print_comparison_table(results: Dict[str, BenchmarkResult]):
    """Print a comparison table for multiple models."""
    print("\n" + "=" * 100)
    print("Model Comparison")
    print("=" * 100)
    print(f"{'Model':<22} {'Params':<12} {'Latency':<10} {'Throughput':<12} {'Energy':<15} {'Accuracy':<10}")
    print(f"{'':22} {'':12} {'(ms)':<10} {'(samples/s)':<12} {'(estimated)':<15} {'(%)':<10}")
    print("-" * 100)
    
    for name, result in results.items():
        # Format energy
        energy_j = result.estimated_energy_per_sample
        if energy_j < 1e-9:
            energy_str = f"{energy_j * 1e12:.1f} pJ"
        elif energy_j < 1e-6:
            energy_str = f"{energy_j * 1e9:.1f} nJ"
        elif energy_j < 1e-3:
            energy_str = f"{energy_j * 1e6:.1f} µJ"
        else:
            energy_str = f"{energy_j * 1e3:.1f} mJ"
        
        # Format accuracy
        if result.num_samples > 0:
            acc_str = f"{result.accuracy:.2f}%"
        else:
            acc_str = "N/A"
        
        print(
            f"{name:<22} "
            f"{result.num_parameters:<12,} "
            f"{result.latency_mean:<10.2f} "
            f"{result.throughput_samples_per_sec:<12.1f} "
            f"{energy_str:<15} "
            f"{acc_str:<10}"
        )
    
    print("-" * 100)
    print("Note: Energy is estimated based on FLOPs. Real measurement requires hardware.")
    print("=" * 100)
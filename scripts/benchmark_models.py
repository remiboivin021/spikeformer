"""Benchmark script for SpikeFormer models.

Usage:
    python scripts/benchmark_models.py --model snn --size base
    python scripts/benchmark_models.py --model ann --size base
    python scripts/benchmark_models.py --compare
    python scripts/benchmark_models.py --all
"""

import argparse
import torch
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.snn.spikeformer import CIFAR10SpikeFormer, create_spikeformer
from src.ann.transformer import CIFAR10ANNTransformer, create_ann_transformer
from src.snn.benchmark import (
    SpikeFormerBenchmark,
    BenchmarkResult,
    format_benchmark_result,
    compare_models,
    print_comparison_table,
)


def get_model_config(size: str, model_type: str):
    """Get model configuration based on size.
    
    Args:
        size: 'tiny', 'small', 'base', 'large'
        model_type: 'snn' or 'ann'
    
    Returns:
        Model configuration dict
    """
    configs = {
        'tiny': dict(channels=64, num_layers=2, T=4),
        'small': dict(channels=96, num_layers=3, T=6),
        'base': dict(channels=128, num_layers=4, T=8),
        'large': dict(channels=192, num_layers=6, T=8),
    }
    
    if size not in configs:
        raise ValueError(f"Unknown size: {size}. Options: {list(configs.keys())}")
    
    return configs[size]


def create_snn_model(size: str = 'base', num_classes: int = 10):
    """Create SNN model.
    
    Args:
        size: Model size
        num_classes: Number of classes
    
    Returns:
        CIFAR10SpikeFormer model
    """
    config = get_model_config(size, 'snn')
    return CIFAR10SpikeFormer(
        num_classes=num_classes,
        channels=config['channels'],
        num_layers=config['num_layers'],
        T=config['T'],
    )


def create_ann_model(size: str = 'base', num_classes: int = 10):
    """Create ANN model.
    
    Args:
        size: Model size
        num_classes: Number of classes
    
    Returns:
        CIFAR10ANNTransformer model
    """
    config = get_model_config(size, 'ann')
    # ANN uses same embed_dim as SNN channels for fair comparison
    embed_dim = config['channels']
    return CIFAR10ANNTransformer(
        num_classes=num_classes,
        embed_dim=embed_dim,
        num_layers=config['num_layers'],
    )


def run_benchmark(
    model,
    model_name: str,
    batch_size: int = 4,
    num_runs: int = 50,
    device: str = 'cpu',
):
    """Run benchmark on a model.
    
    Args:
        model: PyTorch model
        model_name: Name for display
        batch_size: Batch size
        num_runs: Number of timing runs
        device: Device to run on
    
    Returns:
        BenchmarkResult
    """
    benchmark = SpikeFormerBenchmark(
        model=model,
        model_name=model_name,
        device=device,
    )
    
    return benchmark.run(
        batch_size=batch_size,
        num_latency_runs=num_runs,
    )


def benchmark_snn(size: str = 'base', batch_size: int = 4, num_runs: int = 50):
    """Benchmark SNN model.
    
    Args:
        size: Model size
        batch_size: Batch size
        num_runs: Number of timing runs
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking SNN SpikeFormer ({size})")
    print(f"{'='*60}\n")
    
    model = create_snn_model(size)
    model_name = f"SNN SpikeFormer ({size})"
    
    result = run_benchmark(model, model_name, batch_size, num_runs)
    print(format_benchmark_result(result))
    
    return result


def benchmark_ann(size: str = 'base', batch_size: int = 4, num_runs: int = 50):
    """Benchmark ANN model.
    
    Args:
        size: Model size
        batch_size: Batch size
        num_runs: Number of timing runs
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking ANN Transformer ({size})")
    print(f"{'='*60}\n")
    
    model = create_ann_model(size)
    model_name = f"ANN Transformer ({size})"
    
    result = run_benchmark(model, model_name, batch_size, num_runs)
    print(format_benchmark_result(result))
    
    return result


def compare_ann_snn(sizes: list = None, batch_size: int = 4, num_runs: int = 50):
    """Compare ANN and SNN models.
    
    Args:
        sizes: List of sizes to compare
        batch_size: Batch size
        num_runs: Number of timing runs
    """
    if sizes is None:
        sizes = ['tiny', 'base']
    
    print(f"\n{'='*60}")
    print(f"Comparing ANN vs SNN ({', '.join(sizes)})")
    print(f"{'='*60}\n")
    
    models = {}
    
    for size in sizes:
        config = get_model_config(size, 'snn')
        
        # ANN model
        ann_name = f"ANN ({size})"
        models[ann_name] = create_ann_model(size)
        
        # SNN model
        snn_name = f"SNN ({size}, T={config['T']})"
        models[snn_name] = create_snn_model(size)
    
    results = compare_models(models, batch_size=batch_size, num_runs=num_runs)
    print_comparison_table(results)
    
    return results


def benchmark_all(batch_size: int = 4, num_runs: int = 50):
    """Benchmark all models.
    
    Args:
        batch_size: Batch size
        num_runs: Number of timing runs
    """
    print(f"\n{'='*60}")
    print("Benchmarking ALL models")
    print(f"{'='*60}\n")
    
    models = {}
    
    for size in ['tiny', 'small', 'base']:
        config = get_model_config(size, 'snn')
        
        # ANN
        models[f"ANN {size}"] = create_ann_model(size)
        
        # SNN
        models[f"SNN {size} (T={config['T']})"] = create_snn_model(size)
    
    results = compare_models(models, batch_size=batch_size, num_runs=num_runs)
    print_comparison_table(results)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark SpikeFormer models'
    )
    parser.add_argument(
        '--model',
        choices=['ann', 'snn', 'compare', 'all'],
        default='all',
        help='Model to benchmark (default: all)',
    )
    parser.add_argument(
        '--size',
        choices=['tiny', 'small', 'base', 'large'],
        default='base',
        help='Model size for single model benchmark',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Batch size',
    )
    parser.add_argument(
        '--num-runs',
        type=int,
        default=50,
        help='Number of timing runs',
    )
    parser.add_argument(
        '--device',
        choices=['cpu', 'cuda'],
        default='cpu',
        help='Device to run on',
    )
    
    args = parser.parse_args()
    
    if args.model == 'ann':
        benchmark_ann(args.size, args.batch_size, args.num_runs)
    elif args.model == 'snn':
        benchmark_snn(args.size, args.batch_size, args.num_runs)
    elif args.model == 'compare':
        compare_ann_snn(
            sizes=['tiny', 'small', 'base'],
            batch_size=args.batch_size,
            num_runs=args.num_runs,
        )
    else:  # all
        benchmark_all(args.batch_size, args.num_runs)


if __name__ == '__main__':
    main()  # Usage: python scripts/benchmark_models.py --compare
    # Or: python scripts/benchmark_models.py --model compare
"""Benchmark script for SpikeFormer models.

Usage:
    # Latency benchmark only
    python scripts/benchmark_models.py --model snn --size base
    python scripts/benchmark_models.py --model ann --size base
    python scripts/benchmark_models.py --compare
    
    # Benchmark with accuracy (requires trained model)
    python scripts/benchmark_models.py --model snn --size base --accuracy
    python scripts/benchmark_models.py --model ann --size base --accuracy
    
    # Load checkpoint for accuracy
    python scripts/benchmark_models.py --model snn --size base --accuracy --checkpoint checkpoints/snn_best.pth
    python scripts/benchmark_models.py --model ann --size base --accuracy --checkpoint checkpoints_ann/ann_best.pth
"""

import argparse
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.snn.spikeformer import CIFAR10SpikeFormer
from src.ann.transformer import CIFAR10ANNTransformer
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


def get_cifar10_dataloader(batch_size: int = 128):
    """Get CIFAR-10 dataloader for accuracy evaluation.
    
    Args:
        batch_size: Batch size
    
    Returns:
        DataLoader
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    
    dataset = torchvision.datasets.CIFAR10(
        root='./data_cifar10',
        train=False,
        download=True,
        transform=transform,
    )
    
    return DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)


def load_checkpoint(model, checkpoint_path: str, device: str = 'cpu'):
    """Load model checkpoint.
    
    Args:
        model: Model to load weights into
        checkpoint_path: Path to checkpoint file
        device: Device
    
    Returns:
        Model with loaded weights, best accuracy if found
    """
    if os.path.isfile(checkpoint_path):
        print(f"  Loading checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        
        # Try to load state dict (handle different formats)
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            best_acc = checkpoint.get('best_accuracy', checkpoint.get('accuracy', 0))
        elif 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            best_acc = checkpoint.get('best_accuracy', 0)
        else:
            # Direct state dict
            model.load_state_dict(checkpoint)
            best_acc = checkpoint.get('best_accuracy', 0)
        
        print(f"  Loaded! Best accuracy: {best_acc:.2f}%")
        return best_acc
    else:
        print(f"  Warning: Checkpoint not found: {checkpoint_path}")
        return 0


def run_benchmark(
    model,
    model_name: str,
    batch_size: int = 4,
    num_runs: int = 50,
    device: str = 'cpu',
    dataloader = None,
    checkpoint_path: str = None,
):
    """Run benchmark on a model.
    
    Args:
        model: PyTorch model
        model_name: Name for display
        batch_size: Batch size
        num_runs: Number of timing runs
        device: Device to run on
        dataloader: Optional dataloader for accuracy evaluation
        checkpoint_path: Optional path to checkpoint
    
    Returns:
        BenchmarkResult
    """
    # Load checkpoint if provided
    best_accuracy = 0
    if checkpoint_path:
        best_accuracy = load_checkpoint(model, checkpoint_path, device)
    
    benchmark = SpikeFormerBenchmark(
        model=model,
        model_name=model_name,
        device=device,
    )
    
    result = benchmark.run(
        batch_size=batch_size,
        num_latency_runs=num_runs,
        dataloader=dataloader,
    )
    
    # Use loaded accuracy if available
    if best_accuracy > 0:
        result.accuracy = best_accuracy
    
    return result


def benchmark_snn(
    size: str = 'base',
    batch_size: int = 4,
    num_runs: int = 50,
    with_accuracy: bool = False,
    checkpoint: str = None,
):
    """Benchmark SNN model.
    
    Args:
        size: Model size
        batch_size: Batch size
        num_runs: Number of timing runs
        with_accuracy: Evaluate accuracy on CIFAR-10 test set
        checkpoint: Optional path to checkpoint file
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking SNN SpikeFormer ({size})")
    print(f"{'='*60}\n")
    
    model = create_snn_model(size)
    model_name = f"SNN SpikeFormer ({size})"
    
    # Get dataloader if accuracy requested
    dataloader = None
    if with_accuracy:
        print("Loading CIFAR-10 test set...")
        dataloader = get_cifar10_dataloader(batch_size=batch_size)
    
    result = run_benchmark(
        model, model_name, batch_size, num_runs,
        dataloader=dataloader, checkpoint_path=checkpoint
    )
    print(format_benchmark_result(result))
    
    return result


def benchmark_ann(
    size: str = 'base',
    batch_size: int = 4,
    num_runs: int = 50,
    with_accuracy: bool = False,
    checkpoint: str = None,
):
    """Benchmark ANN model.
    
    Args:
        size: Model size
        batch_size: Batch size
        num_runs: Number of timing runs
        with_accuracy: Evaluate accuracy on CIFAR-10 test set
        checkpoint: Optional path to checkpoint file
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking ANN Transformer ({size})")
    print(f"{'='*60}\n")
    
    model = create_ann_model(size)
    model_name = f"ANN Transformer ({size})"
    
    # Get dataloader if accuracy requested
    dataloader = None
    if with_accuracy:
        print("Loading CIFAR-10 test set...")
        dataloader = get_cifar10_dataloader(batch_size=batch_size)
    
    result = run_benchmark(
        model, model_name, batch_size, num_runs,
        dataloader=dataloader, checkpoint_path=checkpoint
    )
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
    parser.add_argument(
        '--accuracy',
        action='store_true',
        help='Evaluate accuracy on CIFAR-10 test set',
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        default=None,
        help='Path to checkpoint file for accuracy evaluation',
    )
    
    args = parser.parse_args()
    
    if args.model == 'ann':
        benchmark_ann(
            args.size, args.batch_size, args.num_runs,
            with_accuracy=args.accuracy, checkpoint=args.checkpoint
        )
    elif args.model == 'snn':
        benchmark_snn(
            args.size, args.batch_size, args.num_runs,
            with_accuracy=args.accuracy, checkpoint=args.checkpoint
        )
    elif args.model == 'compare':
        compare_ann_snn(
            sizes=['tiny', 'small', 'base'],
            batch_size=args.batch_size,
            num_runs=args.num_runs,
        )
    else:  # all
        benchmark_all(args.batch_size, args.num_runs)


if __name__ == '__main__':
    main()
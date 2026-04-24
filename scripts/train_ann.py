"""Training script for ANN Transformer on CIFAR-10.

This script trains the ANN baseline for comparison with SNN SpikeFormer.
It uses separate checkpoints from SNN training.

Usage:
    python scripts/train_ann.py --epochs 100 --batch-size 128
    python scripts/train_ann.py --resume checkpoints/ann_best.pth --epochs 50
"""

import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision
import torchvision.transforms as transforms
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ann.transformer import CIFAR10ANNTransformer, create_ann_transformer


def get_transforms(augment: bool = True):
    """Get data transforms.
    
    Args:
        augment: Use data augmentation
    
    Returns:
        train_transform, test_transform
    """
    if augment:
        train_transform = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
    else:
        train_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
    
    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    
    return train_transform, test_transform


def create_dataloaders(batch_size: int = 128, num_workers: int = 4):
    """Create CIFAR-10 dataloaders.
    
    Args:
        batch_size: Batch size
        num_workers: Number of workers
    
    Returns:
        train_loader, test_loader
    """
    train_transform, test_transform = get_transforms()
    
    # Data directory (separate from SNN)
    data_dir = './data_cifar10_ann'
    os.makedirs(data_dir, exist_ok=True)
    
    train_dataset = torchvision.datasets.CIFAR10(
        root=data_dir,
        train=True,
        download=True,
        transform=train_transform,
    )
    
    test_dataset = torchvision.datasets.CIFAR10(
        root=data_dir,
        train=False,
        download=True,
        transform=test_transform,
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    return train_loader, test_loader


def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train for one epoch.
    
    Args:
        model: Model to train
        train_loader: Training data loader
        criterion: Loss function
        optimizer: Optimizer
        device: Device
    
    Returns:
        Average loss
    """
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for inputs, targets in train_loader:
        inputs = inputs.to(device)
        targets = targets.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        correct += predicted.eq(targets).sum().item()
        total += targets.size(0)
    
    return total_loss / len(train_loader), 100.0 * correct / total


def evaluate(model, test_loader, criterion, device):
    """Evaluate model.
    
    Args:
        model: Model to evaluate
        test_loader: Test data loader
        criterion: Loss function
        device: Device
    
    Returns:
        Average loss, accuracy
    """
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            correct += predicted.eq(targets).sum().item()
            total += targets.size(0)
    
    return total_loss / len(test_loader), 100.0 * correct / total


def save_checkpoint(model, optimizer, epoch, accuracy, best_accuracy, checkpoint_dir):
    """Save training checkpoint.
    
    Args:
        model: Model
        optimizer: Optimizer
        epoch: Current epoch
        accuracy: Current accuracy
        best_accuracy: Best accuracy so far
        checkpoint_dir: Directory to save checkpoints
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Save latest
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'accuracy': accuracy,
        'best_accuracy': best_accuracy,
    }
    torch.save(checkpoint, os.path.join(checkpoint_dir, 'ann_latest.pth'))
    
    # Save best
    if accuracy > best_accuracy:
        torch.save(model.state_dict(), os.path.join(checkpoint_dir, 'ann_best.pth'))
        print(f"  -> New best accuracy: {accuracy:.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Train ANN Transformer on CIFAR-10'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of epochs',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=128,
        help='Batch size',
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=1e-3,
        help='Learning rate',
    )
    parser.add_argument(
        '--size',
        choices=['tiny', 'small', 'base', 'large'],
        default='base',
        help='Model size',
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Resume from checkpoint',
    )
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='./checkpoints_ann',
        help='Checkpoint directory',
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda' if torch.cuda.is_available() else 'cpu',
        help='Device to use',
    )
    
    args = parser.parse_args()
    
    device = torch.device(args.device)
    print(f"\n{'='*60}")
    print(f"Training ANN Transformer ({args.size}) on CIFAR-10")
    print(f"Device: {device}")
    print(f"{'='*60}\n")
    
    # Create model
    configs = {
        'tiny': dict(embed_dim=64, num_layers=2, num_heads=4),
        'small': dict(embed_dim=96, num_layers=3, num_heads=8),
        'base': dict(embed_dim=128, num_layers=4, num_heads=8),
        'large': dict(embed_dim=192, num_layers=6, num_heads=12),
    }
    
    config = configs[args.size]
    model = CIFAR10ANNTransformer(
        num_classes=10,
        embed_dim=config['embed_dim'],
        num_layers=config['num_layers'],
        num_heads=config['num_heads'],
    )
    model = model.to(device)
    
    # Count parameters
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {num_params:,}\n")
    
    # Resume if specified
    start_epoch = 0
    best_accuracy = 0.0
    if args.resume:
        if os.path.isfile(args.resume):
            print(f"Loading checkpoint from {args.resume}")
            checkpoint = torch.load(args.resume, map_location=device)
            model.load_state_dict(checkpoint['model_state_dict'])
            start_epoch = checkpoint.get('epoch', 0) + 1
            best_accuracy = checkpoint.get('best_accuracy', 0.0)
            print(f"Resuming from epoch {start_epoch}, best accuracy: {best_accuracy:.2f}%")
        else:
            print(f"Warning: Checkpoint {args.resume} not found")
    
    # Create dataloaders
    train_loader, test_loader = create_dataloaders(
        batch_size=args.batch_size,
        num_workers=0,  # Set to 0 on Windows
    )
    
    print(f"Training samples: {len(train_loader.dataset):,}")
    print(f"Test samples: {len(test_loader.dataset):,}\n")
    
    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.05)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # Training loop
    print("Starting training...\n")
    start_time = datetime.now()
    
    for epoch in range(start_epoch, args.epochs):
        epoch_start = datetime.now()
        
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device
        )
        
        # Evaluate
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )
        
        # Update scheduler
        scheduler.step()
        
        # Save checkpoint
        save_checkpoint(
            model, optimizer, epoch, test_acc, best_accuracy, args.checkpoint_dir
        )
        best_accuracy = max(best_accuracy, test_acc)
        
        # Print progress
        epoch_time = (datetime.now() - epoch_start).total_seconds()
        print(
            f"Epoch {epoch+1}/{args.epochs} | "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
            f"Test Loss: {test_loss:.4f} | Test Acc: {test_acc:.2f}% | "
            f"Time: {epoch_time:.1f}s"
        )
    
    # Print summary
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"Training completed in {total_time/60:.1f} minutes")
    print(f"Best accuracy: {best_accuracy:.2f}%")
    print(f"Checkpoints saved to: {args.checkpoint_dir}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
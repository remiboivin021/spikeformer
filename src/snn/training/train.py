"""Training pipeline for SpikeFormer."""

import argparse
import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional

from src.snn.config import load_model_config, load_training_config
from src.snn.neurons import LeakyIntegrateAndFire
from src.snn.neurons import BernoulliNeuron
from src.snn.encoding import BernoulliEncoder
from src.snn.architecture import SSAModule


class XpikeformerSNN(nn.Module):
    """SpikeFormer SNN model.
    
    Combines:
    - Bernoulli Encoder (input encoding)
    - SSA Modules (spike sweep architecture)
    - LIF neurons (spiking dynamics)
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int = 3,
        T: int = 8,
        dropout: float = 0.1,
    ):
        """Initialize Xpikeformer SNN.
        
        Args:
            input_dim: Input features (e.g., 3072 for CIFAR-10)
            hidden_dim: Hidden dimension
            output_dim: Output dimension (10 for CIFAR-10)
            num_layers: Number of SSA layers
            T: Number of timesteps
            dropout: Dropout probability
        """
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.T = T
        
        # Input encoder
        self.encoder = BernoulliEncoder(T=T)
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # SSA layers
        self.layers = nn.ModuleList([
            SSAModule(channels=hidden_dim, dropout=dropout)
            for _ in range(num_layers)
        ])
        
        # LIF neurons for each layer
        self.lif_neurons = nn.ModuleList([
            LeakyIntegrateAndFire(threshold=1.0, beta=0.95)
            for _ in range(num_layers)
        ])
        
        # Output projection
        self.output_proj = nn.Linear(hidden_dim, output_dim)
        
        # Count spikes for monitoring
        self.spike_count = 0
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input tensor (batch, input_dim) - flattened images
        
        Returns:
            Output tensor (batch, output_dim)
        """
        batch_size = x.shape[0]
        
        # Encode input to spike probabilities
        x = self.encoder(x)  # (batch, input_dim, T)
        
        # Project to hidden dimension - process per timestep
        # (batch, input_dim, T) -> (batch, T, input_dim) -> (batch, T, hidden_dim) -> (batch, hidden_dim, T)
        x = x.transpose(1, 2)  # (batch, T, input_dim)
        x = self.input_proj(x)  # (batch, T, hidden_dim)
        x = x.transpose(1, 2)  # (batch, hidden_dim, T)
        
        # Apply SSA layers with LIF
        membrane = torch.zeros(batch_size, self.hidden_dim, device=x.device)
        
        for i, (layer, lif) in enumerate(zip(self.layers, self.lif_neurons)):
            # Apply SSA transformation
            x = layer(x)
            
            # LIF dynamics - take first timestep for membrane
            spikes, membrane = lif(membrane, x[:, :, 0])
            x = spikes.unsqueeze(-1).expand_as(x)
        
        # Output projection - sum over timesteps
        x = x.sum(dim=-1)  # (batch, hidden_dim)
        x = self.output_proj(x)  # (batch, output_dim)
        
        return x


def train_epoch(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: str = "cuda",
) -> float:
    """Train for one epoch.
    
    Args:
        model: Model to train
        train_loader: Training data loader
        optimizer: Optimizer
        criterion: Loss criterion
        device: Device (cuda/cpu)
    
    Returns:
        Average loss for epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        # CIFAR-10: (batch, 3, 32, 32) -> (batch, 3072)
        if inputs.dim() == 4:
            inputs = inputs.view(inputs.size(0), -1)
        
        inputs = inputs.to(device)
        targets = targets.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / max(num_batches, 1)


def evaluate(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: str = "cuda",
) -> tuple[float, float]:
    """Evaluate model.
    
    Args:
        model: Model to evaluate
        val_loader: Validation data loader
        criterion: Loss criterion
        device: Device
    
    Returns:
        Tuple of (average loss, accuracy)
    """
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    num_batches = 0
    
    with torch.no_grad():
        for inputs, targets in val_loader:
            # CIFAR-10: (batch, 3, 32, 32) -> (batch, 3072)
            if inputs.dim() == 4:
                inputs = inputs.view(inputs.size(0), -1)
            
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
            
            # Classification accuracy
            predictions = outputs.argmax(dim=-1)
            correct += (predictions == targets).sum().item()
            total += targets.shape[0]
            num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    accuracy = correct / max(total, 1)
    
    return avg_loss, accuracy


def create_dummy_dataloader(
    batch_size: int = 32,
    num_samples: int = 1000,
    input_dim: int = 128,
    num_classes: int = 10,
) -> torch.utils.data.DataLoader:
    """Create dummy dataloader for testing.
    
    Args:
        batch_size: Batch size
        num_samples: Number of samples
        input_dim: Input dimension
        num_classes: Number of classes
    
    Returns:
        DataLoader with dummy data
    """
    # Synthetic classification data
    X = torch.randn(num_samples, input_dim)
    y = torch.randint(0, num_classes, (num_samples,))
    
    dataset = torch.utils.data.TensorDataset(X, y)
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
    )
    
    return loader


def create_cifar10_dataloader(
    batch_size: int = 32,
    data_dir: str = "./data",
    train: bool = True,
    download: bool = True,
    num_workers: int = 2,
) -> torch.utils.data.DataLoader:
    """Create CIFAR-10 dataloader.
    
    Args:
        batch_size: Batch size
        data_dir: Data directory
        train: Training or validation split
        download: Download if not present
        num_workers: Data loading workers
    
    Returns:
        DataLoader with CIFAR-10 data
    """
    import torchvision
    import torchvision.transforms as transforms
    
    # CIFAR-10 transforms
    if train:
        transform = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])
    else:
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ])
    
    dataset = torchvision.datasets.CIFAR10(
        root=data_dir,
        train=train,
        download=download,
        transform=transform,
    )
    
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=train,
        num_workers=num_workers,
    )
    
    return loader


def main(args):
    """Main training function.
    
    Args:
        args: Command line arguments
    """
    # Load configurations
    model_config = load_model_config(args.model)
    train_config = load_training_config(args.config)
    
    # Device
    device = train_config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Model parameters from config
    # CIFAR-10: 32x32x3 = 3072 input, 10 classes
    input_dim = model_config.get("input_dim", 3072)  # CIFAR-10: 32*32*3
    hidden_dim = model_config.get("hidden_dim", 256)
    output_dim = model_config.get("output_dim", 10)  # CIFAR-10: 10 classes
    num_layers = model_config.get("num_layers", 3)
    T = model_config.get("T", 8)
    dropout = model_config.get("dropout", 0.1)
    
    # Create model
    model = XpikeformerSNN(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        num_layers=num_layers,
        T=T,
        dropout=dropout,
    ).to(device)
    
    print(f"Model: {model.__class__.__name__}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")
    
    # Dataset selection
    dataset_name = train_config.get("dataset", "dummy")
    data_dir = train_config.get("data_dir", "./data")
    
    if dataset_name == "cifar10":
        print(f"\nLoading CIFAR-10 dataset...")
        batch_size = train_config.get("batch_size", 32)
        train_loader = create_cifar10_dataloader(
            batch_size=batch_size,
            data_dir=data_dir,
            train=True,
            download=True,
        )
        val_loader = create_cifar10_dataloader(
            batch_size=batch_size,
            data_dir=data_dir,
            train=False,
            download=True,
        )
    else:
        # Create dataloaders
        batch_size = train_config.get("batch_size", 32)
        train_loader = create_dummy_dataloader(
            batch_size=batch_size,
            num_samples=train_config.get("num_train_samples", 1000),
            input_dim=input_dim,
            num_classes=output_dim,
        )
        val_loader = create_dummy_dataloader(
            batch_size=batch_size,
            num_samples=train_config.get("num_val_samples", 200),
            input_dim=input_dim,
            num_classes=output_dim,
        )
    
    # Optimizer and loss
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=train_config.get("learning_rate", 1e-3),
    )
    criterion = nn.CrossEntropyLoss()
    
    # Training loop
    num_epochs = train_config.get("num_epochs", 10)
    
    print(f"\nTraining for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        train_loss = train_epoch(
            model, train_loader, optimizer, criterion, device
        )
        val_loss, val_acc = evaluate(
            model, val_loader, criterion, device
        )
        
        print(f"Epoch {epoch+1}/{num_epochs} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | "
              f"Val Acc: {val_acc:.4f}")
    
    print("\nTraining complete!")
    
    # Save model
    output_path = train_config.get("checkpoint_dir", "checkpoints") / "xpikeformer_final.pt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Xpikeformer SNN")
    parser.add_argument(
        "--config",
        type=str,
        default="config/training/conventional.yaml",
        help="Training config file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="config/model/xpikeformer_small.yaml",
        help="Model config file",
    )
    args = parser.parse_args()
    main(args)

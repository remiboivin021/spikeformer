"""Training pipeline for SpikeFormer with pretrained support."""

import argparse
import torch
import torch.nn as nn
import torchvision.models as models
from pathlib import Path
from typing import Optional

from src.snn.config import load_model_config, load_training_config
from src.snn.neurons import LeakyIntegrateAndFire
from src.snn.neurons import BernoulliNeuron
from src.snn.encoding import BernoulliEncoder
from src.snn.architecture import SSAModule


def load_pretrained_resnet20(num_classes: int = 10) -> nn.Module:
    """Load pretrained ResNet-20 for transfer learning.
    
    Reference: Section IV, Section V-A of Xpikeformer paper
    Uses pretrained ResNet trained on ImageNet, then fine-tunes.
    
    Args:
        num_classes: Number of output classes
    
    Returns:
        Pretrained ResNet-20 model
    """
    # Try to load ResNet20, fall back to ResNet18 if not available
    try:
        model = models.resnet20(weights=models.ResNet20_Weights.IMAGENET1K_V1)
        print("Loaded pretrained ResNet-20 (ImageNet)")
    except Exception:
        try:
            model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            print("Loaded pretrained ResNet-18 (ImageNet)")
        except Exception:
            model = models.resnet18(weights=None)
            print("Warning: Could not load pretrained weights")
    
    # Replace final FC layer for our num_classes
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    
    return model


def load_checkpoint(checkpoint_path: str, device: str = "cpu") -> nn.Module:
    """Load model from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        device: Device to load on
    
    Returns:
        Loaded model
    """
    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    state_dict = torch.load(checkpoint_path, map_location=device)
    
    # Try to create model and load weights
    model = load_pretrained_resnet20(num_classes=10)
    model.load_state_dict(state_dict)
    print(f"Loaded checkpoint from {checkpoint_path}")
    
    return model


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
        x = x.transpose(1, 2)  # (batch, T, input_dim)
        x = self.input_proj(x)  # (batch, T, hidden_dim)
        x = x.transpose(1, 2)  # (batch, hidden_dim, T)
        
        # Apply SSA layers with LIF
        membrane = torch.zeros(batch_size, self.hidden_dim, device=x.device)
        
        for i, (layer, lif) in enumerate(zip(self.layers, self.lif_neurons)):
            x = layer(x)
            spikes, membrane = lif(membrane, x[:, :, 0])
            x = spikes.unsqueeze(-1).expand_as(x)
        
        # Output projection - sum over timesteps
        x = x.sum(dim=-1)  # (batch, hidden_dim)
        x = self.output_proj(x)  # (batch, output_dim)
        
        return x


class ImageNetClassifier(nn.Module):
    """ImageNet-style classifier with pretrained backbone.
    
    Simpler approach: Use pretrained ResNet as feature extractor
    with custom head for CIFAR-10.
    """
    
    def __init__(
        self,
        backbone: str = "resnet18",
        num_classes: int = 10,
        pretrained: bool = True,
        freeze_backbone: bool = False,
    ):
        """Initialize classifier.
        
        Args:
            backbone: Backbone architecture (resnet18/resnet20)
            num_classes: Number of output classes
            pretrained: Use ImageNet pretrained weights
            freeze_backbone: Freeze backbone weights
        """
        super().__init__()
        self.num_classes = num_classes
        self.freeze_backbone = freeze_backbone
        
        # Load backbone
        if backbone == "resnet20":
            try:
                self.backbone = models.resnet20(
                    weights=models.ResNet20_Weights.IMAGENET1K_V1 if pretrained else None
                )
            except Exception:
                self.backbone = models.resnet18(
                    weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
                )
        else:
            self.backbone = models.resnet18(
                weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
            )
        
        # Replace final layer
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)
        
        # Optionally freeze backbone
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
            self.backbone.fc.weight.requires_grad = True
            self.backbone.fc.bias.requires_grad = True
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input tensor (batch, 3, 32, 32) for CIFAR-10
        
        Returns:
            Output tensor (batch, num_classes)
        """
        # ResNet expects (batch, 3, 224, 224) - resize for CIFAR
        if x.shape[-1] == 32:
            x = torch.nn.functional.interpolate(
                x, size=224, mode='bilinear', align_corners=False
            )
        
        x = self.backbone(x)
        return x


def train_epoch(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: str = "cpu",
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, (inputs, targets) in enumerate(train_loader):
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


def train_epoch_imageNet(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: str = "cpu",
) -> float:
    """Train ImageNet classifier for one epoch."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        # inputs already (batch, 3, 32, 32) for CIFAR
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
    device: str = "cpu",
) -> tuple[float, float]:
    """Evaluate model."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    num_batches = 0
    
    with torch.no_grad():
        for inputs, targets in val_loader:
            if inputs.dim() == 4:
                inputs = inputs.view(inputs.size(0), -1)
            
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
            
            predictions = outputs.argmax(dim=-1)
            correct += (predictions == targets).sum().item()
            total += targets.shape[0]
            num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    accuracy = correct / max(total, 1)
    
    return avg_loss, accuracy


def evaluate_imageNet(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: str = "cpu",
) -> tuple[float, float]:
    """Evaluate ImageNet classifier."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    num_batches = 0
    
    with torch.no_grad():
        for inputs, targets in val_loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
            
            predictions = outputs.argmax(dim=-1)
            correct += (predictions == targets).sum().item()
            total += targets.shape[0]
            num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    accuracy = correct / max(total, 1)
    
    return avg_loss, accuracy


def create_cifar10_dataloader(
    batch_size: int = 32,
    data_dir: str = "./data",
    train: bool = True,
    download: bool = True,
    num_workers: int = 2,
):
    """Create CIFAR-10 dataloader."""
    import torchvision
    import torchvision.transforms as transforms
    
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
    """Main training function."""
    from src.snn.config import load_model_config, load_training_config
    
    model_config = load_model_config(args.model)
    train_config = load_training_config(args.config)
    
    # Device selection with GPU compatibility fallback
    config_device = train_config.get("device", "cuda")
    device = config_device
    
    if config_device == "cuda":
        try:
            import torch
            if torch.cuda.is_available():
                test_tensor = torch.tensor([1.0]).cuda()
                del test_tensor
                print("Using device: cuda")
            else:
                device = "cpu"
                print("Warning: CUDA not available. Using CPU.")
        except Exception as e:
            print(f"CUDA not compatible. Using CPU instead.")
            device = "cpu"
    else:
        print(f"Using device: {device}")
    
    # Model selection
    model_type = train_config.get("model_type", "resnet18")
    num_classes = train_config.get("output_dim", 10)
    
    # Load pretrained ImageNet model
    print(f"\nLoading pretrained {model_type} (ImageNet)...")
    
    if model_type in ["resnet18", "resnet20"]:
        model = ImageNetClassifier(
            backbone=model_type,
            num_classes=num_classes,
            pretrained=True,
            freeze_backbone=train_config.get("freeze_backbone", False),
        ).to(device)
    else:
        model = XpikeformerSNN(
            input_dim=model_config.get("input_dim", 3072),
            hidden_dim=model_config.get("hidden_dim", 256),
            output_dim=model_config.get("output_dim", 10),
            num_layers=model_config.get("num_layers", 3),
            T=model_config.get("T", 8),
            dropout=model_config.get("dropout", 0.1),
        ).to(device)
    
    print(f"Model: {model.__class__.__name__}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")
    
    # Dataloaders
    dataset_name = train_config.get("dataset", "cifar10")
    data_dir = train_config.get("data_dir", "./data")
    
    print(f"\nLoading {dataset_name} dataset...")
    
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
    
    # Optimizer - different LR for backbone vs new layers
    if train_config.get("freeze_backbone", False):
        optimizer = torch.optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=train_config.get("learning_rate", 1e-3),
        )
    else:
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=train_config.get("learning_rate", 1e-3),
            weight_decay=train_config.get("weight_decay", 0.05),
        )
    
    criterion = nn.CrossEntropyLoss()
    
    # Training loop
    num_epochs = train_config.get("num_epochs", 100)
    print(f"\nTraining for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        if model_type in ["resnet18", "resnet20"]:
            train_loss = train_epoch_imageNet(
                model, train_loader, optimizer, criterion, device
            )
            val_loss, val_acc = evaluate_imageNet(
                model, val_loader, criterion, device
            )
        else:
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
    checkpoint_dir = train_config.get("checkpoint_dir", "checkpoints")
    if isinstance(checkpoint_dir, str):
        checkpoint_dir = Path(checkpoint_dir)
    output_path = checkpoint_dir / "xpikeformer_final.pt"
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
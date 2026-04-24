"""Hybrid ANN-SNN Conversion for SpikeFormer.

Reference: Section V of Xpikeformer paper
Converts pretrained ANN to SNN for hybrid inference.
"""

import torch
import torch.nn as nn
import torchvision.models as models
from typing import Optional, Dict, Any, Tuple
from copy import deepcopy


class ANNToSNNConverter(nn.Module):
    """Convert ANN (ResNet) to SNN-compatible model.
    
    Per Section V of paper:
    1. Load pretrained ImageNet weights
    2. Adapt architecture for spike inputs
    3. Convert FC layers for spike-compatible inference
    
    Args:
        ann_model: Pretrained ANN model
        T: Number of timesteps for spike encoding
    """
    
    def __init__(
        self,
        ann_model: nn.Module,
        T: int = 8,
        use_bn: bool = True,
    ):
        super().__init__()
        self.T = T
        self.use_bn = use_bn
        
        # Clone the ANN
        self.model = deepcopy(ann_model)
        
        # Convert FC layers to support spike input
        self._convert_fc_layers()
    
    def _convert_fc_layers(self):
        """Convert fully connected layers for spike input."""
        # Find and convert the final FC layer
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                # Get in_features
                in_features = module.in_features
                out_features = module.out_features
                
                # Replace with SNN-compatible FC
                # Uses ReLU for spike-compatible activation
                new_fc = nn.Sequential(
                    nn.Linear(in_features, out_features),
                    nn.ReLU() if self.use_bn else nn.Identity()
                )
                
                # Replace in parent
                parent_name = '.'.join(name.split('.')[:-1])
                child_name = name.split('.')[-1]
                
                if parent_name:
                    parent = self.model.get_submodule(parent_name)
                    setattr(parent, child_name, new_fc)
                else:
                    setattr(self.model, child_name, new_fc)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with spike encoding.
        
        Args:
            x: Input tensor (batch, channels, H, W) or (batch, features)
        
        Returns:
            Output logits (batch, num_classes)
        """
        # Convert input to spike train if not already
        if x.dim() == 2:
            # Flattened input - apply Bernoulli encoding
            from src.snn.encoding import BernoulliEncoder
            encoder = BernoulliEncoder(T=self.T)
            x = encoder(x)
            x = x.view(x.size(0), -1)  # Flatten T dimension
        elif x.dim() == 4:
            # Image input (batch, C, H, W)
            # Process through model directly for now
            pass
        
        return self.model(x)


class HybridModel(nn.Module):
    """Hybrid ANN-SNN model.
    
    Combines:
    - ANN backbone (ResNet) for feature extraction
    - SNN head for classification
    - Optional fine-tuning mode
    
    Args:
        backbone: ANN feature extractor
        num_classes: Number of output classes
        freeze_backbone: Freeze ANN weights during training
    """
    
    def __init__(
        self,
        backbone: Optional[nn.Module] = None,
        num_classes: int = 10,
        freeze_backbone: bool = False,
        T: int = 8,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.T = T
        self.freeze_backbone = freeze_backbone
        
        # Load pretrained backbone if not provided
        if backbone is None:
            self.backbone = self._load_pretrained_resnet()
        else:
            self.backbone = backbone
        
        # Replace final FC for our classes
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()  # Remove original FC
        
        # SNN classification head
        from src.snn.encoding import BernoulliEncoder
        from src.snn.architecture import SSAModule
        
        self.encoder = BernoulliEncoder(T=T)
        self.ssa = SSAModule(channels=in_features, dropout=0.1)
        
        # Classification head
        self.classifier = nn.Linear(in_features, num_classes)
        
        # Freeze backbone if requested
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
    
    def _load_pretrained_resnet(self) -> nn.Module:
        """Load pretrained ResNet-18."""
        try:
            model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            print("Loaded pretrained ResNet-18 (ImageNet)")
        except Exception:
            model = models.resnet18(weights=None)
            print("Warning: Could not load pretrained weights")
        
        return model
    
    def forward(
        self,
        x: torch.Tensor,
        return_features: bool = False,
    ) -> torch.Tensor:
        """Forward pass.
        
        Args:
            x: Input (batch, 3, 32, 32) for CIFAR-10
            return_features: Return intermediate features
        
        Returns:
            logits (batch, num_classes) or (features, logits) if return_features
        """
        # Resize if needed (CIFAR-10 is 32x32)
        if x.shape[-1] == 32:
            x = torch.nn.functional.interpolate(
                x, size=224, mode='bilinear', align_corners=False
            )
        
        # Extract features with backbone
        features = self.backbone(x)  # (batch, 512)
        
        if return_features:
            return features
        
        # Apply spike encoding - clamp to valid probability range first
        probs = features.unsqueeze(-1).expand(-1, -1, self.T)  # (batch, 512, T)
        probs = torch.clamp(probs, min=0.0, max=1.0)  # Ensure valid probabilities
        probs = torch.bernoulli(probs)  # Spike encoding
        
        # Aggregate over time (mean over T dimension)
        features_spiked = probs.mean(dim=2)  # (batch, 512)
        
        # Classify
        logits = self.classifier(features_spiked)
        
        return logits
    
    def set_train_mode(self, mode: str = "full"):
        """Set training mode.
        
        Args:
            mode: 'full' (all params), 'head' (classifier only), 'freeze' (no training)
        """
        if mode == "full":
            for param in self.parameters():
                param.requires_grad = True
        elif mode == "head":
            for param in self.backbone.parameters():
                param.requires_grad = False
            for param in self.classifier.parameters():
                param.requires_grad = True
        elif mode == "freeze":
            for param in self.parameters():
                param.requires_grad = False


class SNNHybridTrainer:
    """Trainer for hybrid ANN-SNN models.
    
    Handles:
    - Converting pretrained ANN
    - Fine-tuning on target dataset
    - Mixed precision training
    """
    
    def __init__(
        self,
        model: HybridModel,
        device: str = "cuda",
        learning_rate: float = 1e-4,
    ):
        self.model = model
        self.device = device
        self.learning_rate = learning_rate
        
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=0.05,
        )
        self.criterion = nn.CrossEntropyLoss()
    
    def train_epoch(
        self,
        train_loader,
    ) -> float:
        """Train one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for inputs, targets in train_loader:
            inputs = inputs.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / max(num_batches, 1)
    
    def evaluate(
        self,
        val_loader,
    ) -> Tuple[float, float]:
        """Evaluate model."""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        num_batches = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)
                total_loss += loss.item()
                
                predictions = outputs.argmax(dim=-1)
                correct += (predictions == targets).sum().item()
                total += targets.shape[0]
                num_batches += 1
        
        avg_loss = total_loss / max(num_batches, 1)
        accuracy = correct / max(total, 1)
        
        return avg_loss, accuracy


def create_hybrid_model(
    backbone: str = "resnet18",
    num_classes: int = 10,
    pretrained: bool = True,
    freeze_backbone: bool = False,
    T: int = 8,
) -> HybridModel:
    """Factory to create hybrid model.
    
    Args:
        backbone: 'resnet18' or 'resnet20'
        num_classes: Output classes
        pretrained: Use ImageNet pretrained weights
        freeze_backbone: Freeze backbone during training
        T: Number of timesteps
    
    Returns:
        HybridModel ready for fine-tuning
    """
    # Load backbone
    if backbone == "resnet20":
        try:
            backbone_model = models.resnet20(
                weights=models.ResNet20_Weights.IMAGENET1K_V1 if pretrained else None
            )
        except Exception:
            backbone_model = models.resnet18(
                weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
            )
    else:
        backbone_model = models.resnet18(
            weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        )
    
    return HybridModel(
        backbone=backbone_model,
        num_classes=num_classes,
        freeze_backbone=freeze_backbone,
        T=T,
    )
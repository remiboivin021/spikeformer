# Interfaces — SpikeFormer

## Interfaces exposées

Ce document liste toutes les interfaces du projet.

## 1. Interfaces Python (CLI)

### 1.1 Scripts d'entraînement

| Script | Entrée | Sortie | Usage |
|--------|--------|--------|-------|
| `scripts/train_ct.py` | YAML config + dataset | checkpoint.pt | Conventional Training |
| `scripts/train_hwat.py` | checkpoint CT + YAML | checkpoint_hwat.pt | Hardware-Aware Training |
| `scripts/export_onnx.py` | checkpoint.pt | model.onnx | Export MATLAB |

### 1.2 Configuration YAML

```yaml
# config/model/xpikeformer_small.yaml
model:
  name: xpikeformer_small
  d_model: 384
  n_heads: 6
  n_layers: 4
  T: 8  # timesteps

training:
  batch_size: 32
  epochs: 100
  lr: 1e-3
  optimizer: adamw
```

## 2. Interfaces consommées

### 2.1 Libraries externes

| Library | Version | Usage |
|---------|---------|-------|
| torch | ≥2.0.0 | ML framework |
| spikingjelly | ≥0.0.0.0.15 | SNN forward |
| snntorch | ≥0.9 | SNN training helper |
| aihwkit | latest | Simulation PCM |
| onnx | ≥1.14 | Export |
| wandb | latest | Tracking |

### 2.2 Datasets

| Dataset | Loading | Location |
|--------|--------|----------|
| CIFAR-10 | torchvision.datasets | Auto-download |

## 3. Interfaces exposées (export)

### 3.1 Modèles exportés

| Format | Emplacement | Importable par |
|--------|------------|---------------|
| PyTorch checkpoint | `models/*.pt` | PyTorch |
| ONNX | `models/*.onnx` | PyTorch, MATLAB, ONNX Runtime |

### 3.2 Configuration exportée

```yaml
# Metadata inclus dans l'export ONNX
model:
  name: xpikeformer_small
  d_model: 384
  n_layers: 4
  T: 8
training:
  dataset: CIFAR-10
  accuracy: 0.823  # si disponibile
```

## 4. API Python interne

### 4.1 Modules publics

```python
# src/snn/neurons/__init__.py
from .lif import LeakyIntegrateAndFire
from .bernoulli_neuron import BernoulliNeuron

# src/snn/encoding/__init__.py
from .bernoulli_encoder import BernoulliEncoder
from .population_encoder import PopulationEncoder

# src/snn/engines/__init__.py
from .aimc import AIMCEngine
from .ssa import SSAEngine

# src/snn/model/__init__.py
from .xpikeformer import XpikeFormer
```

### 4.2 Utilisation

```python
import torch
from src.snn import XpikeFormer

# Chargement config
config = {"d_model": 384, "n_heads": 6, "n_layers": 4, "T": 8}

# Création modèle
model = XpikeFormer(config)

# Forward pass
input_tensor = torch.randn(4, 3, 32, 32)  # CIFAR-10 format
output = model(input_tensor)  # (batch, 10)
```

## 5. Contrats d'interface

### 5.1 Input shape

| Format | Shape | Type |
|--------|-------|------|
| Image | (B, 3, H, W) | torch.Tensor |
| ONNX input | (B, 3, H, W) | float32 |

### 5.2 Output shape

| Format | Shape | Type |
|--------|-------|------|
| Logits | (B, n_classes) | torch.Tensor |
| ONNX output | (B, n_classes) | float32 |

### 5.3 Shape validation

- Images: H, W doivent être divisibles par 4
- Batch: B ≤ 32 (mémoire)
- n_classes: 10 pour CIFAR-10

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
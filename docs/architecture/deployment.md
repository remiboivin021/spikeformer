# Deployment — SpikeFormer

## Modèle de déploiement

Ce document décrit comment le projet est déployé à chaque phase.

## 1. Environnements de déploiement

| Phase | Environnement | Cible |
|-------|------------|-------|
| Développement | PC local + .venv | Code |
| Entraînement | Kaggle (T4 GPU) | Modèles |
| Validation | PC local | Tests |
| Export | PC local | ONNX |
| Production | MATLAB + Embedded Coder | C embarqué |

## 2. Déploiement développement

### 2.1 Setup local

```bash
# Création environnement
python -m venv .venv
source .venv/Scripts/activate  # Windows
# ou
source .venv/bin/activate  # Linux

# Installation
pip install -e ".[dev]"
pip install -r requirements.txt
```

### 2.2 Structure fichiers

```
.venv/                   # Python virtual env (ignorés par git)
.env                     # Variables d'environnement (non commité)
.env.example             # Template
```

## 3. Déploiement entraînement

### 3.1 Kaggle Notebook

```python
# Configuration
accelerator = GPU T4 x2
persistence = Variables and Files
internet = On

# Installation
!pip install torch snntorch spikingjelly wandb onnx -q
```

### 3.2 Workflow entraînement

```
Local (commit) → GitHub → Kaggle (clone)
       ↓
Kaggle (entraînement) → checkpoint.pt / model.onnx
       ↓
Local (pull artifacts) → models/
```

### 3.3 Checkpointing

```python
# Toutes les 10 epochs
torch.save({
    'epoch': epoch,
    'model_state': model.state_dict(),
    'optimizer_state': optimizer.state_dict(),
    'config': config,
}, f'models/checkpoint_ep{epoch}.pt')
```

## 4. Déploiement validation

### 4.1 Tests unitaires

```bash
# Lancement
pytest tests/unit/ -v

# Couverture
pytest tests/ --cov=src --cov-report=html
```

### 4.2 CI GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=src
      - run: ruff check src/
```

## 5. Déploiement export

### 5.1 Export ONNX

```python
import torch.onnx

dummy_input = torch.randn(1, 3, 32, 32)

torch.onnx.export(
    model,
    dummy_input,
    'models/xpikeformer_small.onnx',
    export_params=True,
    opset_version=11,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch'},
        'output': {0: 'batch'}
    }
)
```

### 5.2 Import MATLAB

```matlab
% Import ONNX
net = importONNXNetwork('models/xpikeformer_small.onnx');

% Test
input = rand(1, 3, 32, 32);
output = predict(net, input);
```

## 6. Déploiement production (après validation)

### 6.1 Étapes

```
ONNX → MATLAB Deep Learning Toolbox
       ↓
Embedded Coder → C généré
       ↓
Compile → Binary
       ↓
Deploy → Hardware cible
```

### 6.2 Cibles potentielles

| Cible | RAM | Notes |
|-------|-----|-------|
| Jetson NX | 8GB | Plus simple |
| Jetson Orin | 8GB+ | Plus puissant |
| STM32H7 | 512KB | Ultra contraint |
| PC embarqué | Variable | x86 |

## 7. Versionnage

### 7.1 Git tags

```bash
# Format
v{major}.{minor}.{patch}-{phase}

# Exemples
v0.1.0-alpha  # Phase 1 SNN complet
v0.2.0-beta   # Phase 2 ANN complet
v1.0.0       # Phase 3 hybrid si validé
```

### 7.2 Artefacts

| Type | Emplacement | Naming |
|------|------------|--------|
| Checkpoint | `models/*.pt` | `xpikeformer_small_ep{epoch}.pt` |
| ONNX | `models/*.onnx` | `xpikeformer_small.onnx` |

## 8. Monitoring

### 8.1 Métriques train

| Métrique | Outil |
|---------|-------|
| Loss | wandb |
| Accuracy | wandb |
| Spike rates | wandb custom |
| Énergie (estimée) | script |

### 8.2 Métriques inference

| Métrique | Outil |
|---------|-------|
| Latence | script benchmark |
| Memory | nvidia-smi |

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
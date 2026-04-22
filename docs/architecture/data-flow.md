# Data Flow — SpikeFormer

## Flux de données

Ce document décrit le flux de données à travers le système.

## 1. Flux d'entraînement

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   ENTRAÎNEMENT CT / HWAT                     │
└─────────────────────────────────────────────────────────────────────────────────┘

Dataset (CIFAR-10)
       ↓
┌──────────────┐
│ DataLoader   │  ← shuffle, batch, preprocessing
└──────────────┘
       ↓
┌──────────────────────┐
│ SpikeEncoder       │  ← real → spike (Bernoulli)
└──────────────────────┘
       ↓ (spike trains)
┌──────────────────────┐
│ AIMC Engine         │  ← MVM simulé (crossbar)
└──────────────────────┘
       ↓
┌──────────────────────┐
│ SSA Engine          │  ← Stochastic Attention
└──────────────────────┘
       ↓
┌──────────────────────┐
│ Output Layer        │  ← classification
└──────────────────────┘
       ↓
┌──────────────┐
│ Loss (CE)    │
└──────────────┘
       ↓
┌──────────────┐
│ Backward    │  ← surrogate gradient (HWAT: forward bruité)
└──────────────┘
       ↓
┌──────────────┐
│ Optimizer   │  ← AdamW
└──────────────┘
       ↓
┌──────────────┐
│ weights    │  ← update
└──────────────┘
```

## 2. Flux d'inférence

```
┌─────────────────────────────────────────────────────────────────┐
│                   INFERENCE                     │
└───────────────────────────────────────────────┘

Input (image) → (B, 3, 32, 32)
       ↓
┌──────────────────────┐
│ SpikeEncoder       │  ← T timesteps
└──────────────────────┘
       ↓ spike (B, C, T, H, W)
┌──────────────────────┐
│ AIMC + SSA Block    │  × n_layers
└──────────────────────┘
       ↓
┌──────────────────────┐
│ Output Layer       │  ← avg pooling + FC
└──────────────────────┘
       ↓ logits (B, 10)
┌──────────────┐
│ Argmax       │  ← prédiction
└──────────────┘
```

## 3. Flux de données par phase

### 3.1 Phase 1: SNN Transformer

| Étape | Input | Output | T |
|------|-------|-------|-----|
| Preprocess | Image | normalized tensor | - |
| Encode | tensor | spike trains | T |
| AIMC | spikes | activations | 1 |
| SSA | Q,K,V | attention | 1 |
| Output | features | logits | 1 |

### 3.2 Phase 2: ANN Transformer (équivalent)

| Étape | Input | Output |
|------|-------|---------|
| Preprocess | Image | normalized tensor |
| Embed | tensor | embeddings |
| Linear | embeddings | activations |
| Attention | Q,K,V | attention |
| Output | features | logits |

### 3.3 Phase 3: Hybrid (future)

| Étape | Input | Output |
|------|-------|---------|
| SNN encode | spikes | population vector |
| Bridge | pop vector | tokens |
| ANN transformer | tokens | decision |

## 4. Formats de données

### 4.1 checkpoint.pt

```python
{
    'epoch': int,
    'model_state': OrderedDict,  # state_dict()
    'optimizer_state': OrderedDict,
    'config': dict,
    'accuracy': float,  # si available
}
```

### 4.2 model.onnx

```python
# Input
input.0 : float32[B, 3, 32, 32]

# Output
output.0 : float32[B, 10]
```

## 5. Chemins de données

| Donnée | Chemin | Format |
|-------|--------|--------|
| Code | `src/` | Python |
| Config | `config/*.yaml` | YAML |
| Checkpoints | `models/*.pt` | PyTorch |
| ONNX | `models/*.onnx` | ONNX |
| Logs | wandb | cloud |
| Dataset | Kaggle | downloaded |

## 6. Points de conversion

| Conversion | Lieu | Perte ? |
|-----------|-----|--------|
| Image → tensor | DataLoader | Non |
| Tensor → spikes | Encoder | Oui (quantification) |
| Spikes → logits | Model | Non |
| ONNX → MATLAB | export | Perte possible (opérateurs) |

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
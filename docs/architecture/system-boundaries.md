# System Boundaries — SpikeFormer

## Périmètre du système

Ce document définit ce qui est DANS le périmètre et ce qui est HORS.

## 1. Périmètre fonctionnel

### 1.1 DANS le périmètre

| Fonction | Description |
|----------|-------------|
| SNN Encoder | Taux de coding Bernoulli du papier |
| AIMC Engine | Feedforward via crossbar PCM simulé |
| SSA Engine | Stochastic Spiking Attention |
| Entraînement CT | Conventional Training (FP32 idéal) |
| Entraînement HWAT | Hardware-Aware Training (bruit PCM) |
| Export ONNX | OpSet 11 pour MATLAB |
| Comparaison SNN/ANN | Métriques accuracy/latence/énergie |

### 1.2 HORS périmètre

| Fonction | Raison |
|----------|--------|
| Hardware PCM réel | Simulation only (AIHWKit) |
| Déploiement Jetson/MCU | Après validation PC |
| Hybridation SNN/ANN | Phase 3 |
| Entraînement distribué | Single GPU |
| Fine-tuning LLM | Après validation CIFAR-10 |

## 2. Périmètre données

### 2.1 Données supportées

| Dataset | Support | Phase |
|---------|---------|--------|
| CIFAR-10 | ✅ Entraînement + test | Phase 1 |
| ImageNet | ❌ (trop volumineux) | - |
|自定义 | ❌ | - |

### 2.2 Formats d'entrée

| Format | Support |
|--------|---------|
| Image (HWC, 0-255) | ✅ via DataLoader |
| Tensor (BCHW) | ✅ |
| ONNX | ✅ import only |

## 3. Périmètre interfaces

### 3.1 Interfaces exposées

| Interface | Emplacement | Status |
|----------|------------|--------|
| Python API | `src/snn/` | Interne |
| CLI training | `scripts/train_*.py` | Exposition |
| Config YAML | `config/` | Exposition |
| Export ONNX | `models/` | Export |

### 3.2 Interfaces NON exposées

- API HTTP/REST
- SDK
- Librairie pip installable (pour le moment)

## 4. Périmètre horizontal

### 4.1 Layers du modèle

```
Input → SpikeEncoder → AIMC → SSA → AIMC → SSA → ... → Output
                    (L layers)
```

| Layer | Nb paramètres | Fixed? |
|-------|-------------|-------|
| Embedding | d_model × vocab | Non |
| Encoder Layer | ~2× d_model² | Non |
| Output Head | d_model × n_classes | Non |

### 4.2 Configs modèle

| Config | Layers | d_model | Heads | Params |
|--------|--------|---------|-------|--------|
| small | 4 | 384 | 6 | ~4M |
| medium | 6 | 512 | 8 | ~6M |
| large | 8 | 768 | 12 | ~8M |

## 5. Périmètre temporel

| Phase | Début | Fin |
|-------|------|-----|
| Phase 1 SNN | 2026-04 | À 完成 |
| Phase 2 ANN | Après P1 | À确定 |
| Phase 3 Hybrid | Après P2 | À 确定 |

## 6. Limites connues

| Limite | Valeur | Impact |
|--------|-------|-------|
| T timesteps | 4-16 | Latence |
| Sequence length | 128 max | Mémoire |
| Batch size | 32 max (GPU) | Training |
| Epochs | 100 max | Temps |

## 7. Points d'extension future

Ces fonctionnalités ne sont PAS dans le périmètre actuel mais pourront être ajoutées :

- Event camera (DVS) Eingabe
- Fédération learning
- On-device training
- Quantization post-training

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
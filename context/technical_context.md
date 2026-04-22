# Technical Context — SpikeFormer

## 1. Langage et runtime

| Composant | Version |
|-----------|----------|
| Python | 3.10+ |
| PyTorch | 2.0+ |
| NumPy | 1.24+ |

## 2. Dépendances principales

```toml
dependencies = [
    "numpy>=1.24.0",
    "torch>=2.0.0",
    "pyyaml>=6.0",
    "spikingjelly",
    "snntorch",
    "aihwkit",
    "onnx",
    "wandb",
]
```

## 3. Structure du projet

```
spikeformer/
├── src/
│   ├── snn/
│   │   ├── __init__.py
│   │   ├── neurons/           # LIF, Bernoulli neuron
│   │   │   ├── __init__.py
│   │   │   ├── lif.py
│   │   │   └── bernoulli_neuron.py
│   │   ├── encoding/          # Spike encoding
│   │   │   ├── __init__.py
│   │   │   ├── bernoulli_encoder.py
│   │   │   └── population_encoder.py
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   ├── aimc/          # AIMC Engine
│   │   │   │   ├── __init__.py
│   │   │   │   ├── synaptic_array.py
│   │   │   │   ├── spiking_neuron_tile.py
│   │   │   │   └── drift_compensation.py
│   │   │   └── ssa/           # SSA Engine
│   │   │       ├── __init__.py
│   │   │       ├── sac.py
│   │   │       ├── ssa_tile.py
│   │   │       └── ssa_engine.py
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py
│   │   │   ├── feedforward.py
│   │   │   ├── encoder_layer.py
│   │   │   └── xpikeformer.py
│   │   └── training/
│   │       ├── __init__.py
│   │       ├── trainer.py
│   │       ├── surrogate_gradient.py
│   │       └── metrics.py
│   ├── ann/                  # Phase 2
│   │   └── transformer.py
│   └── bridge/               # Phase 3
│       └── population_bridge.py
├── config/
│   ├── model/
│   │   ├── xpikeformer_small.yaml   # 4-384
│   │   ├── xpikeformer_medium.yaml  # 6-512
│   │   └── xpikeformer_large.yaml    # 8-768
│   ├── training/
│   │   ├── conventional.yaml
│   │   └── hardware_aware.yaml
│   └── hardware/
│       └── pcm_crossbar.yaml
├── models/                  # Checkpoints et ONNX
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── train_ct.py
│   ├── train_hwat.py
│   └── export_onnx.py
└── notebooks/
    ├── 01_spike_encoding_viz.ipynb
    ├── 02_ssa_attention_viz.ipynb
    └── 03_energy_benchmark.ipynb
```

## 4. Outils de build et test

| Outil | Usage |
|-------|-------|
| pytest | Tests unitaires |
| ruff | Linting |
| black | Formatage |
| mypy | Typage statique |
| GitHub Actions | CI/CD |

## 5. Configuration CI

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

## 6. Stockage et persistance

| Donnée | Stockage |
|-------|----------|
| Code source | Git repository |
| Modèles entraînés | `models/` + Git LFS |
| Datasets | Kaggle / download |
| Métriques | wandb |
| Configuration | YAML files |

## 7. Performance targets

| Métrique | Cible |
|---------|-------|
| Accuracy (CIFAR-10) | ≥ 80% |
| Training time (4-384) | < 10h |
| Forward latency | < 50ms |
| Memory usage | < 4GB |

## 8. CompatibilitéMATLAB

- Export ONNX opset 11
- Import Deep Learning Toolbox
- Embedded Coder pour C généré

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
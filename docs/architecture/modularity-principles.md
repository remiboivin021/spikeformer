# Modularity Principles — SpikeFormer

## Principes de modularité

Ce document définit les règles de couplage et dépendances.

## 1. Architecture modulaire

### 1.1 Séparation des préoccupations

```
src/
├── snn/              ← SNN composants
│   ├── neurons/       ← Modèles de neurones
│   ├── encoding/     ← Spike encoding
│   ├── engines/      ← AIMC + SSA
│   ├── model/        ← Assemblage
│   └── training/     ← Entraînement
├── ann/              ← ANN equivalent
│   └── transformer.py
└── bridge/           ← Pont SNN-ANN
    └── population_bridge.py
```

### 1.2 Règle de dépendances

| Module | Dépend de | Ne dépend pas de |
|--------|---------|-----------------|
| neurons/ | numpy, torch | encoding/, engines/ |
| encoding/ | numpy, torch | engines/ |
| engines/ | neurons/ | training/ |
| model/ | engines/, encoding/ | training/ |
| training/ | model/ | - |

## 2. Couplage

### 2.1 Couplage faible (à privilégier)

```python
# BON: Interface abstraite
class SpikeEncoder(ABC):
    @abstractmethod
    def encode(self, x: Tensor) -> Tensor:
        pass

class BernoulliEncoder(SpikeEncoder):
    def encode(self, x: Tensor) -> Tensor:
        # implémentation
```

### 2.2 Couplage fort (à éviter)

```python
# MAUVAIS: Dépendance directe
class Model:
    def __init__(self):
        self.encoder = BernoulliEncoder()  # couplage direct
```

## 3. Patterns recommendationés

### 3.1 Injection de dépendances

```python
# Configuration par YAML
# config → model

# BON: Le modèle reçoit sa config
model = XpikeFormer(config)
```

### 3.2 Factory pattern

```python
# Création de composants
def create_encoder(encoder_type: str, config: dict) -> SpikeEncoder:
    encoders = {
        'bernoulli': BernoulliEncoder,
        'population': PopulationEncoder,
    }
    return encoders[encoder_type](**config)
```

### 3.3 Registry pattern

```python
# Enregistrement des modèles
MODEL_REGISTRY = {
    'xpikeformer_small': XpikeFormerSmall,
    'xpikeformer_medium': XpikeFormerMedium,
    'xpikeformer_large': XpikeFormerLarge,
}

def get_model(name: str, config: dict):
    return MODEL_REGISTRY[name](config)
```

## 4. Règles de dépendances

### 4.1 Régles strictes

| Règle | Description |
|-------|-------------|
| R01 | Pas de cycle d'import |
| R02 | Dépendances explicites dans pyproject.toml |
| R03 | Versions pinning pour reproductibilité |
| R04 | Tests découplés du entraînement |

### 4.2 Régles optionnelles

| Règle | Description |
|-------|-------------|
| O01 | InterfacesABC preferées aux classes concrètes |
| O02 | Composition > héritage |
| O03 | Configuration > hardcoding |

## 5. Points d'extension

### 5.1 Nouveaux encodeurs

```python
# Ajouter dans encoding/
# Implementer SpikeEncoder interface
# Mise à jour factory
```

### 5.2 Nouveaux engines

```python
# Ajouter dans engines/
# Implémenter Engine interface
# Mise à jour registry
```

### 5.3 Nouveaux datasets

```python
# Ajouter dans data/
# Implementer Dataset interface
# Mise à jour DataLoader
```

## 6. Testabilité

### 6.1 Tests unitaires

```python
# Tests indépendante de chaque module
def test_encoder():
    encoder = BernoulliEncoder(T=8)
    x = torch.randn(4, 3, 32, 32)
    spikes = encoder(x)
    assert spikes.shape[1] == 8  # T timesteps
```

### 6.2 Tests d'intégration

```python
# Tests du flux complet
def test_forward_pass():
    model = XpikeFormer(config_small)
    output = model(sample_input)
    assert not torch.isnan(output).any()
```

## 7. Documentation des interfaces

| Interface | Location | Description |
|-----------|----------|-------------|
| SpikeEncoder | encoding/ | Interface d'encodage |
| AIMCEngine | engines/aimc/ | Interface feedforward |
| SSAEngine | engines/ssa/ | Interface attention |
| XpikeFormer | model/ | Interface modèle complet |

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
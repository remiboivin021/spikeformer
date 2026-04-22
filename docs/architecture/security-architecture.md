# Security Architecture — SpikeFormer

## Posture de sécurité

Ce document définit la posture de sécurité du projet.

## 1.Modèle de menace

| Menace | Probabilité | Impact | Mitigation |
|--------|------------|---------|----------|
| Credentials leak | Faible | Élevé | .env non commité |
| Code tampering | Faible | Élevé | Git signed commits |
| Malicious input | Faible | Moyen | Input validation |
| Model inversion | Faible | Moyen | Pas de données sensibles |

## 2. Trust boundaries

### 2.1 Entités de confiance

| Entité |trusted | Raison |
|--------|---------|--------|
| Code auteur | ✅ | Développeur unique |
| Scripts entraînants | ✅ | Pas d'input externe |
| Kaggle | ✅ | Plateforme officielle |
| wandb | ✅ | Tracking only |

### 2.2 Entités non confiées

| Entité | trusted? | Raison |
|--------|----------|--------|
| Input utilisateur | ❌ | À valider |
| Datasets externes | ❌ | À vérifier |
| Modèles importés | ❌ | À valider |

## 3. Sécurité du code

### 3.1 Gestion des secrets

```bash
# .env (non commité)
WANDB_API_KEY=xxx
GITHUB_TOKEN=xxx
KAGGLE_USERNAME=xxx
KAGGLE_KEY=xxx
```

```gitignore
# .gitignore
.env
.venv/
*.pt
models/
```

### 3.2 Validation des entrées

```python
# Validation dataset
def validate_input(x):
    assert x.shape == (B, 3, 32, 32)
    assert x.dtype == torch.float32
    assert x.min() >= -1 and x.max() <= 1
    return True
```

## 4. Sécurité des données

### 4.1Datasets

| Dataset | Source | Sécurité |
|--------|--------|----------|
| CIFAR-10 | torchvision | ✅ Vérifié |
| Custom | - | À vérifier |

### 4.2 Modèles

- Checkpoints salvguardés localement
- ONNX export vérifié avant usage

## 5. Compliance

### 5.1 Licences

| Composant | Licence |
|---------|---------|
| torch | Apache 2.0 |
| spikingjelly | MIT |
| snntorch | BSD |
| aihwkit | Apache 2.0 |

### 5.2 Code ownership

- Auteur unique : Rémi Boivin
- Conventional commits
- Git history préservé

## 6. Opérations sécurisées

### 6.1 Entraînement

```python
# Pas de credentials dans le code
# Pas d'API calls non sécurisées
# Datos locales uniquement
```

### 6.2 Export

```python
# ONNX vérifié
import onnx
model = onnx.load('model.onnx')
onnx.checker.check_model(model)
```

## 7. Monitoring sécurité

| Événement | Action |
|-----------|--------|
| Failed tests | CI fails |
| Linting violations | CI fails |
| Secrets detectés | CI fails |

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
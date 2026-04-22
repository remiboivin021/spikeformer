# Constraints — SpikeFormer

## 1. Contraintes fonctionnelles

| ID | Contrainte | Priorité |
|----|------------|----------|
| F01 | Accuracy SNN ≥ 80% sur CIFAR-10 | Haute |
| F02 | Accuracy ANN ≥ 82% sur CIFAR-10 | Haute |
| F03 | Forward pass sans NaN/Inf | Critique |
| F04 | Gradient flow jusqu'au spike encoder | Haute |
| F05 | Export ONNX valide et importable | Haute |

## 2. Contraintes de performance

| ID | Contrainte | Cible |
|----|------------|-------|
| P01 | Latence forward | < 50ms (CPU) |
| P02 | Mémoire GPU | < 4GB |
| P03 | Temps entraînement (4-384) | < 10h |
| P04 | Couverture tests | > 80% |

## 3. Contraintes de sécurité

| ID | Contrainte |
|----|------------|
| S01 | Pas de secrets dans le dépôt |
| S02 | Credentials via environment variables |
| S03 | tokens GitHub dans Kaggle Secrets |

## 4. Contraintes de compliance

| ID | Contrainte |
|----|------------|
| C01 | Conventional commits |
| C02 | ADR pour changement architecture |
| C03 | Versionnage par Git tag |

## 5. Contraintes opérationnelles

| ID | Contrainte |
|----|------------|
| O01 | Training sur Kaggle (30h/semaine) |
| O02 | Logging wandb |
| O03 | Checkpointing toutes les 10 epochs |

## 6. Contraintes non négociables (de l'article)

| ID | Contrainte | Source |
|----|------------|---------|
| N01 | AIMC Engine pour feedforward | Papier Xpikeformer |
| N02 | SSA Engine pour attention | Papier Xpikeformer |
| N03 | Bernoulli encoding | Papier Xpikeformer |
| N04 | T timesteps 4-16 | Papier Xpikeformer |
| N05 | Configs small/medium/large | Papier Xpikeformer |

## 7. Hardware constraints (simulation)

| Paramètre | Valeur |
|-----------|--------|
| PCM Resolution | 5-bit |
| Bruit PCM (σ) | 0.1 |
| ADC sharing ratio | 8 |
| Drift model | ΔG(t) = G₀·(t/t₀)^(-ν) |

## 8. Déploiement

| Phase | Cible |
|-------|-------|
| Phase 1-2 | PC (x86) |
| Phase 3 | Hardware dédié (après validation) |
| Export | ONNX → MATLAB → C embarqué |

## 9. Coûts

| Ressource | Estimation |
|-----------|-------------|
| GPU Kaggle | 30h/semaine (gratuit) |
| Stockage | ~500MB (checkpoints) |
| Export MATLAB | Deep Learning Toolbox (inclus MATLAB) |

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
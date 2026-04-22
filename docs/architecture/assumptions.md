# Assumptions — SpikeFormer

## Hypothèses de conception

Ces hypothèses sont basées sur le papier Xpikeformer (arXiv:2408.08794v2) et doivent être validées durante l'implémentation.

## 1. Hypothèses sur le papier de référence

| ID | Hypothèse | Source |
|----|----------|--------|
| H01 | Le papier contient assez de détails pour répliquer AIMC + SSA | Papier Song et al. |
| H02 | Les configs small (4-384), medium (6-512), large (8-768) sont documentées | Table I papier |
| H03 | Le bruit PCM suit une gaussienne σ=0.1 | Section III-D papier |
| H04 | La résolution PCM effective est 5-bit | Table II papier |
| H05 | L'ADC sharing ratio est 8 | Table II papier |

## 2. Hypothèses sur les frameworks

| ID | Hypothèse | Source |
|----|----------|--------|
| H10 | SpikingJelly 0.0.0.0.15 est compatible avec PyTorch 2.0+ | Documentation |
| H11 | snntorch 0.9 est compatible avec SpikingJelly | Compatibilité |
| H12 | AIHWKit simule correctement le bruit PCM | Documentation IBM |
| H13 | ONNX opset 11 accepte les opérateurs utilisés | Export tests |

## 3. Hypothèses sur l'entraînement

| ID | Hypothèse | Source |
|----|----------|--------|
| H20 | CIFAR-10 est un benchmark valide pour Xpikeformer | Papier Section V |
| H21 | T=7-10 timesteps est suffisant pour convergence | Papier |
| H22 | Le surrogate gradient (sigmoid) est efficace | Papier + littérature |
| H23 | HWAT améliore la stabilité comparé à CT | Papier Section IV |

## 4. Hypothèses sur les performances

| ID | Hypothèse | Cible |
|----|----------|-------|
| H30 | Accuracy SNN ≥ 80% sur CIFAR-10 (config 4-384) | Papier Table III |
| H31 | Accuracy drop < 1% entre SNN et ANN équivalent | Papier |
| H32 | Latence SNN < ANN (en temps réel) | Papier Figure 8 |
| H33 | Énergie SNN ~13× moins qu'ANN sur GPU | Papier Table III |

## 5. Hypothèses sur le déploiement

| ID | Hypothèse | Source |
|----|----------|--------|
| H40 | Export ONNX est importable dans MATLAB | Compatibilité |
| H41 | MATLAB Embedded Coder peut générer du C | Outils |
| H42 | Le modèle tient sur Jetson NX (4GB RAM) | Contrainte hardware |

## 6. Hypothèses non validées (à tester)

| ID | Hypothèse | Validation requise |
|----|----------|-------------------|
| HN1 | Les rotations géométriques mejoran la performance | Phase 3 |
| HN2 | Le population coding préserve plus d'info que rate coding | Phase 3 |
| HN3 | L'hybridation SNN/ANN est viable temps réel | Phase 3 |

## 7. Ce qui n'est PAS supposé

- Le papier fournit du code source (il n'existe pas — on réimplémente)
- Les poids pré-entraînés sont disponibles (ils ne le sont pas)
- Le hardware PCM réel est disponible (simulation only)

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
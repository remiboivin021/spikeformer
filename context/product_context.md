# Product Context — SpikeFormer

## 1. Identité du projet

| Champ | Valeur |
|-------|--------|
| Nom | SpikeFormer |
| Type | Recherche / Bibliothèque Python (ML) |
| Statut | Active |
| Propriétaire | Rémi Boivin |
| Référent technique | Rémi Boivin |

## 2. Résumé

Réimplementation en PyTorch de l'architecture Xpikeformer (Song et al., 2025) — un transformeur SNN (Spiking Neural Network) avec moteurs AIMC (Analog In-Memory Computing) et SSA (Stochastic Spiking Attention). Le projet inclut un comparatif ANN pour valider les métriques de performance : précision, latence et consommation énergétique.

## 3. Objectif principal

Implémenter et valider une architecture SNN Transformer équivalente en précision à un ANN Transformer, avec une réduction de consommation énergétique significative, comme base pour une future hybridation SNN/ANN sur robot mobile.

## 4. Objectifs secondaires

- Réimplémenter EXACTEMENT l'architecture Xpikeformer (AIMC + SSA) comme décrit dans le papier arXiv:2408.08794v2
- Entraîner et évaluer le modèle SNN sur CIFAR-10 et autres datasets
- Implémenter un ANN Transformer équivalent pour comparaison
- Comparer les métriques : accuracy, latence, consommation énergétique
- Préparer l'export ONNX pour déploiement embarqué

## 5. Hors périmètre

- Déploiement hardware dédié (Jetson, MCU) — sauf après validation PC
- Hybridation SNN/ANN — sauf après phases 1 et 2
- Entraînement sur datasets LLM volumineux — sauf après validation CIFAR-10
- Publication académique — hors périmètre direct

## 6. Utilisateurs cibles

| Profil | Description |
|--------|-------------|
| Principal | Rémi Boivin — développeur, usage personnel pour robot mobile |
| Secondaire | Communauté chercheurs SNN (futur) |

## 7. Besoin à couvrir

### Contexte

Les SNN offrent une efficacité énergétique théorique supérieure aux ANN grâce au codage temporel binaire. Cependant, les preuves expérimentales sur hardware réel (PCM crossbar) sont limitées. Le papier Xpikeformer démontre 13× moins d'énergie qu'un ANN sur GPU, mais l'implémentation de référence n'est pasopen source.

### Problème

Aucune implémentation open-source complète de Xpikeformer n'existe. La comparaison avec un ANN équivalent sur les mêmes conditions n'est pas disponible.

### Impact attendu

- Validation parité SNN/ANN sur CIFAR-10 (>80% accuracy)
- Mesure de latence et consommation énergétique
- Base pour hybridation future sur robot mobile

## 8. Proposition de solution

Implémentation en 3 phases :
- **Phase 1** : SNN Transformer exact (AIMC + SSA) — réplication papier
- **Phase 2** : ANN Transformer équivalent — comparison基准
- **Phase 3** : Hybridation SNN/ANN — si validé

## 9. Contraintes non négociables

| Type | Contrainte |
|------|------------|
| Fonctionnelles | Accuracy ≥ 80% sur CIFAR-10 (SNN) |
| Techniques | Python 3.10+, PyTorch, SpikingJelly, snnTorch |
| Sécurité | Pas de secrets dans le dépôt |
| Gouvernance | Conventional commit format, ADR pour changement architecture |

## 10. Hypothèses

- Le papier arXiv:2408.08794v2 contient suffisamment de détails pour répliquer AIMC + SSA
- Kaggle fournit suffisamment de GPU (30h/semaine) pour l'entraînement
- Export ONNX fonctionnera pour MATLAB Deep Learning Toolbox

## 11. Risques connus

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Gradient vanishing à travers T timesteps | Élevé | Gradient clipping + surrogate sigmoid |
| Drift PCM dégrade accuracy | Élevé | HWAT + GDC obligatoires |
| Mismatch SNN↔Transformer | Moyen | Phase 3 découplée |
| Quota GPU insuffisant pour 8-768 | Faible | Commencer sur 4-384 |

## 12. Contrats publics

Aucun contrat public stable à ce stade. Le projet est en phase de recherche.

| Contrat | Emplacement | Politique |
|---------|-------------|-----------|
| API Python | `src/snn/` | additive-only |
| Config YAML | `config/` | additive-only |
| Export ONNX | `models/` | versionné par tag |

## 13. Architecture cible

```
Input (image/text)
    ↓
[Spike Encoding Layer] ← Bernoulli rate coding
    ↓ spike trains
[AIMC Engine] ← Feedforward (PCM crossbar simulé)
    ↓
[SSA Engine] ← Stochastic Spiking Attention
    ↓
[Output Layer] ← Classification / Language modeling
    ↓
Output
```

- **Phase 1** : AIMC ↔ SSA alternés (comme Figure 6 papier)
- **Phase 2** : nn.Linear ↔ MultiHeadAttention standard
- **Phase 3** : Pont population coding + rotations géométriques

## 14. Stack technique

| Composant | Outil |
|-----------|-------|
| Langage | Python 3.10+ |
| Framework SNN | SpikingJelly + snnTorch |
| Hardware sim | AIHWKit (IBM) |
| Framework ML | PyTorch 2.0+ |
| Tracking | wandb |
| Export | ONNX opset 11 |
| Tests | pytest |
| Linting | ruff + black |
| CI/CD | GitHub Actions |
| Training | Kaggle (T4 GPU, 30h/semaine) |

## 15. Organisation du dépôt

| Zone | Rôle |
|------|------|
| `src/snn/` | Code SNN Transformer (Phase 1) |
| `src/ann/` | Code ANN Transformer (Phase 2) |
| `src/bridge/` | Pont SNN-ANN (Phase 3) |
| `config/` | Configurations YAML (small/medium/large) |
| `models/` | Checkpoints et exports ONNX |
| `tests/` | Tests unitaires et intégration |
| `scripts/` | Scripts d'entraînement et benchmark |
| `notebooks/` | Visualisations et analyses |

## 16. Flux de travail

1. **Développement** : Feature → Branch → Commit → PR
2. **Entraînement** : Kaggle Notebook → Checkpoint → Export ONNX
3. **Validation** : Tests unitaires (CPU) + smoke test (GPU)
4. **Versionnage** : Git tag par modèle entraîné

## 17. Critères de réussite

- [ ] Phase 1 : SNN Xpikeformer entraîné sur CIFAR-10 ≥ 80% accuracy
- [ ] Phase 2 : ANN équivalent entraîné ≥ 82% accuracy
- [ ] Comparaison : Métriques latency + énergie documentées
- [ ] Export : ONNX importable dans MATLAB

## 18. Critères d'acceptation minimum

- Forward pass complet sans NaN
- Gradient flow de la loss jusqu'au spike encoder
- Export ONNX valide (import PyTorch + export)
- Tests unitaires passent (>80% coverage)

## 19. Documentation liée

- README : `README.md`
- NLSPEC : `nl_specs/XPIKEFORMER-IMPL-001.md`
- Architecture : `docs/architecture/`
- ADR : `docs/governance/adr/`

## 20. Instructions pour agents IA

- Lire `AGENTS.md` avant toute action
- Vérifier les invariants et le périmètre avant de modifier du code
- Ne pas inventer de comportement absent du dépôt
- Documenter tout changement de contrat public
- Signaler explicitement les inconnues

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
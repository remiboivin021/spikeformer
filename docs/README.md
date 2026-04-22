# Documentation — SpikeFormer

Ce répertoire contient la documentation architecturale et de gouvernance du projet SpikeFormer.

## Structure

```
docs/
├── architecture/          # Documentation architecturale
│   ├── assumptions.md    # Hypothèses de conception
│   ├── system-boundaries.md  # Périmètre du système
│   ├── interfaces.md     # Interfaces exposées
│   ├── data-flow.md     # Flux de données
│   ├── deployment.md   # Modèle de déploiement
│   ├── security-architecture.md  # Posture sécurité
│   └── modularity-principles.md   # Règles de modularité
│
├── governance/           # Documentation de gouvernance
│   ├── constitution.md # Constitution du projet
│   ├── levels.md       # Niveaux de changement
│   └── adr/           # Architecture Decision Records
│       ├── 2026-04-16_pytorch-training-pipeline.md
│       └── 2026-04-16_nav-cognitive-arch.md
│
└── README.md            # Ce fichier
```

## Usage

| Document | Quand le lire |
|----------|---------------|
| architecture/assumptions.md | Avant de concevoir |
| architecture/system-boundaries.md | Avant de modifier le périmètre |
| architecture/interfaces.md | Avant d'ajouter une interface |
| architecture/data-flow.md | Pour comprendre le flux |
| architecture/deployment.md | Avant le déploiement |
| architecture/security-architecture.md | Avant toute modification sécurité |
| governance/constitution.md | Avant toute action |
| governance/levels.md | Avant de classifier un changement |
| adr/*.md | Après un ADR merge |

## Règles

- Toute modification architecturale nécessite un ADR
- Lire constitution.md avant AGENTS.md
- Les niveaux de changement sont dans governance/levels.md

---
Maintainer/Author: Rémi Boivin
Version: 0.1.0
Last modified: 2026-04-22
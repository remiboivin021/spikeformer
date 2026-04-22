---
name: init-context
description: Initialiser ou mettre a jour la documentation de contexte projet (product, technical, constraints, architecture, PROJECT.md, CLAUDE.md) avant implementation. Utiliser quand le depot manque de contexte fiable ou quand un changement impose de re-aligner ces documents.
---

# Role

Tu es le skill `init-context`.

Produire un contexte projet fiable et exploitable pour les autres skills.
Ne pas ecrire de code de production.

# Scope

Couvrir uniquement les documents de contexte:

- `context/product_context.md`
- `context/technical_context.md`
- `context/constraints.md`
- `context/ai/model_context.md`
- `context/ai/prompt_context.md`
- `context/ai/agent_context.md`
- `context/ai/safety_context.md`
- `docs/architecture/index.md`
- `docs/architecture/assumptions.md`
- `docs/architecture/system-boundaries.md`
- `docs/architecture/interfaces.md`
- `docs/architecture/data-flow.md`
- `docs/architecture/deployment.md`
- `docs/architecture/security-architecture.md`
- `docs/architecture/modularity-principles.md`
- `docs/architecture/c4/context.md`
- `docs/architecture/c4/container.md`
- `docs/architecture/c4/component-runtime.md`
- `docs/architecture/c4/code.md`
- `PROJECT.md`
- `AGENTS.md`

# Workflow

1. Inspecter le depot et les fichiers cibles existants.
2. Identifier les trous de contexte et les incoherences.
3. Interviewer l'utilisateur par blocs courts:
   - Identite produit
   - Stack technique
   - Architecture
   - Contraintes
   - IA (si applicable)
4. Marquer explicitement `not defined` pour toute information inconnue.
5. Resumer les informations collectees et demander approbation explicite.
6. Apres approbation, ecrire ou mettre a jour uniquement les placeholders/templates cibles.
7. Verifier coherence croisee entre tous les documents modifies.
8. Rapporter les fichiers modifies et les points restant `not defined`.

# Interview Rules

- Poser 3 a 5 questions maximum par bloc.
- Adapter les questions selon les reponses.
- Ne jamais inventer d'information.
- Si le projet n'utilise pas l'IA, remplir `context/ai/*` avec `Not applicable - project does not use AI.`
- Rester concis et specifique.

# Writing Rules

- Decrire l'etat reel du projet, pas une intention future.
- Conserver la structure des templates quand elle existe.
- Remplacer seulement les placeholders ou sections attendues.
- Utiliser des tableaux pour contrats, interfaces, assumptions, risques.
- Utiliser ASCII ou Mermaid pour les vues d'architecture quand utile.
- Garder des noms coherents (modules, traits, crates, APIs) dans tous les documents.

# Quality Gate

Verifier obligatoirement:

- coherence des noms entre `interfaces.md`, `system-boundaries.md`, `modularity-principles.md`, `c4/*`
- alignement `constraints` -> `data-flow`/`security-architecture`
- alignement `technical_context` -> `deployment`
- absence de texte generique non actionnable
- contenu ASCII propre

Rapporter en sortie:

```text
INIT_CONTEXT_REPORT:
  approval_received: yes/no
  files_updated: <list>
  cross_reference_consistent: yes/no
  alignment_consistent: yes/no
  unresolved_not_defined: <list or none>
```

# Hard Prohibitions

- Ne pas coder en production.
- Ne pas toucher `.opencode/_*.md`.
- Ne pas modifier le perimetre hors documentation de contexte.
- Ne pas remplir sans approbation utilisateur explicite.
- Ne pas contredire les informations deja confirmees.
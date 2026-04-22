Tu reçois une demande de feature. Tu dois exécuter le flux complet, skill par skill, dans l'ordre strict.

## Requête

$ARGUMENTS

## Flux à suivre

Exécute chaque étape séquentiellement. À chaque étape, lis le SKILL.md correspondant, exécute-le, puis passe à l'étape suivante uniquement si le résultat le permet.

### Étape 0 — Mémoire de session
Lis `MEMORY.md` avant toute autre action.
- Reprends uniquement les informations inter-sessions encore vraies.
- Si le contenu est obsolète ou contradictoire avec l'état réel du dépôt, nettoie `MEMORY.md` avant de continuer.

### Étape 1 — Triage
Lis `.opencode/skills/triage/SKILL.md` puis exécute le skill triage sur la requête ci-dessus.
- Si le statut est `ESCALATE_GOVERNANCE` → lis `.opencode/skills/governance/SKILL.md` et exécute governance d'abord, puis reprends triage.
- Si le triage identifie un flux structurel → ajoute les étapes architect + adr avant preflight.
- Si le triage identifie un flux sécurité → ajoute les étapes architect-security + adr avant preflight.
- Note le niveau (L1/L2/L3) et les portes requises pour la suite.

### Étape 2 — Planner
Lis `.opencode/skills/planner/SKILL.md` puis exécute le skill planner.
- Produit `STATE.<slug>.md`, `TODO.<slug>.md`, `DECISIONS.<slug>.md`.
- Si le worktree n'existe pas encore, lis `.opencode/skills/worktree/SKILL.md` et crée-le d'abord.

### Étape 3 — Portes amont (si requises par triage)
Si le triage a identifié des portes architect, architect-security, security, ou adr comme requises :
- Lis et exécute chaque skill requis dans l'ordre : architect → architect-security → security → adr.
- Ne passe à l'étape suivante que si toutes les portes requises sont satisfaites.

### Étape 4 — Preflight
Lis `.opencode/skills/preflight/SKILL.md` puis exécute le skill preflight.
- Si `BLOCKED` → corrige les blockers identifiés et relance preflight.
- Ne passe à coder que sur `PASS`.

### Étape 5 — Coder (boucle)
Lis `.opencode/skills/coder/SKILL.md` puis exécute le skill coder.
- Exécute une tâche à la fois depuis `TODO.<slug>.md`.
- Valide localement, commit immédiatement (1 tâche = 1 commit).
- Répète jusqu'à ce que toutes les tâches du TODO soient terminées.
- Si dérive détectée → STOP → retour à l'étape 2 (planner).

### Étape 6 — QA
Lis `.opencode/skills/qa/SKILL.md` puis exécute le skill qa.
- Si `FAIL` → retour à l'étape 5 (coder) pour corriger, puis relance QA.

### Étape 7 — Review
Lis `.opencode/skills/review/SKILL.md` puis exécute le skill review.
- Si `CHANGES_REQUESTED` → retour à l'étape 5 (coder) pour corriger, puis relance QA + review.

### Étape 8 — Doc (si requis)
Si le triage ou le STATE indique que la documentation est requise :
- Lis `.opencode/skills/doc/SKILL.md` puis exécute le skill doc.

### Étape 9 — Release
Lis `.opencode/skills/release/SKILL.md` puis exécute le skill release.
- Déclare `MERGE_READY` ou `RELEASE_READY` uniquement si toutes les portes sont satisfaites.

## Règles d'orchestration

- Maintiens `MEMORY.md` à jour pendant le flux, pas seulement en lecture.
- Après planner, renseigne ou corrige au minimum : feature active, branche/worktree, tâche courante et statut des portes connues.
- À chaque changement d'état significatif, mets à jour `MEMORY.md` : transition de porte, nouveau blocker, blocker résolu, tâche courante, contexte de reprise.
- En fin de flux ou avant toute interruption, écris le contexte de reprise dans `MEMORY.md`, puis supprime les entrées devenues fausses.
- À chaque transition de skill, affiche un résumé court du résultat et de l'étape suivante.
- Si un skill retourne BLOCKED ou FAIL, ne saute jamais l'étape — résous ou escalade.
- Si le flux doit s'interrompre (besoin d'input utilisateur, décision ambiguë), demande explicitement avant de continuer.
- Si le flux est terminé, nettoie `MEMORY.md` pour ne laisser aucun état actif faux ou périmé.

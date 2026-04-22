# .agents

This directory contains the immutable governance assets and skill definitions used to operate work safely on this repository.

It is not a scratch space.

It is not a feature workspace.

It is part of the control plane.

---

## Purpose

The `.opencode/` directory exists to separate:

- immutable governance assets
- reusable templates
- skill procedures

from:

- per-feature working artifacts
- implementation changes
- temporary execution state

This keeps the system stable and prevents feature work from silently changing the rules that govern it.

---

## What Lives Here

### Immutable constitutional source

- `.opencode/_constitution.md`

This is the supreme governing document for the repository.

It is the immutable source of truth.

It must not be edited during feature work.

---

### Immutable templates

- `.opencode/_STATE.md`
- `.opencode/_TODO.md`
- `.opencode/_DECISIONS.md`

These are templates.

They are copied to produce per-feature working files.

They must not be edited in place during feature execution.

---

### Skill definitions

- `.opencode/skills/*/SKILL.md`

These files define the detailed behavior of each skill.

They are part of the governance/control system.

They must not be modified during ordinary feature work.

---

## What Does **Not** Live Here

Do not place the following in `.opencode/`:

- feature-specific `STATE.<slug>.md`
- feature-specific `TODO.<slug>.md`
- feature-specific `DECISIONS.<slug>.md`
- temporary task notes
- implementation scratchpads
- code patches
- local debugging logs
- ad hoc planning documents for one branch only

Those belong in the working repository context, not in the immutable control layer.

---

## Working Copies

Per-feature working artifacts are created at the repository root:

- `STATE.<slug>.md`
- `TODO.<slug>.md`
- `DECISIONS.<slug>.md`

These are the files actively used during feature work.

### Meaning

- `STATE.<slug>.md` = feature scope contract
- `TODO.<slug>.md` = execution rail
- `DECISIONS.<slug>.md` = local decision memory

---

## Rule: Templates Are Copied, Never Edited In Place

Correct pattern:

```text
.opencode/_STATE.md       -> STATE.<slug>.md
.opencode/_TODO.md        -> TODO.<slug>.md
.opencode/_DECISIONS.md   -> DECISIONS.<slug>.md
```

Incorrect pattern:

- edit `.opencode/_STATE.md` during a feature
- edit `.opencode/_TODO.md` during a feature
- edit `.opencode/_DECISIONS.md` during a feature

If a template is missing, it should be restored or recreated by repository maintenance - not casually rewritten during active feature work.

---

## Rule: Constitution Has Two Forms

Two constitutional files are expected in an initialized repository:

- `.opencode/_constitution.md` -> immutable source of truth
- `docs/governance/constitution.md` -> human-readable mirror

The mirror exists for readability and onboarding.

If there is any conflict, `.opencode/_constitution.md` wins.

---

## Why This Separation Matters

Without this separation, feature work can accidentally:

- weaken governance rules
- mutate shared templates
- create drift between current work and repository law
- cause future branches to inherit corrupted control artifacts

This repository treats governance assets as part of the system, not as incidental docs.

---

## What Preflight Checks Here

preflight is expected to verify that:

- `.opencode/_constitution.md` exists
- `.opencode/_STATE.md` exists
- `.opencode/_TODO.md` exists
- `.opencode/_DECISIONS.md` exists
- immutable templates remain unmodified
- required skill files exist where expected

If these are missing or altered improperly, coding must be blocked.

---

## Ownership Model

### Repository maintainer owns

- `.opencode/_constitution.md`
- `.opencode/_STATE.md`
- `.opencode/_TODO.md`
- `.opencode/_DECISIONS.md`
- `.opencode/skills/*`

### Planner owns

- `STATE.<slug>.md`

### Active feature execution maintains

- `TODO.<slug>.md`
- `DECISIONS.<slug>.md`

### Coder owns

- production code only

Only `$coder` writes production code.  
That does not give `$coder` ownership over immutable governance assets.

---

## Reading Order

If you are new to this repository, read in this order:

- `AGENTS.md`
- `docs/governance/constitution.md`
- `docs/governance/levels.md`
- `docs/governance/workflows.md`
- `.opencode/README.md`

Then read the specific skill files only when needed.

---

## Non-Negotiable Summary

- `.opencode/` is control plane, not workspace
- templates are copied, never edited in place
- constitution source is immutable
- skill files are not feature-local
- working artifacts live outside `.opencode/`
- if immutable governance assets are missing or altered, execution must stop


# SpikeFormer Constitution

> This document is the human-readable mirror of `.opencode/_constitution.md`.

## System Invariants

| ID | Invariant |
| --- | --- |
| I-01 | Public contracts are additive-only unless migration is provided |
| I-02 | Trust boundaries are explicit and default-deny |
| I-03 | Operations are deterministic given the same inputs |

## Architecture Triggers

Changes below require `$architect` before implementation:

- Module/package boundary changes
- New external dependency with structural impact
- Data model / schema changes
- Public API or CLI contract changes
- Configuration contract changes
- Pipeline or orchestration changes
- Runtime semantics changes
- File format changes
- 30% rewrite of a core module

## Security Triggers

Changes below require `$security`:

- Auth / authorization logic
- Secret or credential handling
- Dependency additions or upgrades
- New network exposure
- Untrusted input parsing
- Connector / plugin / execution boundary changes
- Trust boundary changes
- Command execution / shell bridging

## Forbidden Areas

Require explicit `$architect` approval:

- Storage schema definitions
- Auth / authorization logic
- Core pipeline definitions
- Configuration contract
- Public contract surfaces
- Release / CI workflow files
- Dependency policy files

## Core Principles

1. **Runtime is immutable**: Runtime cannot modify weights or models
2. **Learning is isolated**: C5 operates offline only
3. **Promotion is explicit**: Model updates require validation gate
4. **SAFE_MODE always available**: Fallback action guaranteed

## Governance Files

| File | Rule |
| --- | --- |
| `.opencode/_constitution.md` | Supreme law - never edit |
| `docs/governance/constitution.md` | Human-readable mirror |

## Change Levels

- **L1**: Local low-risk changes
- **L2**: Bounded standard changes
- **L3**: Structural or sensitive changes

## Execution Flows

- Standard feature: triage → planner → preflight → coder → qa → review → doc → release
- Bug fix: triage → planner → preflight → coder → qa → review
- Structural change: governance? → triage → planner → architect → adr → preflight → coder → qa → review → doc → release
- Security-sensitive: governance? → triage → planner → architect-security → adr → preflight → coder → security → qa → review → doc → release
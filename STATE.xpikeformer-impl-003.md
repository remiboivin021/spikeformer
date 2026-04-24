# STATE.xpikeformer-impl-003.md
> Phase 3: Hybrid ANN-SNN Conversion

## Metadata

- **Slug**: xpikeformer-impl-003
- **Phase**: 3 (Hybrid ANN-SNN)
- **Parent**: STATE.xpikeformer-impl-002.md

## Mission

Implement Phase 3 (Hybrid ANN↔SNN conversion) per Section V of paper:
- Convert pretrained ANN (ResNet) to SNN
- Spike encoding for ANN inputs
- Spike-based inference
- Hybrid training mode for fine-tuning

## Feature Type

- **new feature** (hybrid conversion)

## Change Level

- **L2** (standard change with pretrained model)

## Selected Flow

- `standard feature` → `triage → planner → preflight → coder → qa → review → doc → release`

## Classification Confirmation

- Feature type: new feature
- Change level: L2
- Reclassification from triage: no

## Acceptance Criteria

| ID | Criterion | Testable |
|----|-----------|----------|
| AC1 | ANN to SNN conversion function | Yes |
| AC2 | Spike encoding of ResNet features | Yes |
| AC3 | Hybrid model loads pretrained weights | Yes |
| AC4 | Fine-tuning on CIFAR-10 achieves >70% accuracy | Yes |
| AC5 | Unit tests for conversion module | Yes |

## Scope Contract

### Allowed Areas

- `src/snn/hybrid/` (new module)
- `src/snn/hybrid/__init__.py`
- `tests/unit/test_hybrid.py`
- `config/training/hybrid.yaml` (new config)

### Forbidden Areas

- `src/snn/neurons/` (existing - do not modify)
- `src/snn/architecture/` (existing - do not modify)
- `.opencode/` (constitution)

## Public Contract Impact

- **Contract impact**: no
- Surfaces affected: none
- Migration needed: no
- ADR required: no

## Required Gates

| Gate | Required | Notes |
|------|----------|-------|
| governance | no | No constitutional changes |
| architect | no | Bounded L2 change |
| architect-security | no | No security surfaces |
| security | no | No auth/secrets |
| adr | no | No durable decisions |
| doc | yes | New component docs |
| qa | yes | Unit tests required |
| review | yes | Merge gate |
| release | yes | Final merge |

## Blast Radius

- **Classification**: localized (new module)
- **Reason**: Hybrid is isolated new module

## Parallel / Collision Risk

- **Parallel risk**: none
- **Shared surfaces**: None (Phase 1-2 complete)
- **Escalation needed**: no

## Execution Plan

```
P3-T1: Hybrid module structure
- Create src/snn/hybrid/ directory
- Define conversion functions

P3-T2: ANN-to-SNN converter
- Load pretrained ResNet weights
- Convert to SNN-compatible format
- Handle channel differences

P3-T3: Hybrid training
- Fine-tuning mode
- Mixed ANN-SNN forward pass

P3-T4: Unit Tests
- Conversion tests
- Inference tests

P3-T5: Documentation
```

## Drift Conditions

Execution must return to planner if:
- Scope expands beyond Hybrid module
- Additional modules required
- Architecture tension appears

---

**Created**: 2026-04-24
**Status**: ready_for_planning
# Change Levels Policy

## Overview

Change levels classify the risk and scope of work to ensure appropriate gates and review.

## L1 - Local Low-Risk

Use when ALL of the following are true:
- Bounded local change
- No architecture trigger
- No security trigger
- No public contract change
- No invariant surface touched
- No migration needed
- Limited to a small number of files

**Examples:**
- Typo fix
- Documentation-only change
- Test-only addition
- Small local bug fix
- Localized internal implementation tweak

## L2 - Bounded Standard Change

Use when:
- Behavior changes within existing boundaries
- Multiple files may be involved
- Feature or bug fix is real but bounded
- Blast radius is not structural
- Public behavior may change without breaking core contracts

**Examples:**
- Normal feature in an existing module
- Bounded bug fix across several files
- Local refactor with defined scope
- Additive behavior in an existing workflow

## L3 - Structural or Sensitive

Use when ANY of the following are true:
- Architectural boundary change
- Trust boundary change
- Invariant or contract surface touched
- Config/schema/file format/pipeline semantics change
- Dependency introduction/upgrade with meaningful impact
- Migration required
- Rollback planning required
- Security-sensitive surface involved
- Blast radius unclear or cross-system

**Examples:**
- Public API change
- Config contract change
- Structural runtime redesign
- Schema evolution
- Security-sensitive feature
- Pipeline semantics change

## Level Determination

1. Start by assuming L1
2. If any L2 criteria apply → L2
3. If any L3 criteria apply → L3
4. When uncertain → choose higher level

## Gate Requirements by Level

| Gate | L1 | L2 | L3 |
|------|-----|-----|-----|
| triage | ✓ | ✓ | ✓ |
| planner | - | ✓ | ✓ |
| architect | - | - | ✓ |
| adr | - | - | ✓ |
| preflight | ✓ | ✓ | ✓ |
| coder | ✓ | ✓ | ✓ |
| qa | optional | ✓ | ✓ |
| review | ✓ | ✓ | ✓ |
| doc | - | - | ✓ |
| release | ✓ | ✓ | ✓ |

## Review Frequency

- L1: May be self-reviewed
- L2: Requires team review
- L3: Requires architecture review + ADR
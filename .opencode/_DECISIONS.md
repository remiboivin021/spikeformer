# DECISIONS - <feature-name>

This file records **non-trivial local decisions** made during feature execution.

Its purpose is to preserve implementation reasoning that is:

- important enough to remember during the feature
- useful for review
- potentially promotable to ADR later
- too significant to leave implicit
- but not yet a durable architecture decision by itself

This is **feature-local memory**, not constitutional law and not an ADR.

---

## File Scope

This file belongs to exactly one feature/work branch.

Expected naming:

```text
DECISIONS.<slug>.md
```

Examples:

- `DECISIONS.runtime-graph-cache.md`
- `DECISIONS.fix-cli-error-handling.md`

---

## What Belongs Here

Record a decision when at least one of the following is true:

- more than one reasonable implementation path existed
- a tradeoff was made
- a local workaround was necessary
- behavior was preserved in a non-obvious way
- a review comment is likely if the choice is left unexplained
- the choice may later need to be promoted to ADR
- the choice influences testing, rollback, or follow-up work
- the choice constrains the rest of the current feature

## What Does Not Belong Here

Do not record:

- trivial edits
- obvious formatting changes
- restatements of TODO items
- decisions already fully captured by an ADR
- permanent repository law
- vague diary-style notes without an actual decision

If the issue affects:

- architecture
- invariants
- public contracts
- trust boundaries
- migration / rollback strategy
- schema / config / file format compatibility

then escalate to ADR instead of settling it silently here.

---

## Relationship to Other Files

- `STATE.<slug>.md` = what the feature is allowed to do
- `TODO.<slug>.md` = what is currently being executed
- `DECISIONS.<slug>.md` = why certain non-trivial implementation choices were made
- `docs/governance/adr/<yy-mm-dd_slug>.md` = durable structural decisions

This file must not override `STATE.<slug>.md`.

If a decision reveals that the current STATE is no longer accurate:

- stop execution
- return to planner
- update STATE first

---

## Entry Rules

Each entry should be:

- specific
- bounded
- tied to actual implementation work
- understandable later in review
- linked to task and files when possible

Do not hide scope expansion inside a decision entry.

A decision entry is not permission.

---

## Entry Template

Use this structure for each entry.

```text
D-XXX - <short title>

Date: YYYY-MM-DD
Task: T-XXX
Status: Proposed | Applied | Escalated | Superseded
Related files: path/to/file, path/to/file

Context

What local problem or choice appeared?

Options considered

Option A:

Option B:

Option C: (optional)

Decision

What was chosen?

Why

Why was this option selected?

Impact

What does this affect locally?

code structure

behavior

tests

reviewability

follow-up work

ADR check

ADR required: yes / no

If yes: stop and escalate

Follow-up

Any required follow-up action?

Commit

<short-SHA or pending>
```

---

## Status Meaning

### Proposed

The decision is identified but not yet fully applied.

### Applied

The decision was implemented in the current feature work.

### Escalated

The issue cannot be safely resolved locally and must move to:

- planner
- architect
- architect-security
- security
- adr
- governance

### Superseded

A later decision replaced this one.

---

## Promotion Rule

A decision should be promoted to ADR if it affects or may affect:

- architecture boundaries
- invariants
- public API / CLI
- config / schema / file formats
- runtime semantics
- trust boundaries
- migration or rollback assumptions
- long-lived system behavior expectations

If a decision crosses this threshold, local logging is not enough.

Escalate.

---

## Reviewability Rule

A good decision entry should help a reviewer answer:

- Why was this done this way?
- What alternative was rejected?
- Is the tradeoff acceptable?
- Is there follow-up debt?
- Does this need to be promoted to ADR?

If the entry does not answer these kinds of questions, it is too weak.

---

## Minimal Example

```text
D-001 - Preserve parser fallback locally

Date: 2026-03-06
Task: T-003
Status: Applied
Related files: src/parser.rs, tests/parser_fallback.rs

Context

The old parser path returned a fallback value on malformed optional metadata, while the new helper failed hard.

Options considered

Option A: make helper strict and update all callers

Option B: preserve old fallback behavior only in this path

Decision

Selected Option B and preserved fallback behavior for the current feature scope.

Why

Changing all callers would expand scope and alter behavior outside the current contract.

Impact

preserves existing behavior

keeps fix local

adds targeted regression expectation

ADR check

ADR required: no

Follow-up

Revisit whether parser strictness should become a structural cleanup later.

Commit

a1b2c3d
```

---

## Empty Start Is Allowed

This file may start empty.

But it must exist before coding starts if the repo requires it.

Create entries only when there is a real non-trivial decision to log.

---

## Non-Negotiable Summary

- log non-trivial local decisions
- do not log trivia
- do not use this file to expand scope
- do not use this file to bypass gates
- escalate when a decision crosses into architecture, contracts, invariants, or trust boundaries


# TODO - <feature-name>

This file is the **execution rail** for one feature/work branch.

Its purpose is to turn the approved execution plan from `STATE.<slug>.md` into **atomic, reviewable task execution**.

This file is not a brainstorm.  
It is not a backlog.  
It is not a place to redefine scope.

It exists to control:

- current execution focus
- task sequencing
- task completion evidence
- commit traceability

---

## File Scope

This file belongs to exactly one feature/work branch.

Expected naming:

```text
TODO.<slug>.md
```

Examples:

- `TODO.runtime-graph-cache.md`
- `TODO.fix-cli-error-handling.md`

---

## Relationship to Other Files

- `STATE.<slug>.md` = what the feature is allowed to do
- `TODO.<slug>.md` = what is being executed now, next, and already done
- `DECISIONS.<slug>.md` = why non-trivial local choices were made
- `docs/governance/adr/<yy-mm-dd_slug>.md` = durable structural decisions

`TODO.<slug>.md` must never expand or override `STATE.<slug>.md`.

If TODO needs work outside the current STATE contract:

- stop
- return to planner
- update `STATE.<slug>.md`
- re-run required gates and preflight before continuing

---

## Atomicity Rule

This file enforces one of the core laws of the system:

One task = one commit

That means:

- one active current task at a time
- one bounded unit of work at a time
- one validation pass for that task
- one commit immediately after completion

A task must be small enough to be:

- honest
- reviewable
- revertable
- clearly tied to one commit

If a task is too large for one commit, it is not a task yet.
Return to planner and split it properly.

---

## Current Task Rule

At any time before coding starts, this file must contain:

exactly one item under `# Current Task`

Not zero.  
Not two.  
Exactly one.

preflight must block coding if this rule is violated.

---

## Status Sections

This file is organized into three execution states:

- `# Current Task`
- `# Next Tasks`
- `# Done`

### Meaning

#### Current Task

The one task currently approved for implementation.

#### Next Tasks

Approved future tasks that are in scope but not yet active.

#### Done

Completed tasks, each with its commit SHA.

---

## Task Shape Rule

Each task should:

- be concrete
- stay inside Allowed Areas
- map to a single bounded objective
- be completable without hidden structural work
- be small enough for one commit

Good tasks:

- "Add guard for empty graph node list in runtime loader"
- "Add regression test for CLI missing-config exit path"
- "Update error mapping in parser adapter for invalid optional metadata"

Bad tasks:

- "Refactor parser system"
- "Improve runtime"
- "Clean up code"
- "Implement everything needed"
- "Handle all edge cases"

If the task is vague, it is invalid.

---

## Task ID Rule

Every task must have a unique task ID.

Format:

```text
T-001
T-002
T-003
```

Zero-padded numbering is recommended.

Task IDs are used in:

- commit trailer
- decision log entries
- review discussion
- traceability between work and code

---

## Required Task Template

Use this structure for every task item.

```text
- [ ] T-XXX - <short concrete task description>
```

For completed tasks, use:

```text
- [x] T-XXX - <short concrete task description> | commit: <short-SHA>
```

The commit suffix is mandatory in `# Done`.

---

## Section Template

Use this exact layout.

```text
Current Task

 T-001 - <one active task only>

Next Tasks

 T-002 - <next task>

 T-003 - <next task>

Done

 T-000 - <completed task> | commit: <short-SHA>
```

---

## Initialization Rule

When this file is first created from `.opencode/_TODO.md`:

- `# Current Task` must contain exactly one task
- `# Next Tasks` may contain additional already-approved tasks
- `# Done` may be empty

If there is no valid current task, coding must not start.

---

## Update Rules

### When starting work

Only the task under `# Current Task` may be implemented.

Do not pull work from `# Next Tasks` early.

### When completing the current task

Coder must:

- finish the bounded work
- run the required local validation
- commit immediately
- move the completed task to `# Done`
- append `| commit: <short-SHA>`
- promote exactly one next task into `# Current Task` if more work remains

### When blocked by drift

Do not silently rewrite tasks to match reality.

Instead:

- stop
- return to planner
- update `STATE.<slug>.md` first
- then update TODO if the plan changed legitimately

---

## Forbidden Uses

Do not use TODO to:

- add scope not present in STATE
- hide structural work inside vague tasks
- track random ideas
- maintain team backlog
- merge unrelated work under one task
- defer missing planning with "fix later" placeholders

This is an execution file, not a planning scratchpad.

---

## Validation Awareness Rule

A task should be written so the required proof is obvious.

Examples:

- if it is a bug fix, the task should imply a regression test or equivalent proof
- if it changes behavior, QA impact should be visible
- if it touches docs, doc follow-up should be visible
- if it affects contracts or structure, the task probably belongs in a stricter flow

TODO does not replace QA or review, but it should not obscure validation expectations either.

---

## Replanning Rule

Return to planner if any of the following happens:

- current task needs files outside Allowed Areas
- blast radius is larger than expected
- forbidden area becomes necessary
- architecture tension appears
- public contract impact changes
- security/trust impact appears
- current task is too large for one honest commit
- task boundaries in TODO no longer match the real plan

When replanning happens:

- STATE changes first
- TODO changes second
- coding resumes only after preflight PASS again when required

---

## Minimal Example

```text
Current Task

 T-003 - Add regression test for missing optional metadata fallback

Next Tasks

 T-004 - Preserve fallback behavior in parser adapter

 T-005 - Update parser error mapping notes for review

Done

 T-001 - Identify failing parser path and isolate affected files | commit: a1b2c3d

 T-002 - Add fixture for malformed optional metadata input | commit: d4e5f6g
```

---

## Non-Negotiable Summary

- exactly one current task before coding
- one task = one commit
- done tasks must include commit SHA
- TODO must stay inside STATE
- if reality diverges from TODO, replan instead of improvising


```md
# STATE — <feature-name>

Branch: feature/<slug>  
Worktree: ../wt-<slug>  
Planner: planner-agent  
Executor: coder-agent  

---

# Mission

Describe EXACTLY what this feature must deliver.

Be explicit.

Anything not written here is OUT OF SCOPE.

---

# Feature Type

Select one:

- [ ] new feature  
- [ ] bug fix  
- [ ] refactor (approved)  
- [ ] performance improvement  
- [ ] infrastructure  
- [ ] security  

This classification drives routing decisions.

---

# Change Level

Select one:

- [ ] L1 — local low-risk  
- [ ] L2 — bounded standard change  
- [ ] L3 — structural or sensitive  

If uncertain, choose the higher level.

This classification drives gate strictness.

---

# Acceptance Criteria

A feature is COMPLETE only when ALL boxes are checked.

- [ ] ...
- [ ] ...
- [ ] ...

Criteria must be testable.

Avoid vague goals like:  
❌ "improve performance"

Prefer:  
✅ "reduce query latency by 30%"

---

# Scope Contract

## Allowed Areas

Explicitly list files/modules that MAY change.

Example:

- synexis_brain/search/hybrid.py  
- synexis_brain/pipelines/search.dot  
- tests/search/*  

Coder-agent must stay inside this boundary.

---

## Forbidden Areas

List sensitive zones.

Example:

- storage schemas  
- connector layer  
- config contract  
- chunking logic  

Touching these REQUIRES architect-agent approval.

Anything not explicitly allowed is presumed forbidden until planner updates this file.

---

# Public Contract Impact

Does this change affect any public contract?

- [ ] no
- [ ] yes — Rust API
- [ ] yes — CLI
- [ ] yes — config
- [ ] yes — file format / schema
- [ ] yes — pipeline semantics
- [ ] yes — external integration behavior

If yes, specify:

- Migration needed: yes / no
- ADR required: yes / no

---

# Required Gates

Mark all that apply:

- [ ] governance
- [ ] architect
- [ ] architect-security
- [ ] security
- [ ] adr
- [ ] doc
- [ ] qa
- [ ] review
- [ ] release

These gates must reflect the actual triggers and contract impact of this feature.

---

# Blast Radius Assessment

Planner-agent MUST classify expected impact:

- [ ] localized (single module)  
- [ ] multi-module  
- [ ] cross-system  
- [ ] unknown  

If NOT localized → architect-agent review is recommended.  
If unknown → coding must not start.

Never discover blast radius mid-refactor.

---

# Architectural Constraints

Follow existing patterns.

Do NOT:

- introduce new frameworks  
- change module boundaries  
- redesign pipelines  
- modify scoring logic  
- alter runtime semantics  
- expand public surface casually  

WITHOUT:

architect-agent approval + ADR when required.

Prefer extension over invention.

Stability > novelty.

---

# Parallel Safety Check

Planner-agent MUST verify this feature does NOT conflict with:

- active worktrees  
- shared interfaces  
- schemas  
- config  
- pipelines  
- contract surfaces  
- shared core modules  

If conflict risk exists:

STOP → escalate to architect-agent.

Parallel collisions are high risk.

---

# Security Surface Check

Does this feature touch:

- auth / permissions  
- secrets  
- connectors  
- network  
- dependencies  
- untrusted input  
- trust boundaries  
- plugin or command execution surfaces  

If YES:

security-agent review is mandatory.

---

# Execution Plan (Planner Output)

1.
2.
3.

Coder-agent MUST convert this into `TODO.<slug>.md` BEFORE writing code.

No plan → no coding.

---

# Refactor Shield

Refactoring is FORBIDDEN unless explicitly approved.

Forbidden examples:

- renaming modules  
- reorganizing directories  
- cleaning unrelated code  
- modernizing patterns  
- introducing abstractions not required by scope  
- broad “consistency” edits outside the allowed areas  

If refactor pressure appears:

STOP → call planner-agent.

---

# Definition of Done

✔ Acceptance criteria met  
✔ QA passed  
✔ Security approved (if triggered)  
✔ Review approved  
✔ Docs updated (if triggered)  
✔ ADR created (if required)  
✔ Release readiness confirmed (if required by flow)  

Only then may the feature merge.

---

# Drift Detection Protocol

Coder-agent MUST STOP immediately if:

- scope expands  
- architecture tension appears  
- plan becomes invalid  
- unexpected complexity emerges  
- additional files are needed outside Allowed Areas  
- public contract impact changes  
- required gates change during execution  

Call planner-agent before continuing.

Never improvise structural changes.

---

# Local Optimization Rule

Optimize ONLY what this feature touches.

Do NOT optimize the entire repository.

Global optimization is forbidden during feature work.

---

# Decision Bridge

All significant implementation choices MUST be logged in:

`DECISIONS.<slug>.md`

If a decision impacts architecture, trust boundaries, contracts, or invariants → escalate to ADR.

---

# State Integrity Rule

`STATE.<slug>.md` is the single source of truth for feature scope.

If `STATE.<slug>.md` becomes inaccurate:

planner-agent MUST update it immediately.

Never continue with stale state.
```


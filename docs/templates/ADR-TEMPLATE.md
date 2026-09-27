---
id: ADR-000X
title: "[Short, Descriptive Title of Decision]"
type: adr
status: proposed # proposed | accepted | rejected | superseded
date: YYYY-MM-DD
deciders:
  - System Architects / Lead Engineers
epic_id: EPIC-X # Optional
consulted:
  - Claude Code / Antigravity / Team
---

# ADR 000X — [Short, Descriptive Title of Decision]

> **Category:** Architecture Decision Record  
> **Status:** 🟦 Proposed <!-- or ✅ Accepted -->  
> **Index:** [`docs/adr/README.md`](./README.md)  
> **Applies to:** [`docs/backlog/epic-X-NAME/EPIC-X-NAME.md`](../backlog/epic-X-NAME/EPIC-X-NAME.md)

---

## 1. Context & Problem Statement
[Describe the context, problem statement, and forces at play. What changed? What architectural conflict or performance/isolation limit did we encounter?]

---

## 2. Decision Drivers & Invariants
* **Driver 1**: [e.g., Strict multi-tenant isolation via PostgreSQL RLS]
* **Driver 2**: [e.g., Deterministic offline-first Mac client behavior]
* **Driver 3**: [e.g., Token and cost efficiency for multi-turn agent execution]

---

## 3. Considered Options
1. **Option 1**: [Description of Option 1]
   - *Pros*: ...
   - *Cons*: ...
2. **Option 2**: [Description of Option 2]
   - *Pros*: ...
   - *Cons*: ...
3. **Option 3 (Chosen)**: [Description of Option 3]
   - *Pros*: ...
   - *Cons*: ...

---

## 4. Decision Outcome
**Chosen Option**: Option 3 because [clear, concise rationale explaining non-obvious trade-offs].

### Key Architectural Invariants Established
1. [Invariant 1]
2. [Invariant 2]

---

## 5. Consequences & Trade-offs
* **Positive Consequences**:
  - [What becomes easier, safer, or faster?]
* **Negative Consequences / Mitigations**:
  - [What becomes harder? How do we mitigate it?]

---

## 6. Implementation & Compliance Lineage
* **Parent Epic**: [`docs/backlog/epic-X-NAME/EPIC-X-NAME.md`](../backlog/epic-X-NAME/EPIC-X-NAME.md)
* **Stories Enforcing this ADR**:
  - [`Story X.1`](../backlog/epic-X-NAME/stories/STORY-X.1-SLUG.md)

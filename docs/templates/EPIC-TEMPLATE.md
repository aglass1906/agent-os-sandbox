---
id: EPIC-X
title: "[Initiative / Capability Title]"
type: epic-plan
status: planned # planned | in_progress | completed | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
design_spec: docs/design-specs/FEATURE-SPEC.md # Optional / if applicable
adrs:
  - docs/adr/000X-TITLE.md # Optional / if applicable
surfaces:
  - mac-app
  - orchestrator
  - supabase
stories_total: 0
stories_done: 0
---

# Epic X — [Initiative / Capability Title]

> **Category:** Master Backlog & Epic Execution Plan  
> **Status:** 🟦 Planned  
> **Master Epic Backlog:** [`docs/backlog/BACKLOG.md`](../BACKLOG.md)  
> **Living Execution Tracker:** [`docs/STATUS.md`](../../STATUS.md)  
> **Stories Directory:** [`./stories/`](./stories/)

---

## 1. Executive Summary & Goal
[Concise 1-2 paragraph description of the business/user goal, the architectural capability being unlocked, and why it matters.]

---

## 2. Architecture Lineage & Invariants
- **Design Lineage**: Links to ADRs (`docs/adr/`) and Feature Design Specs (`docs/design-specs/`).
- **Core Invariants**:
  1. [Invariant 1: e.g. Data boundary, offline safety, RLS isolation]
  2. [Invariant 2: e.g. Transport compatibility, no silent errors]
  3. [Invariant 3: e.g. Domain model parity]

---

## 3. Story Breakdown & Acceptance Gates

| Story | Title | Status | Specification |
|---|---|---|---|
| [`Story X.1`](./stories/STORY-X.1-SLUG.md) | [Story 1 Title] | 🟦 Planned | [`STORY-X.1`](./stories/STORY-X.1-SLUG.md) |
| [`Story X.2`](./stories/STORY-X.2-SLUG.md) | [Story 2 Title] | 🟦 Planned | [`STORY-X.2`](./stories/STORY-X.2-SLUG.md) |

### Mandatory Acceptance Gate for Every Story
Before marking any story complete, the implementing agent must:
1. Self-audit code, schema, and protocol contracts.
2. Execute automated tests (`pytest`, `xcodebuild`, `make test-mac-ui`).
3. Record commands, outputs, and verification evidence in the story handoff.

---

## 4. Verification & Testing Strategy

### Mandatory 3-Phase Testing Protocol
```bash
# Phase 1: Setup
make test-db

# Phase 2: Test Execution
cd orchestrator && pytest -q
xcodebuild -workspace mac-app/AgentOS.xcworkspace -scheme AgentOS build
make test-mac-ui

# Phase 3: Teardown & Cleanup
make reset-test-db
git worktree prune
rm -rf /tmp/agentos-test* "$TMPDIR/agentos-ui-tests"
git status --short
```

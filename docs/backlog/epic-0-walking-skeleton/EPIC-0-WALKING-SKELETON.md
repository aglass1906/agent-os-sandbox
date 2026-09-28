---
id: "EPIC-0"
title: "Walking Skeleton"
type: "epic-plan"
status: "completed"
created: "2026-09-27"
updated: "2026-09-28"
surfaces:
  - core
stories_total: 1
stories_done: 1
---

# Epic 0 — Walking Skeleton

> **Category:** Master Backlog & Epic Execution Plan  
> **Status:** ✅ Completed  
> **Master Epic Backlog:** [`docs/backlog/BACKLOG.md`](../BACKLOG.md)  
> **Living Execution Tracker:** [`docs/STATUS.md`](../../STATUS.md)  
> **Stories Directory:** [`./stories/`](./stories/)

---

## 1. Executive Summary & Goal
Establish the initial walking skeleton, project repository structure, build automation, and documentation governance.

---

## 2. Architecture Lineage & Invariants
- Minimal zero-dependency baseline.
- Automated verification via Makefile.

---

## 3. Story Breakdown & Acceptance Gates

| Story | Title | Status | Specification |
|---|---|---|---|
| [`Story 0.1`](./stories/STORY-0.1-REPOSITORY-INITIALIZATION.md) | Repository initialization | ✅ Completed | [`STORY-0.1`](./stories/STORY-0.1-REPOSITORY-INITIALIZATION.md) |

### Mandatory Acceptance Gate for Every Story
Before marking any story complete, the implementing agent must:
1. Self-audit code, schema, and protocol contracts for diff hygiene and defect remediation.
2. Reconcile living design documentation (`docs/design-specs/` or `docs/architecture/`) to ensure code and specs never diverge.
3. Execute automated tests (`pytest`, `xcodebuild`, `make test-mac-ui`) and document the human verification procedure.
4. Record commands, outputs, and verification evidence in the story handoff.

### Two-Tier Documentation Invariant
- **Tier 1 (Story Task — Mandatory)**: Every code story that modifies APIs, schemas, UI states, or invariants must include an atomic task to update the corresponding feature design spec (`docs/design-specs/`) or architecture spec (`docs/architecture/`).
- **Tier 2 (Epic Story — Large Initiatives)**: For complex multi-story Epics (5+ stories or major architectural initiatives), scope a concluding story (e.g. `Story X.Z — Subsystem Architectural Consolidation, Sequence Diagrams & Runbook`) to synthesize end-to-end system flows and operator runbooks.

---

## 4. Verification & Testing Strategy
- Clean make build and status generation.

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

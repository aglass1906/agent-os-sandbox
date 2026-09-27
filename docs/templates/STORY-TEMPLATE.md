---
id: STORY-X.Y
epic_id: EPIC-X
title: "[Story Title]"
type: story-spec
status: planned # planned | in_progress | completed
surfaces:
  - mac-app
  - orchestrator
parent_epic: docs/roadmap/epic-X-NAME/EPIC-X-NAME.md
design_spec: docs/design-specs/FEATURE-NAME.md # Optional
adrs:
  - docs/adr/000X-TITLE.md # Optional
---

# Story X.Y — [Story Title]

> **Parent Epic:** [Epic X — [Epic Title]](../EPIC-X-NAME.md)  
> **Status:** 🟦 Planned  
> **Living Tracker:** [`docs/STATUS.md`](../../../STATUS.md)

---

## 1. Executive Summary & User/Operator Benefit
[As a [role], I want [capability] so that [benefit]. Concrete 1-2 sentence description.]

---

## 2. Scope & Technical Requirements
- [ ] **Surface 1 (e.g. Mac Client)**: [UI components, ViewModels, navigation, event subscriptions]
- [ ] **Surface 2 (e.g. Orchestrator API)**: [Endpoints, state transitions, JobDriver actions]
- [ ] **Surface 3 (e.g. Supabase DB)**: [Migrations, tables, RLS policies, indexes]
- [ ] **Invariants**: [Boundary rules, performance constraints, error handling]

---

## 3. Atomic Tasks
- [ ] **Task X.Y.1**: [Concrete technical task 1 — e.g. schema migration and DAL repository]
- [ ] **Task X.Y.2**: [Concrete technical task 2 — e.g. protocol message handler]
- [ ] **Task X.Y.3**: [Concrete technical task 3 — e.g. SwiftUI View & ViewModel integration]
- [ ] **Task X.Y.4**: [Concrete technical task 4 — e.g. Automated test coverage & live verification]

---

## 4. Acceptance Gates & Verification Evidence
- **Automated Verification**:
  - `pytest -q tests/test_feature.py`
  - `xcodebuild -workspace mac-app/AgentOS.xcworkspace -scheme AgentOS build`
- **Manual Verification**:
  - [Step-by-step verification steps in running Mac app / CLI]
- **Evidence Record**:
  - [Test output log, pass counts, or link to handoff document]

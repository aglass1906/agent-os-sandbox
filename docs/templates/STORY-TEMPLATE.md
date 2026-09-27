---
id: STORY-X.Y
epic_id: EPIC-X
title: "[Story Title]"
type: story-spec
status: planned # planned | in_progress | completed
surfaces:
  - mac-app
  - orchestrator
parent_epic: docs/backlog/epic-X-NAME/EPIC-X-NAME.md
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
- [ ] **Task X.Y.5**: [Documentation reconciliation — update relevant design spec in docs/design-specs/ or architecture spec in docs/architecture/ with shipped behavior, contracts, and flags]
- [ ] **Task X.Y.6**: [Session handoff — update docs/history/handoffs/HANDOFF-EPIC-X.md with test evidence, git commits, and next steps]

---

## 4. Acceptance Gates & AI Self-Audit

### Automated Verification Gates
- [ ] `[Test command 1 — e.g. pytest -q tests/test_feature.py]`
- [ ] `[Build / compile command — e.g. xcodebuild or make build]`
- [ ] `[Lint / type-check — e.g. make lint or mypy]`

### AI Self-Audit & Defect Remediation (Mandatory for Code Changes)
> *The AI agent MUST complete this audit and resolve all issues prior to marking the story completed or submitting work.*
- [ ] **Diff Hygiene**: Inspect `git diff` to verify only intended files/lines were touched. Ensure no leftover debugging statements, temporary prints, or commented-out code.
- [ ] **Defect & Regression Triage**: Investigate and fix any newly failing tests, compilation errors, or linter warnings immediately. Never bypass or silence failing checks.
- [ ] **Documentation Reconciliation**: Verify that relevant design specs (`docs/design-specs/`) and architecture docs (`docs/architecture/`) were updated to reflect actual shipped behavior, contracts, and flags.
- [ ] **Handoff Document Maintenance**: Updated `docs/history/handoffs/HANDOFF-EPIC-X.md` with commit log, test command outputs, and next-story guidance for subsequent agents.
- [ ] **Edge Cases & Error Handling**: Verify null/nil safety, error boundary captures, network timeouts, and boundary condition inputs.
- [ ] **State & Resource Teardown**: Confirm scratch databases, temp files, ephemeral worktrees, and test processes have been safely cleaned up.

---

## 5. Human Verification Procedure (Step-by-Step)
> *Required for any functional, visual, or interactive change. Provides explicit, step-by-step instructions for human operator validation.*

### Prerequisites
- [e.g. Services running: local orchestrator on port 8000, Postgres running]
- [e.g. Test account / user role configured]
- [e.g. App launched or test environment URL: `http://localhost:3000` / Mac app running]

### Step-by-Step Verification Flow
1. **[Step 1: Initial State & Navigation]**:
   - **Action**: [e.g. Navigate to Backlog View from the sidebar]
   - **Expected Outcome**: [e.g. View loads with current Epics listed, search bar visible]
2. **[Step 2: Trigger Primary Functional Action]**:
   - **Action**: [e.g. Click 'New Epic' button, enter title 'Billing Service', click 'Create']
   - **Expected Outcome**: [e.g. Modal closes cleanly, new Epic appears at the top with 'Planned' status pill]
3. **[Step 3: Verify Persistence & Feedback]**:
   - **Action**: [e.g. Refresh the window or reopen the view]
   - **Expected Outcome**: [e.g. Newly created Epic remains present with data intact]
4. **[Step 4: Edge Case / Failure Path]**:
   - **Action**: [e.g. Attempt to submit the form with an empty title]
   - **Expected Outcome**: [e.g. Form displays an inline error 'Title is required' and prevents submission]

### Operator Sign-Off
- [ ] **Human Verification Verified By**: `[Operator Name / Handle]`
- [ ] **Verification Date**: `YYYY-MM-DD`
- [ ] **Outcome**: Pass / Needs Revision

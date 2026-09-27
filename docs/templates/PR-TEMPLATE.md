---
id: PR-TEMPLATE
title: Pull Request & Delivery Completion Template
type: pr-completion-template
status: template
---

# Pull Request Completion Report

> **Usage**: Use this structure for Pull Request descriptions, implementation review notes, and delivery completion audits. Keep the report concise and link to durable repository documents rather than copying massive raw logs.

---

## 1. What Changed

- **Outcome**: Describe the user-visible, operational, or architectural outcome delivered.
- **Key Changes**: Summarize the principal implementation modifications across directories.
- **Traceability**:
  - Closes #`[issue_number]`
  - Parent Story: [`STORY-X.Y-NAME.md`](../backlog/epic-X-NAME/stories/STORY-X.Y-NAME.md)
  - Parent Epic: [`EPIC-X-NAME.md`](../backlog/epic-X-NAME/EPIC-X-NAME.md)

---

## 2. Architecture & Security Decisions

- **Material Boundaries**: Identify interfaces, database schemas/migrations, RLS policies, tenant boundaries, or production-safety controls changed.
- **Test Infrastructure**: State whether test-only infrastructure, mocks, or fixtures were introduced or altered.
- **Architectural Linkage**: Link relevant decision or design documents ([`ADR-000X`](../adr/) or [`DESIGN-SPEC`](../design-specs/)). Write `None` if no material design decision was required.

---

## 3. Verification & Evidence

> [!IMPORTANT]
> **Zero-Tolerance Quality Gate**: Local verification must be executed and recorded before submitting or merging. Do not claim tests or checks that were not executed.

* **Agent / Human Author**: `[Name / Model / Subagent]`
* **Date**: `YYYY-MM-DD`
* **Environment**: `[Local Mac / Docker / Linux VPS / CI]`
* **Commands Executed**:
  ```bash
  # List all verification commands run locally:
  <command 1>
  <command 2>
  ```
* **Results**: `[Pass / Fail / Blocked]`
* **Commands Not Run & Rationale**:
  - `<command>` — `<reason for omission>`
* **Known Gaps / Deferred Coverage**:
  - `<gap description or follow-up issue>`

---

## 4. Known Limitations & Residual Risks

- List residual risks, accepted limitations, deferred work, compatibility concerns, or operational assumptions.
- Link follow-up issues or backlog stories where available.
- Write `None known` only after reviewing the complete diff (`git diff HEAD~1`).

---

## 5. Manual Acceptance Steps

1. **Environment & Setup**: State the environment and required baseline data/configuration.
2. **End-to-End Verification Path**: Describe the shortest end-to-end path demonstrating the approved outcome:
   1. `Step 1...`
   2. `Step 2...`
   3. **Expected Result**: `[What should happen]`
3. **Negative / Edge Verification**: Describe behavior under invalid inputs, authorization rejections, or error conditions.

---

## 6. Pre-Merge Completion Checklist

- [ ] The change stays strictly within approved issue/story scope and non-goals.
- [ ] No extraneous refactoring, debug artifacts, or temporary scratch files introduced.
- [ ] Tests and documentation were updated where required.
- [ ] Required local verification passed without failures or unhandled warnings.
- [ ] No secrets, credentials, or private keys were committed.
- [ ] Known limitations and residual risks are disclosed.
- [ ] Manual acceptance steps are verified and complete.
- [ ] Living status tracker (`docs/STATUS.md`) and category README indices updated.
- [ ] Ready for independent peer/architect review.

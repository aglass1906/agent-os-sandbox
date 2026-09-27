---
id: STORY-0.1
epic_id: EPIC-0
title: "Repository initialization"
type: story-spec
status: completed
surfaces:
  - core
parent_epic: docs/backlog/epic-0-walking-skeleton/EPIC-0-WALKING-SKELETON.md
---

# Story 0.1 — Repository initialization

> **Parent Epic:** [Walking Skeleton](../EPIC-0-WALKING-SKELETON.md)  
> **Status:** ✅ Completed  
> **Living Tracker:** [`docs/STATUS.md`](../../../STATUS.md)

---

## 1. Executive Summary & User/Operator Benefit
Initialize the AgentOS Sandbox codebase with documentation governance, scaffolding tools, and an interactive status dashboard.

---

## 2. Scope & Technical Requirements
- Standard documentation hierarchy established.
- Makefile automation with new-epic, new-story, and dashboard targets.

---

## 3. Atomic Tasks
- [x] Task 0.1.1: Initialize project directory and git repository.
- [x] Task 0.1.2: Install documentation templates and dashboard generator.
- [x] Task 0.1.3: Generate initial status dashboard.

---

## 4. Acceptance Gates & Verification Evidence
- [x] `make dashboard` produces `docs/status-dashboard.html`.
- [x] Zero drift detected between documents and `docs/STATUS.md`.

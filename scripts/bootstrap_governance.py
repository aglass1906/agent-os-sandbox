#!/usr/bin/env python3
"""Bootstrap Agent OS Documentation & Planning Governance into any repository.

Sets up:
1. Standard categorized documentation layout:
   docs/{templates,backlog,architecture,design-specs,adr,history/handoffs}
2. Canonical starter templates (Epic, Story, ADR, Design Spec, Handoff)
3. Document-driven status dashboard generator & slide-over Markdown reader
4. Makefile scaffolding targets (new-epic, new-story, new-adr, new-design-spec, new-handoff, dashboard, sync-status)
5. AI Agent governance rules (AGENTS.md)
6. Optional starter Epic 0 (Walking Skeleton)

Usage:
    python3 scripts/bootstrap_governance.py /path/to/target-repo --name "Project Name"
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]


def print_step(msg: str) -> None:
    print(f"\033[1;32m==>\033[0m {msg}")


def print_info(msg: str) -> None:
    print(f"    {msg}")


MAKEFILE_HEADER_TEMPLATE = """# __PROJECT_NAME__ — Makefile
.DEFAULT_GOAL := help

## Show this help menu of available commands.
help:
	@echo "__PROJECT_NAME__ — Makefile Commands:"
	@echo ""
	@awk '/^## / { \\
		if (helpMessage == "") { \\
			helpMessage = substr($$0, 4); \\
		} \\
	} \\
	/^[a-zA-Z\\-_0-9]+:/ { \\
		if (helpMessage != "") { \\
			helpCommand = substr($$1, 0, index($$1, ":")-1); \\
			printf "  %-16s %s\\n", helpCommand, helpMessage; \\
			helpMessage = ""; \\
		} \\
	}' $(MAKEFILE_LIST)
	@echo ""
"""

MAKEFILE_SNIPPET = """
# ------------------------------------------------------------------------------
# Documentation & Governance Scaffolding Targets
# ------------------------------------------------------------------------------

## Pull latest governance scripts and templates from GitHub and rebuild dashboard.
update-governance:
	python3 scripts/bootstrap_governance.py --update

## Regenerate docs/status-dashboard.html directly from canonical backlog documents.
dashboard:
	python3 scripts/generate_status_dashboard.py

## Reconcile docs/STATUS.md with the canonical story documents on disk (zero drift).
sync-status:
	python3 scripts/generate_status_dashboard.py --sync

## Audit backlog and epic documentation against canonical templates: make lint-docs [EPIC=30] [STATUS=in_progress] [TARGET=stories]
lint-docs:
	python3 scripts/reconcile_docs.py --check $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)

## Preview diff of proposed template reconciliation without touching disk: make diff-docs [EPIC=30] [STATUS=in_progress]
diff-docs:
	python3 scripts/reconcile_docs.py --dry-run $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)

## Reconcile backlog and epic documentation to match canonical templates: make sync-docs [EPIC=30] [STATUS=in_progress,planned]
sync-docs:
	python3 scripts/reconcile_docs.py --fix $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)

## Scaffold a new Epic directory & plan: make new-epic ID=1 SLUG=user-auth TITLE="User Authentication"
new-epic:
	@test -n "$(ID)" || (echo "Usage: make new-epic ID=<num> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-epic ID=<num> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \\
	mkdir -p docs/backlog/epic-$(ID)-$(SLUG)/stories; \\
	sed -e 's/EPIC-X/EPIC-$(ID)/g' \\
	    -e 's/Epic X/Epic $(ID)/g' \\
	    -e 's/\\[Initiative \\/ Capability Title\\]/$(TITLE)/g' \\
	    docs/templates/EPIC-TEMPLATE.md > docs/backlog/epic-$(ID)-$(SLUG)/EPIC-$(ID)-$$UPPER_SLUG.md; \\
	echo "Created docs/backlog/epic-$(ID)-$(SLUG)/EPIC-$(ID)-$$UPPER_SLUG.md and stories/ directory."

## Scaffold a new Story specification: make new-story EPIC_ID=1 STORY_NUM=1 SLUG=jwt-login TITLE="JWT Login"
new-story:
	@test -n "$(EPIC_ID)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@test -n "$(STORY_NUM)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-story EPIC_ID=<num> STORY_NUM=<subnum> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@TARGET_DIR=$$(find docs/backlog -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); \\
	if [ -z "$$TARGET_DIR" ]; then TARGET_DIR=$$(find docs/roadmap -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); fi; \\
	if [ -z "$$TARGET_DIR" ]; then echo "Epic directory for Epic $(EPIC_ID) not found in docs/backlog/"; exit 1; fi; \\
	EPIC_FOLDER=$$(basename "$$TARGET_DIR"); \\
	EPIC_FILE=$$(ls "$$TARGET_DIR" | grep '^EPIC-' | head -n 1); \\
	UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \\
	sed -e 's/STORY-X\\.Y/STORY-$(EPIC_ID).$(STORY_NUM)/g' \\
	    -e 's/Story X\\.Y/Story $(EPIC_ID).$(STORY_NUM)/g' \\
	    -e 's/EPIC-X/EPIC-$(EPIC_ID)/g' \\
	    -e 's/Epic X/Epic $(EPIC_ID)/g' \\
	    -e 's/\\[Story Title\\]/$(TITLE)/g' \\
	    -e "s|epic-X-NAME/EPIC-X-NAME\\.md|$$EPIC_FOLDER/$$EPIC_FILE|g" \\
	    -e "s|\\.\\./EPIC-X-NAME\\.md|\\.\\./$$EPIC_FILE|g" \\
	    docs/templates/STORY-TEMPLATE.md > "$$TARGET_DIR/stories/STORY-$(EPIC_ID).$(STORY_NUM)-$$UPPER_SLUG.md"; \\
	echo "Created $$TARGET_DIR/stories/STORY-$(EPIC_ID).$(STORY_NUM)-$$UPPER_SLUG.md"

## Scaffold a new Architecture Decision Record: make new-adr ID=1 SLUG=use-postgres TITLE="Use Postgres"
new-adr:
	@test -n "$(ID)" || (echo "Usage: make new-adr ID=<num> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@test -n "$(SLUG)" || (echo "Usage: make new-adr ID=<num> SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@PADDED_ID=$$(printf "%04d" $(ID)); \\
	LOWER_SLUG=$$(echo "$(SLUG)" | tr '[:upper:]' '[:lower:]'); \\
	TODAY=$$(date +%Y-%m-%d); \\
	sed -e "s/ADR-000X/ADR-$$PADDED_ID/g" \\
	    -e "s/ADR 000X/ADR $$PADDED_ID/g" \\
	    -e 's/\\[Short, Descriptive Title of Decision\\]/$(TITLE)/g' \\
	    -e "s/YYYY-MM-DD/$$TODAY/g" \\
	    docs/templates/ADR-TEMPLATE.md > docs/adr/$$PADDED_ID-$$LOWER_SLUG.md; \\
	echo "Created docs/adr/$$PADDED_ID-$$LOWER_SLUG.md"

## Scaffold a new Product Requirements Document: make new-prd SLUG=member-portal TITLE="Member Portal"
new-prd:
	@test -n "$(SLUG)" || (echo "Usage: make new-prd SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \\
	TODAY=$$(date +%Y-%m-%d); \\
	sed -e "s/PRD-\\[NAME\\]/PRD-$$UPPER_SLUG/g" \\
	    -e 's/\\[Product Initiative \\/ Feature Requirements\\]/$(TITLE)/g' \\
	    -e 's/\\[Initiative Name\\]/$(TITLE)/g' \\
	    -e "s/YYYY-MM-DD/$$TODAY/g" \\
	    docs/templates/PRD-TEMPLATE.md > docs/product/PRD-$$UPPER_SLUG.md; \\
	echo "Created docs/product/PRD-$$UPPER_SLUG.md"

## Scaffold a new Feature Design Spec: make new-design-spec SLUG=checkout-flow TITLE="Checkout Flow"
new-design-spec:
	@test -n "$(SLUG)" || (echo "Usage: make new-design-spec SLUG=<slug> TITLE=\\"<Title>\\"" && exit 1)
	@UPPER_SLUG=$$(echo "$(SLUG)" | tr '[:lower:]' '[:upper:]'); \\
	TODAY=$$(date +%Y-%m-%d); \\
	sed -e "s/SPEC-\\[NAME\\]/SPEC-$$UPPER_SLUG/g" \\
	    -e 's/\\[Feature \\/ Subsystem Design Specification\\]/$(TITLE)/g' \\
	    -e 's/\\[Feature Name\\]/$(TITLE)/g' \\
	    -e "s/YYYY-MM-DD/$$TODAY/g" \\
	    docs/templates/DESIGN-SPEC-TEMPLATE.md > docs/design-specs/$$UPPER_SLUG.md; \\
	echo "Created docs/design-specs/$$UPPER_SLUG.md"

## Scaffold a new Epic Handoff document: make new-handoff EPIC_ID=1
new-handoff:
	@test -n "$(EPIC_ID)" || (echo "Usage: make new-handoff EPIC_ID=<num>" && exit 1)
	@TARGET_DIR=$$(find docs/backlog -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); \\
	if [ -z "$$TARGET_DIR" ]; then TARGET_DIR=$$(find docs/roadmap -maxdepth 1 -type d -name "epic-$(EPIC_ID)-*" 2>/dev/null | head -n 1); fi; \\
	if [ -z "$$TARGET_DIR" ]; then echo "Epic directory for Epic $(EPIC_ID) not found in docs/backlog/"; exit 1; fi; \\
	EPIC_FOLDER=$$(basename "$$TARGET_DIR"); \\
	EPIC_FILE=$$(ls "$$TARGET_DIR" | grep '^EPIC-' | head -n 1); \\
	TODAY=$$(date +%Y-%m-%d); \\
	sed -e "s/HANDOFF-EPIC-X/HANDOFF-EPIC-$(EPIC_ID)/g" \\
	    -e "s/EPIC-X/EPIC-$(EPIC_ID)/g" \\
	    -e "s/Epic X/Epic $(EPIC_ID)/g" \\
	    -e "s|epic-X-NAME/EPIC-X-NAME\\.md|$$EPIC_FOLDER/$$EPIC_FILE|g" \\
	    -e "s/YYYY-MM-DD/$$TODAY/g" \\
	    docs/templates/HANDOFF-TEMPLATE.md > "docs/history/handoffs/HANDOFF-EPIC-$(EPIC_ID).md"; \\
	echo "Created docs/history/handoffs/HANDOFF-EPIC-$(EPIC_ID).md"

## Install GitHub PR template or scaffold PR completion note: make new-pr [OUT=.github/pull_request_template.md]
new-pr:
	@mkdir -p .github
	@if [ -n "$(OUT)" ]; then \\
		cp docs/templates/PR-TEMPLATE.md "$(OUT)"; \\
		echo "Created $(OUT)"; \\
	else \\
		cp docs/templates/PR-TEMPLATE.md .github/pull_request_template.md; \\
		echo "Installed .github/pull_request_template.md"; \\
	fi
"""

AGENTS_SNIPPET_TEMPLATE = """# __PROJECT_NAME__ — AI Coding Assistant & Documentation Governance Guide

Welcome! This document provides core architectural rules and documentation governance guidelines for AI coding assistants working in the **__PROJECT_NAME__** repository.

---

## 1. Work Breakdown Taxonomy (Epic → Story → Task)
All work decomposition strictly follows this hierarchy:
* **Epic**: Major architectural capability or subsystem initiative (e.g. `Epic 0`, `Epic 1`). Authored at `docs/backlog/epic-X-NAME/EPIC-X-NAME.md`.
* **Story**: Cohesive vertical slice delivering an independently testable operator/user benefit (e.g. `Story 1.1`). Scoped under its parent Epic. Each Story is authored as an independent machine-readable specification in `docs/backlog/epic-X-NAME/stories/STORY-X.Y-NAME.md`.
* **Task**: Concrete engineering work item (1 commit / 1 PR / 1 test file).
* 🚫 **PROHIBITION**: Never use "Slice", "Milestone", or ad-hoc sub-phase labels in roadmaps or status trackers. Always decompose Epics into numbered Stories (`Story X.1`, `Story X.2`), and Stories into concrete Tasks.

---

## 2. Document Scaffolding via Make
Always use `make` targets to scaffold new documents:
* **New PRD**: `make new-prd SLUG=<slug> TITLE="<Title>"`
* **New Epic**: `make new-epic ID=<num> SLUG=<slug> TITLE="<Title>"`
* **New Story**: `make new-story EPIC_ID=<num> STORY_NUM=<num> SLUG=<slug> TITLE="<Title>"`
* **New ADR**: `make new-adr ID=<num> SLUG=<slug> TITLE="<Title>"`
* **New Design Spec**: `make new-design-spec SLUG=<slug> TITLE="<Title>"`
* **New Handoff**: `make new-handoff EPIC_ID=<num>`
* **New PR / Completion Report**: `make new-pr`
* **Sync Tracker**: `make sync-status` (keeps `docs/STATUS.md` 100% in sync with disk)
* **Rebuild Dashboard**: `make dashboard` (rebuilds `docs/status-dashboard.html`)
* **Audit Docs**: `make lint-docs` (audits active specs against canonical templates)
* **Reconcile Docs**: `make sync-docs` (auto-aligns specs with templates non-destructively)

---

## 3. Directory Placement Rules
* **Product Requirements (PRDs)**: `docs/product/PRD-NAME.md`
* **Backlog & Stories**: `docs/backlog/epic-X-NAME/stories/STORY-X.Y-NAME.md`
* **Architecture Specifications**: `docs/architecture/XX-NAME.md`
* **Design Specs**: `docs/design-specs/FEATURE-NAME.md`
* **Architecture Decision Records**: `docs/adr/000X-NAME.md`
* **Session Handoffs**: `docs/history/handoffs/HANDOFF-EPIC-X.md`
* 🚫 **PROHIBITIONS**:
  - NEVER place new `.md` files in the repository root (`/`). Root is reserved for `README.md`, `AGENTS.md`, and build files.
  - NEVER place new `.md` files directly in `docs/` root (except living updates to `docs/STATUS.md`).
"""

STATUS_MD_TEMPLATE = """# __PROJECT_NAME__ — Epic & Story Status Tracker

> **Living checklist of what is done vs left.**
> Master Backlog / exit criteria stay in canonical plans in `docs/backlog/`.
> Work is strictly organized by Epic → Story → Task.

---

## Rollup

| Epic | Name | Status |
|---|---|---|
| 0 | Walking Skeleton | ✅ Done |

---

## Epic 0 — Walking Skeleton ✅
> Establish the initial repository structure, build automation, and documentation governance.

- [x] [**Story 0.1**](./backlog/epic-0-walking-skeleton/stories/STORY-0.1-REPOSITORY-INITIALIZATION.md): Repository initialization

"""

EPIC0_TEMPLATE = """---
id: EPIC-0
title: Walking Skeleton
type: epic-plan
status: completed
created: 2026-09-27
updated: 2026-09-27
surfaces:
  - core
stories_total: 1
stories_done: 1
---

# Epic 0 — Walking Skeleton

> **Status:** ✅ Completed
> **Canonical Plan:** this file
> **Master Backlog:** [`docs/STATUS.md`](../../STATUS.md)

## 1. Executive Summary & Goal
Establish the initial walking skeleton, project repository structure, build automation, and documentation governance.

## 2. Architecture Lineage & Invariants
- Minimal zero-dependency baseline.
- Automated verification via Makefile.

## 3. Story Breakdown & Acceptance Gates

| Story | Title | Status | Specification |
|---|---|---|---|
| [`Story 0.1`](./stories/STORY-0.1-REPOSITORY-INITIALIZATION.md) | Repository initialization | ✅ Completed | [`STORY-0.1`](./stories/STORY-0.1-REPOSITORY-INITIALIZATION.md) |

## 4. Verification & Testing Strategy
- Clean make build and status generation.
"""

STORY0_TEMPLATE = """---
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
Initialize the __PROJECT_NAME__ codebase with documentation governance, scaffolding tools, and an interactive status dashboard.

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
"""

README_STATUS_SNIPPET = """## 🚦 Roadmap & Living Status

- 📊 **Interactive Roadmap Dashboard**: [`docs/status-dashboard.html`](docs/status-dashboard.html) *(Open locally in your browser)*
- 📋 **Living Progress Tracker**: [`docs/STATUS.md`](docs/STATUS.md)
- 🤖 **AI Coding Assistant Guidelines**: [`AGENTS.md`](AGENTS.md)
- 📝 **Engineering Starter Templates**: [`docs/templates/`](docs/templates/)
"""

DOCS_ROOT_README_TEMPLATE = """# __PROJECT_NAME__ — Documentation Map & Master Hub

> **Quick Links:**
> - Living Roadmap Status & Checklist: [`STATUS.md`](./STATUS.md)
> - Interactive Visual Dashboard: [`status-dashboard.html`](./status-dashboard.html)
> - AI Assistant Operating Guide: [`../AGENTS.md`](../AGENTS.md)
> - Starter Engineering Templates: [`templates/`](templates/)

---

## 📁 Documentation Taxonomy & Category Indices

To maintain clarity and prevent merge contention across parallel AI coding sessions, the __PROJECT_NAME__ documentation tree is organized into dedicated categorical directories, each maintaining its own scoped index:

| Directory | Index | Scope & Purpose | Document Lifecycle |
|---|---|---|---|
| [`product/`](product/) | [`product/README.md`](product/README.md) | **Product Requirements & Strategy**<br>PRDs, MVP specifications, persona definitions, and business requirements. | **Living Product Specs**<br>Feature requirements & scope gates |
| [`backlog/`](backlog/) | [`backlog/README.md`](backlog/README.md) | **Epic Execution Plans & Backlog Stories**<br>Delivery sequence, platform capabilities, and machine-readable Story specifications. | **Backlog**<br>Active goals and epic execution plans |
| [`architecture/`](architecture/) | [`architecture/README.md`](architecture/README.md) | **Core Living Specifications**<br>System topology, data models, protocols, and security boundaries. | **Living**<br>Updated as code and architecture evolve |
| [`design-specs/`](design-specs/) | [`design-specs/README.md`](design-specs/README.md) | **Feature Design Specifications**<br>UX interaction flows, deep technical walkthroughs, UI layout plans, and component specs. | **Design Spec**<br>Feature and subsystem reference |
| [`adr/`](adr/) | [`adr/README.md`](adr/README.md) | **Architecture Decision Records**<br>Formal log of technical choices, design trade-offs, and architectural invariants. | **Immutable ADR**<br>Append-only decision log |
| [`history/`](history/) | [`history/README.md`](history/README.md) | **Historical Archives & Handoffs**<br>Milestone handoffs, canary test evidence, completion audits, and operator runbooks. | **Archived**<br>Read-only milestone records |
| [`user-guides/`](user-guides/) | [`user-guides/README.md`](user-guides/README.md) | **User & Developer Guides**<br>Task-oriented operational guides for operators and engineers. | **Living**<br>Matches current production behavior |
| [`templates/`](templates/) | [`templates/README.md`](templates/README.md) | **Starter Engineering Templates**<br>Canonical templates for PRDs, Epics, Stories, ADRs, Design Specs, and Handoffs. | **Living Standards**<br>Starter templates for new docs |

---

## 🧭 Navigation & AI Contributor Protocol

All AI coding assistants contributing to __PROJECT_NAME__ must adhere to the folder-level index governance in [`../AGENTS.md`](../AGENTS.md):
* **Placement**: Place new documents inside their appropriate categorical directory (`product/`, `backlog/`, `architecture/`, `design-specs/`, `adr/`, `history/`, or `user-guides/`).
* **Registration**: When creating or updating a document, update the corresponding `README.md` index inside that specific directory.
* **Prohibition**: Never place new standalone documentation files in the repository root or directly in `docs/` (except living updates to `STATUS.md`).
"""

PRODUCT_README_TEMPLATE = """# Product Requirements & Strategy Specifications (`docs/product/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Governance Standard:** [`../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md`](../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md)  
> **Status Policy:** **Living Product Specs** (Product Requirements Documents, MVP specifications, and user journey definitions)

This directory houses Product Requirements Documents (PRDs), MVP specifications, user journey maps, and business goals governing the platform. Each PRD defines the problem statement, persona workflows, prioritized requirements (P0/P1/P2), and explicit non-goals before work is decomposed into Epics and Stories in `docs/backlog/`.

---

## 🎯 Product Specifications

| Document | Type | Summary | Target Epic | Status |
|---|---|---|---|---|
| *(No PRDs recorded yet. Scaffold your first with `make new-prd SLUG=name TITLE="Feature Name"`)* | | | | |
"""

BACKLOG_README_TEMPLATE = """# Master Backlog & Epic Execution Plans (`docs/backlog/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Living Status Dashboard:** [`../STATUS.md`](../STATUS.md)  
> **Status Policy:** **Backlog** (Structured Epic blueprints and standalone Story specifications)

This directory organizes all project initiatives into dedicated Epic directories. Each Epic contains its primary execution plan (`EPIC-X-NAME.md`) and a `stories/` directory containing machine-readable, testable Story specifications (`STORY-X.Y-NAME.md`).

---

## 📦 Project Epics & Story Specifications

| Epic Directory | Title | Story Count | Story Specifications | Status |
|---|---|---|---|---|
__BACKLOG_EPIC_ROWS__
"""

ARCHITECTURE_README_TEMPLATE = """# Core Architecture Specifications (`docs/architecture/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Status Policy:** **Living** (Must be maintained and updated as code and contracts evolve)

This directory contains foundational technical specifications, system invariants, security boundaries, and protocol contracts governing __PROJECT_NAME__.

---

## 📚 Architecture Documents

| Document | Summary | Status |
|---|---|---|
| *(No architecture documents yet. Add your first spec here)* | | |
"""

DESIGN_SPECS_README_TEMPLATE = """# Feature Design Specs & Technical Walkthroughs (`docs/design-specs/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Status Policy:** **Design Spec** (Living feature specifications and technical walkthroughs)

This directory contains feature specifications, UX interaction designs, technical walkthroughs, and UI layout plans.

---

## 🎨 Feature Design Specifications

| Document | Category | Summary | Related Epic |
|---|---|---|---|
| *(No design specs yet. Scaffold your first with `make new-design-spec SLUG=name TITLE="Feature Name"`)* | | | |
"""

ADR_README_TEMPLATE = """# Architecture Decision Records (`docs/adr/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Status Policy:** **Immutable ADR** (Append-only historical record of foundational technical decisions)

This directory contains the formal log of fundamental architecture decisions, design trade-offs, and invariants.

---

## 🏛️ Architecture Decision Log

| Number | Document | Decision Summary | Status |
|---|---|---|---|
| *(No ADRs recorded yet. Scaffold your first with `make new-adr ID=1 SLUG=decision-title TITLE="Decision Title"`)* | | | |
"""

HISTORY_README_TEMPLATE = """# Historical Archives & Handoffs (`docs/history/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Status Policy:** **Archived** (Read-only historical snapshots, handoff records, canary audits, and operator runbooks)

This directory preserves epic transition handoffs, evidence runs, completion audits, and operator runbooks across development milestones.

---

## 📦 Implementation Handoffs (`handoffs/`)

| Document | Epic / Scope | Summary |
|---|---|---|
| *(No handoffs archived yet. Scaffold one with `make new-handoff EPIC_ID=1`)* | | |
"""

USER_GUIDES_README_TEMPLATE = """# User & Developer Guides (`docs/user-guides/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Status Policy:** **Living** (Must match current application capabilities and developer workflows)

This directory contains task-oriented operational guides, workflows, and walkthroughs for users, developers, and operators.

---

## 📖 Available Guides

| Guide | Audience / Domain | Summary |
|---|---|---|
| [`STATUS-DASHBOARD.md`](./STATUS-DASHBOARD.md) | AI Agents, Developers & Operators | Interactive visual roadmap dashboard generator, zero-drift synchronization, and CLI reference |
| [`MAKEFILE-COMMANDS.md`](./MAKEFILE-COMMANDS.md) | AI Agents, Architects & Developers | Complete reference guide for documentation scaffolding, governance, anti-drift, and dashboard Makefile targets |
"""


def analyze_project(
    target: Path,
    project_name: str,
    init_epic0: bool,
    update_readme: bool = True,
) -> None:
    target = target.resolve()
    print("\n" + "=" * 80)
    print("  \033[1;36mAgent OS Documentation & Planning Governance — Impact Analysis (Dry Run)\033[0m")
    print("=" * 80)
    print(f"  Target Repository: \033[1m{target}\033[0m")
    print(f"  Project Title:     \033[1m{project_name}\033[0m")
    print(f"  Starter Epic 0:    {'Scaffold Walking Skeleton' if init_epic0 else 'Omit (--no-epic0)'}")
    print(f"  Root README Links: {'Update with status section' if update_readme else 'Omit (--no-readme)'}")
    print("=" * 80 + "\n")

    if not target.exists():
        print("  \033[1;33m[!] Target directory does not exist yet. It will be initialized as a new folder.\033[0m\n")

    # 1. Directories
    print("\033[1;34m📁 1. Directory Structure Plan:\033[0m")
    dirs = [
        "docs/product",
        "docs/templates",
        "docs/backlog",
        "docs/architecture",
        "docs/design-specs",
        "docs/adr",
        "docs/history/handoffs",
        "docs/user-guides",
        "scripts",
    ]
    for d in dirs:
        dp = target / d
        if dp.exists():
            print(f"   \033[0;32m✓\033[0m {d}/ (already exists)")
        else:
            print(f"   \033[1;32m+\033[0m {d}/ (will be created)")

    # 2. Files to be Created (New)
    print("\n\033[1;34m📄 2. Files to be CREATED (New):\033[0m")
    created_count = 0

    makefile = target / "Makefile"
    if not makefile.exists():
        print("   \033[1;32m+\033[0m Makefile (New file with help, dashboard, sync-status, and scaffolding targets)")
        created_count += 1

    print("   \033[1;32m+\033[0m scripts/generate_status_dashboard.py (Status synchronizer & dashboard generator)")
    print("   \033[1;32m+\033[0m scripts/reconcile_docs.py (Template reconciler & drift linter)")
    print("   \033[1;32m+\033[0m docs/status-dashboard.template.html (Customized dashboard HTML template)")
    print("   \033[1;32m+\033[0m docs/status-dashboard.html (Zero-dependency visual dashboard compiled from disk)")
    created_count += 4

    dash_guide = target / "docs" / "user-guides" / "STATUS-DASHBOARD.md"
    if not dash_guide.exists():
        print("   \033[1;32m+\033[0m docs/user-guides/STATUS-DASHBOARD.md (Status dashboard user guide & CLI reference)")
        created_count += 1

    makefile_guide = target / "docs" / "user-guides" / "MAKEFILE-COMMANDS.md"
    if not makefile_guide.exists():
        print("   \033[1;32m+\033[0m docs/user-guides/MAKEFILE-COMMANDS.md (Makefile & scaffolding commands reference guide)")
        created_count += 1

    reconcile_guide = target / "docs" / "user-guides" / "DOCUMENTATION-RECONCILIATION-RUNBOOK.md"
    if not reconcile_guide.exists():
        print("   \033[1;32m+\033[0m docs/user-guides/DOCUMENTATION-RECONCILIATION-RUNBOOK.md (Template reconciliation runbook)")
        created_count += 1



    status_md = target / "docs" / "STATUS.md"
    if not status_md.exists():
        print("   \033[1;32m+\033[0m docs/STATUS.md (Initial living checklist tracker)")
        created_count += 1

    templates = [
        "docs/templates/PRD-TEMPLATE.md",
        "docs/templates/EPIC-TEMPLATE.md",
        "docs/templates/STORY-TEMPLATE.md",
        "docs/templates/ADR-TEMPLATE.md",
        "docs/templates/DESIGN-SPEC-TEMPLATE.md",
        "docs/templates/HANDOFF-TEMPLATE.md",
        "docs/templates/PR-TEMPLATE.md",
        "docs/templates/README.md",
    ]
    for t in templates:
        tp = target / t
        if not tp.exists():
            print(f"   \033[1;32m+\033[0m {t}")
            created_count += 1

    indices = [
        "docs/README.md",
        "docs/product/README.md",
        "docs/backlog/README.md",
        "docs/architecture/README.md",
        "docs/design-specs/README.md",
        "docs/adr/README.md",
        "docs/history/README.md",
        "docs/user-guides/README.md",
    ]
    for idx in indices:
        ip = target / idx
        if not ip.exists():
            print(f"   \033[1;32m+\033[0m {idx} (Category index table)")
            created_count += 1

    if init_epic0:
        print("   \033[1;32m+\033[0m docs/backlog/epic-0-walking-skeleton/EPIC-0-WALKING-SKELETON.md")
        print("   \033[1;32m+\033[0m docs/backlog/epic-0-walking-skeleton/stories/STORY-0.1-REPOSITORY-INITIALIZATION.md")
        created_count += 2

    # 3. Files to be Modified
    print("\n\033[1;34m✏️  3. Files to be MODIFIED (Non-destructive appends):\033[0m")
    modified_count = 0

    if makefile.exists():
        mf_content = makefile.read_text(encoding="utf-8")
        if "generate_status_dashboard.py" not in mf_content:
            print("   \033[1;33m~\033[0m Makefile (Preserves existing targets; appends 8 governance & scaffolding targets)")
            modified_count += 1
        else:
            print("   \033[0;32m✓\033[0m Makefile (Already contains governance targets; no changes)")

    agents_md = target / "AGENTS.md"
    if agents_md.exists():
        ag_content = agents_md.read_text(encoding="utf-8")
        line_count = len(ag_content.splitlines())
        if "Work Breakdown Taxonomy" not in ag_content:
            print(f"   \033[1;33m~\033[0m AGENTS.md (Preserves {line_count} existing lines; appends AI governance rules to bottom)")
            modified_count += 1
        else:
            print("   \033[0;32m✓\033[0m AGENTS.md (Already contains governance rules; no changes)")
    else:
        print("   \033[1;32m+\033[0m AGENTS.md (New AI coding assistant governance guide)")
        created_count += 1

    if update_readme:
        readme_md = target / "README.md"
        if readme_md.exists():
            rm_content = readme_md.read_text(encoding="utf-8")
            if "status-dashboard.html" not in rm_content and "STATUS.md" not in rm_content:
                print("   \033[1;33m~\033[0m README.md (Preserves existing content; appends Roadmap & Living Status links)")
                modified_count += 1
            else:
                print("   \033[0;32m✓\033[0m README.md (Already references status dashboard; no changes)")
        else:
            print("   \033[1;32m+\033[0m README.md (New project overview with Roadmap & Living Status links)")
            created_count += 1
    else:
        print("   \033[0;37m-\033[0m README.md (Skipped via --no-readme)")

    # 4. Existing Content Preserved
    print("\n\033[1;34m🛡️  4. Existing Content That Will Remain Untouched:\033[0m")
    prod_dir = target / "docs" / "product"
    if prod_dir.exists():
        existing_prods = [f.name for f in prod_dir.glob("*.md") if f.name != "README.md"]
        if existing_prods:
            print(f"   \033[0;32m✓\033[0m {len(existing_prods)} existing product spec(s) in docs/product/ ({', '.join(existing_prods[:3])}{'...' if len(existing_prods) > 3 else ''})")

    adr_dir = target / "docs" / "adr"
    if adr_dir.exists():
        existing_adrs = [f.name for f in adr_dir.glob("*.md") if f.name != "README.md"]
        if existing_adrs:
            print(f"   \033[0;32m✓\033[0m {len(existing_adrs)} existing ADR(s) in docs/adr/ ({', '.join(existing_adrs[:3])}{'...' if len(existing_adrs) > 3 else ''})")

    arch_dir = target / "docs" / "architecture"
    if arch_dir.exists():
        existing_arch = [f.name for f in arch_dir.glob("*.md") if f.name != "README.md"]
        if existing_arch:
            print(f"   \033[0;32m✓\033[0m {len(existing_arch)} existing architecture spec(s) in docs/architecture/ ({', '.join(existing_arch[:3])})")

    docs_dir = target / "docs"
    if docs_dir.exists():
        standard_subdirs = {"templates", "product", "backlog", "architecture", "design-specs", "adr", "history", "user-guides"}
        custom_subdirs = [d.name for d in docs_dir.iterdir() if d.is_dir() and d.name not in standard_subdirs]
        if custom_subdirs:
            print(f"   \033[0;32m✓\033[0m {len(custom_subdirs)} existing custom doc folder(s) ({', '.join(custom_subdirs[:4])}{'...' if len(custom_subdirs) > 4 else ''})")

    print("   \033[0;32m✓\033[0m All application source code, package configurations, tests, and database models")

    print("\n" + "=" * 80)
    print(f"  \033[1;32mAnalysis Complete:\033[0m {created_count} file(s) to create, {modified_count} file(s) to safely append.")
    print("  \033[1;33mNo files were modified. This was a dry-run analysis.\033[0m")
    print("  To apply these changes, run the command without --analyze (or without --dry-run).")
    print("=" * 80 + "\n")


def bootstrap_project(
    target: Path,
    project_name: str,
    init_epic0: bool,
    update_readme: bool = True,
) -> None:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    print_step(f"Bootstrapping documentation governance into: {target}")
    print_info(f"Project Name: {project_name}")

    # 1. Scaffolding directories
    dirs = [
        "docs/product",
        "docs/templates",
        "docs/backlog",
        "docs/architecture",
        "docs/design-specs",
        "docs/adr",
        "docs/history/handoffs",
        "docs/user-guides",
        "scripts",
    ]
    for d in dirs:
        (target / d).mkdir(parents=True, exist_ok=True)
    print_step("Created standard categorized directories in docs/")

    # 1b. Category Index READMEs
    epic0_row = (
        "| [`epic-0-walking-skeleton`](./epic-0-walking-skeleton/EPIC-0-WALKING-SKELETON.md) | **Walking Skeleton** | 1 stories | [`stories/`](./epic-0-walking-skeleton/stories/) | ✅ Completed |"
        if init_epic0
        else "| *(No Epics created yet. Scaffold your first with `make new-epic ID=1 SLUG=core TITLE=\"Core Feature\"`)* | | | | |"
    )

    indices = [
        ("docs/README.md", DOCS_ROOT_README_TEMPLATE),
        ("docs/product/README.md", PRODUCT_README_TEMPLATE),
        ("docs/backlog/README.md", BACKLOG_README_TEMPLATE.replace("__BACKLOG_EPIC_ROWS__", epic0_row)),
        ("docs/architecture/README.md", ARCHITECTURE_README_TEMPLATE),
        ("docs/design-specs/README.md", DESIGN_SPECS_README_TEMPLATE),
        ("docs/adr/README.md", ADR_README_TEMPLATE),
        ("docs/history/README.md", HISTORY_README_TEMPLATE),
        ("docs/user-guides/README.md", USER_GUIDES_README_TEMPLATE),
    ]

    for rel_path, tmpl in indices:
        idx_path = target / rel_path
        if not idx_path.exists():
            idx_path.write_text(tmpl.replace("__PROJECT_NAME__", project_name), encoding="utf-8")
            print_step(f"Created category index {rel_path}")
        else:
            print_info(f"{rel_path} already exists (preserving).")

    # 2. Copy templates
    templates = [
        "PRD-TEMPLATE.md",
        "EPIC-TEMPLATE.md",
        "STORY-TEMPLATE.md",
        "ADR-TEMPLATE.md",
        "DESIGN-SPEC-TEMPLATE.md",
        "HANDOFF-TEMPLATE.md",
        "PR-TEMPLATE.md",
        "README.md",
    ]
    for t in templates:
        src = SOURCE_ROOT / "docs" / "templates" / t
        dst = target / "docs" / "templates" / t
        if src.exists():
            shutil.copy2(src, dst)
    print_step("Copied canonical starter templates to docs/templates/")

    # 3. Copy dashboard tools and governance engines
    dash_script = SOURCE_ROOT / "scripts" / "generate_status_dashboard.py"
    shutil.copy2(dash_script, target / "scripts" / "generate_status_dashboard.py")
    (target / "scripts" / "generate_status_dashboard.py").chmod(0o755)

    reconcile_script = SOURCE_ROOT / "scripts" / "reconcile_docs.py"
    if reconcile_script.exists():
        shutil.copy2(reconcile_script, target / "scripts" / "reconcile_docs.py")
        (target / "scripts" / "reconcile_docs.py").chmod(0o755)

    dash_template_src = SOURCE_ROOT / "docs" / "status-dashboard.template.html"
    dash_html_content = dash_template_src.read_text(encoding="utf-8")
    dash_html_content = dash_html_content.replace(
        "<title>Agent OS — Status Dashboard</title>",
        f"<title>{project_name} — Status Dashboard</title>",
    ).replace(
        "<h1>Agent OS</h1>",
        f"<h1>{project_name}</h1>",
    )
    (target / "docs" / "status-dashboard.template.html").write_text(
        dash_html_content, encoding="utf-8"
    )

    dash_guide_src = SOURCE_ROOT / "docs" / "user-guides" / "STATUS-DASHBOARD.md"
    if dash_guide_src.exists():
        dash_guide_dst = target / "docs" / "user-guides" / "STATUS-DASHBOARD.md"
        dash_guide_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dash_guide_src, dash_guide_dst)

    makefile_guide_src = SOURCE_ROOT / "docs" / "user-guides" / "MAKEFILE-COMMANDS.md"
    if makefile_guide_src.exists():
        makefile_guide_dst = target / "docs" / "user-guides" / "MAKEFILE-COMMANDS.md"
        makefile_guide_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(makefile_guide_src, makefile_guide_dst)

    reconcile_guide_src = SOURCE_ROOT / "docs" / "user-guides" / "DOCUMENTATION-RECONCILIATION-RUNBOOK.md"
    if reconcile_guide_src.exists():
        reconcile_guide_dst = target / "docs" / "user-guides" / "DOCUMENTATION-RECONCILIATION-RUNBOOK.md"
        reconcile_guide_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reconcile_guide_src, reconcile_guide_dst)

    print_step("Installed status dashboard generator, reconciliation engine, templates, and user guides")

    # 4. Makefile setup
    makefile_path = target / "Makefile"
    if not makefile_path.exists():
        initial_makefile = MAKEFILE_HEADER_TEMPLATE.replace("__PROJECT_NAME__", project_name) + "\n" + MAKEFILE_SNIPPET
        makefile_path.write_text(initial_makefile, encoding="utf-8")
        print_step("Created new Makefile with help menu and scaffolding targets")
    else:
        existing_content = makefile_path.read_text(encoding="utf-8")
        if "generate_status_dashboard.py" not in existing_content:
            makefile_path.write_text(
                existing_content.rstrip() + "\n" + MAKEFILE_SNIPPET,
                encoding="utf-8",
            )
            print_step("Appended scaffolding & dashboard targets to existing Makefile")
        else:
            print_info("Makefile already contains governance scaffolding targets.")

    # 5. AGENTS.md setup
    agents_path = target / "AGENTS.md"
    agents_snippet = AGENTS_SNIPPET_TEMPLATE.replace("__PROJECT_NAME__", project_name)
    if not agents_path.exists():
        agents_path.write_text(agents_snippet, encoding="utf-8")
        print_step("Created AGENTS.md with documentation governance instructions")
    else:
        existing_agents = agents_path.read_text(encoding="utf-8")
        if "Work Breakdown Taxonomy" not in existing_agents:
            agents_path.write_text(
                existing_agents.rstrip() + "\n\n" + agents_snippet,
                encoding="utf-8",
            )
            print_step("Appended documentation governance rules to existing AGENTS.md")

    # 6. README.md setup (link to dashboard & status)
    if update_readme:
        readme_path = target / "README.md"
        if not readme_path.exists():
            initial_readme = f"# {project_name}\n\n{README_STATUS_SNIPPET}\n"
            readme_path.write_text(initial_readme, encoding="utf-8")
            print_step("Created README.md with Roadmap & Living Status links")
        else:
            existing_readme = readme_path.read_text(encoding="utf-8")
            if "status-dashboard.html" not in existing_readme and "STATUS.md" not in existing_readme:
                readme_path.write_text(
                    existing_readme.rstrip() + "\n\n---\n\n" + README_STATUS_SNIPPET + "\n",
                    encoding="utf-8",
                )
                print_step("Appended Roadmap & Living Status links to existing README.md")
            else:
                print_info("README.md already references status-dashboard or STATUS.md.")

    # 7. Starter Epic 0 (optional)
    if init_epic0:
        epic0_dir = target / "docs" / "backlog" / "epic-0-walking-skeleton"
        stories_dir = epic0_dir / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)

        epic0_file = epic0_dir / "EPIC-0-WALKING-SKELETON.md"
        if not epic0_file.exists():
            epic0_file.write_text(EPIC0_TEMPLATE, encoding="utf-8")

        story0_file = stories_dir / "STORY-0.1-REPOSITORY-INITIALIZATION.md"
        if not story0_file.exists():
            story0_file.write_text(STORY0_TEMPLATE.replace("__PROJECT_NAME__", project_name), encoding="utf-8")
        print_step("Scaffolded starter Epic 0 (Walking Skeleton)")

    # 8. Initial STATUS.md
    status_path = target / "docs" / "STATUS.md"
    if not status_path.exists():
        status_path.write_text(STATUS_MD_TEMPLATE.replace("__PROJECT_NAME__", project_name), encoding="utf-8")
        print_step("Created initial docs/STATUS.md")

    # 9. Run sync & dashboard generator in target
    print_step("Running initial sync and dashboard generation...")
    subprocess.run(
        [sys.executable, str(target / "scripts" / "generate_status_dashboard.py"), "--sync"],
        cwd=target,
        check=True,
    )

    print("\n\033[1;32m🎉 Successfully bootstrapped documentation & governance!\033[0m")
    print(f"To view the dashboard:\n    open {target / 'docs' / 'status-dashboard.html'}\n")
    print(f"To scaffold new work:\n    cd {target}\n    make new-epic ID=1 SLUG=core TITLE=\"Core Subsystem\"\n")


CANONICAL_GOVERNANCE_FILES = [
    "scripts/bootstrap_governance.py",
    "scripts/generate_status_dashboard.py",
    "scripts/reconcile_docs.py",
    "docs/status-dashboard.template.html",
    "docs/templates/PRD-TEMPLATE.md",
    "docs/templates/EPIC-TEMPLATE.md",
    "docs/templates/STORY-TEMPLATE.md",
    "docs/templates/ADR-TEMPLATE.md",
    "docs/templates/DESIGN-SPEC-TEMPLATE.md",
    "docs/templates/HANDOFF-TEMPLATE.md",
    "docs/templates/PR-TEMPLATE.md",
    "docs/templates/README.md",
    "docs/user-guides/STATUS-DASHBOARD.md",
    "docs/user-guides/MAKEFILE-COMMANDS.md",
    "docs/user-guides/DOCUMENTATION-RECONCILIATION-RUNBOOK.md",
]


def extract_canonical_files(content: str) -> list[str]:
    match = re.search(r"CANONICAL_GOVERNANCE_FILES\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if not match:
        return []
    items: list[str] = []
    for line in match.group(1).splitlines():
        line = line.strip().strip(",").strip("\"'")
        if line and not line.startswith("#"):
            items.append(line)
    return items


def get_github_auth_token() -> str | None:
    # 1. gh CLI if authenticated
    try:
        clean_env = os.environ.copy()
        clean_env.pop("GH_TOKEN", None)
        out = subprocess.check_output(
            ["gh", "auth", "token"],
            env=clean_env,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        ).strip()
        if out and out.startswith(("gho_", "ghp_", "github_pat_")):
            return out
    except Exception:
        pass

    # 2. git credential fill
    try:
        clean_env = os.environ.copy()
        clean_env.pop("GH_TOKEN", None)
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=clean_env,
        )
        stdout, _ = proc.communicate("protocol=https\nhost=github.com\n", timeout=3)
        for line in stdout.splitlines():
            if line.startswith("password="):
                token = line.split("=", 1)[1].strip()
                if token and token.startswith(("gho_", "ghp_", "github_pat_")):
                    return token
    except Exception:
        pass

    # 3. Ambient env var if valid
    for env_var in ("GITHUB_TOKEN", "GH_TOKEN"):
        t = os.environ.get(env_var, "").strip()
        if t and t.startswith(("gho_", "ghp_", "github_pat_")):
            return t

    return None


def update_governance(
    target: Path,
    remote: str = "aglass1906/agent-os",
    branch: str = "master",
    source: Path | None = None,
) -> None:
    target = target.resolve()
    print_step(f"Updating governance tooling in: {target}")

    files_to_sync = list(CANONICAL_GOVERNANCE_FILES)

    if source:
        source = source.resolve()
        print_info(f"Source: Local directory ({source})")
        src_bootstrap = source / "scripts" / "bootstrap_governance.py"
        if src_bootstrap.exists():
            for rf in extract_canonical_files(src_bootstrap.read_text(encoding="utf-8")):
                if rf not in files_to_sync:
                    files_to_sync.append(rf)
        for rel_str in files_to_sync:
            src_file = source / rel_str
            dst_file = target / rel_str
            if src_file.exists():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print_info(f"✓ Copied {rel_str}")
            else:
                print_info(f"⚠ Warning: {rel_str} not found in local source {source}")
    else:
        print_info(f"Source: GitHub (https://github.com/{remote}/tree/{branch})")
        import urllib.error
        import urllib.request

        base_url = f"https://raw.githubusercontent.com/{remote}/{branch}/"
        headers = {"User-Agent": "agent-os-bootstrap/1.0"}
        token = get_github_auth_token()
        if token:
            headers["Authorization"] = f"token {token}"

        # Resolve latest commit SHA to bypass 5-minute CDN branch caching on raw.githubusercontent.com
        target_ref = branch
        try:
            sha_url = f"https://api.github.com/repos/{remote}/commits/{branch}"
            sha_req = urllib.request.Request(
                sha_url,
                headers={**headers, "Accept": "application/vnd.github.sha"},
            )
            with urllib.request.urlopen(sha_req, timeout=5) as resp:
                if resp.status == 200:
                    sha_text = resp.read().decode("utf-8").strip()
                    if len(sha_text) == 40:
                        target_ref = sha_text
                        print_info(f"Latest commit: {target_ref[:7]}")
        except Exception:
            pass

        base_url = f"https://raw.githubusercontent.com/{remote}/{target_ref}/"

        self_updated = False
        updated_count = 0
        idx = 0
        while idx < len(files_to_sync):
            rel_str = files_to_sync[idx]
            idx += 1
            file_url = base_url + rel_str
            dst_file = target / rel_str
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(file_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        dst_file.write_bytes(content)
                        if rel_str.endswith(".py"):
                            st = dst_file.stat()
                            dst_file.chmod(st.st_mode | 0o111)
                        print_info(f"✓ Updated {rel_str}")
                        updated_count += 1

                        # Dynamically discover any newly added canonical files from the latest bootstrap script
                        if rel_str == "scripts/bootstrap_governance.py":
                            self_updated = True
                            try:
                                remote_files = extract_canonical_files(content.decode("utf-8"))
                                for rf in remote_files:
                                    if rf not in files_to_sync:
                                        files_to_sync.append(rf)
                            except Exception:
                                pass
                    else:
                        print_info(f"⚠ Failed to download {rel_str}: HTTP {resp.status}")
            except Exception as e:
                print_info(f"⚠ Error downloading {rel_str}: {e}")

        # If HTTP download failed (e.g. auth issue on private repo), fallback to git shallow clone
        if updated_count < len(files_to_sync):
            print_info("Attempting ephemeral git clone fallback...")
            import tempfile
            with tempfile.TemporaryDirectory(prefix="agentos-gov-sync-") as tmpdir:
                clean_env = os.environ.copy()
                clean_env.pop("GH_TOKEN", None)
                repo_url = f"https://github.com/{remote}.git"
                try:
                    subprocess.run(
                        ["git", "clone", "--depth", "1", "--branch", branch, repo_url, tmpdir],
                        env=clean_env,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    tmp_path = Path(tmpdir)
                    clone_bootstrap = tmp_path / "scripts" / "bootstrap_governance.py"
                    if clone_bootstrap.exists():
                        for rf in extract_canonical_files(clone_bootstrap.read_text(encoding="utf-8")):
                            if rf not in files_to_sync:
                                files_to_sync.append(rf)
                    for rel_str in files_to_sync:
                        src_file = tmp_path / rel_str
                        dst_file = target / rel_str
                        if src_file.exists():
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)
                            if rel_str.endswith(".py"):
                                st = dst_file.stat()
                                dst_file.chmod(st.st_mode | 0o111)
                            print_info(f"✓ Synced {rel_str} via git")
                            updated_count += 1
                except Exception as e:
                    print_info(f"⚠ Git fallback error: {e}")
        print_step(f"Refreshed {updated_count}/{len(files_to_sync)} canonical files from GitHub.")

        # If bootstrap_governance.py was updated and hasn't re-executed yet, reload so new post-sync logic runs immediately
        if self_updated and not os.environ.get("_AGENTOS_BOOTSTRAP_REEXEC"):
            os.environ["_AGENTOS_BOOTSTRAP_REEXEC"] = "1"
            os.execv(sys.executable, [sys.executable] + sys.argv)

    # Ensure target Makefile has latest governance targets
    makefile_path = target / "Makefile"
    if makefile_path.exists():
        mf_content = makefile_path.read_text(encoding="utf-8")
        missing_targets = []
        if "update-governance:" not in mf_content:
            missing_targets.append("""
## Pull latest governance scripts and templates from GitHub and rebuild dashboard.
update-governance:
	python3 scripts/bootstrap_governance.py --update
""")
        if "lint-docs:" not in mf_content:
            missing_targets.append("""
## Audit backlog and epic documentation against canonical templates: make lint-docs [EPIC=30] [STATUS=in_progress] [TARGET=stories]
lint-docs:
	python3 scripts/reconcile_docs.py --check $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)
""")
        if "diff-docs:" not in mf_content:
            missing_targets.append("""
## Preview diff of proposed template reconciliation without touching disk: make diff-docs [EPIC=30] [STATUS=in_progress]
diff-docs:
	python3 scripts/reconcile_docs.py --dry-run $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)
""")
        if "sync-docs:" not in mf_content:
            missing_targets.append("""
## Reconcile backlog and epic documentation to match canonical templates: make sync-docs [EPIC=30] [STATUS=in_progress,planned]
sync-docs:
	python3 scripts/reconcile_docs.py --fix $(if $(STATUS),--status $(STATUS),) $(if $(EPIC),--epic $(EPIC),) $(if $(EPICS),--epics $(EPICS),) $(if $(TARGET),--target $(TARGET),)
""")
        if missing_targets:
            makefile_path.write_text(mf_content.rstrip() + "\n" + "".join(missing_targets), encoding="utf-8")
            print_step(f"Appended {len(missing_targets)} missing governance targets to Makefile")

    # Run dashboard generator in target
    generator_script = target / "scripts" / "generate_status_dashboard.py"
    if generator_script.exists():
        print_step("Regenerating docs/status-dashboard.html with updated generator...")
        subprocess.run(
            [sys.executable, str(generator_script)],
            cwd=target,
            check=True,
        )

    print("\n\033[1;32m🎉 Successfully updated governance tooling & status dashboard!\033[0m")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap or update Agent OS documentation and governance into any target repository."
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Path to the target repository or directory (defaults to current working directory).",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Pull and update governance scripts and templates from GitHub without touching project backlog or documents.",
    )
    parser.add_argument(
        "--remote",
        type=str,
        default="aglass1906/agent-os",
        help="GitHub repository to pull updates from in format 'owner/repo' (default: aglass1906/agent-os).",
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="master",
        help="Git branch to fetch from GitHub (default: master).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional local path to source agent-os repo instead of pulling from GitHub.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Project name (defaults to the target folder name).",
    )
    parser.add_argument(
        "--no-epic0",
        action="store_true",
        help="Do not scaffold starter Epic 0.",
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Do not modify or create root README.md with status links.",
    )
    parser.add_argument(
        "--analyze",
        "--dry-run",
        action="store_true",
        help="Analyze target repository and print a preview of planned changes without modifying any files.",
    )
    args = parser.parse_args()

    if args.update:
        update_governance(args.target, remote=args.remote, branch=args.branch, source=args.source)
        return 0

    project_name = args.name or args.target.name.replace("-", " ").replace("_", " ").title()
    if args.analyze:
        analyze_project(args.target, project_name, not args.no_epic0, not args.no_readme)
    else:
        bootstrap_project(args.target, project_name, not args.no_epic0, not args.no_readme)
    return 0


if __name__ == "__main__":
    sys.exit(main())

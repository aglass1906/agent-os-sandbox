# Status Dashboard & Roadmap Generator Guide

> **Audience:** AI Agents, Software Architects, Engineering Leads & Developers  
> **Index Level:** User & Operator Guides (`docs/user-guides/`)  
> **Master Index:** [`docs/README.md`](../README.md)  
> **Governance Standard:** [`docs/architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md`](../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md)  
> **Operating Guide:** [`AGENTS.md`](../../AGENTS.md)

This guide documents the **Agent OS Status Dashboard Generator** (`scripts/generate_status_dashboard.py`), its document-driven ingestion architecture, zero-drift synchronization, interactive UI capabilities, and distribution workflows across repositories.

---

## 1. Executive Summary & Core Purpose

In large software projects and AI-assisted workflows, roadmap spreadsheets, issue trackers, and hand-edited status documents frequently fall out of sync with actual codebase specifications.

The **Status Dashboard Generator** solves this problem by treating the **filesystem specifications as the single source of truth**:
1. **Document-Driven Ingestion**: It directly parses structured YAML frontmatter and Markdown sections from Epic execution plans, Story specs, PRDs, Design Specs, and ADRs.
2. **Zero-Drift Synchronization (`make sync-status`)**: It reconciles living checklist tracking (`docs/STATUS.md`) against specifications on disk, ensuring checkboxes (`[x]` vs `[ ]`) and titles match reality.
3. **Standalone Offline Visualization (`docs/status-dashboard.html`)**: It generates a portable, zero-dependency HTML dashboard featuring instant search, status filtering, progress metrics, and a slide-over Markdown reader drawer.
4. **Autonomous Governance & Portability**: It distributes seamlessly to any repository via `scripts/bootstrap_governance.py` and stays up to date via `make update-governance`.

```text
 ┌────────────────────────────────────────────────────────┐
 │              CANONICAL SPECIFICATIONS                  │
 │  docs/backlog/epic-X-NAME/                             │
 │    ├── EPIC-X-NAME.md                                  │
 │    └── stories/STORY-X.Y-NAME.md  (YAML Frontmatter)   │
 │  docs/product/PRD-*.md                                 │
 │  docs/design-specs/*.md                                │
 │  docs/adr/*.md                                         │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
         scripts/generate_status_dashboard.py
            ├── --sync       ──► Reconciles docs/STATUS.md
            ├── --check-only ──► CI Drift Detection (Exit 0 or 1)
            └── (default)    ──► Injects JSON data into template
                             │
                             ▼
           docs/status-dashboard.html
      (Interactive, Searchable, Offline Dashboard)
```

---

## 2. Ingestion Pipeline & Data Architecture

The generator requires **no external database or runtime service**; it uses Python's standard library to inspect the repository hierarchy:

### Ingested Sources

| Source Directory | File Pattern | Extracted Attributes |
|---|---|---|
| **Backlog Epics** | `docs/backlog/epic-*/EPIC-*.md` | Epic ID, Title, Status, Executive Summary, Lineage (`design_spec`, `adrs`) |
| **Backlog Stories** | `docs/backlog/epic-*/stories/STORY-*.md` | Story ID (`STORY-X.Y`), Title, Status (`completed`, `in_progress`, `planned`), Surfaces, Relative Path, Summary |
| **Product Specs** | `docs/product/PRD-*.md` | Title, Status, Target Milestone, Persona/Scope summary |
| **Design Specs** | `docs/design-specs/*.md` | Title, Surfaces, Related Epics, UI/Component summary |
| **ADRs** | `docs/adr/*.md` | ADR Number, Title, Decision Status (`Accepted`, `Proposed`, `Deprecated`) |
| **Templates** | `docs/templates/*.md` | Available starter templates and guidelines |

### Frontmatter Schema

Story documents use standard YAML frontmatter parsed by `generate_status_dashboard.py`:

```yaml
---
id: STORY-35.1
epic_id: EPIC-35
title: "Interactive Status Dashboard Generation"
type: story-spec
status: completed # completed | in_progress | planned
surfaces:
  - mac-app
  - orchestrator
parent_epic: docs/backlog/epic-35-governance/EPIC-35-GOVERNANCE.md
---
```

- When `status: completed`, the dashboard marks the story as **DONE** (green) and checks the box in `docs/STATUS.md`.
- When `status: in_progress`, the dashboard marks the story as **IN PROGRESS** (amber).
- When `status: planned`, the dashboard marks the story as **PLANNED** (slate gray).

### Template Injection

The generator reads [`docs/status-dashboard.template.html`](file:///Users/alanglass/_dev/agent-os-platform/agent-os/docs/status-dashboard.template.html) and populates two placeholders:
1. `__AS_OF_DATE__`: Derived from git commit history or system timestamp.
2. `__DATA_JSON__`: The compiled JSON array containing all epics, stories, PRDs, design specs, and ADRs.

Output is written directly to [`docs/status-dashboard.html`](file:///Users/alanglass/_dev/agent-os-platform/agent-os/docs/status-dashboard.html).

---

## 3. Daily Workflow & Command Reference

### Makefile Automation Targets

In repositories configured with the Agent OS governance framework, standard `make` targets are available:

```bash
# Rebuild the status dashboard from disk documents
make dashboard

# Reconcile docs/STATUS.md checkboxes and titles with disk (zero drift)
make sync-status

# Pull latest generator, templates, and this guide from upstream
make update-governance
```

### Direct CLI Usage & Arguments

You can invoke `scripts/generate_status_dashboard.py` directly with Python 3:

```bash
python3 scripts/generate_status_dashboard.py [OPTIONS]
```

| Option / Flag | Description | Typical Use Case |
|---|---|---|
| *(no flags)* | Compiles `docs/status-dashboard.html` and reports any detected drift. | Local build after adding or updating stories. |
| `--sync` | Automatically rewrites `docs/STATUS.md` so checklist checkmarks and titles reflect disk specs. | Pre-commit cleanup or after completing stories. |
| `--check-only` | Exits with status `0` if zero drift is detected; exits with status `1` and lists discrepancies if drift exists. | CI/CD pipelines and git pre-push hooks. |
| `--name "<Name>"` | Overrides the project title displayed in the dashboard header and title bar. | Multi-repo customization or white-labeling. |

### Example CLI Executions

```bash
# 1. Normal compilation
python3 scripts/generate_status_dashboard.py
# Output: Wrote docs/status-dashboard.html from 36 epics (142 stories), 4 PRDs, 12 design specs, and 8 ADRs.

# 2. Automated status sync
python3 scripts/generate_status_dashboard.py --sync
# Output: Synchronized docs/STATUS.md with disk specifications.

# 3. Continuous Integration drift gate
python3 scripts/generate_status_dashboard.py --check-only
# If in sync: Zero drift detected: docs/STATUS.md matches disk specifications. (Exit 0)
# If drifted: Drift detected (2 discrepancies): ... (Exit 1)
```

---

## 4. Interactive Dashboard Features

The generated [`docs/status-dashboard.html`](file:///Users/alanglass/_dev/agent-os-platform/agent-os/docs/status-dashboard.html) runs entirely inside any modern web browser without a web server:

```bash
open docs/status-dashboard.html
```

### Key Capabilities

1. **Instant Search & Real-Time Filtering**:
   - Real-time search by keyword, title, tag, or Epic number.
   - Matching epics and stories auto-expand while irrelevant sections collapse.
2. **Status Pills**:
   - Quick filters for **ALL**, **DONE**, **IN PROGRESS**, and **PLANNED**.
   - Real-time progress bar reflecting completion percentage across all scoped stories.
3. **In-Dashboard Markdown Reader Drawer**:
   - Clicking any story or epic slides open a right-hand drawer.
   - Renders the full Markdown specification directly within the browser using embedded client-side formatting.
4. **Developer IDE Integration**:
   - **📋 Copy Path**: Copies the relative file path for quick editor opening (`code <path>` / `cursor <path>`).
   - **↗ Open File**: Opens the local file link directly in your browser or default Markdown viewer.
5. **Zero Dependencies & Total Privacy**:
   - No external CDNs, fonts, or tracking scripts.
   - Fully functional offline on air-gapped machines or airplanes.

---

## 5. Distribution, Kit Packaging & Auto-Updates

To ensure consistent project governance across multiple repositories, the dashboard generator and its companion documentation are packaged together.

### Why This Guide Is Bundled with the Generator

When external projects adopt the Agent OS documentation governance framework, they need both the executable generator and its operational user guide. Including this guide ensures:
- New team members or AI coding agents in downstream repositories have immediate access to operational instructions.
- As the generator gains new flags (e.g. `--check-only`, `--sync`), the corresponding documentation updates simultaneously.

### How Downstream Repositories Receive Updates

When downstream projects run:
```bash
make update-governance
# or: python3 scripts/bootstrap_governance.py --update
```
The update engine refreshes the canonical governance assets:
- `scripts/generate_status_dashboard.py`
- `docs/status-dashboard.template.html`
- `docs/templates/*.md`
- **`docs/user-guides/STATUS-DASHBOARD.md`** *(this guide)*

### Packaging the Governance Kit

To produce a portable distribution zip containing the generator, template, starter docs, and this guide:

```bash
make package-kit
# Output: Packaged dist/agent-os-governance-kit.zip

# Optionally copy directly to Desktop or distribution folder:
make package-kit DEST=~/Desktop
```

---

## 6. Testing & Quality Assurance

The generator is covered by automated unit and integration tests under [`orchestrator/tests/test_generate_status_dashboard.py`](file:///Users/alanglass/_dev/agent-os-platform/agent-os/orchestrator/tests/test_generate_status_dashboard.py):

```bash
# Run dashboard generator test suite
orchestrator/.venv/bin/pytest orchestrator/tests/test_generate_status_dashboard.py -q
```

### Verified Test Gates

- **Frontmatter Extraction**: Tests standard YAML parsing, empty frontmatter, and multi-line surface lists.
- **Epic & Story Parsing**: Verifies parsing of parent Epic execution plans and individual story specs.
- **Drift Detection**: Validates that discrepancies between `docs/STATUS.md` and disk specifications are accurately flagged.
- **Status Sync**: Verifies that `--sync` rewrites `docs/STATUS.md` checkboxes without corrupting surrounding prose.
- **Template Substitution**: Validates that generated HTML contains expected JSON structures and valid date stamps.

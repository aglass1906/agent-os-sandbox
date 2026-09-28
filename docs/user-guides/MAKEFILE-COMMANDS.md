# Makefile & Scaffolding Commands Guide

> **Audience:** AI Agents, Software Architects, Engineering Leads & Developers  
> **Index Level:** User & Operator Guides (`docs/user-guides/`)  
> **Master Index:** [`docs/README.md`](../README.md)  
> **Governance Standard:** [`docs/architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md`](../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md)  
> **Operating Guide:** [`AGENTS.md`](../../AGENTS.md)

This guide documents the canonical **Makefile automation commands** for the Agent OS documentation and planning governance framework. These targets provide a unified developer and AI pair-programming interface to scaffold specifications, reconcile living trackers, build interactive status dashboards, and maintain synchronized repositories.

---

## 1. Executive Summary & Design Invariants

Rather than creating Markdown files manually by hand, developers and AI coding assistants use Makefile targets. This ensures:
1. **Consistent Naming & Folder Conventions**: IDs, slugs, and casing follow the platform's strict `Epic → Story → Task` taxonomy.
2. **Standard YAML Frontmatter**: Scaffolds include pre-configured metadata headers ready for parsing by the status dashboard generator.
3. **Traceable Architecture Lineage**: Parent-child links between PRDs, Epics, Stories, ADRs, and Design Specs are automatically wired.
4. **Zero-Drift Synchronization**: Living checklist trackers (`docs/STATUS.md`) stay synchronized with specs on disk.

---

## 2. Command Quick Reference

| Command | Category | Description | Primary Arguments |
|---|---|---|---|
| `make help` | Discovery | Prints the interactive menu of all available Makefile targets. | *(None)* |
| `make new-epic` | Scaffolding | Scaffolds an Epic directory, plan, and `stories/` folder. | `ID=<num>`, `SLUG=<slug>`, `TITLE="<Title>"` |
| `make new-story` | Scaffolding | Scaffolds a Story specification inside its parent Epic. | `EPIC_ID=<num>`, `STORY_NUM=<num>`, `SLUG=<slug>`, `TITLE="<Title>"` |
| `make new-prd` | Scaffolding | Scaffolds a Product Requirements Document (PRD). | `SLUG=<slug>`, `TITLE="<Title>"` |
| `make new-adr` | Scaffolding | Scaffolds an Architecture Decision Record (auto-pads ID to 4 digits). | `ID=<num>`, `SLUG=<slug>`, `TITLE="<Title>"` |
| `make new-design-spec` | Scaffolding | Scaffolds a Feature UI/UX Design Specification. | `SLUG=<slug>`, `TITLE="<Title>"` |
| `make new-handoff` | Scaffolding | Scaffolds a multi-commit Epic Implementation Handoff log. | `EPIC_ID=<num>` |
| `make new-pr` | Scaffolding | Generates a GitHub PR template or completion report. | `[OUT=<path>]` |
| `make dashboard` | Dashboard | Recompiles the offline interactive `docs/status-dashboard.html`. | *(None)* |
| `make sync-status` | Anti-Drift | Reconciles `docs/STATUS.md` checkmarks and titles with disk. | *(None)* |
| `make lint-docs` | Governance | Audits backlog specs against canonical templates in `docs/templates/`. | `[EPIC=<num>]`, `[STATUS=<status>]`, `[TARGET=<kind>]` |
| `make diff-docs` | Governance | Previews diffs of template reconciliation without writing to disk. | `[EPIC=<num>]`, `[STATUS=<status>]` |
| `make sync-docs` | Governance | Reconciles backlog specs to match current canonical templates. | `[EPIC=<num>]`, `[STATUS=<status>]`, `[TARGET=<kind>]` |
| `make update-governance` | Upstream Sync | Fetches the latest generator, templates, and guides from GitHub. | *(None)* |
| `make package-kit` | Packaging | Bundles the portable governance kit into a standalone zip file. | `[DEST=<dir>]` |

---

## 3. Scaffolding Commands (Step-by-Step)

### A. New Epic (`make new-epic`)
Creates a new Epic folder (`docs/backlog/epic-<ID>-<slug>/`), the parent Epic plan document (`EPIC-<ID>-<SLUG>.md`), and the nested `stories/` directory.

```bash
make new-epic ID=1 SLUG=user-auth TITLE="User Authentication"
```

- **Output File**: `docs/backlog/epic-1-user-auth/EPIC-1-USER-AUTH.md`
- **Output Directory**: `docs/backlog/epic-1-user-auth/stories/`
- **Arguments**:
  - `ID`: Numeric Epic ID (e.g. `1`, `35`).
  - `SLUG`: Lowercase hyphenated descriptor (e.g. `user-auth`, `fleet-mesh`).
  - `TITLE`: Human-readable title in quotes (e.g. `"User Authentication"`).

---

### B. New Story (`make new-story`)
Creates a machine-readable Story specification inside the corresponding Epic's `stories/` folder with pre-filled YAML frontmatter linked to the parent Epic plan.

```bash
make new-story EPIC_ID=1 STORY_NUM=1 SLUG=jwt-login TITLE="JWT Login Endpoint"
```

- **Output File**: `docs/backlog/epic-1-user-auth/stories/STORY-1.1-JWT-LOGIN.md`
- **Arguments**:
  - `EPIC_ID`: Numeric parent Epic ID (e.g. `1`).
  - `STORY_NUM`: Sub-item number (e.g. `1` for Story 1.1).
  - `SLUG`: Lowercase hyphenated descriptor (e.g. `jwt-login`).
  - `TITLE`: Human-readable story title in quotes.

---

### C. New Product Requirements Document (`make new-prd`)
Scaffolds a high-level product strategy and MVP scope document under `docs/product/`.

```bash
make new-prd SLUG=member-portal TITLE="Member Portal & Billing"
```

- **Output File**: `docs/product/PRD-MEMBER-PORTAL.md`
- **Arguments**:
  - `SLUG`: Lowercase hyphenated descriptor (e.g. `member-portal`).
  - `TITLE`: Initiative or feature title in quotes.

---

### D. New Architecture Decision Record (`make new-adr`)
Scaffolds an immutable decision record under `docs/adr/`. Automatically zero-pads the ID to 4 digits (e.g. `ID=1` becomes `0001`).

```bash
make new-adr ID=1 SLUG=use-postgres TITLE="Use Postgres for Primary Persistence"
```

- **Output File**: `docs/adr/0001-use-postgres.md`
- **Arguments**:
  - `ID`: Numeric decision sequence number (e.g. `1`, `12`).
  - `SLUG`: Lowercase hyphenated decision slug (e.g. `use-postgres`).
  - `TITLE`: Descriptive decision title in quotes.

---

### E. New Feature Design Spec (`make new-design-spec`)
Scaffolds a UX/UI and technical implementation specification under `docs/design-specs/`.

```bash
make new-design-spec SLUG=checkout-flow TITLE="Multi-Step Checkout Flow"
```

- **Output File**: `docs/design-specs/CHECKOUT-FLOW.md`
- **Arguments**:
  - `SLUG`: Lowercase hyphenated descriptor (e.g. `checkout-flow`).
  - `TITLE`: Feature name in quotes.

---

### F. New Session Handoff (`make new-handoff`)
Scaffolds a multi-commit work-in-progress tracking log under `docs/history/handoffs/`.

```bash
make new-handoff EPIC_ID=1
```

- **Output File**: `docs/history/handoffs/HANDOFF-EPIC-1.md`
- **Arguments**:
  - `EPIC_ID`: Numeric Epic ID being executed across sessions.

---

### G. New Pull Request Template / Completion Note (`make new-pr`)
Installs or scaffolds a structured GitHub PR template or completion note under `.github/pull_request_template.md`.

```bash
# Default installation
make new-pr

# Custom output destination
make new-pr OUT=docs/history/audits-and-runbooks/PR-EPIC-1.md
```

---

## 4. Governance & Dashboard Commands

### A. Rebuild Status Dashboard (`make dashboard`)
Executes `scripts/generate_status_dashboard.py` to parse all backlog specs, PRDs, design specs, and ADRs, compiling them into a zero-dependency offline HTML dashboard:

```bash
make dashboard
open docs/status-dashboard.html
```

---

### B. Reconcile Living Tracker (`make sync-status`)
Runs `scripts/generate_status_dashboard.py --sync` to compare `docs/STATUS.md` with the YAML frontmatter of all Story files on disk. Automatically flips checkmarks (`[x]` vs `[ ]`) and synchronizes story titles without modifying surrounding commentary.

```bash
make sync-status
```

---

### C. Pull Upstream Governance Updates (`make update-governance`)
Pulls the latest scripts, HTML dashboard templates, document templates, and user guides from the canonical GitHub repository:

```bash
make update-governance
```

- Automatically refreshes:
  - `scripts/bootstrap_governance.py`
  - `scripts/generate_status_dashboard.py`
  - `docs/status-dashboard.template.html`
  - Canonical templates in `docs/templates/*.md`
  - Canonical user guides (`STATUS-DASHBOARD.md`, `MAKEFILE-COMMANDS.md`)
- Automatically regenerates `docs/status-dashboard.html`.

---

### D. Package Governance Toolkit (`make package-kit`)
Packages all canonical governance files into a portable zip file (`dist/agent-os-governance-kit.zip`) for distribution:

```bash
# Package to dist/
make package-kit

# Package and copy directly to Desktop or target folder:
make package-kit DEST=~/Desktop
```

---

### E. Template Reconciliation & Governance Auditing (`make lint-docs`, `make diff-docs`, `make sync-docs`)
Audit and automatically reconcile active specifications against current templates in `docs/templates/`:

```bash
# 1. Audit drift across active backlog (fails in CI if drift exists)
make lint-docs

# 2. Preview unified diffs without modifying files
make diff-docs
make diff-docs EPIC=30

# 3. Reconcile specifications in place
make sync-docs
make sync-docs EPIC=30
make sync-docs TARGET=stories STATUS=in_progress
make sync-docs TARGET=design-specs
make sync-docs TARGET=adrs
make sync-docs TARGET=all-docs
```

- **Supported Targets**: `stories`, `epics`, `backlog`, `design-specs`, `adrs`, `prds`, `handoffs`, `all`, `all-docs`.
- **Invariants**: Preserves 100% of custom engineering analysis, diagrams, DDLs, endpoints, and task completion checkboxes.
- **Reference**: See [`DOCUMENTATION-RECONCILIATION-RUNBOOK.md`](./DOCUMENTATION-RECONCILIATION-RUNBOOK.md) for full runbook details.

---

## 5. Typical AI Agent & Developer Workflow

A typical engineering workflow using these commands proceeds as follows:

```bash
# 1. Start a new initiative by creating an Epic
make new-epic ID=2 SLUG=notifications TITLE="In-App Notifications"

# 2. Decompose the Epic into vertical Stories
make new-story EPIC_ID=2 STORY_NUM=1 SLUG=schema TITLE="Notification Schema & Migration"
make new-story EPIC_ID=2 STORY_NUM=2 SLUG=delivery TITLE="WebSocket Delivery Engine"

# 3. Create an ADR for architectural decisions
make new-adr ID=5 SLUG=use-sse-for-events TITLE="Use Server-Sent Events for Live Alerts"

# 4. Synchronize the living status checklist
make sync-status

# 5. Build and inspect the visual dashboard
make dashboard
open docs/status-dashboard.html
```

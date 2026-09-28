# Standard Engineering Documentation Templates (`docs/templates/`)

> **Index Level:** Subdirectory Index  
> **Master Hub:** [`../README.md`](../README.md)  
> **Governance Standard:** [`../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md`](../architecture/15-DOCUMENTATION-AND-PLANNING-GOVERNANCE.md) · [`../../AGENTS.md`](../../AGENTS.md)  
> **Status Policy:** **Living Standards**

This directory contains canonical starter templates for engineering plans, story specifications, architectural decision records (ADRs), and technical design specs. AI agents and developers must use these templates when creating new documentation.

---

## 📋 Available Templates

| Template | File Path | When to Use | Output Destination |
|---|---|---|---|
| **Product Requirements Document** | [`PRD-TEMPLATE.md`](./PRD-TEMPLATE.md) | Authoring product goals, persona journeys, MVP scope & non-goals | `docs/product/PRD-000X-NAME.md` |
| **Epic Execution Plan** | [`EPIC-TEMPLATE.md`](./EPIC-TEMPLATE.md) | Authoring a new platform initiative or architectural capability | `docs/backlog/epic-X-NAME/EPIC-X-NAME.md` |
| **Story Specification** | [`STORY-TEMPLATE.md`](./STORY-TEMPLATE.md) | Authoring an independently testable deliverable under an Epic | `docs/backlog/epic-X-NAME/stories/STORY-X.Y-NAME.md` |
| **Architecture Decision Record** | [`ADR-TEMPLATE.md`](./ADR-TEMPLATE.md) | Documenting a fundamental design trade-off, invariant, or paradigm | `docs/adr/000X-TITLE.md` |
| **Feature Design Spec** | [`DESIGN-SPEC-TEMPLATE.md`](./DESIGN-SPEC-TEMPLATE.md) | Authoring UI/UX wireframes, protocol payloads, and state transitions | `docs/design-specs/FEATURE-NAME.md` |
| **Session Handoff** | [`HANDOFF-TEMPLATE.md`](./HANDOFF-TEMPLATE.md) | Documenting multi-commit progress, test evidence, and remaining gates | `docs/history/handoffs/HANDOFF-EPIC-X.md` |
| **Pull Request Completion** | [`PR-TEMPLATE.md`](./PR-TEMPLATE.md) | Standardizing pull request summaries, test evidence, and checklists | `.github/pull_request_template.md` or PR notes |

---

## 🚀 Quick Starter Commands

### Option A: Automated via `make` (Recommended)
```bash
# 1. Scaffold a new Product Requirements Document (PRD)
make new-prd ID=1 SLUG=member-portal TITLE="Member Portal"

# 2. Scaffold a new Epic directory, plan, and stories/ folder
make new-epic ID=37 SLUG=fleet-mesh TITLE="Fleet Mesh"

# 3. Scaffold a new Story specification inside its parent Epic
make new-story EPIC_ID=37 STORY_NUM=1 SLUG=mesh-protocol TITLE="Mesh Protocol"

# 4. Scaffold a new Architecture Decision Record (auto-pads ID to 4 digits)
make new-adr ID=15 SLUG=stream-compression TITLE="Stream Compression"

# 5. Scaffold a new Feature Design Spec
make new-design-spec SLUG=multi-window-studio TITLE="Multi-Window Studio"

# 6. Scaffold a new Session Handoff document
make new-handoff EPIC_ID=37

# 7. Install default GitHub PR template or scaffold PR completion note
make new-pr
```

### Option B: Manual Copy
```bash
# 1. Create a new Epic directory and plan
mkdir -p docs/backlog/epic-37-fleet-mesh/stories
cp docs/templates/EPIC-TEMPLATE.md docs/backlog/epic-37-fleet-mesh/EPIC-37-FLEET-MESH.md

# 2. Create a new Story specification
cp docs/templates/STORY-TEMPLATE.md docs/backlog/epic-37-fleet-mesh/stories/STORY-37.1-MESH-PROTOCOL.md

# 3. Create a new Architecture Decision Record
cp docs/templates/ADR-TEMPLATE.md docs/adr/0015-stream-compression.md

# 4. Create a new Feature Design Spec
cp docs/templates/DESIGN-SPEC-TEMPLATE.md docs/design-specs/MULTI-WINDOW-STUDIO.md

# 5. Create a new Session Handoff
cp docs/templates/HANDOFF-TEMPLATE.md docs/history/handoffs/HANDOFF-EPIC-37.md

# 6. Install standard GitHub Pull Request template
mkdir -p .github && cp docs/templates/PR-TEMPLATE.md .github/pull_request_template.md
```

---

## 🏷️ Numbering Rules Summary

* **Epic Numbering**: Sequential integer (`Epic 0`, `Epic 1`, ... `Epic 36`, `Epic 37`). Check [`docs/backlog/BACKLOG.md`](../backlog/BACKLOG.md) for the next number.
* **Story Numbering**: Parent-scoped dot notation (`Story X.1`, `Story X.2`, ..., `Story X.N`). Check `docs/backlog/epic-X-NAME/stories/` for the next sub-index.
* **ADR Numbering**: 4-digit zero-padded sequence (`0001`, `0002`, ..., `0014`, `0015`). Check [`docs/adr/README.md`](../adr/README.md) for the next number.
* **Design Specs**: Descriptive kebab-case slug without numbers (`FEATURE-NAME.md`).

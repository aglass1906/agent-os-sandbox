# Timbuk2 Games Hub — Agent Instructions & Developer Guide

This document outlines key technical conventions, project architecture, and rules for AI agents and human contributors working on the **Timbuk2 Games Hub** project.

---

## 1. Project Overview & Core Architectural Constraints

Grounded in **`PROJECT_OVERVIEW_DRAFT.md`** and the **`Coding Conventions and Style Guide`**:

- **Browser-Native Stack**: Built using pure vanilla HTML5, strict-mode ES6+ JavaScript, and CSS3.
- **Zero Build Tools / Dependencies**: No frameworks (React, Vue, etc.), no package managers (`npm`, `yarn`), no bundlers (`Webpack`, `Vite`), and no backend servers.
- **Self-Contained Games**: Each game lives in its own directory under `src/games/<game>/` and must operate independently.
- **Hub Navigation**: Playable games are linked from `src/games/index.html` and must include back-navigation to return to the hub.

---

## 2. Standard Directory Layout

```text
src/games/
├── index.html       # Central Hub game-selection page
├── style.css        # Shared Hub presentation styles
├── <game>/          # Game-specific directory
│   ├── index.html   # Semantic page structure & canvas/controls
│   ├── style.css    # Responsive styling & theme
│   ├── game.js      # Strict-mode state machine, input handling, and rendering
│   ├── rules.html   # (Optional) Standalone game instructions
│   └── *_design.md  # Game specification source of truth
```

---

## 3. Mandatory Development Conventions

Grounded in **`Coding Conventions and Style Guide`**:

### JavaScript Guidelines
1. **Strict Mode**: Every JavaScript file must begin with `"use strict";`.
2. **State Management**:
   - Centralize state within a single state object.
   - Initialize state via a `createInitialState()` function.
   - Ensure predictable, action-driven state mutations.
3. **Naming Conventions**:
   - `UPPERCASE_SNAKE` for constants (e.g., `MAX_GUESSES`, `STATUS_PLAYING`).
   - `camelCase` for variables and functions (e.g., `renderBoard`, `isValidWord`).
   - `PascalCase` for classes (e.g., `GameEngine`).

### Accessibility & Responsiveness
- Support mouse, keyboard, and touch interactions.
- Provide visible text for status and terminal states (win/loss/draw).
- Use dynamic live regions (`aria-live`) for accessible status announcements.
- Maintain responsive fluid layouts usable across desktop and mobile screens.

---

## 4. Current Inventory & Status

Grounded in **`PROJECT_OVERVIEW_DRAFT.md`**:

| Game | Status | Repository Location | Source Specification |
| --- | --- | --- | --- |
| **Tic Tac Toe** | Implemented & Linked | `src/games/tic-tac-toe/` | `tictactoe_design.md` |
| **Wordle** | Implemented & Linked | `src/games/wordle/` | `wordle_design.md` |
| **Sudoku** | Implemented & Linked | `src/games/sudoku/` | `sudoku_design.md` |
| **Connect Four** | Design Phase | `src/games/connect-four/` | `connectfour_design.md` |
| **Asteroids Redux** | Implemented & Linked | `src/games/asteroids/` | `asteroids_design.md` |

---

## 5. Quality & Verification Criteria

Before declaring any feature or game implementation complete:
1. Verify gameplay and state transitions in standard web browsers.
2. Confirm invalid actions do not mutate or corrupt game state.
3. Ensure game reset/restart cleanly restores all state variables and DOM elements to initial defaults.
4. Verify responsive layout down to narrow mobile viewports (<768px).
5. Ensure hub integration: link added to `src/games/index.html` when game is ready.

### Test Policy
The canonical project test policy is `bash test_canary_badge.sh`. It must exit `0` before the work is considered complete. The gate verifies the release canary badge marker line (`[Phase 3 Canary: take 3 on the release testing]`) exists exactly once in `README.md`.

# AgentOS Sandbox — AI Coding Assistant & Documentation Governance Guide

Welcome! This document provides core architectural rules and documentation governance guidelines for AI coding assistants working in the **AgentOS Sandbox** repository.

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

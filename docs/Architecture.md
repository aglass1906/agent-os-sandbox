# Technical Architecture — Timbuk2 Games Hub

> **Document Type:** Architectural Specification
> **Target Path:** `docs/Architecture.md`
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, `AGENTS.md`, and `src/games/asteroids/asteroids_design.md`.

---

## 1. Core Architectural Principles & Stack Constraints

The **Timbuk2 Games Hub** is engineered as a zero-dependency, browser-native game portal (*Source: `PROJECT_OVERVIEW_DRAFT.md`*).

- **Browser-Native Stack:** Constructed exclusively with standard HTML5, strict-mode ES6+ JavaScript, CSS3, and the Web Audio API.
- **Zero External Dependencies:** No web frameworks (React, Vue), package managers (`npm`, `yarn`), bundlers (`Vite`, `Webpack`), or backend services (*Source: `Coding Conventions and Style Guide`*).
- **Self-Contained Isolation:** Every game operates independently in its own directory structure under `src/games/<game>/` without shared runtime JS dependencies (*Source: `AGENTS.md`*).

---

## 2. System Structure & Directory Layout

### 2.1 Central Hub Architecture
The central hub provides game discovery and navigation back-and-forth (*Source: `PROJECT_OVERVIEW_DRAFT.md`*):
- `src/games/index.html`: Main game selection interface linking to playable game cards.
- `src/games/style.css`: Shared hub presentation, card grids, and global styling rules.

### 2.2 Standard Game Module Directory Layout
Every game follows a uniform layout pattern (*Source: `Coding Conventions and Style Guide`*, `AGENTS.md`):
```text
src/games/<game>/
├── index.html       # Semantic page structure, canvas/DOM grid, and controls
├── style.css        # Game-specific responsive styling and themes
├── game.js          # Strict-mode state machine, input handlers, and renderers
├── rules.html       # (Optional) Standalone user instructions
└── *_design.md      # Game specification & architectural source of truth
```

---

## 3. Game Engine & State Architecture

### 3.1 Strict State Management Pattern
Grounded in `Coding Conventions and Style Guide`:
1. **Strict Execution:** Every JavaScript module begins with `"use strict";`.
2. **State Centralization:** All mutable runtime state resides within a single, schema-defined state object.
3. **State Lifecycle:** State is explicitly initialized and reset via `createInitialState()`.
4. **Predictable Mutations:** State changes strictly occur via deterministic action/event handlers.

### 3.2 Subsystem Breakdown
- **Turn-Based Grid Games (Tic-Tac-Toe, Wordle, Sudoku, Connect Four):** Rely on DOM event listeners (`click`, `keydown`), DOM board rendering, and explicit turn/win state validation logic (*Source: `PROJECT_OVERVIEW_DRAFT.md`*).
- **Real-Time Canvas Games (Asteroids Redux):** Implements a high-performance `requestAnimationFrame` game loop, torus-wrapping physics dynamics, vector rendering with canvas glow effects, particle systems, and procedural Web Audio API audio synthesis (*Source: `Asteroids Redux Design Document`*).

---

## 4. Input, Responsive & Accessibility Subsystems

- **Multi-Modal Input System:** Supports keyboard (`Arrow` keys, `WASD`, `Space`), mouse click/drag, and touch controls (*Source: `AGENTS.md`*).
- **Mobile Touch Overlay:** Dynamically renders virtual touch controls (e.g., D-pad, action buttons) on viewport widths $<768\text{px}$ (*Source: `Asteroids Redux Design Document`*).
- **Accessibility & UX Rules:** Enforces semantic HTML, visible status regions, dynamic `aria-live` region updates for game outcomes, and color-blind accessible visual cues (*Source: `AGENTS.md`*).

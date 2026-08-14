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
| **Asteroids Redux** | Design Phase | `src/games/asteroids/` | `Asteroids Redux Design Document` / `asteroids_design.md` |

---

## 5. Quality & Verification Criteria

Before declaring any feature or game implementation complete:
1. Verify gameplay and state transitions in standard web browsers.
2. Confirm invalid actions do not mutate or corrupt game state.
3. Ensure game reset/restart cleanly restores all state variables and DOM elements to initial defaults.
4. Verify responsive layout down to narrow mobile viewports (<768px).
5. Ensure hub integration: link added to `src/games/index.html` when game is ready.

# Repository Governance & Documentation Overview — Timbuk2 Games Hub

> **Document Type:** Repository Governance Overview
> **Target Path:** `docs/README.md`
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, and `Asteroids Redux Design Document`.

---

## 1. Overview & Architectural Principles

The **Timbuk2 Games Hub** is a collection of browser-native casual games (*Source: `PROJECT_OVERVIEW_DRAFT.md`*).

### Core Technical Rules
1. **Browser-Native Stack:** Built strictly with vanilla HTML5, strict-mode ES6+ JavaScript, CSS3, and browser APIs (such as Web Audio API).
2. **Zero External Dependencies:** Frameworks (React, Vue), package managers (`npm`, `yarn`), bundlers (`Webpack`, `Vite`), or backend servers are strictly prohibited (*Source: `Coding Conventions and Style Guide`*).
3. **Self-Contained Game Isolation:** Each game lives in its own folder under `src/games/<game>/` and functions independently without shared JS runtime dependencies (*Source: `PROJECT_OVERVIEW_DRAFT.md`*).
4. **Hub Integration:** Playable games must be linked from `src/games/index.html` with navigation back to the hub (*Source: `Coding Conventions and Style Guide`*).

---

## 2. Directory & Documentation Structure

```text
docs/
├── README.md               # Repository governance and documentation directory index
└── Architecture.md         # Technical architecture specification
src/games/
├── index.html              # Game hub entry page
├── style.css               # Shared hub presentation styles
└── <game>/                 # Self-contained game module
    ├── index.html          # Semantic HTML & layout
    ├── style.css           # Responsive styling
    ├── game.js             # Strict-mode JS game logic & state machine
    ├── rules.html          # Optional standalone rules page
    └── *_design.md         # Game design specification source of truth
```

---

## 3. Contribution & Coding Conventions

Grounded in `Coding Conventions and Style Guide`:
- **JavaScript Strict Mode:** All `.js` files must begin with `"use strict";`.
- **State Management:** Single state object initialized via `createInitialState()` with predictable, event-driven state mutations.
- **Naming Standards:** `UPPERCASE_SNAKE` for constants, `camelCase` for variables and functions, `PascalCase` for classes.
- **Accessibility & Responsiveness:** Fluid responsive layouts supporting mouse, keyboard, and touch interactions (including virtual touch controls on viewports $<768\text{px}$), semantic HTML, and `aria-live` dynamic status updates.

---

## 4. Verification & Readiness Criteria

Grounded in `PROJECT_OVERVIEW_DRAFT.md`:
1. Documented game rules and state transitions tested and working in standard browsers.
2. Terminal states (win/loss/draw) block further input mutations until clean reset.
3. Restart cleanly resets all state and DOM elements to initial defaults.
4. Hub card linked in `src/games/index.html` with working back navigation.
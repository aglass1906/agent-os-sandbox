# Agent Instructions — Timbuk2 Games Hub

> Grounded in `PROJECT_OVERVIEW_DRAFT.md` and project design specifications.

## 1. Project Architecture & Core Conventions
- **Browser-Native Stack:** Vanilla HTML5, CSS3, and ES6+ JavaScript only. No build tools, package managers, frameworks, or external libraries.
- **Directory Structure:** Each game lives in its own self-contained directory under `src/games/<game>/`:
  - `index.html` — Semantic structure, status displays, and controls
  - `style.css` — Game-specific responsive presentation
  - `game.js` — Strict-mode state machine, rules, rendering, and input handling
  - `*_design.md` — Game design specification
- **Central Hub Integration:** `src/games/index.html` links all playable game cards.

## 2. Quality & Behavior Expectations
- **Input & Controls:** Support keyboard, mouse, and touch interaction as defined per game design.
- **State & Terminal Rules:** Input during terminal states (win/loss/draw) must be ignored until reset. Restarting must reset all state variables and visual elements cleanly.
- **Accessibility & Responsiveness:** Announce dynamic status updates via live regions. Layouts must remain responsive on narrow mobile devices.

## 3. Game-Specific Grounding
- **Connect Four:** Local 2-player 6x7 grid game. See `src/games/connect-four/connect_four_design.md`.
- **Asteroids Redux:** Real-time HTML5 Canvas vector shooter with procedural Web Audio API sounds, momentum physics, and touch overlays. UFOs, power-ups, and persistent high scores are out of scope. See `src/games/asteroids/asteroids_design.md`.

---
id: "SPEC-MEMORY-MATCH"
title: "Memory Match Technical Design Specification"
type: "design-spec"
status: "living"
created: "2026-09-01"
updated: "2026-09-27"
surfaces:
  - web-client
---

# Feature Design Spec — Memory Match Technical Design Specification

> **Category:** Technical & UX Design Specification  
> **Status:** 🟢 Living  
> **Index:** [`docs/design-specs/README.md`](./README.md)
> **Document Type:** Design Specification
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, and `docs/README.md`.

---

## 1. Executive Summary & Architecture

**Memory Match** is a browser-native card-matching game for the Timbuk2 Games Hub that follows the same conventions as existing games. Built using vanilla HTML5 Canvas, strict-mode ES6+ JavaScript, CSS3, and the Web Audio API, it requires no external libraries or build steps (*Source: `Coding Conventions and Style Guide`*).

### File Structure & Hub Integration
```text
src/games/memory-match/
├── index.html             # Game canvas, status HUD, and accessible controls
├── style.css              # Retro theme, responsive layout, and mobile touch controls
├── game.js                # Strict-mode state engine, card matching logic, and audio
└── memory_match_design.md # Technical design document source of truth
```
When playable, a game card will be linked in `src/games/index.html` with back-navigation to the central hub (*Source: `docs/README.md`*).

---

## 2. Core Game Mechanics & System Design

### 2.1 Game Board & Card System
- **Game Board:** 4x4 grid of 16 cards (8 matching pairs)
- **Card States:** 
  - Hidden (face down)
  - Revealed (face up, not matched)
  - Matched (face up, permanently revealed)
- **Card Matching:** Players flip two cards at a time to find matching pairs

### 2.2 Game Flow & Scoring
- **Objective:** Find all matching pairs with the fewest moves and in the shortest time
- **Scoring:** 
  - Moves counter (lower is better)
  - Timer (shorter is better)
  - Bonus points for completing quickly
- **Win Condition:** All 8 pairs matched successfully
- **Lose Condition:** None — game only has win state

### 2.3 User Interface & Controls
- **Controls:** 
  - Mouse clicks for card selection
  - Touch support for mobile devices
  - Keyboard support (optional)
- **Visual Feedback:**
  - Card flip animations
  - Match confirmation
  - Mismatch animation
  - Win celebration

---

## 3. Audiovisual & Technical Architecture

### 3.1 Visual System & UI
- **Canvas Rendering:** Fixed aspect ratio $4:3$ canvas scaled dynamically to screen size
- **Color Palette:** Clean, high-contrast design with distinct card colors
- **Card Design:** 
  - Cards have a clean, modern look
  - Back of cards have a consistent pattern
  - Matched cards have a distinct visual indicator
- **Accessibility HUD:** Text-based status updates rendered in DOM with `aria-live="polite"` region (*Source: `Coding Conventions and Style Guide`*).

### 3.2 Web Audio API Procedural Sound
Synthesizes retro audio without asset files:
- **Card Flip:** Short blip sound ($440\text{Hz}$)
- **Match Success:** Harmonic chime ($523\text{Hz} \to 659\text{Hz}$)
- **Match Mismatch:** Dissonant tone ($220\text{Hz}$)
- **Win Celebration:** Multi-tone arpeggio sequence

---

## 4. Quality & Terminal State Rules

Grounded in `PROJECT_OVERVIEW_DRAFT.md`:
1. **Terminal States:** Victory state locks input mutations until clean reset.
2. **Reset Execution:** Restart button completely re-initializes card positions, matching state, and game timers via `createInitialState()`.
3. **Hub Navigation:** Back link returns to `src/games/index.html`.
4. **Game State Management:** 
   - Game state is managed in a single object
   - State transitions are predictable and well-documented
   - Invalid actions do not corrupt game state

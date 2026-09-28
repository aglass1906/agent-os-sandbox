---
id: "SPEC-ADVENTURE-GAME"
title: "Adventure Game Technical Design Specification"
type: "design-spec"
status: "living"
created: "2026-09-02"
updated: "2026-09-27"
surfaces:
  - web-client
---

# Feature Design Spec — Adventure Game Technical Design Specification

> **Category:** Technical & UX Design Specification  
> **Status:** 🟢 Living  
> **Index:** [`docs/design-specs/README.md`](./README.md)
> **Document Type:** Design Specification
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, and `docs/README.md`.

---

## 1. Executive Summary & Architecture

**Adventure** is a browser-native adaptation of the classic Atari 2600 action-adventure game for the Timbuk2 Games Hub (*Source: `PROJECT_OVERVIEW_DRAFT.md`*). Built using vanilla HTML5 Canvas, strict-mode ES6+ JavaScript, CSS3, and the Web Audio API, it requires no external libraries or build steps (*Source: `Coding Conventions and Style Guide`*).

### File Structure & Hub Integration
```text
src/games/adventure/
├── index.html          # Game canvas, status HUD, and accessible controls
├── style.css           # Retro theme, responsive layout, and mobile touch controls
├── game.js             # Strict-mode state engine, room graph, entity logic, and audio
└── adventure_design.md # Technical design document source of truth
```
When playable, a game card will be linked in `src/games/index.html` with back-navigation to the central hub (*Source: `docs/README.md`*).

---

## 2. Core Game Mechanics & System Design

### 2.1 Spatial Structure & Room Graph
- **Room Grid:** Multi-room interconnected screens (Yellow Castle, White Castle, Black Castle, Catacombs/Mazes, Kingdom fields).
- **Boundary Navigation:** Touching screen edge transitions player avatar smoothly to adjacent room node.

### 2.2 Entity Systems & Inventory
- **Player Avatar:** Movable square controllable via Keyboard (Arrow keys / `WASD`) or Virtual D-Pad on touch screens ($<768\text{px}$).
- **Items:**
  - **Keys:** Open corresponding Castle Gate barriers.
  - **Sword:** Slays dragons on collision contact.
  - **Enchanted Chalice:** Goal item; returning it to Yellow Castle triggers victory.
  - **Magnet:** Attracts nearest item through walls.
- **Dragon AI:** State machine (Roaming, Hunting, Bitten, Dead) pursuing the player square.

---

## 3. Audiovisual & Technical Architecture

### 3.1 Visual System & UI
- **Canvas Rendering:** Fixed aspect ratio $4:3$ canvas scaled dynamically to screen size.
- **Color Palette:** High-contrast retro 8-bit aesthetic with distinct room background hues.
- **Accessibility HUD:** Text-based status updates rendered in DOM with `aria-live="polite"` region (*Source: `Coding Conventions and Style Guide`*).

### 3.2 Web Audio API Procedural Sound
Synthesizes retro audio without asset files:
- **Item Pick/Drop:** Frequency blip ($440\text{Hz} \to 880\text{Hz}$).
- **Gate Unlock:** Low resonant pulse ($150\text{Hz}$).
- **Dragon Roar/Bite:** Filtered noise buffer sweep.
- **Victory Fanfare:** Arpeggiated multi-tone sine wave sequence.

---

## 4. Quality & Terminal State Rules

Grounded in `PROJECT_OVERVIEW_DRAFT.md`:
1. **Terminal States:** Victory or player death locks input mutations until clean reset.
2. **Reset Execution:** Restart button completely re-initializes room graph, player position, item locations, and dragon states via `createInitialState()`.
3. **Hub Navigation:** Back link returns to `src/games/index.html`.

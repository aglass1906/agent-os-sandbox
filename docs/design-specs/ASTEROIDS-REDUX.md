---
id: SPEC-ASTEROIDS-REDUX
title: "Asteroids Redux Technical Design Specification"
type: design-spec
status: living
created: 2026-09-02
updated: 2026-09-27
surfaces:
  - web-client
---

# Asteroids Redux — Technical Design Document

> **Document Type:** Design Specification  
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md` (Project overview document) and repository file `src/games/asteroids/asteroids_design.md`.

---

## 1. Executive Summary & Architecture

**Asteroids Redux** is a browser-native adaptation of the classic arcade space shooter for the Timbuk2 Games Hub. Following the conventions defined in `PROJECT_OVERVIEW_DRAFT.md`, the game is self-contained with no build steps, external libraries, or package managers, built entirely with vanilla HTML5 Canvas, strict-mode ES6+ JavaScript, CSS3, and the Web Audio API.

### File Structure & Hub Integration
```text
src/games/asteroids/
├── index.html          # Game canvas container, HUD, and instructions
├── style.css           # Neon theme, responsive layout, and mobile touch controls
├── game.js             # Game loop, entity components, state machine, and audio engine
└── asteroids_design.md # Full design document source of truth
```
When playable, a game card will be linked in `src/games/index.html`.

---

## 2. Core Game Mechanics & Physics

### 2.1 Spatial Topology & Physics (Torus World)
- **Screen Wrapping:** Entities (`Ship`, `Asteroid`, `Laser`) wrapping seamlessly across canvas boundaries:
  - $X < 0 \implies X = \text{Width}$, $X > \text{Width} \implies X = 0$
  - $Y < 0 \implies Y = \text{Height}$, $Y > \text{Height} \implies Y = 0$
- **Player Dynamics:**
  - **Rotation:** $360^\circ/\text{sec}$ ($2\pi\text{ rad/sec}$) via Left/Right arrows or `A`/`D`.
  - **Thrust:** $400\text{ px/sec}^2$ forward acceleration via Up arrow or `W`.
  - **Damping:** $0.985$ drag factor/frame for authentic momentum drift.
  - **Max Speed:** $600\text{ px/sec}$ velocity cap.
  - **Invulnerability:** 3.0s blink state on wave start or respawn.
  - **Hyperspace Warp:** `Shift` / `H` teleports to random location (15% risk of near-asteroid spawn).

### 2.2 Projectiles & Asteroid Hierarchy
- **Laser Cannons:** Max 4 shots/sec, 8 active lasers max, 1.2s lifetime, velocity = ship velocity + $800\text{ px/sec}$.
- **Asteroid Splitting & Scoring:**
  - **Large Asteroid:** Radius 40px | Speed 40–80 px/s | Score: 20 pts | Splits into 2 Medium Asteroids ($\pm 45^\circ$).
  - **Medium Asteroid:** Radius 20px | Speed 80–160 px/s | Score: 50 pts | Splits into 2 Small Asteroids ($\pm 60^\circ$).
  - **Small Asteroid:** Radius 10px | Speed 160–260 px/s | Score: 100 pts | Destroyed into particle debris.

---

## 3. Audiovisual & Technical Architecture

### 3.1 Vector Visual System & HUD
- **Color Palette:** Neon glow aesthetic using Canvas `shadowBlur`:
  - Background: Deep Space (`#070712`)
  - Primary Vector: Cyan (`#00F3FF`) — Ship, Thrust, HUD
  - Hazard Vector: Yellow (`#FFB703`) — Asteroids
  - Danger Vector: Pink/Red (`#FF2A6D`) — Laser Projectiles
- **Particle System:** Procedural particle emission for engine thrust, asteroid explosions, and ship destruction shockwaves.
- **HUD & Touch Overlay:** Real-time Score, Session High Score, Wave counter, and Lives. On screens $<768\text{px}$, virtual D-pad and dual action buttons (`THRUST` and `FIRE`) render.

### 3.2 Procedural Web Audio API
Synthesizes procedural audio without asset loads:
- **Thrust Hum:** Filtered low-frequency sawtooth oscillator.
- **Laser Blast:** Frequency sweep ($880\text{Hz} \to 110\text{Hz}$ over 120ms).
- **Explosion:** Filtered noise buffer with exponential decay scaled to asteroid size.
- **Background Heartbeat:** Dual-tone sine pulse ($110\text{Hz} / 98\text{Hz}$) accelerating as asteroid count decreases.

---

## 4. Scope Boundaries & Constraints

As established in `src/games/asteroids/asteroids_design.md` and `PROJECT_OVERVIEW_DRAFT.md`:
1. **No Alien UFOs:** Scope limited strictly to wave-based asteroid field survival.
2. **No Power-Ups:** Skill-based gameplay using standard directional laser cannon.
3. **Session-Only High Score:** High score tracked in-memory per session (resets on page reload; no `localStorage` or external storage).

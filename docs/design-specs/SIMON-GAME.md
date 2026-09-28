---
id: "SPEC-SIMON-GAME"
title: "Simon Game Technical Design Specification"
type: "design-spec"
status: "living"
created: "2026-09-05"
updated: "2026-09-27"
surfaces:
  - web-client
---

# Feature Design Spec — Simon Game Technical Design Specification

> **Category:** Technical & UX Design Specification  
> **Status:** 🟢 Living  
> **Index:** [`docs/design-specs/README.md`](./README.md)
> **Document Type:** Design Specification
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, and `docs/README.md`.

---

## 1. Executive Summary & Architecture

**Simon** is a browser-native audio-visual sequence memory game for the Timbuk2 Games Hub (*Source: `PROJECT_OVERVIEW_DRAFT.md`*). The player watches and hears an ever-growing pattern of four colored pads, then repeats it. Built with vanilla HTML5, strict-mode ES6+ JavaScript, CSS3, and the Web Audio API — no external libraries, package managers, or build steps (*Source: `Coding Conventions and Style Guide`*).

Unlike canvas shooters (Asteroids) or grid puzzles (Sudoku), Simon is **DOM-first**: four semantic `<button>` pads, a status HUD, and procedural tones. That keeps it in the same lightweight family as Tic Tac Toe, Wordle, and Memory Match.

### File Structure & Hub Integration

```text
src/games/simon/
├── index.html       # Semantic layout: pads, HUD, Start/Restart, How to Play
├── style.css        # High-contrast pad theme, responsive layout, focus styles
├── game.js          # Strict-mode state machine, sequence engine, input, audio
└── simon_design.md  # Technical design document source of truth
```

When playable, a game card is linked from `src/games/index.html` with back-navigation to the hub (*Source: `docs/README.md`*).

---

## 2. Core Game Mechanics & System Design

### 2.1 Pads & Palette

Exactly **four** pads, each with a fixed identity:

| Id | Color name | Suggested CSS hue | Tone (Hz) | Keyboard |
| --- | --- | --- | --- | --- |
| `0` | Green | `#2ECC71` | 329.63 (E4) | `1` / `Q` |
| `1` | Red | `#E74C3C` | 261.63 (C4) | `2` / `W` |
| `2` | Yellow | `#F1C40F` | 220.00 (A3) | `3` / `A` |
| `3` | Blue | `#3498DB` | 164.81 (E3) | `4` / `S` |

Pads are rendered as labeled buttons (not color-only). Visible text or `aria-label` includes the color name so status and controls remain understandable without relying only on color or sound (*Source: `PROJECT_OVERVIEW_DRAFT.md` §5*).

### 2.2 Sequence Model

- **Sequence:** `number[]` of pad ids in `[0, 3]`.
- **Round `n`:** sequence length equals `n` (round 1 → length 1).
- **Growth rule:** After a successful player repeat, append one uniformly random pad id and advance to the next round.
- **Playback:** Game illuminates/sounds each step in order with a fixed step duration and inter-step gap.
- **Player input:** Player must press the exact pad for each index; any mismatch ends the game in loss.

### 2.3 Phase / State Machine

Central state via `createInitialState()` (*Source: `Coding Conventions and Style Guide`*):

```text
STATUS_IDLE      → waiting for Start (no sequence yet)
STATUS_WATCHING  → playing back the current sequence; input locked
STATUS_INPUT     → accepting player presses for the current sequence
STATUS_WON       → reached MAX_ROUNDS successfully (terminal)
STATUS_LOST      → wrong pad pressed (terminal)
```

Suggested state object fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `status` | string constant | Current phase |
| `sequence` | `number[]` | Full pattern to date |
| `playerIndex` | number | Next expected sequence index during `STATUS_INPUT` |
| `round` | number | Current round (1-based); equals `sequence.length` while playing |
| `score` | number | Highest completed round this session |

**Default product rule (v1):** On mismatch → `STATUS_LOST`. Restart via New Game only.

### 2.4 Input Rules

- **Accepted while `STATUS_INPUT` only.** Presses during `STATUS_WATCHING`, `STATUS_IDLE`, `STATUS_WON`, or `STATUS_LOST` do not mutate sequence or score.
- **Mouse / touch:** click or tap on a pad button.
- **Keyboard:** map keys to pads (`1`/`2`/`3`/`4`), documented in How to Play. Focusable buttons with visible focus rings.
- **Invalid / out-of-order:** mismatch → terminal loss; announce via `aria-live`.
- **Start / Restart:** `createInitialState()` then begin round 1.

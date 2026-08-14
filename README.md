# Timbuk2 Games Hub

[![Build Status](https://img.shields.io/badge/status-Passing-success)](https://img.shields.io/badge/status-Passing-success)

Timbuk2 Games Hub is a collection of casual browser games built with vanilla HTML, CSS, and JavaScript. A central game-selection page links to independent, self-contained game pages without external frameworks, build tools, package managers, or backend dependencies.

---

## 🎮 Game Inventory

| Game | Status | Primary Interaction | Location |
| --- | --- | --- | --- |
| **Tic Tac Toe** | Implemented | Local 2-player grid selection | `src/games/tic-tac-toe/` |
| **Wordle** | Implemented | Physical / on-screen keyboard | `src/games/wordle/` |
| **Sudoku** | Implemented | Grid selection & digit entry | `src/games/sudoku/` |
| **Connect Four** | Design Phase | Local 2-player column selection | `src/games/connect-four/` |
| **Asteroids Redux** | Design Phase | Real-time keyboard & touch controls | `src/games/asteroids/` |

---

## 🚀 Getting Started

Since the project uses browser-native technologies with zero build steps or package dependencies:

1. Clone or download the repository.
2. Open `src/games/index.html` directly in any modern web browser.
3. Select a game from the hub interface to play.

---

## 📁 Repository Structure & Architecture

```text
src/games/
├── index.html       # Central Hub game-selection page
├── style.css        # Shared Hub presentation styles
├── tic-tac-toe/     # Tic Tac Toe implementation
├── wordle/          # Wordle implementation
├── sudoku/          # Sudoku implementation
├── connect-four/    # Connect Four design & specification
└── asteroids/       # Asteroids Redux design & specification
```

### Conventions & Principles
- **Self-contained**: Each game lives in its own directory under `src/games/<game>/`.
- **Vanilla Tech**: Built using strict-mode ES6+ JavaScript, standard HTML5 DOM/Canvas, and CSS3.
- **Responsive & Accessible**: Support mouse, keyboard, and touch interactions with accessible status regions.
- **Hub Link**: Playable games are linked from `src/games/index.html` and provide back navigation to the hub.

---

## 📄 Documentation

Project specifications and design documents are grounded in:
- `PROJECT_OVERVIEW_DRAFT.md`: Overall Hub architecture, product goals, and completion criteria.
- `src/games/asteroids/asteroids_design.md`: Technical design document for Asteroids Redux.
- `src/games/connect-four/connect_four_design.md`: Design specification for Connect Four.

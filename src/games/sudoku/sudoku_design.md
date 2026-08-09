# Sudoku Game — Design Document

This document describes the design for a browser-based Sudoku game. It follows
the same structure and conventions as the Tic Tac Toe and Wordle design
documents (`src/games/tic-tac-toe/tictactoe_design.md` and
`src/games/wordle/wordle_design.md`), adapted to Sudoku's mechanics. It is a
design document only; the sections below specify how the 9x9 board is
represented in code, how digits are entered and validated in real time against
the Sudoku rules, how the puzzle is generated, how the win condition is
detected, and how the game resets.

## 1. Game scope and rules

A single-player browser game on a standard **9x9 Sudoku grid** divided into
**nine 3x3 subgrids** (boxes). A completed grid is correct when **every row,
every column, and every 3x3 box contains the digits 1-9 exactly once**.

Some cells are pre-filled at the start (the *givens*); those cells are locked
and cannot be changed. The player fills the remaining empty cells with digits
1-9. The game:

- accepts digit input **1-9** into empty (non-given) cells,
- validates each entry **in real time** against the Sudoku rules (no duplicate
  in the same row, column, or box), flagging rule conflicts visually and in the
  status line,
- declares a **win** only when every cell is filled with the correct solution.

The design focuses on the core game logic and a minimal, accessible UI,
mirroring the existing games in the project (vanilla HTML + CSS + JavaScript,
no framework or build step).

## 2. Grid representation

The playing surface is a fixed 2-dimensional digit grid with **9 rows and 9
columns**:

- `grid: array[9][9] of digit` — each cell holds a digit in `[1,9]` or
  `0` (empty). Cell coordinates are row-major: row `r` in `[0,9)`, column `c`
  in `[0,9)`.

Three parallel structures complete the board model:

- `solution: array[9][9] of digit` — the completed, unique solution for the
  current puzzle. It is never rendered to the player until the game ends; it is
  the reference for win detection (Section 6).
- `given: array[9][9] of bool` — `true` for cells pre-filled at game start.
  Given cells are locked: digit input and erase are rejected for them.
- `errors: array[9][9] of bool` — real-time conflict flags (Section 4). A cell
  with `errors[r][c] === true` currently violates a Sudoku rule.

The board model is isomorphic to the flat 81-indexed view via
`index = r * 9 + c` when serialization convenience matters.

## 3. Turn and state management

A single game state object carries everything needed to render and advance the
game:

- `grid` — the 9x9 player-visible board (Section 2).
- `solution` — the unique completed solution.
- `given` — the locked-cell mask.
- `errors` — the real-time conflict mask.
- `selected` — the currently selected cell `{ r, c }`, or `null` when no cell
  is selected. Digit input targets the selected cell.
- `filled_count` — the number of non-empty cells (drives progress feedback).
- `status` — one of `PLAYING` or `WON`.

Action flow (single state mutation per action):

1. `select_cell(r, c)` — sets `selected`. Selection is allowed for any cell
   (given or empty) so keyboard navigation can move across the whole grid.
2. `input_digit(d)` — valid only when the game is `PLAYING`, a cell is
   selected, that cell is empty, and the cell is not given. Writes digit `d`
   into the cell, recomputes conflict flags, and evaluates the win condition.
3. `erase_cell()` — valid only when the game is `PLAYING`, a cell is selected,
   and that cell is not given and not already empty. Clears the cell, recomputes
   conflict flags, and evaluates the win condition.

Rows that contain no empty cells are, by definition, full; there is no
turn-taking (single player). A `WON` state is terminal: no further input or
erase action mutates the state.

## 4. Real-time rule validation

After every accepted `input_digit` or `erase_cell`, the `errors` mask is
recomputed from scratch by scanning every unit:

- 9 rows, 9 columns, and 9 boxes (each box is the 3x3 block rooted at
  `(br * 3, bc * 3)` for `br, bc in [0,3)`).

Within each unit, cells holding the same non-empty digit are all flagged:
`errors` is set on every cell of a duplicated digit, not just the newly placed
one. This guarantees a player immediately sees *both* conflicting cells, whether
the conflict partner is a given or another entered digit. A digit is therefore
**valid** (rule-clean) exactly when no unit contains it twice; the check runs
against the current player-visible board, so conflicts with givens are caught
just like conflicts between two entered digits.

The player is free to keep a conflicting digit on the board (standard Sudoku
behavior) — it is highlighted, and it simply cannot be part of a correct
solution, so it blocks the win condition until fixed.

## 5. Puzzle generation

Each new game generates a fresh puzzle with a **unique solution**:

1. **Base grid.** A canonical valid completed grid is relabeled by a random
   permutation of the digits 1-9, and its rows/columns are permuted within
   their 3-row bands / 3-column stacks (and bands/stacks permuted among
   themselves). These transformations preserve validity, yielding a uniformly
   random completed board used as `solution`.
2. **Digging.** Starting from the full grid, cells are visited in random order
   and temporarily cleared. A cell is *kept* cleared only if the resulting
   puzzle still has exactly one solution, verified by a backtracking solver
   that counts solutions up to a limit of 2 (`count_solutions(grid, 2) === 1`);
   otherwise the cell is restored. Digging stops once a target number of cells
   (45) has been removed, leaving 36 givens.

The uniqueness guarantee is important: it makes rule-clean play deterministic —
with a unique solution, a fully filled rule-clean board is necessarily the
solution, so "validated against the rules" and "correct" coincide at the end.

## 6. Win detection

A win occurs exactly when the player-visible grid equals the hidden solution:

- After every accepted `input_digit` / `erase_cell`, compare `grid[r][c]` with
  `solution[r][c]` for all 81 cells. If every cell matches, set
  `status = WON`.

Equality with `solution` implies every cell is non-empty and rule-clean, so the
win is reported precisely when the puzzle is solved correctly. Because puzzles
have a unique solution (Section 5), a full board that is rule-clean but not the
solution cannot occur; a board that differs from the solution always contains a
detectable conflict or an empty cell, so no separate "stuck" state is needed.

## 7. Input and UI layout

Two input paths feed the same logic:

- **Physical keyboard:** digit keys `1`-`9` (input), arrow keys (move the
  selected cell), and `Backspace` / `Delete` / `0` (erase the selected cell).
- **On-screen number pad:** nine digit buttons plus an erase (`⌫`) button wired
  to the same handlers.

Layout (centered column, matching the existing games):

- the game title and a "Back to Game Selection" link,
- an `aria-live` status line describing the current objective or the win,
- a validation message line that explains rule conflicts, locked cells, and
  pending-selection hints,
- the 9x9 board (`role="grid"` with `role="gridcell"` cells) with visually
  separated 3x3 boxes,
- the on-screen number pad,
- a "New Game" button and a "How to Play" link (separate `rules.html` page,
  mirroring Wordle).

Board feedback states:

- `given` — starting-puzzle cells (locked, visually distinct).
- `selected` — the currently targeted cell.
- `peer-row` / `peer-col` / `peer-box` — cells sharing a row, column, or box
  with the selection, softly highlighted.
- `error` — cells involved in a rule conflict (duplicate in row/column/box).

Win feedback mirrors Tic Tac Toe: a celebratory announcement in the status line
plus a short pop animation.

## 8. State reset

`reset()` (via the "New Game" button) returns the game to a clean starting
state:

- a brand-new puzzle is generated (fresh `solution`, `grid`, and `given`),
- `errors` cleared, `selected` cleared, `filled_count` reset,
- `status` set to `PLAYING`.

Reset may be invoked at any time (mid-game or after a win). No memory of the
previous game is retained.

## 9. Invariants and constraints

These hold after construction, every accepted action, and every reset:

- `grid[r][c]` is `0` or an integer in `[1,9]` for all `r`, `c`.
- `given[r][c]` implies `grid[r][c]` is a non-empty digit, and no accepted
  action changes a given cell.
- `errors[r][c]` is true for a cell if and only if its digit is duplicated
  within its row, column, or box.
- The puzzle generated by `reset()` has exactly one solution, and that solution
  is `solution`.
- If `status != PLAYING`, no input or erase action mutates the state.
- `filled_count` equals the number of non-empty cells in `grid`.

# Tic Tac Toe Game — Design Document (Initial Pass)

This document describes the design for a Tic Tac Toe game. It is a design
document only; no implementation is included. The sections below specify how
the board is represented in code, how turn/state is managed, how win and draw
conditions are detected, and how the game resets.

## 1. Scope

A single human-vs-human (Player X vs Player O) Tic Tac Toe game on a standard
3x3 board. The design focuses on the core game logic and avoids UI/framework
concerns so it can be ported to any presentation layer later.

## 2. Grid representation

The board is represented as a fixed 2-dimensional array with **3 rows and 3
columns**:

- `grid: array[3][3] of marker` (equivalently `array[9]` flat when memory or
  serialization convenience matters; the two views are isomorphic and indexed
  by `row * 3 + column`).

Each cell holds one of three values:

- `EMPTY` — cell is unoccupied.
- `X`   — occupied by Player X.
- `O`   — occupied by Player O.

`EMPTY` is the initial value of every cell. Cell coordinates are addressed in
row-major order: row `r` in `[0,3)`, column `c` in `[0,3)`, flat index
`i = r * 3 + c`.

The `EMPTY` marker doubles as the "legal move" signal: a move is legal if and
only if the target cell equals `EMPTY`.

## 3. Turn and state management

A small game state object carries everything needed to render and advance the
game:

- `grid` — the 3x3 board (see Section 2).
- `current_player` — the player whose turn it is (`X` or `O`).
- `move_count` — the number of moves placed so far (drives draw detection).
- `status` — one of `PLAYING`, `WIN_X`, `WIN_O`, or `DRAW`.

Turn flow (single state mutation per action):

1. `apply_move(row, col)` validates coordinates are in range and the target
   cell is `EMPTY`. If invalid, the move is rejected and the state is
   unchanged.
2. Place `current_player` in the cell.
3. Increment `move_count`.
4. Evaluate win/draw (Section 4).
5. If still `PLAYING`, flip `current_player` to the other marker; otherwise the
   game is terminal and no further moves are accepted.

The rule "X always moves first" is guaranteed by initializing `current_player`
to `X` at reset.

## 4. Win-detection algorithm

A win occurs when three identical, non-`EMPTY` markers form a continuous line.
On a 3x3 board there are exactly **8 candidate lines**:

- 3 horizontal lines (one per row).
- 3 vertical lines (one per column).
- 2 diagonal lines (main `\` and anti `\` i.e. `/`).

Detection is evaluated only after a marker is placed. To be efficient, the
check is anchored on the just-placed cell:

1. Let `m` be the marker just placed and `(r, c)` its location.
2. If `m == EMPTY`, return "no win".
3. Because any winning line containing `m` must pass through `(r, c)`, test
   only the up to 4 line directions that pass through `(r, c)`:
   - Horizontal: cells `(r, 0)`..`(r, 2)` all equal `m`.
   - Vertical: cells `(0, c)`..`(2, c)` all equal `m`.
   - Main diagonal (only if `r == c`): cells `(0,0)`, `(1,1)`, `(2,2)` all
     equal `m`.
   - Anti diagonal (only if `r + c == 2`): cells `(0,2)`, `(1,1)`, `(2,0)` all
     equal `m`.
4. If any of these direction checks succeed, the player owning `m` wins.

The direction guards (only checking diagonals when the placed cell lies on that
diagonal) avoid redundant scans but remain correct: any line of three must
include the placed cell, so checking only lines through that cell is sufficient
and complete.

## 5. Draw detection

A draw occurs when all 9 cells are filled and no player has won. Because every
win is detected immediately in Section 4, reaching a full board without a win
is the draw condition:

- Draw is declared when `move_count == 9` **and** no win was detected.

Ordering note: the win check runs before the draw check at each move. Since a
played cell can complete a line, a win is always reported in preference to a
draw for the same terminal state. Draw is exactly the complement: board full,
no line of three.

## 6. State reset

`reset()` returns the game to a clean starting state:

- Every cell of `grid` set to `EMPTY`.
- `current_player` set to `X`.
- `move_count` set to `0`.
- `status` set to `PLAYING`.

Reset may be invoked at any time (new game, after a win, or after a draw). No
memory of the previous game is retained. A `PLAYING` state guarantees a legal
next move is always available until a terminal state is reached.

## 7. Invariants

These hold after construction, every accepted move, and every reset:

- `move_count` equals the number of non-`EMPTY` cells.
- `0 <= move_count <= 9`.
- If `status != PLAYING`, no legal moves are accepted.
- `current_player` is always `X` or `O` (never `EMPTY`).
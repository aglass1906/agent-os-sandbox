# Connect Four Game — Design Document (Initial Pass)

This document describes the design for a Connect Four game. It is a design
document only; no implementation is included. The sections below specify how
the board is represented in code, how discs are dropped into columns, how turn
and state are managed, how win and draw conditions are detected, and how the
game resets.

## 1. Scope

A single human-vs-human (Red vs Yellow) Connect Four game on a standard
6-row by 7-column board. The design focuses on the core game logic and avoids
UI/framework concerns so it can be ported to any presentation layer later.

## 2. Grid representation

The board is represented as a fixed 2-dimensional array with **6 rows and 7
columns**:

- `grid: array[6][7] of marker`

Each cell holds one of three values:

- `EMPTY` — cell is unoccupied.
- `R`   — occupied by a Red disc.
- `Y`   — occupied by a Yellow disc.

`EMPTY` is the initial value of every cell. Cell coordinates are addressed in
row-major order: row `r` in `[0,6)`, column `c` in `[0,7)`. Row `0` is the top
of the board; row `5` is the bottom. A disc is only ever placed in the lowest
open row of its column (Section 3), so the top row of a column is occupied only
once that column is full.

## 3. Disc-drop mechanics

A move targets a **column**, never an individual cell:

1. Validate the column index is an integer in `[0,7)`.
2. Reject the move if a terminal state has been reached (status is no longer
   `PLAYING`).
3. Find the **lowest open row** in the column: scan rows from `5` up to `0`
   and take the first row whose cell is `EMPTY`.
4. If no open row exists (the column is full), reject the move.
5. Place the current player's marker in `grid[row][col]`.

Because every row below the chosen row in that column is already occupied, the
disc appears to "fall" to the lowest open row. Rejected moves leave the state
unchanged.

## 4. Turn and state management

A small game state object carries everything needed to render and advance the
game:

- `grid` — the 6x7 board (see Section 2).
- `current_player` — the player whose turn it is (`R` or `Y`).
- `move_count` — the number of discs placed so far (drives draw detection).
- `status` — one of `PLAYING`, `WIN_RED`, `WIN_YELLOW`, or `DRAW`.
- `winner` — the winning marker, or `EMPTY` while playing / on a draw.
- `win_cells` — the coordinates `{r, c}` of the four-or-more winning discs.
- `last_move` — the `{r, c}` coordinates of the most recently placed disc.

Turn flow (single state mutation per action):

1. `drop_disc(col)` validates the column per Section 3. If invalid, the move
   is rejected and the state is unchanged.
2. Place `current_player` in the lowest open row of the column.
3. Increment `move_count`.
4. Evaluate win/draw (Sections 5 and 6).
5. If still `PLAYING`, flip `current_player` to the other marker; otherwise
   the game is terminal and no further moves are accepted.

The rule "Red always moves first" is guaranteed by initializing
`current_player` to `R` at reset.

## 5. Win-detection algorithm

A win occurs when four identical, non-`EMPTY` markers form a continuous line.
Winning lines may be horizontal, vertical, or diagonal (both `/` and `\`).

Detection is evaluated only after a disc is placed. To be efficient, the check
is anchored on the just-placed cell `(r, c)`:

1. Let `m` be the marker just placed and `(r, c)` its location.
2. If `m == EMPTY`, return "no win".
3. Because any winning line containing `m` must pass through `(r, c)`, test
   only the 4 line directions through `(r, c)`:
   - Horizontal `(0, 1)`: count consecutive `m` cells to the left and right
     of `(r, c)`.
   - Vertical `(1, 0)`: count consecutive `m` cells upward and downward.
   - Diagonal `(1, 1)` (southeast/northwest).
   - Anti-diagonal `(1, -1)` (southwest/northeast).
4. For each direction, take the union of `(r, c)` with all contiguous matching
   cells in both extending directions. If that run contains at least **4**
   cells, the player owning `m` wins and the run's cell coordinates become the
   winning line.
5. Return `[]` if no direction reaches 4 in a row.

The anchored check remains complete: a line of four that includes `(r, c)`
must lie on one of these four directions, so no winning line is missed.

## 6. Draw detection

A draw occurs when all 42 cells are filled and no player has won. Because
every win is detected immediately in Section 5, reaching a full board without
a win is the draw condition:

- Draw is declared when `move_count == 42` **and** no win was detected.

Ordering note: the win check runs before the draw check at each move. Since a
played disc can complete a line, a win is always reported in preference to a
draw for the same terminal state. Draw is exactly the complement: board full,
no line of four.

## 7. State reset

`reset()` returns the game to a clean starting state:

- Every cell of `grid` set to `EMPTY`.
- `current_player` set to `R`.
- `move_count` set to `0`.
- `status` set to `PLAYING`.
- `winner` set to `EMPTY`, `win_cells` and `last_move` cleared.

Reset may be invoked at any time (new game, after a win, or after a draw). No
memory of the previous game is retained. A `PLAYING` state guarantees a legal
next move is always available until a terminal state is reached.

## 8. Invariants

These hold after construction, every accepted move, and every reset:

- `move_count` equals the number of non-`EMPTY` cells.
- `0 <= move_count <= 42`.
- Discs never float: for every non-`EMPTY` cell `(r, c)`, every cell `(r', c)`
  with `r' > r` (below it in the same column) is also non-`EMPTY`.
- If `status != PLAYING`, no legal moves are accepted.
- `current_player` is always `R` or `Y` (never `EMPTY`).
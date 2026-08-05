# Wordle Game — Design Document

This document describes the design for a browser-based Wordle game. It is a
design document; the sections below specify how the letter grid is represented
in code, how turns/attempts are managed, how letter feedback is classified, and
how win/lose conditions are detected. It follows the standard Wordle rules.

## 1. Scope

A single-player browser game in which the player has **6 attempts** to guess a
hidden **5-letter word**. The player types letters via the physical keyboard or
an on-screen keyboard. After each submitted guess every letter receives visual
feedback (correct position, present in word, or absent), and the game ends in a
win when the guess equals the answer or in a loss when all 6 attempts are
exhausted without a match.

The design focuses on the core game logic and a minimal, accessible UI.

## 2. Grid representation

The playing surface is a fixed 2-dimensional letter grid with **6 rows** (one
per attempt) and **5 columns** (one per letter position):

- `grid: array[6][5] of letter` — each cell holds either a single uppercase
  letter `A`–`Z` or `""` (empty). Cell coordinates are row-major: row `r` in
  `[0,6)`, column `c` in `[0,5)`.

Each cell carries a *feedback state* that is unset while the row is being
edited and assigned once the row is submitted:

- `correct` — the letter is in the answer **and** in the same position.
- `present` — the letter is in the answer but in a different position.
- `absent` — the letter is not in the answer (or is a duplicate already fully
  consumed by the answer).
- `empty` — feedback not yet assigned (row still being edited).

The hidden answer is stored separately from the grid (`answer: string[5]`) and
is not rendered to the player until the game ends.

## 3. Turn and state management

A single game state object carries everything needed to render and advance the
game:

- `answer` — the hidden 5-letter target word (uppercase).
- `grid` — the 6x5 letter grid (Section 2).
- `feedback` — a parallel 6x5 array of per-cell feedback states.
- `current_row` — the attempt (row) currently being edited, in `[0,6)`.
- `current_col` — the next column to fill within the current row, in `[0,5]`.
- `status` — one of `PLAYING`, `WON`, or `LOST`.
- `keyboard` — a map of each letter `A`–`Z` to its best-known feedback state
  (see Section 5) for driving on-screen key colors.

Attempt flow (single state mutation per action):

1. `input_letter(letter)` — if the game is `PLAYING` and `current_col < 5`,
   write the uppercase letter into `grid[current_row][current_col]` and advance
   `current_col`. Rows that are already submitted are not editable.
2. `delete_letter()` — if the game is `PLAYING` and `current_col > 0`, clear the
   letter at `current_col - 1` and decrement `current_col`. Deleting resets the
   affected cell to an unset/empty feedback state.
3. `submit_guess()` — valid only when the game is `PLAYING` and the current row
   is full (`current_col == 5`). The guess must also be a valid word from the
   dictionary (see Section 6); invalid words are rejected with the row left
   unchanged. On a valid guess:
   - Classify each cell's feedback per Section 4.
   - Update the keyboard map (Section 5).
   - Evaluate win/lose per Section 6 and advance `current_row` if the game
     continues.

The rule "the first guess occupies row 0, guesses proceed top to bottom" is
guaranteed by initializing `current_row` to `0` at reset.

## 4. Letter feedback classification

Feedback is assigned per submitted row, anchored on the answer. To be faithful
to Wordle's duplicate-handling rules, a two-pass algorithm over the row's 5
columns is used:

1. **First pass (correct / absent):** for each column `c`, if
   `guess[c] == answer[c]` mark the cell `correct` and consume that occurrence
   of the letter in the answer (decrement its remaining count); otherwise mark
   it as a candidate for `present`/`absent`.
2. **Second pass (present / absent):** for each unassigned column `c`, if the
   guessed letter still has remaining occurrences in the answer (not already
   consumed by correct placements or earlier `present` marks) mark it `present`
   and consume one occurrence; otherwise mark it `absent`.

This guarantees a duplicated guess letter is only shown `present` or `correct`
as many times as it actually occurs in the answer, never more.

## 5. Keyboard and visual feedback

Two input paths feed the same logic:

- **Physical keyboard:** keydown events for `A`–`Z` (case-insensitive),
  `Backspace` (delete), and `Enter` (submit).
- **On-screen keyboard:** one button per letter plus `Enter` and
  `Backspace`/`⌫` buttons wired to the same handlers.

The `keyboard` map records, for each letter, the *best* state observed so far.
The state hierarchy is `correct` > `present` > `absent`: a later guess may only
raise a key's state, never lower it. On-screen keys are re-rendered with the
matching CSS class after every submit so the player sees accumulated knowledge
across attempts. The grid cells are likewise re-rendered with their per-cell
feedback classes.

## 6. Win/lose detection and dictionary

A win occurs exactly when a submitted guess equals `answer`:

- On `submit_guess()`, if `guess == answer`, set `status = WON` and stop
  accepting further input.

A loss occurs when the current row was the last attempt and the guess did not
match:

- If `status` is still `PLAYING` after a non-matching submit and
  `current_row == 5`, set `status = LOST`.

Until the terminal condition, `current_row` advances by 1 and editing continues
in the next row.

**Dictionary:** a curated uppercase word list of valid 5-letter guesses
(`VALID_WORDS`) and a subset of answer words (`ANSWERS`). A guess is legal only
if it is `PLAYING`, the row is full, and the word is present in `VALID_WORDS`.
`ANSWERS` should be a subset of `VALID_WORDS` so any answer is also a legal
guess. The answer is chosen uniformly at random from `ANSWERS` at game start.

## 7. State reset

`reset()` returns the game to a clean starting state:

- `grid` set to all empty cells.
- `feedback` set to all empty states.
- `answer` re-chosen at random from `ANSWERS`.
- `current_row` set to `0`.
- `current_col` set to `0`.
- `status` set to `PLAYING`.
- `keyboard` reset so every letter is unknown.

Reset may be invoked at any time (new game, after a win, or after a loss). No
memory of the previous game is retained.

## 8. Invariants

These hold after construction, every accepted action, and every reset:

- `grid[r][c]` is either `""` or an uppercase letter for all `r`, `c`.
- `current_row` and `current_col` are in `[0,6)` and `[0,5]` respectively.
- Cells in rows `< current_row` are fully submitted; rows `>= current_row` are
  empty or partially edited.
- If `status != PLAYING`, no input or submit action mutates the state.
- `answer` has length 5 and is an element of `VALID_WORDS`.

## 9. UI layout and technical requirements

- **Layout:** a centered column containing the game title, a status/announcement
  line, the 6x5 letter grid, an on-screen QWERTY keyboard, and a "New Game"
  button.
- **Feedback colors (WCAG-aware pairing of hue + strong contrast):**
  - `correct` — green background.
  - `present` — yellow/amber background.
  - `absent` — dark gray background.
  - unsubmitted — light neutral background.
- **Reveal animation:** a short per-cell flip reveals feedback in order, then a
  win/lose banner (e.g. "You won!" / "You lost — the word was X") is announced.
- **Accessibility:** the status line uses `aria-live="polite"`; the on-screen
  keys are real buttons; the grid uses a `role="grid"` container with labeled
  rows so the revealed answer is readable by assistive tech.
- **Technology:** vanilla HTML + CSS + JavaScript with no external framework or
  build step, mirroring the existing game's structure and file layout.

# Simon Game — Design Document

This document describes the design for a Simon memory game. It is a design
document only; no implementation is included. The sections below specify how
the sequence is generated, how turn and state are managed, how success and
failure conditions are detected, and how the game resets.

## 1. Scope

A single-player Simon game. The computer generates a sequence of color flashes
and the player must repeat the sequence correctly. The design focuses on the
core game logic and avoids UI/framework concerns so it can be ported to any
presentation layer later.

## 2. Color Pad Representation

The game uses four colored pads, each identified by a unique color constant:

- `GREEN` — Green pad.
- `RED` — Red pad.
- `YELLOW` — Yellow pad.
- `BLUE` — Blue pad.

Each pad also maps to a keyboard shortcut:

| Pad | Keyboard |
|-----|----------|
| Green | `1` |
| Red | `2` |
| Yellow | `3` |
| Blue | `4` |

The set of valid colors is fixed: `{GREEN, RED, YELLOW, BLUE}`.

## 3. Sequence Representation

The game sequence is an ordered array of color values:

- `sequence: array of color` — grows by one element per level.

At level `n`, the sequence has exactly `n` elements. Each element is one of the
four valid colors, chosen uniformly at random (or via any deterministic
generator with sufficient entropy).

The sequence is append-only during normal play: each new level adds exactly one
random color to the end of the existing sequence.

## 4. Turn and State Management

A small game state object carries everything needed to render and advance the
game:

- `sequence` — the full color sequence (Section 3).
- `level` — the current level (number of completed rounds; starts at 0).
- `score` — the player's cumulative score.
- `highScore` — the best score achieved in the current browser session.
- `status` — one of `IDLE`, `DEMO`, `PLAYER`, `WON`, or `GAME_OVER`.
- `inputIndex` — the player's current position in the sequence during input.

### Status values

| Status | Meaning |
|--------|---------|
| `IDLE` | Game has not started or has been reset. Awaiting Start. |
| `DEMO` | Computer is flashing the sequence. Player input is disabled. |
| `PLAYER` | Player's turn to repeat the sequence. Input is accepted. |
| `WON` | Player completed the current sequence correctly. Brief celebration. |
| `GAME_OVER` | Player pressed the wrong pad. Game is over. |

### State transitions

```
IDLE  --[start]--> DEMO
DEMO  --[sequence complete]--> PLAYER
PLAYER --[correct input at end of sequence]--> WON
WON   --[after celebration delay]--> DEMO  (next level)
PLAYER --[wrong input]--> GAME_OVER
GAME_OVER --[start]--> DEMO  (new game)
```

## 5. Demo Phase (Computer's Turn)

During `DEMO` status:

1. A new random color is appended to `sequence`.
2. `level` is incremented.
3. The full sequence is displayed one pad at a time with a configurable delay
   between flashes (e.g., 600 ms on, 400 ms off).
4. After the last pad flashes, status transitions to `PLAYER` and
   `inputIndex` is reset to `0`.

During `DEMO`, all player input (clicks and key presses) is ignored.

## 6. Player Input Phase

During `PLAYER` status:

1. The player presses a pad (click or keyboard shortcut).
2. The pressed color is compared to `sequence[inputIndex]`.
3. **If correct:**
   - `inputIndex` is incremented.
   - If `inputIndex == sequence.length`, the entire sequence was completed
     correctly. Status transitions to `WON`.
4. **If incorrect:**
   - Status transitions to `GAME_OVER`.
   - No further input is accepted.

## 7. Win Condition

A win for the current level occurs when `inputIndex == sequence.length` during
`PLAYER` status. This means the player successfully repeated every element of
the current sequence in order.

After a level win:
1. `score` is updated (e.g., `score += level`).
2. `highScore` is updated if `score > highScore`.
3. Status briefly becomes `WON` to allow for a visual celebration.
4. After a short delay, status transitions back to `DEMO` for the next level.

There is no upper level limit: the game continues indefinitely until the
player makes a mistake.

## 8. Game Over Condition

Game over occurs when the player presses a pad whose color does not match
`sequence[inputIndex]` during `PLAYER` status.

After game over:
1. Status becomes `GAME_OVER`.
2. No further input is accepted until the player presses Start.
3. The final score and level are displayed.
4. Pressing Start resets the game to `IDLE` then immediately transitions to
   `DEMO` for a new game.

## 9. State Reset

`reset()` returns the game to a clean starting state:

- `sequence` is cleared (empty array).
- `level` is set to `0`.
- `score` is set to `0`.
- `status` is set to `IDLE`.
- `inputIndex` is set to `0`.
- `highScore` is preserved (not reset by game reset).

Reset may be invoked at any time (new game, after a win, or after game over).
No memory of the previous game's sequence is retained.

## 10. Invariants

These hold after construction, every accepted input, and every reset:

- `sequence.length == level` (one element per completed level).
- `0 <= inputIndex <= sequence.length`.
- `0 <= level`.
- If `status == PLAYER`, then `0 <= inputIndex < sequence.length`.
- If `status == IDLE` or `status == DEMO`, player input is ignored.
- If `status == GAME_OVER`, no further input is accepted until reset.
- `highScore >= score` at all times.

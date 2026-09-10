# Asteroids Redux — Design Document (Initial Pass)

This document describes the design for the Asteroids Redux game. It is a
design document only; the companion `game.js`, `index.html`, and `style.css`
files implement the system described here. The sections below specify the
coordinate model, the entity types, the state machine, ship control and
firing, asteroid spawning and wave progression, collision handling and
scoring, and how the game resets.

## 1. Scope

A single-player arcade shooter rendered on an HTML5 canvas. The player pilots a
ship that rotates and thrusts in a friction-damped asteroid field, firing
bullets to split and destroy asteroids. Destroying every asteroid advances the
wave; losing the ship's last life ends the game. The design focuses on the core
game logic and rendering loop, and avoids any external dependencies or asset
files (all visuals are vector-drawn and all feedback is procedural).

## 2. Coordinate system

The play area is a logical canvas of **800- by 600-pixels**. CSS scales the
canvas to fit any viewport width while the logical resolution stays constant,
so physics and rendering remain resolution-independent.

The arena is a **torus**: an entity that moves off one edge reappears on the
opposite edge. Wrapping is applied per-axis:

- `x = wrap(x + vx * dt, 800)`
- `y = wrap(y + vy * dt, 600)`

Renderers draw wrapped copies of entities near the borders so objects visibly
slide across edges instead of popping out of existence. No collision is tested
across the seam, so gameplay is equivalent to a flat screen with wrap-around
motion.

## 3. The ship

The ship is a triangle with a known heading, position, and velocity:

- `x`, `y` — position in arena coordinates.
- `angle` — heading in radians; `-PI/2` (pointing up) at spawn.
- `vx`, `vy` — velocity in px/s.
- `radius` — collision radius (12 px).
- `thrusting` — whether the engine flame should render.
- `alive` — false once the last life is spent.
- `invulnTimer` — seconds of post-respawn invulnerability.

Rotation is direct: holding a left/right control rotates `angle` at a fixed
angular speed. Thrust accelerates the ship along its heading; exponential
drag (`exp(-drag * dt)`) plus a hard speed cap keep velocities bounded. Input
comes from keyboard (arrows/WASD) and from on-screen touch buttons that feed
the same control flags.

## 4. Bullets

Bullets spawn at the ship's nose and inherit the firing heading at a fixed
speed:

- travel in a straight line, wrapping on both axes.
- expire after `BULLET_LIFETIME` seconds.
- are capped to a small concurrent maximum so fire is rate-limited.
- fire rate is gated by a cooldown timer.

Holding the fire control fires continuously at the cooldown rate. Each bullet
is a pure projectile: it never accelerates and never interacts with the ship.

## 5. State machine and game states

Every mutable value lives on a single state object initialized by
`createInitialState()`, so a new game is a clean object rebuild. The game is
always in exactly one of four statuses:

- `READY` — awaiting the first Start. Input is ignored.
- `PLAYING` — the simulation runs and all controls are live.
- `PAUSED` — the simulation is frozen; rendering continues.
- `GAME_OVER` — all lives are spent; no further input is accepted.

Transitions:

- Start (button, or Space/Enter while `READY` or `GAME_OVER`) → `PLAYING`.
- Pause (button or `P`) toggles `PLAYING` ↔ `PAUSED`.
- Last life lost → `GAME_OVER`.
- Tab visibility loss auto-pauses a running game.

`reset()`/`startNewGame()` restores score, lives, wave, ship, bullets,
asteroids, particles, and all timers to their initial defaults.

## 6. Asteroids and waves

Asteroids are jagged polygons defined by a center, a heading, a speed, a
radius, and a fixed per-rock set of vertex radii (so each rock has a stable
silhouette). Three sizes exist — large (46 px), medium (26 px), and small
(14 px) — and only large rocks appear at wave start.

Wave progression:

- A new game and every wave cleared spawn `3 + wave` large asteroids, capped.
- Spawns are rejected within a safe radius around the ship so a fresh wave is
  never an immediate cheap kill.
- Asteroid speed scales modestly with the wave number.
- Destroying the final asteroid clears the wave and spawns the next one.

When any asteroid is destroyed, it scores and, if larger than small, splits
into two children one size smaller, each inheriting a boosted speed. This is
the classic split mechanic that turns one large rock into four small ones over
two hits.

## 7. Collisions and scoring

Collisions are tested as simple distance checks (circle vs circle):

- **Bullet vs asteroid**: within `asteroid.radius + bullet` → destroy. The
  rock is removed, split down a size if possible, particles spawn, and score
  is awarded.
- **Ship vs asteroid**: within `ship.radius + asteroid.radius` and the ship is
  not invulnerable → the ship is "destroyed". One life is lost; a fresh ship
  respawns at the center with `SHIP_RESPAWN_INVULN` seconds of invulnerability
  (rendered as a blink). At zero lives the game transitions to `GAME_OVER`.

Because the ship spawns at the exact center and asteroids wrap torus-style,
the invulnerability window exists specifically to prevent instant respawn
deaths. Collisions are only resolved while `status === PLAYING`.

Scoring is size-based:

| Rock size | Points |
| --- | --- |
| Large | 20 |
| Medium | 50 |
| Small | 100 |

## 8. Rendering and feedback

Rendering is a `requestAnimationFrame` loop with a fixed-step-invariant `dt`
(clamped to 50 ms so a background tab never causes giant jumps):

1. Clear the canvas to the void background.
2. Draw the static starfield (deterministic pseudo-random, resolution-scaled).
3. Draw particles (fading, decelerating points from hits and explosions).
4. Draw bullets and asteroids with neon glow strokes, wrapped at edges.
5. Draw the ship with a thrust flame and invulnerability blink.
6. Draw overlays for `READY`, `PAUSED`, and `GAME_OVER`.

HUD values (score, lives, wave) live in the DOM and update on every frame.
Status changes are announced twice: the visible status line uses an
`aria-live="polite"` region, and decisive events (wave start, life lost, game
over) are pushed to a visually hidden `role="status"` region so screen readers
announce them. Under `prefers-reduced-motion` particle bursts are suppressed
and CSS transitions removed.

## 9. Invariants

These hold after construction, every accepted input, and every reset:

- `status` is always exactly one of `READY`, `PLAYING`, `PAUSED`, `GAME_OVER`.
- `score`, `lives`, and `wave` are never negative; `lives` starts at 3.
- Bullets, asteroids, and particles arrays never contain expired entries after
  an update pass completes.
- A destroyed asteroid is always removed from the asteroid list exactly once.
- Ship position always lies within the torus arena after an update.
- No gameplay mutations occur while `status !== PLAYING`.
- `reset()` restores every field to its `createInitialState()` default.
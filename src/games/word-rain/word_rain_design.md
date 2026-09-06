# Word Rain — Technical Design Specification

> **Document Type:** Technical Design Specification
> **Target Path:** `src/games/word-rain/word_rain_design.md`
> **Source Documents:** Grounded in `PROJECT_OVERVIEW_DRAFT.md`, `Coding Conventions and Style Guide`, `AGENTS.md`, and `docs/Architecture.md`.

This document is the design source of truth for the **Word Rain** game. It is a
design document only; no implementation is included. It specifies the system
architecture, the state schema, the lexical data structures, the falling-loop
physics, scoring/streak mechanics, multi-modal input rules, Web Speech / Web
Audio synthesis, and accessibility guidelines. It follows the same canonical
format and section structure as `src/games/simon/simon_design.md` and the other
`*_design.md` specifications in the Hub.

---

## 1. Scope

Word Rain is a single-player, audio-comprehension arcade game. At the start of
each **round**, the game presents an English concept in the Prompt panel and
pronounces the associated **target word** aloud using the Web Speech API. Three
words then fall down a three-lane arena; the player must select the word that
matches the spoken target before it falls off the bottom of the arena.

The design focuses on the core game logic, a deterministic state machine, the
lexical data layer, the physics loop, and the browser-native audio subsystems.
It avoids framework concerns so it can be ported to any presentation layer
later.

Grounded in `PROJECT_OVERVIEW_DRAFT.md`, the Hub is "a collection of browser
games built with vanilla HTML, CSS, and JavaScript" and every self-contained
game module "has no external frameworks, build tools, package managers, or
backend dependencies." Word Rain honors those constraints: __1__ HTML file,
__1__ CSS file, __1__ strict-mode ES6+ JavaScript file, zero runtime
dependencies.

---

## 2. Grounding in canonical constraints

The following rules from the `Coding Conventions and Style Guide` are binding on
every Word Rain source file and are encoded in the sections below
*(Source: `Coding Conventions and Style Guide`)*:

1. **Strict mode** — `game.js` begins with `"use strict";`.
2. **State centralization** — all mutable runtime state lives in a single,
   schema-defined state object (Section 5); no module-level mutable globals.
3. **State lifecycle** — state is initialized via `createInitialState()` and
   re-initialized via `resetGame()` (Sections 5 and 15).
4. **Predictable mutations** — all state changes flow through the deterministic
   action handlers of `applyAction()` (Section 6); invalid actions are rejected
   and leave state unchanged.
5. **Naming conventions** — `UPPERCASE_SNAKE` constants (e.g. `MAX_LIVES`,
   `FALL_TIME_BASE_MS`, `STATUS_PLAYING`), `camelCase` variables/functions
   (e.g. `createInitialState`, `pickDistractors`), `PascalCase` classes
   (e.g. `AudioEngine`, `WordRainClock`).

The following `PROJECT_OVERVIEW_DRAFT.md` constraints are binding as well
*(Source: `PROJECT_OVERVIEW_DRAFT.md`)*:

- Browser-native stack only: HTML5, ES6+, CSS3, Web Speech API, Web Audio API.
- Zero external dependencies: no `npm`/`yarn`, no bundlers, no backend.
- Self-contained isolation under `src/games/word-rain/` with no shared runtime
  JS modules.
- Multi-modal interaction support: mouse, keyboard, and touch
  (see `docs/Architecture.md` and `AGENTS.md`).
- Terminal states block further input mutations until a clean reset.
- Reset restores all state variables and DOM elements to initial defaults.
- Responsive and accessible, with dynamic `aria-live` status announcements.

---

## 3. System architecture

Word Rain is decomposed into six cooperating subsystems, all owned by the
single `game.js` module so the game remains self-contained:

| Subsystem | Responsibility | Principal interfaces |
|-----------|----------------|----------------------|
| **State machine** | Owns the schema-defined state object, status enum, and deterministic `applyAction()` reducer. | `createInitialState()`, `applyAction(action, payload)` |
| **Lexical layer** | Owns the immutable lexicon, band index, target picker, and distractor sampler. | `pickTarget(level, rng)`, `pickDistractors(target, level, rng)` |
| **Falling loop** | Advances round physics on a `requestAnimationFrame` clock with a fixed timestep; owns `velocityY(level)` escalation. | `tick(dtMs)`, `renderLoop(nowMs)` |
| **Input subsystem** | Normalizes keyboard, click, tap, and button events into reducer actions. | `onKeyDown`, `onPointerDown`, `onClick` |
| **Speech subsystem** | Web Speech API text-to-speech for prompt words. | `speakPrompt()`, `listenTap()` |
| **Audio engine** | Procedural Web Audio API oscillator synthesis for feedback cues. | `AudioEngine` class, `playCorrect()`, `playWrong()`, `playLifeLost()`, `playGameOver()`, `playSpawn()` |

Data flow is one-directional: input events and timers produce **actions**;
`applyAction()` performs guarded, deterministic mutations; the render pass
paints state to the DOM; the speech and audio engines respond to side effects
that actions schedule.

---

## 4. Constants

All tunable game parameters are module-level `UPPERCASE_SNAKE` constants so
difficulty tuning never touches game logic:

| Constant | Value | Meaning |
|----------|-------|---------|
| `LANE_COUNT` | `3` | Number of vertical falling lanes. |
| `MAX_LIVES` | `3` | Starting lives; reaching `0` ends the game. |
| `SCORE_BASE` | `10` | Points awarded for a single correct pick before streak bonus. |
| `STREAK_TIER` | `5` | Correct picks per streak-multiplier tier. |
| `WORDS_PER_LEVEL` | `5` | Correct picks that advance `level` by 1. |
| `FALL_TIME_BASE_MS` | `8000` | Round fall duration at level 0. |
| `FALL_TIME_MIN_MS` | `2500` | Lower bound on round fall duration. |
| `FALL_DECAY` | `0.93` | Per-level multiplier on fall duration (`0 < FALL_DECAY < 1`). |
| `RECENT_WINDOW` | `6` | Rounds a word stays excluded from re-selection. |
| `BAND_COUNT` | `4` | Number of difficulty bands (`0`–`3`). |
| `AUDIO_MASTER_GAIN` | `0.15` | Master gain for synthesized tones (dB-safe, non-clipping). |

---

## 5. State schema and status enum

The entire runtime state is a single plain object. It is returned by
`createInitialState()` and is the only object ever mutated by the reducer.

```
state = {
  status: "STATUS_IDLE" | "STATUS_PLAYING" | "STATUS_PAUSED" | "STATUS_GAME_OVER",

  rng:      { seed, next() },        // deterministic PRNG (mulberry32); next() -> [0,1)
  score:        0,                   // cumulative points
  highScore:    0,                   // session best; preserved across resets
  streak:       0,                   // consecutive correct picks
  lives:        MAX_LIVES,           // remaining hearts
  totalCorrect: 0,                   // lifetime correct picks in current game
  level:        0,                   // difficulty level driving fall velocity

  round: {
    id:        0,                    // monotonically increasing round id
    fallTimeMs: FALL_TIME_BASE_MS,   // this round's fall duration (Section 9)
    elapsedMs:  0,                   // time since round spawn
    resolved:  false                 // set true exactly once when round ends
  },

  lanes: [                           // exactly LANE_COUNT entries
    { entryId, lane, selected: false, gone: false },
    ...
  ],
  targetEntryId: null,               // entryId of the correct word this round

  prompt: {
    entryId:      null,              // entryId of the current target
    concept:      "",                // visible English gloss in the Prompt panel
    lastSpokenRound: -1              // round id when TTS last spoke the word
  },

  sound: {
    ttsSupported: true,              // "speechSynthesis" in window
    audioSupported: true,            // "AudioContext" in window
    audioReady: false                // true after first user gesture
  },

  lastEvent: null                    // {action, ok, detail} diagnostic last result
}
```

### 5.1 Status values

| Status | Meaning |
|--------|---------|
| `STATUS_IDLE` | Game has not started, or has been reset. Awaiting Start. |
| `STATUS_PLAYING` | A round is active; falling physics and input are enabled. |
| `STATUS_PAUSED` | Round is suspended; physics and input are frozen. |
| `STATUS_GAME_OVER` | `lives == 0`. Terminal; only start/restart are accepted. |

The status values are exactly the four constants `STATUS_IDLE`,
`STATUS_PLAYING`, `STATUS_PAUSED`, and `STATUS_GAME_OVER`, declared at module
scope so strict-mode spelling errors surface immediately.

---

## 6. Deterministic state transitions

All state mutation flows through one reducer with an action table. An action is
**accepted** only when the `(status, action)` cell is allowed; otherwise the
action is **rejected** and state is unchanged (the rejection is recorded in
`lastEvent` and, if visible to the player, announced via the live region).

### 6.1 Action table

| Action | `IDLE` | `PLAYING` | `PAUSED` | `GAME_OVER` |
|--------|--------|-----------|----------|-------------|
| `startGame` | accepted | replay: reset then begin | replay: reset then begin | replay: reset then begin |
| `pauseGame` | ignored | accepted | ignored | ignored |
| `resumeGame` | ignored | ignored | accepted | ignored |
| `restartGame` | = `startGame` | accepted (reset then begin) | = `startGame` | = `startGame` |
| `selectLane(n)` | rejected | accepted if `0 <= n < LANE_COUNT` and round unresolved | rejected | rejected |
| `selectWord(entryId)` | rejected | accepted if round unresolved | rejected | rejected |
| `tick(dtMs)` | no-op | advances physics / resolves round | no-op | no-op |
| `listenPrompt()` | rejected | accepted (re-speak prompt) | rejected | rejected |
| `visibilityHidden()` | no-op | → `PAUSED` | no-op | no-op |

### 6.2 Transition diagram

```
STATUS_IDLE     --[startGame]-----------------------------> STATUS_PLAYING
STATUS_PLAYING  --[pauseGame | visibilityHidden]----------> STATUS_PAUSED
STATUS_PAUSED   --[resumeGame]----------------------------> STATUS_PLAYING
STATUS_PLAYING  --[lives becomes 0]------------------------> STATUS_GAME_OVER
STATUS_GAME_OVER --[startGame | restartGame]---------------> STATUS_PLAYING (fresh game)
STATUS_IDLE     --[startGame]-----------------------------> STATUS_PLAYING  (fresh game)
```

### 6.3 Round resolution rules

While `STATUS_PLAYING` and `round.resolved == false`, at most one resolution
fires per round, in priority order:

1. **Correct pick** — `selectLane(n)`/`selectWord(id)` where the selected
   entry id equals `targetEntryId`.
   - `score += SCORE_BASE * streakMultiplier(streak)` with
     `streakMultiplier(s) = 1 + floor(s / STREAK_TIER)`.
   - `streak += 1`, `totalCorrect += 1`, `level = floor(totalCorrect / WORDS_PER_LEVEL)`.
   - `highScore = max(highScore, score)`.
   - Mark `round.resolved = true`; schedule `spawnRound()` for the next round.
   - Play `correct` audio cue; announce score/streak.
2. **Wrong pick** — a `selectLane`/`selectWord` whose entry id differs from
   `targetEntryId`.
   - `lives -= 1`, `streak = 0`.
   - Mark `round.resolved = true`; schedule `spawnRound()`.
   - Play `wrong` audio cue; announce "wrong word".
3. **Missed target** — `round.elapsedMs >= round.fallTimeMs` while the round is
   still unresolved (the target word has fallen past the bottom of the arena).
   - `lives -= 1`, `streak = 0`.
   - Mark `round.resolved = true`; schedule `spawnRound()`.
   - Play `lifeLost` audio cue; announce the word that was missed.

After any resolution, if `lives <= 0` the game transitions to
`STATUS_GAME_OVER` **instead of** spawning a new round; the arena is frozen and
the final score/level are displayed. Because the rules above are total and
ordered, exactly one of {correct, wrong, miss} applies to any round and each
round mutates state at most once — the resolution is deterministic.

---

## 7. Lexical data structures

The lexicon is a fixed, immutable array authored in `game.js` (or an adjacent
data file loaded without network I/O). Every entry conforms to the lexical
schema:

```
lexical entry = {
  id:         string,   // unique stable key, e.g. "welcome"
  word:       string,   // the answer as spoken/displayed, lowercase, e.g. "welcome"
  concept:    string,   // short English gloss shown in the Prompt panel, e.g. "a friendly greeting"
  difficulty: 0 | 1 | 2 | 3   // difficulty band (mapped from level in Section 8)
}
```

Derived indexes are computed once at module load:

- `LEXICON_BY_ID: Map<id, entry>` — O(1) lookup of any entry.
- `BAND_INDEX: Array<entry[]>` — one list per difficulty band (`BAND_COUNT`
  lists), used by target and distractor selection.
- `RECENT_IDS: ring buffer (capacity RECENT_WINDOW)` — ids recently shown, to
  avoid immediate repeats. It is runtime state, not lexical data, and lives in
  the state object as `rng`-driven bookkeeping.

### 7.1 Target selection

`pickTarget(level, rng)` selects the entry for the current round:

1. Map `level` to a difficulty band:
   `band(level) = level < 3 ? 0 : level < 8 ? 1 : level < 15 ? 2 : 3`, clamped
   to `[0, BAND_COUNT)`.
2. From `BAND_INDEX[band]`, exclude any id present in `RECENT_IDS`.
3. Uniformly sample one remaining entry via `rng.next()`.
4. Append the chosen id to `RECENT_IDS`, evicting the oldest past the
   `RECENT_WINDOW` capacity.

### 7.2 Distractor selection heuristics

`pickDistractors(target, level, rng)` returns the `LANE_COUNT - 1 = 2`
distractor entries for the round, applying the following heuristics in order:

1. **Same band** — sample from `BAND_INDEX[target.difficulty]` so distractors
   are comparable in difficulty to the target.
2. **No self-match** — `entry.id != target.id`; a round never contains two
   copies of the target word.
3. **No recent repeat** — exclude ids in `RECENT_IDS`.
4. **No duplicate words** — reject candidates whose `word` equals the current
   `target.word` (normalized for case) or a word already chosen this round.
5. **Recency-weighted shuffle** — the remaining candidates are Fisher–Yates
   shuffled with the seeded `rng`, and the first two are taken. When the band
   pool is too small to yield two non-repeating candidates, the sampler falls
   back to the nearest populated band (`band ± 1`) before widening; this keeps
   the round always renderable with exactly 3 distinct words.
6. **Orthographic de-confliction (default)** — candidates whose `word` shares
   the target's leading letter and length are deprioritized, so the round tests
   listening comprehension rather than visual scanning. Tunable: at
   `level >= 8`, one distractor may intentionally match the leading letter to
   raise difficulty. This is a soft preference applied during shuffle, never a
   hard exclusion, so selection remains total and deterministic per seed.

### 7.3 Round spawn

`spawnRound()` (state `PLAYING`) composes one round:

- `targetEntryId = pickTarget(level, rng).id`.
- `distractors = pickDistractors(target, level, rng)`.
- `targetLane = floor(rng.next() * LANE_COUNT)`.
- `lanes[x].entryId` is set to the target in the target lane and to the two
  distractors in the remaining lanes, in shuffled order.
- `round.fallTimeMs = fallTime(level)`, `round.elapsedMs = 0`,
  `round.resolved = false`, `round.id += 1`.
- `prompt.entryId` / `prompt.concept` are updated; the round's word is spoken
  via the speech subsystem once `prompt.lastSpokenRound != round.id`
  (Section 12).

---

## 8. Falling loop physics

### 8.1 Loop and clock

The arena is driven by a single `requestAnimationFrame` loop that only runs
while `status == STATUS_PLAYING`. Physics uses a **fixed timestep accumulator**
(step `dt = 16.666... ms`):

```
tick(dtMs):
  if status != PLAYING: return
  round.elapsedMs += dtMs
  if round.resolved: return
  for lane in lanes:
    lane.y = progress(round.elapsedMs / round.fallTimeMs) * (ARENA_HEIGHT_PX + 2 * WORD_HEIGHT_PX) - WORD_HEIGHT_PX
  if round.elapsedMs >= round.fallTimeMs:
    resolveRound("miss")        // only the target exiting the bottom matters
```

Word vertical position is a pure function of elapsed fraction, so a single
round is **replayable bit-for-bit** for a fixed seed and level. Distractors exit
the bottom at the same instant as the target (all share the round's
`fallTimeMs`); only the *target* exit triggers the miss resolution, per
Section 6.3.

### 8.2 Velocity escalation formulas

Difficulty escalates by reducing the round fall duration each level. The
canonical formula is exponential decay:

```
fallTime(level) = max(FALL_TIME_MIN_MS, round(FALL_TIME_BASE_MS * FALL_DECAY^level))
velocityY(level, arenaH) = (arenaH + 2 * WORD_HEIGHT_PX) / fallTime(level)
```

- `FALL_DECAY^level` is evaluated as `Math.pow(FALL_DECAY, level)`.
- `round()` maps to the nearest integer millisecond, keeping `fallTimeMs` an
  integer for stable HUD display.
- `velocityY` is expressed in px/ms so the loop computes `lane.y` by
  elapsed-fraction without per-frame float drift (Section 8.1).

A linear approximation — `fallTime(level) = max(MIN, BASE - level * STEP)` with
`STEP = (BASE - MIN) / MAX_LEVEL` — is acceptable for implementation but must
keep the ground truth `FALL_DECAY` formula as the specification source. Either
choice must preserve the invariant `FALL_TIME_MIN_MS <= fallTime(level) <=
FALL_TIME_BASE_MS` for all levels.

### 8.3 Pause semantics

On `pauseGame`/`visibilityHidden`, the loop's last `requestAnimationFrame` is
cancelled, `performance.now()` deltas are discarded, and no physics advances
until `resumeGame`. Because position is elapsed-fraction based and the loop
re-seeds `round.elapsedMs` from the saved value, a resume resumes exactly where
it paused — no word "teleports."

---

## 9. Scoring and streak mechanics

| Mechanic | Rule |
|----------|------|
| Correct pick | `score += SCORE_BASE * (1 + floor(streak / STREAK_TIER))`; `streak += 1` |
| Wrong pick | `lives -= 1`; `streak = 0` |
| Missed target | `lives -= 1`; `streak = 0` |
| Game over | `lives == 0` → `STATUS_GAME_OVER`; no further mutations |
| High score | `highScore = max(highScore, score)` after every score increase |
| Level | `level = floor(totalCorrect / WORDS_PER_LEVEL)` (drives Section 8.2) |

The streak multiplier is therefore discrete: `streak >= 5` doubles base score,
`streak >= 10` triples it, and so on. Streak and high score are both preserved
across pause/resume and both displayed in the HUD (score, streak, lives) already
present in `index.html`.

---

## 10. Multi-modal input mapping

The input subsystem listens for `keydown`, `click`/`pointerdown`, the arena
`focus`/`blur` pair, and `visibilitychange`. All events normalize into reducer
actions (Section 6); events that resolve to a rejected action are quietly
dropped.

| Input | Action | Applies when |
|-------|--------|--------------|
| `1` | `selectLane(0)` | `STATUS_PLAYING` |
| `2` | `selectLane(1)` | `STATUS_PLAYING` |
| `3` | `selectLane(2)` | `STATUS_PLAYING` |
| Click on a falling word | `selectWord(entryId)` (from `data-word-id`) | `STATUS_PLAYING` |
| Tap on a falling word | `selectWord(entryId)` (`pointerdown`/`pointerup` within the word's hit bounds) | `STATUS_PLAYING` |
| `Space` / `P` | toggle `pauseGame` / `resumeGame` | `STATUS_PLAYING` / `STATUS_PAUSED` |
| `Enter` | `startGame` (or `restartGame`) | `IDLE`, `PLAYING`, `PAUSED`, `GAME_OVER` |
| `L` | `listenPrompt()` (re-speak the current word) | `STATUS_PLAYING` |
| Click Start button | `startGame` / `restartGame` | any status |
| Click Listen button | `listenPrompt()` | `STATUS_PLAYING`, `STATUS_IDLE` (idle speaks the example only if a target exists) |

Supplementary `preventDefault` rules: `Space` and `1`–`3` are prevented from
scrolling/re-activating focused buttons; the arena element carries
`tabindex="0"` and receives `focus()` on Start so keyboard play never requires a
mouse. Click/tap hit-testing resolves the top-most word whose axis-aligned
bounds contain the pointer; touch targets must be at least `44 x 44 px`.

---

## 11. Web Speech synthesis architecture

The Speech subsystem wraps `window.speechSynthesis` and
`SpeechSynthesisUtterance` (Web Speech API) with a minimal, dependency-free
interface:

```
speakPrompt():
  if !sound.ttsSupported or status in {IDLE without prompt}: return
  speechSynthesis.cancel()                 // avoid utterance queue backlog
  u = new SpeechSynthesisUtterance(target.word)
  u.lang = "en-US"; u.rate = 0.9; u.volume = 1.0
  speechSynthesis.speak(u)
  prompt.lastSpokenRound = round.id
```

Rules:

1. **Capability probe** — at load, `sound.ttsSupported = "speechSynthesis" in
   window`. When unsupported, `sound.audioReady` gating is skipped and the
   game remains fully playable through the visible `concept` + rendered word
   spelling fallback (Section 13).
2. **User-gesture gating** — the `AudioContext` and any TTS utterances are only
   created after the first `startGame` click/tap/Enter, satisfying browser
   autoplay policies. `sound.audioReady = true` is set on that first gesture.
3. **Voice selection** — `voiceschanged` caches a preferred `en-US` voice; if
   none is available, the default voice is used. Voice choice never affects
   game state.
4. **Re-speak** — the Listen button and `L` key re-invoke `speakPrompt()`
   without affecting round state.
5. **Auto-speak** — each new round speaks its word once via
   `prompt.lastSpokenRound` tracking, so a round is never spoken twice from an
   accidental duplicate call.
6. **Cleanup** — on `pagehide`, `speechSynthesis.cancel()` is called so a
   partially-uttered word never resumes on a hidden page.

---

## 12. Web Audio synthesis architecture

All feedback audio is **procedurally synthesized** — no audio assets, no
external audio files — using the Web Audio API primitives `OscillatorNode`,
`GainNode`, and `AudioParam` envelope ramps `(Source: `Coding Conventions and
Style Guide`/`docs/Architecture.md`: audio is synthesized with the Web Audio
API)`.

The `AudioEngine` class holds a single shared `AudioContext` (created lazily on
the first user gesture) and a master `GainNode` at `AUDIO_MASTER_GAIN`. The
tone primitive is:

```
tone(freq, durMs, type, attackMs, releaseMs):
  osc = audioCtx.createOscillator(); osc.type = type; osc.frequency.value = freq
  g   = audioCtx.createGain()
  g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(1, t0 + attackMs)
  g.gain.exponentialRampToValueAtTime(0.001, t0 + durMs)
  osc.connect(g).connect(masterGain).connect(audioCtx.destination)
  osc.start(t0); osc.stop(t0 + durMs)
```

Cue map:

| Cue | Trigger | Synthesis recipe |
|-----|---------|------------------|
| `playCorrect()` | correct pick | two-note rising arpeggio: `tone(440, 120, "triangle")` then `tone(660, 160, "triangle")` |
| `playWrong()` | wrong pick | `tone(110, 200, "square")` low buzz |
| `playLifeLost()` | life lost (miss or wrong) | descending sweep `tone(220, 300, "sawtooth")` → `110 Hz` |
| `playGameOver()` | → `STATUS_GAME_OVER` | three descending notes `392`→`330`→`262` Hz, each 180 ms |
| `playSpawn()` | new round | short `tone(880, 60, "sine")` blip |
| `playListen()` | Listen/L pressed | `tone(1320, 60, "sine")` high blip |

Lifecycle rules:

- `audioCtx.suspend()` on `pauseGame`; `audioCtx.resume()` on `resumeGame`;
  `audioCtx.close()` on `pagehide` `(Source: Simon game conventions)`.
- No cue is scheduled while `status == STATUS_PAUSED` or
  `status == STATUS_GAME_OVER` except the `playGameOver()` cue itself at the
  transition.
- `sound.audioSupported = "AudioContext" in window` gates all cues; the game
  runs silently (never throws) when unsupported.

---

## 13. Accessibility guidelines

Grounded in `AGENTS.md` and `Coding Conventions and Style Guide`
accessibility requirements:

1. **Sound-independent play** — the Prompt panel renders the English `concept`
   as visible text (as in the existing `index.html`), and when TTS is
   unavailable the target `word` is rendered in the prompt with a "spelling"
   fallback role, so the game is fully playable by deaf/hard-of-hearing and
   motion-disabled users. Audio is an enhancement, never the only channel.
2. **Live regions** — a single `role="status"` `aria-live="polite"`
   `aria-atomic="true"` region announces: current spoken word, correct/wrong/
   missed results, remaining lives, and game-over. Crucial state changes
   (life loss, game over) also use the semantic HUD values so screen readers
   hear deltas.
3. **Keyboard operability** — the complete mapping table (Section 10) makes the
   game playable without a mouse; the arena is focusable (`tabindex="0"`) and
   all buttons are real `<button>` elements with visible focus rings.
4. **Touch access** — pointer events resolve taps; touch targets are ≥ `44 x
   44 px`; on viewports < `768px` the virtual lanes remain full-width tap
   columns (matching the touch-overlay convention in `docs/Architecture.md`).
5. **Contrast & color** — text and background pairs meet WCAG AA; color is never
   the sole indicator (word identity is textual, lanes are numbered 1–3 in the
   HUD legend). High-contrast focus and hover states use both border and
   background changes.
6. **Reduced motion** — under `prefers-reduced-motion`, the loop disables
   non-essential animation (spawn pop-in, lane wobble, readout tweening). The
   falling physics itself is core gameplay and retains its slower-start, flat
   motion; the pause controls give reduced-motion users full control of pacing.
7. **Pause affordance** — `Space`/`P`, an on-screen Pause button, and
   automatic pause on `visibilitychange`/`blur` ensure players are never rushed
   by off-screen state.
8. **Responsive layout** — the arena spans ≥ `3` lanes at all widths, the HUD
   stacks gracefully below `480px`, and no fixed pixel minimums cause
   horizontal scroll above `320px`.

---

## 14. Hub integration

Per `PROJECT_OVERVIEW_DRAFT.md` and `AGENTS.md`, when the game is implemented
and verified, `src/games/index.html` will link a **Word Rain** hub card pointing
at `src/games/word-rain/index.html`, and the game page already provides
"Back to Game Selection" navigation to the hub. This document is committed
standalone; hub linkage is a later implementation-phase step.

---

## 15. Reset procedures

`resetGame()` — invoked by `startGame`/`restartGame` from any non-`PAUSED`
status — runs `createInitialState()` and then:

- preserves `highScore` from the outgoing state (session-best survives resets),
- preserves the `rng` seed policy: a new game draws a fresh seed via
  `Math.random()` so subsequent games are not bit-identical (per-game
  reproducibility, not cross-game),
- clears `RECENT_IDS`,
- nullifies round/lanes/prompt,
- sets `status = "STATUS_PLAYING"` and immediately calls `spawnRound()`.

Reset restores every state variable and DOM element (score, streak, lives,
prompt, arena) to initial defaults. Pause is explicitly released on reset — a
reset from `STATUS_PAUSED` behaves as `startGame`, never resuming a stale
round.

---

## 16. Invariants

These hold after construction, every accepted action, and every reset:

- `status` is always one of the four enum values in Section 5.1.
- `lanes.length == LANE_COUNT`; every `lanes[i].lane == i` with unique lanes.
- While a round is unresolved in `STATUS_PLAYING`, exactly one lane holds
  `targetEntryId`, and the other two lanes hold distinct distractors that never
  equal the target's `word` or `entryId`.
- `FALL_TIME_MIN_MS <= round.fallTimeMs <= FALL_TIME_BASE_MS`.
- `0 <= score`, `0 <= streak`, `0 <= lives <= MAX_LIVES`, `highScore >= score`.
- If `status != STATUS_PLAYING`, no input or tick action mutates the state.
- Each round resolves exactly once (`round.resolved` flips once, then a new
  round spawns or the game ends).
- Every rejected action leaves the state object bit-identical.
- All audio/TTS side effects are gated on capability probes and never throw;
  unsupported browsers play the game silently.

---

## 17. Verification criteria

Before the game is marked complete *(per `PROJECT_OVERVIEW_DRAFT.md` readiness
criteria)*:

1. Gameplay and state transitions verified in standard browsers (Chrome,
   Firefox, Safari); `test_canary_badge.sh` exits `0`.
2. Invalid actions (e.g. `selectLane` when idle/paused/over, `selectLane(9)`)
   do not mutate state; verified via the `lastEvent.rejected` counter.
3. `resetGame()` restores all state variables and DOM elements to initial
   defaults and preserves `highScore`.
4. Responsive layout verified down to `< 768px` and `< 320px` viewports,
   including full-width touch lanes.
5. Correct/wrong/miss resolutions, streak tiers, velocity escalation, and
   pause/resume resume-at-same-position behavior verified against the
   formulas in Sections 6 and 8.
6. `src/games/index.html` gains the Word Rain hub card with back-navigation
   when the implementation lands.

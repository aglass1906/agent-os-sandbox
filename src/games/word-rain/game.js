"use strict";

const STATUS_IDLE = "STATUS_IDLE";
const STATUS_PLAYING = "STATUS_PLAYING";
const STATUS_PAUSED = "STATUS_PAUSED";
const STATUS_GAME_OVER = "STATUS_GAME_OVER";

const LANE_COUNT = 3;
const MAX_LIVES = 3;
const SCORE_BASE = 10;
const STREAK_BONUS = 5;
const STREAK_TIER = 5;
const WORDS_PER_LEVEL = 5;
const FALL_TIME_BASE_MS = 8000;
const FALL_TIME_MIN_MS = 2500;
const FALL_DECAY = 0.93;
const RECENT_WINDOW = 6;
const BAND_COUNT = 4;
const AUDIO_MASTER_GAIN = 0.15;
const TONE_ATTACK_MS = 0.01;
const TONE_RELEASE_MS = 0.08;
const CHIME_NOTE_1_HZ = 523;
const CHIME_NOTE_2_HZ = 659;
const CHIME_NOTE_1_MS = 140;
const CHIME_NOTE_2_MS = 220;
const CHIME_STEP_MS = 90;
const MISS_BUZZER_HZ = 110;
const MISS_BUZZER_MS = 260;
const GAME_OVER_NOTES = [392, 330, 262];
const GAME_OVER_NOTE_MS = 200;
const GAME_OVER_STEP_MS = 140;
const STREAK_BONUS_FREQUENCY_HZ = 880;
const STREAK_BONUS_FREQUENCY_2_HZ = 1174.66;
const STREAK_BONUS_MS = 130;
const STREAK_BONUS_STEP_MS = 80;

const WORD_HEIGHT_PX = 48;
const SPAWN_STAGGER_PX = 26;
const DEFAULT_ARENA_HEIGHT_PX = 432;
const FALL_VELOCITY_BASE_PS = 60;
const FALL_VELOCITY_MAX_PS = 220;
const FALL_VELOCITY_STEP_PS = 16;
const MAX_FRAME_DELAY_MS = 250;
const ROUND_TRANSITION_MS = 900;
const LIVES_ICON = "\u2665";
const PROMPT_IDLE_TEXT =
  "Press Start to begin. Match the Spanish word to its English meaning before it falls.";

const BUILTIN_WORDS = [
  { id: "sun", word: "sol", concept: "the star that lights the day", difficulty: 0 },
  { id: "cat", word: "gato", concept: "a small furry pet", difficulty: 0 },
  { id: "cup", word: "taza", concept: "holds your drink", difficulty: 0 },
  { id: "fish", word: "pez", concept: "swims in the sea", difficulty: 0 },
  { id: "leaf", word: "hoja", concept: "grows on a tree", difficulty: 1 },
  { id: "star", word: "estrella", concept: "a dot that lights the night", difficulty: 1 },
  { id: "bridge", word: "puente", concept: "crosses over a river", difficulty: 1 },
  { id: "storm", word: "tormenta", concept: "strong wind and heavy rain", difficulty: 1 },
  { id: "whale", word: "ballena", concept: "the largest ocean animal", difficulty: 2 },
  { id: "castle", word: "castillo", concept: "a king's stone home", difficulty: 2 },
  { id: "snake", word: "serpiente", concept: "a long animal without legs", difficulty: 2 },
  { id: "rainbow", word: "arcoíris", concept: "a colorful arc after rain", difficulty: 2 }
];

const BAND_INDEX = buildBandIndex();

let state = createInitialState();
let animationFrameId = null;
let pendingTimers = [];
let wordElementByEntryId = new Map();
let audioContext = null;
let audioMasterGain = null;
let activeSounds = [];

function buildBandIndex() {
  const bands = [];
  for (let index = 0; index < BAND_COUNT; index += 1) {
    bands.push([]);
  }
  for (const entry of BUILTIN_WORDS) {
    bands[entry.difficulty].push(entry);
  }
  return bands;
}

function createInitialState() {
  return {
    status: STATUS_IDLE,
    score: 0,
    streak: 0,
    totalCorrect: 0,
    lives: MAX_LIVES,
    speed: FALL_TIME_BASE_MS,
    level: 0,
    currentPrompt: "",
    fallingWords: [],
    sessionHighScore: 0,
    roundId: 0,
    targetEntryId: null,
    roundResolved: true,
    recentIds: [],
    rngSeed: 0,
    rng: null,
    lastFrameTimeMs: null
  };
}

function cancelAnimationFrameId() {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

function cancelPendingTimers() {
  for (let i = 0; i < pendingTimers.length; i += 1) {
    clearTimeout(pendingTimers[i]);
  }
  pendingTimers = [];
}

function cancelPendingSpeech() {
  if (!hasDom()) return;
  if (typeof window === "undefined") return;
  if ("speechSynthesis" in window) {
    try {
      window.speechSynthesis.cancel();
    } catch (error) {
      return;
    }
  }
}

function resetGame() {
  cancelAnimationFrameId();
  cancelPendingTimers();
  stopAllAudio();
  cancelPendingSpeech();
  wordElementByEntryId.clear();
  const previousHighScore = state.sessionHighScore;
  state = createInitialState();
  state.sessionHighScore = previousHighScore;
  return state;
}

function generateSeed() {
  return Math.floor(Math.random() * 0x100000000);
}

function mulberry32(seed) {
  let value = seed >>> 0;
  return function next() {
    value |= 0;
    value = (value + 0x6d2b79f5) | 0;
    let t = Math.imul(value ^ (value >>> 15), 1 | value);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function initRng(seed) {
  const generator = mulberry32(seed);
  return { seed: seed, next: generator };
}

function shuffle(items, rng) {
  const result = items.slice();
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    const tmp = result[i];
    result[i] = result[j];
    result[j] = tmp;
  }
  return result;
}

function recordRecentId(recentIds, entryId) {
  recentIds.push(entryId);
  if (recentIds.length > RECENT_WINDOW) {
    recentIds.shift();
  }
}

function pickTarget(band, rng, recentIds) {
  const pool = BAND_INDEX[band].filter(function (entry) {
    return recentIds.indexOf(entry.id) === -1;
  });
  const source = pool.length > 0 ? pool : BAND_INDEX[band];
  return source[Math.floor(rng() * source.length)];
}

function pickDistractors(target, band, count, rng, recentIds) {
  const chosen = [];
  let widenDelta = 0;
  while (chosen.length < count) {
    let pool = [];
    for (let delta = 0; delta <= widenDelta; delta += 1) {
      if (band + delta < BAND_COUNT) {
        pool = pool.concat(BAND_INDEX[band + delta]);
      }
      if (delta > 0 && band - delta >= 0) {
        pool = pool.concat(BAND_INDEX[band - delta]);
      }
    }
    const candidates = shuffle(
      pool.filter(function (entry) {
        if (entry.id === target.id) return false;
        if (recentIds.indexOf(entry.id) !== -1) return false;
        for (let i = 0; i < chosen.length; i += 1) {
          if (chosen[i].id === entry.id) return false;
        }
        return true;
      }),
      rng
    );
    if (candidates.length === 0) {
      widenDelta += 1;
      continue;
    }
    chosen.push(candidates[0]);
  }
  return chosen;
}

function spawnOffsetFor(columnIndex) {
  return -(WORD_HEIGHT_PX + SPAWN_STAGGER_PX + columnIndex * SPAWN_STAGGER_PX);
}

function fallVelocityPxPerSecond(streak) {
  const clampedStreak = Math.max(0, streak);
  return Math.min(
    FALL_VELOCITY_MAX_PS,
    FALL_VELOCITY_BASE_PS + clampedStreak * FALL_VELOCITY_STEP_PS
  );
}

function wordCurrentY(word) {
  if (word === null || typeof word !== "object") return -WORD_HEIGHT_PX;
  if (Number.isFinite(word.y)) return word.y;
  if (Number.isFinite(word.offsetY)) return word.offsetY;
  return -WORD_HEIGHT_PX;
}

function hasDom() {
  return typeof document !== "undefined";
}

function arenaHeightPx() {
  if (!hasDom()) return DEFAULT_ARENA_HEIGHT_PX;
  const arena = document.getElementById("arena");
  if (!arena) return DEFAULT_ARENA_HEIGHT_PX;
  return arena.clientHeight || DEFAULT_ARENA_HEIGHT_PX;
}

function hasCrossedFloor(y, floorY) {
  return y >= floorY;
}

function tick(dtMs) {
  if (state.status !== STATUS_PLAYING) return;
  if (state.roundResolved) return;
  const velocityPxMs = fallVelocityPxPerSecond(state.streak) / 1000;
  const floorY = arenaHeightPx();
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    const word = state.fallingWords[i];
    word.y = wordCurrentY(word) + velocityPxMs * dtMs;
    positionWordElement(word);
  }
  detectFloorCrossings(floorY);
}

function detectFloorCrossings(floorY) {
  let crossedTarget = null;
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    const word = state.fallingWords[i];
    if (hasCrossedFloor(wordCurrentY(word), floorY) && word.entryId === state.targetEntryId) {
      crossedTarget = word;
      break;
    }
  }
  if (crossedTarget !== null) {
    resolveMiss(crossedTarget);
    return;
  }
  const remaining = [];
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    const word = state.fallingWords[i];
    if (hasCrossedFloor(wordCurrentY(word), floorY)) {
      cleanupDistractor(word);
    } else {
      remaining.push(word);
    }
  }
  state.fallingWords = remaining;
}

function cleanupDistractor(word) {
  const element = wordElementByEntryId.get(word.entryId);
  if (element && element.parentNode) {
    element.parentNode.removeChild(element);
  }
  wordElementByEntryId.delete(word.entryId);
}

function removeDistractorsFromArena(missedWord) {
  const remaining = [];
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    const word = state.fallingWords[i];
    if (word.entryId === missedWord.entryId) {
      remaining.push(word);
    } else {
      cleanupDistractor(word);
    }
  }
  state.fallingWords = remaining;
}

function resolveMiss(missedWord) {
  state.lives -= 1;
  state.streak = 0;
  state.roundResolved = true;
  markMissedVisual(missedWord);
  removeDistractorsFromArena(missedWord);
  playMissBuzzer();
  syncHud();
  announce(
    "Missed \u201c" + missedWord.word + "\u201d. One life lost. " + state.lives + " lives left."
  );
  if (state.lives <= 0) {
    endGame();
  } else {
    scheduleNextRound();
  }
}

function markMissedVisual(missedWord) {
  if (!hasDom()) return;
  const element = wordElementByEntryId.get(missedWord.entryId);
  if (element) {
    element.classList.add("incorrect");
  }
  const arena = document.getElementById("arena");
  if (arena) {
    arena.classList.remove("life-lost");
    void arena.offsetWidth;
    arena.classList.add("life-lost");
  }
}

function findWordByEntryId(entryId) {
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    if (state.fallingWords[i].entryId === entryId) {
      return state.fallingWords[i];
    }
  }
  return null;
}

function findWordByLane(laneNumber) {
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    if (state.fallingWords[i].lane === laneNumber) {
      return state.fallingWords[i];
    }
  }
  return null;
}

function markCorrectVisual(word) {
  if (!hasDom()) return;
  const element = wordElementByEntryId.get(word.entryId);
  if (element) {
    element.classList.add("correct");
  }
}

function markIncorrectVisual(pickedWord) {
  if (!hasDom()) return;
  const pickedElement = wordElementByEntryId.get(pickedWord.entryId);
  if (pickedElement) {
    pickedElement.classList.add("incorrect");
  }
  const targetElement = wordElementByEntryId.get(state.targetEntryId);
  if (targetElement) {
    targetElement.classList.add("correct");
  }
  const arena = document.getElementById("arena");
  if (arena) {
    arena.classList.remove("life-lost");
    void arena.offsetWidth;
    arena.classList.add("life-lost");
  }
}

function resolveCorrect(word) {
  const gained = SCORE_BASE + state.streak * STREAK_BONUS;
  state.score += gained;
  state.streak += 1;
  state.totalCorrect += 1;
  state.level = Math.floor(state.totalCorrect / WORDS_PER_LEVEL);
  state.roundResolved = true;
  markCorrectVisual(word);
  speakSpanish(word.word);
  playCorrectChime();
  if (state.streak > 0 && state.streak % STREAK_TIER === 0) {
    playStreakBonus();
  }
  syncHud();
  announce(
    "Correct! \u201c" +
      word.word +
      "\u201d is a match. +" +
      gained +
      " points. Streak is now " +
      state.streak +
      "."
  );
  scheduleNextRound();
}

function resolveIncorrect(pickedWord) {
  state.lives -= 1;
  state.streak = 0;
  state.roundResolved = true;
  markIncorrectVisual(pickedWord);
  playMissBuzzer();
  syncHud();
  const targetWord = findWordByEntryId(state.targetEntryId);
  const targetLabel = targetWord === null ? state.currentPrompt : targetWord.word;
  announce(
    "Wrong pick. \u201c" +
      pickedWord.word +
      "\u201d does not match. The correct word was \u201c" +
      targetLabel +
      "\u201d. One life lost. " +
      state.lives +
      " lives left."
  );
  if (state.lives <= 0) {
    endGame();
  } else {
    scheduleNextRound();
  }
}

function handleWordSelection(entryId) {
  if (state.status !== STATUS_PLAYING || state.roundResolved) {
    return { accepted: false, action: "selectWord", reason: "STATE_GUARD" };
  }
  if (typeof entryId !== "string" || entryId === "") {
    return { accepted: false, action: "selectWord", reason: "INVALID_TARGET" };
  }
  const word = findWordByEntryId(entryId);
  if (word === null) {
    return { accepted: false, action: "selectWord", reason: "UNKNOWN_WORD" };
  }
  const wasCorrect = word.entryId === state.targetEntryId;
  if (wasCorrect) {
    resolveCorrect(word);
  } else {
    resolveIncorrect(word);
  }
  return { accepted: true, action: "selectWord", word: word.word, wasCorrect: wasCorrect };
}

function selectLane(laneNumber) {
  if (state.status !== STATUS_PLAYING || state.roundResolved) {
    return { accepted: false, action: "selectLane", reason: "STATE_GUARD" };
  }
  if (typeof laneNumber !== "number" || laneNumber < 0 || laneNumber >= LANE_COUNT) {
    return { accepted: false, action: "selectLane", reason: "OUT_OF_RANGE" };
  }
  const word = findWordByLane(laneNumber);
  if (word === null) {
    return { accepted: false, action: "selectLane", reason: "NO_WORD_IN_LANE" };
  }
  const wasCorrect = word.entryId === state.targetEntryId;
  if (wasCorrect) {
    resolveCorrect(word);
  } else {
    resolveIncorrect(word);
  }
  return { accepted: true, action: "selectLane", lane: laneNumber, wasCorrect: wasCorrect };
}

const SPANISH_LANG = "es-ES";
const SPANISH_LANG_FALLBACK = "es-MX";
const SPANISH_RATE = 0.875;

function speakSpanish(text) {
  if (!hasDom()) return;
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) return;
  if (typeof text !== "string" || text === "") return;
  let utterance;
  try {
    utterance = new SpeechSynthesisUtterance(text);
  } catch (error) {
    return;
  }
  utterance.lang = SPANISH_LANG;
  utterance.rate = SPANISH_RATE;
  utterance.volume = 1;
  try {
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  } catch (error) {
    return;
  }
}

function speakPrompt() {
  if (state.currentPrompt === "") return;
  const targetWord = findWordByEntryId(state.targetEntryId);
  const text = targetWord === null ? state.currentPrompt : targetWord.word;
  speakSpanish(text);
}

function audioSupported() {
  return typeof window !== "undefined" &&
    !!(window.AudioContext || window.webkitAudioContext);
}

function createAudioContext() {
  if (!audioSupported()) return null;
  try {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    const context = new AudioContextCtor();
    const masterGain = context.createGain();
    masterGain.gain.value = AUDIO_MASTER_GAIN;
    masterGain.connect(context.destination);
    audioContext = context;
    audioMasterGain = masterGain;
    return context;
  } catch (error) {
    audioContext = null;
    audioMasterGain = null;
    return null;
  }
}

function getAudioContext() {
  if (!audioContext && audioSupported()) {
    createAudioContext();
  }
  return audioContext;
}

function resumeAudio() {
  const context = getAudioContext();
  if (!context) return;
  if (context.state === "suspended" && typeof context.resume === "function") {
    const resumePromise = context.resume();
    if (resumePromise && typeof resumePromise.catch === "function") {
      resumePromise.catch(function () {});
    }
  }
}

function suspendAudio() {
  if (!audioContext) return;
  if (audioContext.state === "running" && typeof audioContext.suspend === "function") {
    try {
      audioContext.suspend();
    } catch (error) {
    }
  }
}

function removeActiveSound(sound) {
  const index = activeSounds.indexOf(sound);
  if (index !== -1) {
    activeSounds.splice(index, 1);
  }
}

function playTone(frequency, type, duration, gain) {
  const context = getAudioContext();
  if (!context || !audioMasterGain) return;
  if (typeof frequency !== "number" || !isFinite(frequency) || frequency <= 0) return;
  if (typeof duration !== "number" || !isFinite(duration) || duration <= 0) return;
  const oscillatorType = typeof type === "string" && type !== "" ? type : "sine";
  const volume = typeof gain === "number" && isFinite(gain) && gain > 0 ? gain : 1;

  const now = context.currentTime;
  const attackSec = TONE_ATTACK_MS / 1000;
  const releaseSec = TONE_RELEASE_MS / 1000;
  const durationSec = duration / 1000;
  const sustainEndSec = Math.max(attackSec, durationSec - releaseSec);

  const oscillator = context.createOscillator();
  oscillator.type = oscillatorType;
  oscillator.frequency.setValueAtTime(frequency, now);

  const envelope = context.createGain();
  envelope.gain.setValueAtTime(0, now);
  envelope.gain.linearRampToValueAtTime(volume, now + attackSec);
  envelope.gain.setValueAtTime(volume, now + sustainEndSec);
  envelope.gain.linearRampToValueAtTime(0, now + durationSec);

  oscillator.connect(envelope);
  envelope.connect(audioMasterGain);

  const sound = { oscillator: oscillator, envelope: envelope };
  activeSounds.push(sound);

  const stopTime = now + durationSec + 0.02;
  try {
    oscillator.start(now);
    oscillator.stop(stopTime);
  } catch (error) {
    removeActiveSound(sound);
    return;
  }

  oscillator.addEventListener("ended", function cleanup() {
    oscillator.removeEventListener("ended", cleanup);
    removeActiveSound(sound);
    try {
      oscillator.disconnect();
    } catch (error) {
    }
    try {
      envelope.disconnect();
    } catch (error) {
    }
  });
}

function stopAllAudio() {
  while (activeSounds.length > 0) {
    const sound = activeSounds[activeSounds.length - 1];
    activeSounds.pop();
    if (sound.oscillator) {
      try {
        sound.oscillator.stop();
      } catch (error) {
      }
      try {
        sound.oscillator.disconnect();
      } catch (error) {
      }
    }
    if (sound.envelope) {
      try {
        sound.envelope.disconnect();
      } catch (error) {
      }
    }
  }
}

function playCorrectChime() {
  playTone(CHIME_NOTE_1_HZ, "triangle", CHIME_NOTE_1_MS, 1);
  const timer = setTimeout(function () {
    playTone(CHIME_NOTE_2_HZ, "triangle", CHIME_NOTE_2_MS, 1);
  }, CHIME_STEP_MS);
  pendingTimers.push(timer);
}

function playMissBuzzer() {
  playTone(MISS_BUZZER_HZ, "sawtooth", MISS_BUZZER_MS, 1);
}

function playGameOverSound() {
  for (let i = 0; i < GAME_OVER_NOTES.length; i += 1) {
    const timer = setTimeout(function () {
      playTone(GAME_OVER_NOTES[i], "sawtooth", GAME_OVER_NOTE_MS, 1);
    }, i * GAME_OVER_STEP_MS);
    pendingTimers.push(timer);
  }
}

function playStreakBonus() {
  playTone(STREAK_BONUS_FREQUENCY_HZ, "square", STREAK_BONUS_MS, 0.7);
  const timer = setTimeout(function () {
    playTone(STREAK_BONUS_FREQUENCY_2_HZ, "square", STREAK_BONUS_MS, 0.7);
  }, STREAK_BONUS_STEP_MS);
  pendingTimers.push(timer);
}

function closeAudio() {
  cancelPendingTimers();
  stopAllAudio();
  if (audioContext) {
    try {
      if (typeof audioContext.close === "function") {
        audioContext.close();
      }
    } catch (error) {
    }
  }
  audioContext = null;
  audioMasterGain = null;
}

function hitTestFallingWord(event) {
  if (typeof document !== "undefined" && typeof document.elementsFromPoint === "function") {
    const elements = document.elementsFromPoint(event.clientX, event.clientY);
    for (let i = 0; i < elements.length; i += 1) {
      if (elements[i].classList && elements[i].classList.contains("falling-word")) {
        return elements[i];
      }
    }
    return null;
  }
  const target = event.target;
  if (target && typeof target.closest === "function") {
    return target.closest(".falling-word");
  }
  return null;
}

function handleArenaClick(event) {
  if (state.status !== STATUS_PLAYING || state.roundResolved) return;
  const wordElement = hitTestFallingWord(event);
  if (!wordElement) return;
  const entryId = wordElement.getAttribute("data-word-id");
  if (typeof entryId === "string" && entryId !== "") {
    handleWordSelection(entryId);
  }
}

function handleArenaPointerDown(event) {
  if (state.status !== STATUS_PLAYING || state.roundResolved) return;
  if (typeof event.pointerType === "string" && event.pointerType === "mouse") {
    return;
  }
  const wordElement = hitTestFallingWord(event);
  if (!wordElement) return;
  const entryId = wordElement.getAttribute("data-word-id");
  if (typeof entryId === "string" && entryId !== "") {
    handleWordSelection(entryId);
  }
}

function handleKeyDown(event) {
  const target = event.target;
  if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
    return;
  }
  const key = event.key;
  if (key === "1" || key === "2" || key === "3") {
    event.preventDefault();
    applyAction("selectLane", Number(key) - 1);
    return;
  }
  if (key === " " || key === "Spacebar") {
    event.preventDefault();
    if (state.status === STATUS_PLAYING) {
      applyAction("pauseGame");
    } else if (state.status === STATUS_PAUSED) {
      applyAction("resumeGame");
    }
    return;
  }
  if (key === "p" || key === "P") {
    if (state.status === STATUS_PLAYING) {
      applyAction("pauseGame");
    } else if (state.status === STATUS_PAUSED) {
      applyAction("resumeGame");
    }
    return;
  }
  if (key === "Enter") {
    event.preventDefault();
    applyAction("startGame");
    return;
  }
  if (key === "l" || key === "L") {
    applyAction("listenPrompt");
  }
}

function handleVisibilityChange() {
  if (typeof document === "undefined") return;
  if (document.hidden) {
    applyAction("visibilityHidden");
  }
}

function handleWindowBlur() {
  applyAction("visibilityHidden");
}

function handlePageHide() {
  if (!hasDom()) return;
  if (typeof window === "undefined") return;
  if ("speechSynthesis" in window) {
    try {
      window.speechSynthesis.cancel();
    } catch (error) {
      return;
    }
  }
  closeAudio();
}

function focusArena() {
  if (!hasDom()) return;
  const arena = document.getElementById("arena");
  if (arena) {
    arena.focus();
  }
}

function scheduleNextRound() {
  const timer = setTimeout(function () {
    if (state.status !== STATUS_PLAYING || !state.roundResolved) return;
    clearArena();
    spawnRound();
  }, ROUND_TRANSITION_MS);
  pendingTimers.push(timer);
}

function endGame() {
  state.status = STATUS_GAME_OVER;
  if (state.score > state.sessionHighScore) {
    state.sessionHighScore = state.score;
  }
  cancelAnimationFrameId();
  cancelPendingTimers();
  clearArena();
  playGameOverSound();
  renderGameOver();
  announce("Game over. Final score " + state.score + ".");
}

function startLoop() {
  cancelAnimationFrameId();
  state.lastFrameTimeMs = null;
  if (typeof requestAnimationFrame === "undefined") return;
  animationFrameId = requestAnimationFrame(frame);
}

function frame(nowMs) {
  if (state.status !== STATUS_PLAYING) {
    cancelAnimationFrameId();
    return;
  }
  let dtMs = 0;
  if (state.lastFrameTimeMs !== null) {
    dtMs = Math.max(0, Math.min(nowMs - state.lastFrameTimeMs, MAX_FRAME_DELAY_MS));
  }
  state.lastFrameTimeMs = nowMs;
  tick(dtMs);
  if (state.status === STATUS_PLAYING) {
    animationFrameId = requestAnimationFrame(frame);
  }
}

function spawnRound() {
  state.roundId += 1;
  const target = pickTarget(0, state.rng.next, state.recentIds);
  const distractors = pickDistractors(target, 0, LANE_COUNT - 1, state.rng.next, state.recentIds);
  recordRecentId(state.recentIds, target.id);
  const ordered = shuffle([target].concat(distractors), state.rng.next);
  state.fallingWords = ordered.map(function (entry, index) {
    return {
      entryId: entry.id,
      word: entry.word,
      concept: entry.concept,
      difficulty: entry.difficulty,
      lane: index,
      badge: index + 1,
      roundIndex: index,
      offsetY: spawnOffsetFor(index),
      y: spawnOffsetFor(index)
    };
  });
  state.targetEntryId = target.id;
  state.currentPrompt = target.concept;
  state.roundResolved = false;
  renderArena();
  renderPrompt();
  syncHud();
  announce(
    "Round " +
      state.roundId +
      ": \u201c" +
      target.concept +
      "\u201d is the prompt. Pick the matching falling word."
  );
}

function announce(message) {
  if (!hasDom()) return;
  const region = document.getElementById("announcements");
  if (region) {
    region.textContent = message;
  }
}

function syncHud() {
  if (!hasDom()) return;
  const scoreElement = document.getElementById("score");
  const streakElement = document.getElementById("streak");
  const livesElement = document.getElementById("lives");
  if (scoreElement) {
    scoreElement.textContent = String(state.score);
  }
  if (streakElement) {
    streakElement.textContent = String(state.streak);
  }
  if (livesElement) {
    livesElement.textContent = LIVES_ICON.repeat(state.lives);
    livesElement.setAttribute("aria-label", state.lives + " lives remaining");
  }
}

function renderPrompt() {
  if (!hasDom()) return;
  const promptElement = document.getElementById("promptText");
  if (!promptElement) return;
  promptElement.textContent =
    state.currentPrompt === ""
      ? PROMPT_IDLE_TEXT
      : "Pick the word that matches \u201c" + state.currentPrompt + "\u201d before it falls.";
}

function renderGameOver() {
  syncHud();
  renderPrompt();
  if (!hasDom()) return;
  const promptElement = document.getElementById("promptText");
  if (promptElement) {
    promptElement.textContent = "Game over! Final score: " + state.score + ". Press Start to play again.";
  }
}

function buildWordElement(word) {
  if (!hasDom()) return null;
  const element = document.createElement("div");
  element.className = "falling-word";
  element.setAttribute("data-word-id", word.entryId);
  element.dataset.lane = String(word.lane);

  const badge = document.createElement("kbd");
  badge.className = "key-badge";
  badge.textContent = String(word.badge);
  badge.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.textContent = word.word;

  element.appendChild(badge);
  element.appendChild(label);
  return element;
}

function positionWordElement(word) {
  const element = wordElementByEntryId.get(word.entryId);
  if (!element) return;
  const columnCount = Math.max(state.fallingWords.length, LANE_COUNT);
  const leftPercent = ((word.lane + 0.5) / columnCount) * 100;
  element.style.left = leftPercent.toFixed(3) + "%";
  element.style.top = wordCurrentY(word) + "px";
}

function renderArena() {
  if (!hasDom()) return;
  wordElementByEntryId.clear();
  const arena = document.getElementById("arena");
  if (!arena) return;
  arena.textContent = "";
  for (let i = 0; i < state.fallingWords.length; i += 1) {
    const word = state.fallingWords[i];
    const element = buildWordElement(word);
    wordElementByEntryId.set(word.entryId, element);
    arena.appendChild(element);
    positionWordElement(word);
  }
}

function clearArena() {
  wordElementByEntryId.clear();
  if (!hasDom()) return;
  const arena = document.getElementById("arena");
  if (arena) {
    arena.textContent = "";
  }
}

function resetDom() {
  clearArena();
  renderPrompt();
  syncHud();
}

function beginGame() {
  resetGame();
  resumeAudio();
  const seed = generateSeed();
  state.rngSeed = seed;
  state.rng = initRng(seed);
  state.status = STATUS_PLAYING;
  spawnRound();
  startLoop();
  focusArena();
}

function applyAction(action, payload) {
  if (action === "resetGame") {
    resetGame();
    resetDom();
    return { accepted: true, action: action };
  }
  if (action === "startGame" || action === "restartGame") {
    beginGame();
    return { accepted: true, action: action };
  }
  if (action === "pauseGame") {
    if (state.status !== STATUS_PLAYING) {
      return { accepted: false, action: action, reason: "STATE_GUARD" };
    }
    state.status = STATUS_PAUSED;
    cancelAnimationFrameId();
    state.lastFrameTimeMs = null;
    suspendAudio();
    return { accepted: true, action: action };
  }
  if (action === "resumeGame") {
    if (state.status !== STATUS_PAUSED) {
      return { accepted: false, action: action, reason: "STATE_GUARD" };
    }
    state.status = STATUS_PLAYING;
    resumeAudio();
    startLoop();
    return { accepted: true, action: action };
  }
  if (action === "selectLane") {
    const laneNumber =
      typeof payload === "number" ? payload : payload && typeof payload.lane === "number" ? payload.lane : Number.NaN;
    return selectLane(laneNumber);
  }
  if (action === "selectWord") {
    const entryId = typeof payload === "string" ? payload : payload && payload.entryId;
    return handleWordSelection(entryId);
  }
  if (action === "listenPrompt") {
    if (state.status !== STATUS_PLAYING) {
      return { accepted: false, action: action, reason: "STATE_GUARD" };
    }
    if (state.currentPrompt === "") {
      return { accepted: false, action: action, reason: "NO_PROMPT" };
    }
    speakPrompt();
    return { accepted: true, action: action };
  }
  if (action === "visibilityHidden") {
    if (state.status !== STATUS_PLAYING) {
      return { accepted: false, action: action, reason: "STATE_GUARD" };
    }
    state.status = STATUS_PAUSED;
    cancelAnimationFrameId();
    state.lastFrameTimeMs = null;
    suspendAudio();
    return { accepted: true, action: action };
  }
  if (action === "tick") {
    if (state.status !== STATUS_PLAYING) {
      return { accepted: false, action: action, reason: "STATE_GUARD" };
    }
    const dtMs = payload && typeof payload.dtMs === "number" ? payload.dtMs : 0;
    tick(dtMs);
    return { accepted: true, action: action };
  }
  return { accepted: false, action: action, reason: "UNKNOWN_ACTION" };
}

function setupAudioUnlock() {
  if (typeof document === "undefined") return;
  function unlock() {
    resumeAudio();
    document.removeEventListener("pointerdown", unlock);
    document.removeEventListener("keydown", unlock);
    document.removeEventListener("touchstart", unlock);
  }
  document.addEventListener("pointerdown", unlock);
  document.addEventListener("keydown", unlock);
  document.addEventListener("touchstart", unlock);
}

function init() {
  setupAudioUnlock();
  const startButton = document.getElementById("startBtn");
  if (startButton) {
    startButton.addEventListener("click", function () {
      applyAction("startGame");
    });
  }
  const listenButton = document.getElementById("listenBtn");
  if (listenButton) {
    listenButton.addEventListener("click", function () {
      applyAction("listenPrompt");
    });
  }
  const arena = document.getElementById("arena");
  if (arena) {
    arena.addEventListener("click", handleArenaClick);
    arena.addEventListener("pointerdown", handleArenaPointerDown);
  }
  document.addEventListener("keydown", handleKeyDown);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  if (typeof window !== "undefined") {
    window.addEventListener("blur", handleWindowBlur);
    window.addEventListener("pagehide", handlePageHide);
  }
  renderPrompt();
  syncHud();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    LANE_COUNT: LANE_COUNT,
    MAX_LIVES: MAX_LIVES,
    RECENT_WINDOW: RECENT_WINDOW,
    BAND_COUNT: BAND_COUNT,
    STREAK_BONUS: STREAK_BONUS,
    FALL_VELOCITY_BASE_PS: FALL_VELOCITY_BASE_PS,
    FALL_VELOCITY_MAX_PS: FALL_VELOCITY_MAX_PS,
    FALL_VELOCITY_STEP_PS: FALL_VELOCITY_STEP_PS,
    DEFAULT_ARENA_HEIGHT_PX: DEFAULT_ARENA_HEIGHT_PX,
    WORD_HEIGHT_PX: WORD_HEIGHT_PX,
    SPANISH_LANG: SPANISH_LANG,
    SPANISH_LANG_FALLBACK: SPANISH_LANG_FALLBACK,
    SPANISH_RATE: SPANISH_RATE,
    createInitialState: createInitialState,
    fallVelocityPxPerSecond: fallVelocityPxPerSecond,
    hasCrossedFloor: hasCrossedFloor,
    arenaHeightPx: arenaHeightPx,
    tick: tick,
    detectFloorCrossings: detectFloorCrossings,
    resolveMiss: resolveMiss,
    cleanupDistractor: cleanupDistractor,
    endGame: endGame,
    spawnRound: spawnRound,
    resetGame: resetGame,
    beginGame: beginGame,
    applyAction: applyAction,
    selectLane: selectLane,
    handleWordSelection: handleWordSelection,
    resolveCorrect: resolveCorrect,
    resolveIncorrect: resolveIncorrect,
    findWordByEntryId: findWordByEntryId,
    findWordByLane: findWordByLane,
    speakSpanish: speakSpanish,
    audioSupported: audioSupported,
    getAudioContext: getAudioContext,
    resumeAudio: resumeAudio,
    suspendAudio: suspendAudio,
    closeAudio: closeAudio,
    playTone: playTone,
    playCorrectChime: playCorrectChime,
    playMissBuzzer: playMissBuzzer,
    playGameOverSound: playGameOverSound,
    playStreakBonus: playStreakBonus,
    stopAllAudio: stopAllAudio,
    getState: function () {
      return state;
    }
  };
}

"use strict";

const STATUS_IDLE = "STATUS_IDLE";
const STATUS_PLAYING = "STATUS_PLAYING";
const STATUS_PAUSED = "STATUS_PAUSED";
const STATUS_GAME_OVER = "STATUS_GAME_OVER";

const LANE_COUNT = 3;
const MAX_LIVES = 3;
const SCORE_BASE = 10;
const STREAK_TIER = 5;
const WORDS_PER_LEVEL = 5;
const FALL_TIME_BASE_MS = 8000;
const FALL_TIME_MIN_MS = 2500;
const FALL_DECAY = 0.93;
const RECENT_WINDOW = 6;
const BAND_COUNT = 4;
const AUDIO_MASTER_GAIN = 0.15;

const CATEGORY_ANIMALS = "animals";
const CATEGORY_FOOD = "food";
const CATEGORY_HOME = "home";
const CATEGORY_ACTIONS = "actions";
const CATEGORY_NATURE = "nature";

const WORD_HEIGHT_PX = 48;
const SPAWN_STAGGER_PX = 26;
const LIVES_ICON = "\u2665";
const PROMPT_IDLE_TEXT =
  "Press the Listen button to hear a word, then type it before it falls.";

const ANIMAL_WORDS = [
  { id: "cat", word: "el gato", concept: "cat", difficulty: 0, category: CATEGORY_ANIMALS },
  { id: "dog", word: "el perro", concept: "dog", difficulty: 0, category: CATEGORY_ANIMALS },
  { id: "fish", word: "el pez", concept: "fish", difficulty: 1, category: CATEGORY_ANIMALS },
  { id: "cow", word: "la vaca", concept: "cow", difficulty: 1, category: CATEGORY_ANIMALS },
  { id: "bird", word: "el p\u00e1jaro", concept: "bird", difficulty: 2, category: CATEGORY_ANIMALS },
  { id: "horse", word: "el caballo", concept: "horse", difficulty: 3, category: CATEGORY_ANIMALS },
  { id: "lion", word: "el le\u00f3n", concept: "lion", difficulty: 3, category: CATEGORY_ANIMALS }
];

const FOOD_WORDS = [
  { id: "bread", word: "el pan", concept: "bread", difficulty: 0, category: CATEGORY_FOOD },
  { id: "water", word: "el agua", concept: "water", difficulty: 0, category: CATEGORY_FOOD },
  { id: "milk", word: "la leche", concept: "milk", difficulty: 1, category: CATEGORY_FOOD },
  { id: "cheese", word: "el queso", concept: "cheese", difficulty: 1, category: CATEGORY_FOOD },
  { id: "apple", word: "la manzana", concept: "apple", difficulty: 1, category: CATEGORY_FOOD },
  { id: "egg", word: "el huevo", concept: "egg", difficulty: 2, category: CATEGORY_FOOD },
  { id: "orange", word: "la naranja", concept: "orange", difficulty: 2, category: CATEGORY_FOOD }
];

const HOME_WORDS = [
  { id: "house", word: "la casa", concept: "house", difficulty: 0, category: CATEGORY_HOME },
  { id: "door", word: "la puerta", concept: "door", difficulty: 1, category: CATEGORY_HOME },
  { id: "bed", word: "la cama", concept: "bed", difficulty: 1, category: CATEGORY_HOME },
  { id: "table", word: "la mesa", concept: "table", difficulty: 1, category: CATEGORY_HOME },
  { id: "chair", word: "la silla", concept: "chair", difficulty: 2, category: CATEGORY_HOME },
  { id: "key", word: "la llave", concept: "key", difficulty: 2, category: CATEGORY_HOME },
  { id: "window", word: "la ventana", concept: "window", difficulty: 3, category: CATEGORY_HOME }
];

const ACTION_WORDS = [
  { id: "eat", word: "comer", concept: "to eat", difficulty: 0, category: CATEGORY_ACTIONS },
  { id: "run", word: "correr", concept: "to run", difficulty: 0, category: CATEGORY_ACTIONS },
  { id: "drink", word: "beber", concept: "to drink", difficulty: 1, category: CATEGORY_ACTIONS },
  { id: "sleep", word: "dormir", concept: "to sleep", difficulty: 1, category: CATEGORY_ACTIONS },
  { id: "swim", word: "nadar", concept: "to swim", difficulty: 2, category: CATEGORY_ACTIONS },
  { id: "dance", word: "bailar", concept: "to dance", difficulty: 2, category: CATEGORY_ACTIONS },
  { id: "sing", word: "cantar", concept: "to sing", difficulty: 3, category: CATEGORY_ACTIONS }
];

const NATURE_WORDS = [
  { id: "sun", word: "el sol", concept: "sun", difficulty: 0, category: CATEGORY_NATURE },
  { id: "moon", word: "la luna", concept: "moon", difficulty: 1, category: CATEGORY_NATURE },
  { id: "tree", word: "el \u00e1rbol", concept: "tree", difficulty: 1, category: CATEGORY_NATURE },
  { id: "flower", word: "la flor", concept: "flower", difficulty: 1, category: CATEGORY_NATURE },
  { id: "rain", word: "la lluvia", concept: "rain", difficulty: 2, category: CATEGORY_NATURE },
  { id: "snow", word: "la nieve", concept: "snow", difficulty: 3, category: CATEGORY_NATURE },
  { id: "star", word: "la estrella", concept: "star", difficulty: 3, category: CATEGORY_NATURE }
];

const VOCABULARY = [].concat(ANIMAL_WORDS, FOOD_WORDS, HOME_WORDS, ACTION_WORDS, NATURE_WORDS);

const LEXICON_BY_ID = new Map(VOCABULARY.map((entry) => [entry.id, entry]));
const CATEGORY_INDEX = buildCategoryIndex();
const BAND_INDEX = buildBandIndex();

function buildCategoryIndex() {
  const categories = {};
  for (const entry of VOCABULARY) {
    if (!categories[entry.category]) {
      categories[entry.category] = [];
    }
    categories[entry.category].push(entry);
  }
  return categories;
}

function buildBandIndex() {
  const bands = [];
  for (let index = 0; index < BAND_COUNT; index += 1) {
    bands.push([]);
  }
  for (const entry of VOCABULARY) {
    bands[entry.difficulty].push(entry);
  }
  return bands;
}

let state = createInitialState();
let animationFrameId = null;
let pendingTimers = [];

function createInitialState() {
  return {
    status: STATUS_IDLE,
    score: 0,
    streak: 0,
    lives: MAX_LIVES,
    speed: FALL_TIME_BASE_MS,
    level: 0,
    sessionHighScore: 0,
    roundId: 0,
    rngSeed: 0,
    rng: null,
    currentPrompt: "",
    currentPromptCategory: "",
    targetEntryId: null,
    fallingWords: [],
    recentIds: []
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

function resetGame() {
  cancelAnimationFrameId();
  cancelPendingTimers();
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

function bandForLevel(level) {
  if (level < 3) return 0;
  if (level < 8) return 1;
  if (level < 15) return 2;
  return 3;
}

function resolveBand(requestedBand) {
  const clamped = Math.max(0, Math.min(BAND_COUNT - 1, requestedBand));
  if (BAND_INDEX[clamped].length > 0) {
    return clamped;
  }
  for (let delta = 1; delta <= BAND_COUNT; delta += 1) {
    if (clamped + delta < BAND_COUNT && BAND_INDEX[clamped + delta].length > 0) {
      return clamped + delta;
    }
    if (clamped - delta >= 0 && BAND_INDEX[clamped - delta].length > 0) {
      return clamped - delta;
    }
  }
  return 0;
}

function recordRecentId(recentIds, entryId) {
  recentIds.push(entryId);
  if (recentIds.length > RECENT_WINDOW) {
    recentIds.shift();
  }
}

function pickTarget(band, rng, recentIds) {
  const pool = BAND_INDEX[band].filter((entry) => !recentIds.includes(entry.id));
  const source = pool.length > 0 ? pool : BAND_INDEX[band];
  if (source.length === 0) {
    return VOCABULARY[Math.floor(rng() * VOCABULARY.length)];
  }
  return source[Math.floor(rng() * source.length)];
}

function appendUnique(list, entries) {
  const seen = new Set(list.map((entry) => entry.id));
  for (const entry of entries) {
    if (!seen.has(entry.id)) {
      list.push(entry);
      seen.add(entry.id);
    }
  }
  return list;
}

function bandCandidatesWithWiden(band, widenDelta) {
  const list = [];
  for (let delta = 0; delta <= widenDelta; delta += 1) {
    if (band + delta < BAND_COUNT) {
      appendUnique(list, BAND_INDEX[band + delta]);
    }
    if (delta > 0 && band - delta >= 0) {
      appendUnique(list, BAND_INDEX[band - delta]);
    }
  }
  return list;
}

function samplePreferredCandidate(pool, target, usedIds, usedWords, recentIds, rng) {
  const nonClash = [];
  const clash = [];
  for (const entry of pool) {
    if (
      usedIds.has(entry.id) ||
      usedWords.has(entry.word) ||
      recentIds.includes(entry.id)
    ) {
      continue;
    }
    const sharesOrthography =
      entry.word.charAt(0) === target.word.charAt(0) &&
      entry.word.length === target.word.length;
    if (sharesOrthography) {
      clash.push(entry);
    } else {
      nonClash.push(entry);
    }
  }
  const preferred = nonClash.length > 0 ? nonClash : clash;
  if (preferred.length === 0) {
    return null;
  }
  return preferred[Math.floor(rng() * preferred.length)];
}

function pickDistractors(target, band, count, rng, recentIds) {
  const chosen = [];
  const usedIds = new Set([target.id]);
  const usedWords = new Set([target.word]);
  let widenDelta = 0;
  while (chosen.length < count) {
    const pool = bandCandidatesWithWiden(band, widenDelta);
    const candidate = samplePreferredCandidate(pool, target, usedIds, usedWords, recentIds, rng);
    if (candidate !== null) {
      chosen.push(candidate);
      usedIds.add(candidate.id);
      usedWords.add(candidate.word);
    } else {
      widenDelta += 1;
    }
  }
  return chosen;
}

function resolveWordCount(requested) {
  if (Number.isInteger(requested) && requested >= 3) {
    return Math.min(requested, LANE_COUNT + 1);
  }
  return LANE_COUNT;
}

function spawnOffsetFor(columnIndex) {
  return -(WORD_HEIGHT_PX + SPAWN_STAGGER_PX + columnIndex * SPAWN_STAGGER_PX);
}

function generateRound(level, rng, recentIds, wordCount) {
  const count = resolveWordCount(wordCount);
  const band = resolveBand(bandForLevel(level));
  const target = pickTarget(band, rng, recentIds);
  recordRecentId(recentIds, target.id);
  const distractors = pickDistractors(target, band, count - 1, rng, recentIds);
  const ordered = shuffle([target, ...distractors], rng);
  const words = ordered.map((entry, index) => {
    return {
      entryId: entry.id,
      word: entry.word,
      concept: entry.concept,
      category: entry.category,
      difficulty: entry.difficulty,
      lane: index,
      badge: index + 1,
      roundIndex: index,
      offsetY: spawnOffsetFor(index)
    };
  });
  return {
    prompt: { entryId: target.id, concept: target.concept, category: target.category },
    targetEntryId: target.id,
    distractorEntryIds: distractors.map((distractor) => distractor.id),
    words: words
  };
}

function announce(message) {
  const region = document.getElementById("announcements");
  if (region) {
    region.textContent = message;
  }
}

function syncHud() {
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
  const promptElement = document.getElementById("promptText");
  if (!promptElement) {
    return;
  }
  promptElement.textContent =
    state.currentPrompt === ""
      ? PROMPT_IDLE_TEXT
      : "Pick the Spanish word for \u201c" + state.currentPrompt + "\u201d";
}

function buildFallingWordElement(word) {
  const element = document.createElement("div");
  element.className = "falling-word";
  element.setAttribute("data-word-id", word.entryId);
  element.dataset.lane = String(word.lane);
  element.dataset.badge = String(word.badge);
  element.setAttribute("role", "button");
  element.setAttribute("tabindex", "0");
  element.setAttribute("aria-label", word.word);

  const badge = document.createElement("kbd");
  badge.className = "key-badge";
  badge.textContent = String(word.badge);
  badge.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.textContent = word.word;

  element.append(badge, label);
  return element;
}

function positionFallingWord(element, word, columnCount) {
  const leftPercent = ((word.lane + 0.5) / columnCount) * 100;
  element.style.left = leftPercent.toFixed(3) + "%";
  element.style.top = word.offsetY + "px";
  return element;
}

function instantiateFallingWords(round, arenaElement) {
  arenaElement.textContent = "";
  const words = round.words || [];
  const columnCount = Math.max(words.length, LANE_COUNT);
  for (let index = 0; index < words.length; index += 1) {
    const word = words[index];
    const element = buildFallingWordElement(word);
    positionFallingWord(element, word, columnCount);
    arenaElement.appendChild(element);
  }
  return arenaElement.children.length;
}

function renderRound(round) {
  const arenaElement = document.getElementById("arena");
  if (arenaElement) {
    instantiateFallingWords(round, arenaElement);
  }
  renderPrompt();
}

function resetDom() {
  const arenaElement = document.getElementById("arena");
  if (arenaElement) {
    arenaElement.textContent = "";
  }
  renderPrompt();
  syncHud();
}

function spawnRound() {
  state.roundId += 1;
  const round = generateRound(state.level, state.rng.next, state.recentIds, LANE_COUNT);
  state.targetEntryId = round.targetEntryId;
  state.currentPrompt = round.prompt.concept;
  state.currentPromptCategory = round.prompt.category;
  state.fallingWords = round.words;
  renderRound(round);
  syncHud();
  announce(
    "New round. The English prompt is \u201c" +
      round.prompt.concept +
      "\u201d. Pick the matching Spanish word with keys 1 through " +
      LANE_COUNT +
      " or by selecting a falling word."
  );
}

function beginGame() {
  resetGame();
  const seed = generateSeed();
  state.rngSeed = seed;
  state.rng = initRng(seed);
  state.status = STATUS_PLAYING;
  spawnRound();
}

function applyAction(action) {
  if (action === "resetGame") {
    resetGame();
    resetDom();
    return { accepted: true, action: action };
  }
  if (action === "startGame" || action === "restartGame") {
    beginGame();
    return { accepted: true, action: action };
  }
  return { accepted: false, action: action, reason: "UNKNOWN_ACTION" };
}

function init() {
  const startButton = document.getElementById("startBtn");
  if (startButton) {
    startButton.addEventListener("click", function () {
      applyAction("startGame");
    });
  }
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
    VOCABULARY: VOCABULARY,
    LEXICON_BY_ID: LEXICON_BY_ID,
    CATEGORY_INDEX: CATEGORY_INDEX,
    BAND_INDEX: BAND_INDEX,
    generateRound: generateRound,
    resolveWordCount: resolveWordCount,
    spawnOffsetFor: spawnOffsetFor,
    bandForLevel: bandForLevel,
    resolveBand: resolveBand,
    recordRecentId: recordRecentId,
    buildFallingWordElement: buildFallingWordElement,
    positionFallingWord: positionFallingWord,
    instantiateFallingWords: instantiateFallingWords,
    LANE_COUNT: LANE_COUNT,
    BAND_COUNT: BAND_COUNT,
    RECENT_WINDOW: RECENT_WINDOW,
    createInitialState: createInitialState
  };
}

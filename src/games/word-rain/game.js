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
    currentPrompt: "",
    fallingWords: [],
    sessionHighScore: 0
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

function applyAction(action) {
  if (action === "resetGame" || action === "restartGame") {
    resetGame();
    return { accepted: true, action: action };
  }
  return { accepted: false, action: action, reason: "UNKNOWN_ACTION" };
}
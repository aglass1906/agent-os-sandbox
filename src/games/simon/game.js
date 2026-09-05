"use strict";

const STATUS_IDLE = "IDLE";
const STATUS_DEMO = "DEMO";
const STATUS_INPUT = "INPUT";
const STATUS_WON = "WON";
const STATUS_LOST = "LOST";

const PAD_COUNT = 4;
const PAD_IDS = [0, 1, 2, 3];
const PAD_COLORS = ["green", "red", "yellow", "blue"];
const PAD_KEYS = {
  "1": 0, "2": 1, "3": 2, "4": 3,
  "q": 0, "w": 1, "a": 2, "s": 3,
  "Q": 0, "W": 1, "A": 2, "S": 3,
};

const PAD_FREQUENCIES = {
  0: 329.63,
  1: 261.63,
  2: 220.0,
  3: 164.81,
};

const WIN_LEVEL = 20;

const STEP_ON_MS = 600;
const STEP_GAP_MS = 400;
const DEMO_START_DELAY_MS = 400;
const CELEBRATION_DELAY_MS = 1000;

const TONE_VOLUME = 0.25;
const TONE_ATTACK_MS = 10;
const TONE_DECAY_MS = 80;

let state = createInitialState();
let pendingTimers = [];
let audioContext = null;
let audioMasterGain = null;

function createInitialState() {
  return {
    sequence: [],
    level: 0,
    score: 0,
    highScore: 0,
    status: STATUS_IDLE,
    playerIndex: 0,
  };
}

function cancelTimers() {
  for (let i = 0; i < pendingTimers.length; i++) {
    clearTimeout(pendingTimers[i]);
  }
  pendingTimers = [];
}

function scheduleTimer(callback, delayMs) {
  const timer = setTimeout(function () {
    removeTimer(timer);
    callback();
  }, delayMs);
  pendingTimers.push(timer);
  return timer;
}

function removeTimer(timer) {
  const index = pendingTimers.indexOf(timer);
  if (index !== -1) {
    pendingTimers.splice(index, 1);
  }
}

function getPadElements() {
  return {
    0: document.getElementById("pad-green"),
    1: document.getElementById("pad-red"),
    2: document.getElementById("pad-yellow"),
    3: document.getElementById("pad-blue"),
  };
}

function setPadLit(padId, lit) {
  const pad = getPadElements()[padId];
  if (pad) {
    pad.classList.toggle("lit", !!lit);
  }
}

function setPadActive(padId, active) {
  const pad = getPadElements()[padId];
  if (pad) {
    pad.classList.toggle("active", !!active);
  }
}

function clearAllActivePads() {
  for (let i = 0; i < PAD_COUNT; i++) {
    setPadActive(i, false);
  }
}

function clearAllPads() {
  for (let i = 0; i < PAD_COUNT; i++) {
    setPadLit(i, false);
  }
}

function createAudioContext() {
  const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextCtor) {
    return null;
  }
  const context = new AudioContextCtor();
  const masterGain = context.createGain();
  masterGain.gain.value = TONE_VOLUME;
  masterGain.connect(context.destination);
  audioContext = context;
  audioMasterGain = masterGain;
  return context;
}

function getAudioContext() {
  if (!audioContext && typeof window !== "undefined") {
    createAudioContext();
  }
  return audioContext;
}

function resumeAudio() {
  const context = getAudioContext();
  if (!context) {
    return;
  }
  if (context.state === "suspended" && typeof context.resume === "function") {
    const resumePromise = context.resume();
    if (resumePromise && typeof resumePromise.catch === "function") {
      resumePromise.catch(function () {});
    }
  }
}

function playTone(frequency, durationMs) {
  const context = getAudioContext();
  if (!context || !audioMasterGain) {
    return;
  }
  if (typeof frequency !== "number" || !isFinite(frequency) || frequency <= 0) {
    return;
  }
  if (typeof durationMs !== "number" || !isFinite(durationMs) || durationMs <= 0) {
    return;
  }

  const now = context.currentTime;
  const attackSec = TONE_ATTACK_MS / 1000;
  const decaySec = TONE_DECAY_MS / 1000;
  const durationSec = durationMs / 1000;
  const sustainEndSec = Math.max(attackSec, durationSec - decaySec);

  const oscillator = context.createOscillator();
  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(frequency, now);

  const envelope = context.createGain();
  envelope.gain.setValueAtTime(0, now);
  envelope.gain.linearRampToValueAtTime(1, now + attackSec);
  envelope.gain.setValueAtTime(1, now + sustainEndSec);
  envelope.gain.linearRampToValueAtTime(0, now + durationSec);

  oscillator.connect(envelope);
  envelope.connect(audioMasterGain);

  oscillator.start(now);
  oscillator.stop(now + durationSec + 0.02);

  oscillator.addEventListener("ended", function cleanup() {
    oscillator.removeEventListener("ended", cleanup);
    oscillator.disconnect();
    envelope.disconnect();
  });
}

function flashPad(padId) {
  setPadLit(padId, true);
  playTone(PAD_FREQUENCIES[padId], STEP_ON_MS);
  scheduleTimer(function () {
    setPadLit(padId, false);
  }, STEP_ON_MS);
}

function randomPadId() {
  return Math.floor(Math.random() * PAD_COUNT);
}

function randomPad() {
  return PAD_IDS[randomPadId()];
}

function padIdForColor(color) {
  return PAD_COLORS.indexOf(color);
}

function aboutModalOpen() {
  const aboutModal = document.getElementById("aboutModal");
  return !!aboutModal && !aboutModal.hidden;
}

function playSequence() {
  state.status = STATUS_DEMO;
  render();
  scheduleTimer(function () {
    playDemoStep(0);
  }, DEMO_START_DELAY_MS);
}

function playDemoStep(index) {
  if (state.status !== STATUS_DEMO) {
    return;
  }
  if (index >= state.sequence.length) {
    beginInputPhase();
    return;
  }
  flashPad(state.sequence[index]);
  scheduleTimer(function () {
    playDemoStep(index + 1);
  }, STEP_ON_MS + STEP_GAP_MS);
}

function beginInputPhase() {
  clearAllPads();
  state.playerIndex = 0;
  state.status = STATUS_INPUT;
  render();
}

function advanceRound() {
  state.sequence.push(randomPad());
  state.level = state.sequence.length;
  render();
  playSequence();
}

function startGame() {
  cancelTimers();
  resetGame();
  resumeAudio();
  advanceRound();
}

function resetGame() {
  cancelTimers();
  const previousHighScore = state.highScore;
  state = createInitialState();
  state.highScore = previousHighScore;
  clearAllPads();
  hideCelebration();
  render();
}

function handleCorrectInput() {
  state.playerIndex += 1;
  if (state.playerIndex >= state.sequence.length) {
    levelWon();
  } else {
    render();
  }
}

function levelWon() {
  state.score += state.level;
  if (state.score > state.highScore) {
    state.highScore = state.score;
  }
  state.status = STATUS_WON;
  render();
  showCelebration();
  scheduleTimer(function () {
    hideCelebration();
    if (state.status === STATUS_WON) {
      if (state.level >= WIN_LEVEL) {
        gameWin();
      } else {
        advanceRound();
      }
    }
  }, CELEBRATION_DELAY_MS);
}

function gameWin() {
  state.status = STATUS_IDLE;
  render();
}

function gameLost() {
  state.status = STATUS_LOST;
  render();
}

function handlePadInput(padId) {
  if (state.status !== STATUS_INPUT) {
    return;
  }
  flashPad(padId);
  if (padId === state.sequence[state.playerIndex]) {
    handleCorrectInput();
  } else {
    gameLost();
  }
}

function statusMessage() {
  switch (state.status) {
    case STATUS_IDLE:
      return "Press Start to begin";
    case STATUS_DEMO:
      return "Watch the sequence...";
    case STATUS_INPUT:
      return "Your turn! Repeat the sequence";
    case STATUS_WON:
      return "Nice! Next sequence";
    case STATUS_LOST:
      return "Game Over! Press Start to play again";
    default:
      return "";
  }
}

function render() {
  const statusEl = document.getElementById("status");
  if (statusEl) {
    statusEl.textContent = statusMessage();
  }

  const levelEl = document.getElementById("level");
  if (levelEl) {
    levelEl.textContent = "Level: " + state.level;
  }

  const scoreEl = document.getElementById("score");
  if (scoreEl) {
    scoreEl.textContent = "Score: " + state.score;
  }

  const highScoreEl = document.getElementById("highScore");
  if (highScoreEl) {
    highScoreEl.textContent = "Best: " + state.highScore;
  }
}

function showCelebration() {
  const el = document.getElementById("celebration");
  if (el) {
    el.classList.add("celebrate");
  }
}

function hideCelebration() {
  const el = document.getElementById("celebration");
  if (el) {
    el.classList.remove("celebrate");
  }
}

function padIdFromPadElement(pad) {
  if (!pad) {
    return -1;
  }
  const color = pad.getAttribute("data-color");
  return padIdForColor(color);
}

function setupBoard() {
  const board = document.getElementById("board");
  if (!board) {
    return;
  }

  board.addEventListener("pointerdown", function (event) {
    resumeAudio();
    const pad = event.target.closest(".pad");
    const padId = padIdFromPadElement(pad);
    if (padId !== -1) {
      setPadActive(padId, true);
    }
  });

  function releasePad(event) {
    const pad = event.target.closest(".pad");
    const padId = padIdFromPadElement(pad);
    if (padId !== -1) {
      setPadActive(padId, false);
    }
  }

  board.addEventListener("pointerup", releasePad);
  board.addEventListener("pointercancel", releasePad);
  board.addEventListener("pointerleave", clearAllActivePads);
  document.addEventListener("pointerup", clearAllActivePads);
  document.addEventListener("pointercancel", clearAllActivePads);

  board.addEventListener("click", function (event) {
    const pad = event.target.closest(".pad");
    const padId = padIdFromPadElement(pad);
    if (padId !== -1) {
      handlePadInput(padId);
    }
  });
}

function setupKeyboard() {
  document.addEventListener("keydown", function (event) {
    if (!(event.key in PAD_KEYS)) {
      return;
    }
    if (aboutModalOpen()) {
      return;
    }
    event.preventDefault();
    resumeAudio();
    const padId = PAD_KEYS[event.key];
    setPadActive(padId, true);
    handlePadInput(padId);
  });
  document.addEventListener("keyup", function (event) {
    if (!(event.key in PAD_KEYS)) {
      return;
    }
    setPadActive(PAD_KEYS[event.key], false);
  });
}

function setupStartButton() {
  const startBtn = document.getElementById("startBtn");
  if (startBtn) {
    startBtn.addEventListener("click", startGame);
  }
}

function setupAboutModal() {
  const aboutBtn = document.getElementById("aboutBtn");
  const aboutClose = document.getElementById("aboutClose");
  const aboutModal = document.getElementById("aboutModal");

  function openModal() {
    if (aboutModal) {
      aboutModal.hidden = false;
    }
  }

  function closeModal() {
    if (aboutModal) {
      aboutModal.hidden = true;
    }
  }

  if (aboutBtn) {
    aboutBtn.addEventListener("click", openModal);
  }
  if (aboutClose) {
    aboutClose.addEventListener("click", closeModal);
  }
  if (aboutModal) {
    aboutModal.addEventListener("click", function (event) {
      if (event.target === aboutModal) {
        closeModal();
      }
    });
  }
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeModal();
    }
  });
}

function setupAudioUnlock() {
  if (typeof document === "undefined") {
    return;
  }
  function unlock() {
    resumeAudio();
    document.removeEventListener("pointerdown", unlock);
    document.removeEventListener("keydown", unlock);
    document.removeEventListener("touchstart", unlock, { passive: true });
  }
  document.addEventListener("pointerdown", unlock);
  document.addEventListener("keydown", unlock);
  document.addEventListener("touchstart", unlock, { passive: true });
}

function init() {
  setupBoard();
  setupKeyboard();
  setupStartButton();
  setupAboutModal();
  setupAudioUnlock();
  render();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}

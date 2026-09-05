"use strict";

const STATUS_IDLE = "IDLE";
const STATUS_WATCHING = "WATCHING";
const STATUS_INPUT = "INPUT";
const STATUS_WON = "WON";
const STATUS_LOST = "LOST";

const PAD_GREEN = "green";
const PAD_RED = "red";
const PAD_YELLOW = "yellow";
const PAD_BLUE = "blue";

const FLASH_ON_MS = 600;
const FLASH_OFF_MS = 400;
const CELEBRATION_DELAY_MS = 1000;

let state = createInitialState();
let pendingTimers = [];

function createInitialState() {
  return {
    sequence: [],
    level: 0,
    score: 0,
    highScore: 0,
    status: STATUS_IDLE,
    inputIndex: 0,
  };
}

function cancelTimers() {
  for (let i = 0; i < pendingTimers.length; i++) {
    clearTimeout(pendingTimers[i]);
  }
  pendingTimers = [];
}

function resetGame() {
  cancelTimers();
  const previousHighScore = state.highScore;
  state = createInitialState();
  state.highScore = previousHighScore;
}

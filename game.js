"use strict";

const EMPTY = "";
const MARKER_X = "X";
const MARKER_O = "O";

const STATUS_PLAYING = "PLAYING";
const STATUS_WIN_X = "WIN_X";
const STATUS_WIN_O = "WIN_O";
const STATUS_DRAW = "DRAW";

const ROWS = 3;
const COLS = 3;

function createInitialState() {
  return {
    grid: [
      [EMPTY, EMPTY, EMPTY],
      [EMPTY, EMPTY, EMPTY],
      [EMPTY, EMPTY, EMPTY],
    ],
    current_player: MARKER_X,
    move_count: 0,
    status: STATUS_PLAYING,
  };
}

let state = createInitialState();

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const resetBtn = document.getElementById("reset");

// Win detection per Design Doc Section 4:
// anchored on the just-placed cell (r, c), checking only the directions
// that pass through it. Returns the winning marker or EMPTY (no win).
function detectWin(r, c, marker) {
  if (marker === EMPTY) return EMPTY;

  let allMatch = true;
  for (let col = 0; col < COLS; col++) {
    if (state.grid[r][col] !== marker) {
      allMatch = false;
      break;
    }
  }
  if (allMatch) return marker;

  allMatch = true;
  for (let row = 0; row < ROWS; row++) {
    if (state.grid[row][c] !== marker) {
      allMatch = false;
      break;
    }
  }
  if (allMatch) return marker;

  if (r === c) {
    allMatch = true;
    for (let d = 0; d < ROWS; d++) {
      if (state.grid[d][d] !== marker) {
        allMatch = false;
        break;
      }
    }
    if (allMatch) return marker;
  }

  if (r + c === ROWS - 1) {
    allMatch = true;
    for (let d = 0; d < ROWS; d++) {
      if (state.grid[d][ROWS - 1 - d] !== marker) {
        allMatch = false;
        break;
      }
    }
    if (allMatch) return marker;
  }

  return EMPTY;
}

// Design Doc Section 3 apply_move flow (single state mutation per action).
function applyMove(row, col) {
  if (state.status !== STATUS_PLAYING) return false;
  if (row < 0 || row >= ROWS || col < 0 || col >= COLS) return false;
  if (state.grid[row][col] !== EMPTY) return false;

  const marker = state.current_player;
  state.grid[row][col] = marker;
  state.move_count += 1;

  const winner = detectWin(row, col, marker);
  if (winner === MARKER_X) {
    state.status = STATUS_WIN_X;
  } else if (winner === MARKER_O) {
    state.status = STATUS_WIN_O;
  } else if (state.move_count === ROWS * COLS) {
    // Design Doc Section 5: board full with no win => draw.
    state.status = STATUS_DRAW;
  } else {
    state.current_player = marker === MARKER_X ? MARKER_O : MARKER_X;
  }

  return true;
}

// Design Doc Section 6 reset().
function resetGame() {
  state = createInitialState();
  renderBoard();
  renderStatus();
}

function renderBoard() {
  boardEl.innerHTML = "";
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const cell = document.createElement("button");
      cell.className = "cell";
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-rowindex", String(r + 1));
      cell.setAttribute("aria-colindex", String(c + 1));

      const value = state.grid[r][c];
      cell.textContent = value;
      if (value === MARKER_X) cell.classList.add("x-marker");
      if (value === MARKER_O) cell.classList.add("o-marker");

      if (state.status !== STATUS_PLAYING) {
        cell.classList.add("disabled");
      }

      cell.addEventListener("click", () => {
        if (applyMove(r, c)) {
          renderBoard();
          renderStatus();
        }
      });

      boardEl.appendChild(cell);
    }
  }
}

function renderStatus() {
  switch (state.status) {
    case STATUS_PLAYING:
      statusEl.textContent = "Player " + state.current_player + "'s turn";
      break;
    case STATUS_WIN_X:
      statusEl.textContent = "Player X wins!";
      break;
    case STATUS_WIN_O:
      statusEl.textContent = "Player O wins!";
      break;
    case STATUS_DRAW:
      statusEl.textContent = "It's a draw!";
      break;
  }
}

resetBtn.addEventListener("click", resetGame);

renderBoard();
renderStatus();
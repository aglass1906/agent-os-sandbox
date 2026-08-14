"use strict";

const EMPTY = "";
const MARKER_RED = "R";
const MARKER_YELLOW = "Y";

const STATUS_PLAYING = "PLAYING";
const STATUS_WIN_RED = "WIN_RED";
const STATUS_WIN_YELLOW = "WIN_YELLOW";
const STATUS_DRAW = "DRAW";

const ROWS = 6;
const COLS = 7;
const WIN_LENGTH = 4;

// Design Doc Section 2: fixed 6x7 grid, every cell initially EMPTY.
function makeGrid() {
  return Array.from({ length: ROWS }, () => new Array(COLS).fill(EMPTY));
}

// Design Doc Section 4 / 7: clean starting state.
function createInitialState() {
  return {
    grid: makeGrid(),
    current_player: MARKER_RED,
    move_count: 0,
    status: STATUS_PLAYING,
    winner: EMPTY,
    win_cells: [],
    last_move: null,
  };
}

let state = createInitialState();

function inBounds(r, c) {
  return r >= 0 && r < ROWS && c >= 0 && c < COLS;
}

// Design Doc Section 3: lowest open row of a column, or -1 if full.
function findLowestOpenRow(grid, col) {
  for (let r = ROWS - 1; r >= 0; r--) {
    if (grid[r][col] === EMPTY) return r;
  }
  return -1;
}

// Design Doc Section 5: anchored win detection on the just-placed cell (r, c).
// Returns the winning run of cells ({r, c}) or [] when no line of four exists.
function detectWin(grid, r, c, marker) {
  if (marker === EMPTY) return [];

  const DIRECTIONS = [
    [0, 1],
    [1, 0],
    [1, 1],
    [1, -1],
  ];

  for (const [dr, dc] of DIRECTIONS) {
    const cells = [{ r, c }];

    let nr = r + dr;
    let nc = c + dc;
    while (inBounds(nr, nc) && grid[nr][nc] === marker) {
      cells.push({ r: nr, c: nc });
      nr += dr;
      nc += dc;
    }

    nr = r - dr;
    nc = c - dc;
    while (inBounds(nr, nc) && grid[nr][nc] === marker) {
      cells.unshift({ r: nr, c: nc });
      nr -= dr;
      nc -= dc;
    }

    if (cells.length >= WIN_LENGTH) return cells;
  }

  return [];
}

// Design Doc Section 3 / 4: drop a disc for the current player into a column.
// Rejected moves (out of range, column full, or game over) return false and
// leave the state unchanged.
function dropDisc(col) {
  if (state.status !== STATUS_PLAYING) return false;
  if (!Number.isInteger(col) || col < 0 || col >= COLS) return false;

  const row = findLowestOpenRow(state.grid, col);
  if (row === -1) return false;

  const marker = state.current_player;
  state.grid[row][col] = marker;
  state.move_count += 1;
  state.last_move = { r: row, c: col };

  const winCells = detectWin(state.grid, row, col, marker);
  if (winCells.length > 0) {
    // Design Doc Section 5: win is reported before the draw check.
    state.winner = marker;
    state.win_cells = winCells;
    state.status = marker === MARKER_RED ? STATUS_WIN_RED : STATUS_WIN_YELLOW;
  } else if (state.move_count === ROWS * COLS) {
    // Design Doc Section 6: full board with no win => draw.
    state.status = STATUS_DRAW;
  } else {
    state.current_player = marker === MARKER_RED ? MARKER_YELLOW : MARKER_RED;
  }

  return true;
}

// ---- DOM wiring (runs only in a browser) ----------------------------------

const isBrowser =
  typeof document !== "undefined" && typeof window !== "undefined";

if (isBrowser) {
  const boardEl = document.getElementById("board");
  const statusEl = document.getElementById("status");
  const celebrationEl = document.getElementById("celebration");
  const resetBtn = document.getElementById("reset");

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
        if (value === MARKER_RED) cell.classList.add("red-marker");
        if (value === MARKER_YELLOW) cell.classList.add("yellow-marker");

        const isWinCell = state.win_cells.some(
          (cellPos) => cellPos.r === r && cellPos.c === c
        );
        if (isWinCell) cell.classList.add("win-cell");

        const isLastMove =
          state.last_move && state.last_move.r === r && state.last_move.c === c;
        if (isLastMove) cell.classList.add("last-move");

        if (state.status !== STATUS_PLAYING) {
          cell.classList.add("disabled");
        }

        cell.addEventListener("click", () => {
          if (dropDisc(c)) {
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
      case STATUS_WIN_RED:
        statusEl.textContent = "Player Red wins!";
        break;
      case STATUS_WIN_YELLOW:
        statusEl.textContent = "Player Yellow wins!";
        break;
      case STATUS_DRAW:
        statusEl.textContent = "It's a draw!";
        break;
    }

    if (state.status === STATUS_WIN_RED || state.status === STATUS_WIN_YELLOW) {
      celebrationEl.textContent = "Congratulations, Player " + state.winner + "!";
      celebrationEl.classList.add("celebrate");
    } else {
      celebrationEl.textContent = "";
      celebrationEl.classList.remove("celebrate");
    }
  }

  function resetGame() {
    state = createInitialState();
    renderBoard();
    renderStatus();
  }

  resetBtn.addEventListener("click", resetGame);

  // About / How to Play screen.
  const aboutBtn = document.getElementById("aboutBtn");
  const aboutModal = document.getElementById("aboutModal");
  const aboutCloseBtn = document.getElementById("aboutClose");

  function openAbout() {
    aboutModal.hidden = false;
    aboutCloseBtn.focus();
  }

  function closeAbout() {
    aboutModal.hidden = true;
    aboutBtn.focus();
  }

  aboutBtn.addEventListener("click", openAbout);
  aboutCloseBtn.addEventListener("click", closeAbout);

  aboutModal.addEventListener("click", (event) => {
    if (event.target === aboutModal) closeAbout();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !aboutModal.hidden) closeAbout();
  });

  renderBoard();
  renderStatus();
}

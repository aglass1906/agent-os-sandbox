"use strict";

const SIZE = 9;
const BOX = 3;
const EMPTY = 0;
const TARGET_REMOVED = 45;

const STATUS_PLAYING = "PLAYING";
const STATUS_WON = "WON";

const boardEl = document.getElementById("board");
const padEl = document.getElementById("pad");
const statusEl = document.getElementById("status");
const messageEl = document.getElementById("message");
const celebrationEl = document.getElementById("celebration");
const resetBtn = document.getElementById("reset");

// ---- Puzzle generation (Design Doc Section 5) -----------------------------

function randInt(n) {
  return Math.floor(Math.random() * n);
}

function shuffledArray(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = randInt(i + 1);
    const tmp = a[i];
    a[i] = a[j];
    a[j] = tmp;
  }
  return a;
}

function makeGrid() {
  return Array.from({ length: SIZE }, () => new Array(SIZE).fill(EMPTY));
}

// Permute rows within their bands and bands among themselves, then the same
// for columns, then relabel digits 1-9 by a random permutation. Applied to a
// valid base grid this preserves validity and yields a random solution.
function buildSolution() {
  const base = [
    [1, 2, 3, 4, 5, 6, 7, 8, 9],
    [4, 5, 6, 7, 8, 9, 1, 2, 3],
    [7, 8, 9, 1, 2, 3, 4, 5, 6],
    [2, 3, 4, 5, 6, 7, 8, 9, 1],
    [5, 6, 7, 8, 9, 1, 2, 3, 4],
    [8, 9, 1, 2, 3, 4, 5, 6, 7],
    [3, 4, 5, 6, 7, 8, 9, 1, 2],
    [6, 7, 8, 9, 1, 2, 3, 4, 5],
    [9, 1, 2, 3, 4, 5, 6, 7, 8],
  ];

  const labels = shuffledArray([1, 2, 3, 4, 5, 6, 7, 8, 9]);
  const bands = shuffledArray([0, 1, 2]);
  const rowPerm = [];
  for (const band of bands) {
    for (const row of shuffledArray([0, 1, 2])) {
      rowPerm.push(band * BOX + row);
    }
  }
  const stacks = shuffledArray([0, 1, 2]);
  const colPerm = [];
  for (const stack of stacks) {
    for (const col of shuffledArray([0, 1, 2])) {
      colPerm.push(stack * BOX + col);
    }
  }

  const solution = makeGrid();
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const digit = base[rowPerm[r]][colPerm[c]];
      solution[r][c] = labels[digit - 1];
    }
  }
  return solution;
}

function boxOrigin(r, c) {
  return { br: Math.floor(r / BOX) * BOX, bc: Math.floor(c / BOX) * BOX };
}

function candidatesFor(grid, r, c) {
  const used = new Set();
  for (let i = 0; i < SIZE; i++) {
    used.add(grid[r][i]);
    used.add(grid[i][c]);
  }
  const { br, bc } = boxOrigin(r, c);
  for (let dr = 0; dr < BOX; dr++) {
    for (let dc = 0; dc < BOX; dc++) {
      used.add(grid[br + dr][bc + dc]);
    }
  }
  const cands = [];
  for (let d = 1; d <= SIZE; d++) {
    if (!used.has(d)) cands.push(d);
  }
  return cands;
}

// Backtracking solver that counts solutions, stopping at `limit`.
function countSolutions(grid, limit) {
  let count = 0;

  function solve() {
    if (count >= limit) return;
    let best = null;
    let bestCands = null;
    for (let r = 0; r < SIZE; r++) {
      for (let c = 0; c < SIZE; c++) {
        if (grid[r][c] !== EMPTY) continue;
        const cands = candidatesFor(grid, r, c);
        if (cands.length === 0) return;
        if (best === null || cands.length < bestCands.length) {
          best = [r, c];
          bestCands = cands;
        }
      }
    }
    if (best === null) {
      count += 1;
      return;
    }
    for (const d of bestCands) {
      grid[best[0]][best[1]] = d;
      solve();
      grid[best[0]][best[1]] = EMPTY;
      if (count >= limit) return;
    }
  }

  solve();
  return count;
}

function generatePuzzle() {
  const solution = buildSolution();
  const grid = solution.map((row) => row.slice());
  const given = Array.from({ length: SIZE }, () => new Array(SIZE).fill(true));

  const cells = [];
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      cells.push([r, c]);
    }
  }

  let removed = 0;
  for (const [r, c] of shuffledArray(cells)) {
    if (removed >= TARGET_REMOVED) break;
    const backup = grid[r][c];
    grid[r][c] = EMPTY;
    given[r][c] = false;
    if (countSolutions(grid, 2) === 1) {
      removed += 1;
    } else {
      grid[r][c] = backup;
      given[r][c] = true;
    }
  }

  return { solution, grid, given };
}

// ---- State management (Design Doc Sections 3 and 8) ------------------------

function countFilled(grid) {
  let n = 0;
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      if (grid[r][c] !== EMPTY) n += 1;
    }
  }
  return n;
}

function createInitialState() {
  const puzzle = generatePuzzle();
  return {
    solution: puzzle.solution,
    grid: puzzle.grid,
    given: puzzle.given,
    errors: makeGrid(),
    selected: null,
    filled_count: countFilled(puzzle.grid),
    status: STATUS_PLAYING,
  };
}

let state = createInitialState();

// ---- Real-time rule validation (Design Doc Section 4) ----------------------

function recomputeErrors() {
  const errs = makeGrid();

  const flagUnit = (cells) => {
    const seen = {};
    for (const [r, c] of cells) {
      const v = state.grid[r][c];
      if (v === EMPTY) continue;
      if (seen[v] !== undefined) {
        errs[r][c] = true;
        errs[seen[v][0]][seen[v][1]] = true;
      } else {
        seen[v] = [r, c];
      }
    }
  };

  for (let r = 0; r < SIZE; r++) {
    const row = [];
    for (let c = 0; c < SIZE; c++) row.push([r, c]);
    flagUnit(row);
  }
  for (let c = 0; c < SIZE; c++) {
    const col = [];
    for (let r = 0; r < SIZE; r++) col.push([r, c]);
    flagUnit(col);
  }
  for (let br = 0; br < BOX; br++) {
    for (let bc = 0; bc < BOX; bc++) {
      const boxCells = [];
      for (let dr = 0; dr < BOX; dr++) {
        for (let dc = 0; dc < BOX; dc++) {
          boxCells.push([br * BOX + dr, bc * BOX + dc]);
        }
      }
      flagUnit(boxCells);
    }
  }

  state.errors = errs;
}

// ---- Win detection (Design Doc Section 6) ----------------------------------

function isSolved() {
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      if (state.grid[r][c] !== state.solution[r][c]) return false;
    }
  }
  return true;
}

// ---- Actions ---------------------------------------------------------------

function selectCell(r, c) {
  state.selected = { r, c };
  renderBoard();
  updateMessage();
}

function inputDigit(digit) {
  if (state.status !== STATUS_PLAYING) return;
  if (!state.selected) {
    statusEl.textContent = "Select an empty cell first, then enter a digit";
    return;
  }
  const { r, c } = state.selected;
  if (state.given[r][c]) return;
  if (state.grid[r][c] === digit) return;

  state.grid[r][c] = digit;
  state.filled_count = countFilled(state.grid);
  recomputeErrors();
  if (isSolved()) {
    state.status = STATUS_WON;
  }
  renderBoard();
  renderStatus();
  updateMessage();
}

function eraseCell() {
  if (state.status !== STATUS_PLAYING) return;
  if (!state.selected) return;
  const { r, c } = state.selected;
  if (state.given[r][c]) return;
  if (state.grid[r][c] === EMPTY) return;

  state.grid[r][c] = EMPTY;
  state.filled_count = countFilled(state.grid);
  recomputeErrors();
  renderBoard();
  renderStatus();
  updateMessage();
}

function moveSelection(dr, dc) {
  const cur = state.selected || { r: 4, c: 4 };
  let r = cur.r + dr;
  let c = cur.c + dc;
  if (r < 0) r = SIZE - 1;
  if (r >= SIZE) r = 0;
  if (c < 0) c = SIZE - 1;
  if (c >= SIZE) c = 0;
  selectCell(r, c);
}

// ---- Rendering -------------------------------------------------------------

function renderBoard() {
  boardEl.innerHTML = "";
  for (let r = 0; r < SIZE; r++) {
    for (let c = 0; c < SIZE; c++) {
      const cell = document.createElement("button");
      cell.className = "cell";
      cell.type = "button";
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-rowindex", String(r + 1));
      cell.setAttribute("aria-colindex", String(c + 1));

      const value = state.grid[r][c];
      cell.textContent = value === EMPTY ? "" : String(value);
      cell.setAttribute("aria-label", value === EMPTY ? "Empty" : String(value));

      if (state.given[r][c]) cell.classList.add("given");
      if (c === BOX - 1 || c === BOX * 2 - 1) cell.classList.add("box-right");
      if (r === BOX - 1 || r === BOX * 2 - 1) cell.classList.add("box-bottom");
      if (state.errors[r][c]) cell.classList.add("error");

      if (state.selected) {
        const { r: sr, c: sc } = state.selected;
        if (sr === r && sc === c) {
          cell.classList.add("selected");
        } else {
          const peerBox = boxOrigin(sr, sc);
          if (sr === r) cell.classList.add("peer-row");
          if (sc === c) cell.classList.add("peer-col");
          if (
            r >= peerBox.br &&
            r < peerBox.br + BOX &&
            c >= peerBox.bc &&
            c < peerBox.bc + BOX
          ) {
            cell.classList.add("peer-box");
          }
        }
      }

      cell.addEventListener("click", () => selectCell(r, c));
      boardEl.appendChild(cell);
    }
  }
}

const PAD_DIGITS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

function buildPad() {
  padEl.innerHTML = "";
  for (const d of PAD_DIGITS) {
    const btn = document.createElement("button");
    btn.className = "pad-btn";
    btn.type = "button";
    btn.textContent = String(d);
    btn.setAttribute("aria-label", "Enter digit " + d);
    btn.addEventListener("click", () => inputDigit(d));
    padEl.appendChild(btn);
  }
  const erase = document.createElement("button");
  erase.className = "pad-btn wide";
  erase.type = "button";
  erase.textContent = "⌫";
  erase.setAttribute("aria-label", "Erase selected cell");
  erase.addEventListener("click", eraseCell);
  padEl.appendChild(erase);
}

function renderStatus() {
  if (state.status === STATUS_WON) {
    statusEl.textContent = "Solved! Congratulations!";
    if (celebrationEl) {
      celebrationEl.textContent = "Puzzle complete!";
      celebrationEl.classList.add("celebrate");
    }
    return;
  }

  if (celebrationEl) {
    celebrationEl.textContent = "";
    celebrationEl.classList.remove("celebrate");
  }

  const remaining = SIZE * SIZE - state.filled_count;
  statusEl.textContent = "Cells remaining: " + remaining;
}

function updateMessage() {
  if (messageEl) messageEl.textContent = "";
  if (state.status === STATUS_WON) return;
  const sel = state.selected;
  if (!sel) return;
  if (state.given[sel.r][sel.c]) {
    messageEl.textContent =
      "This cell is part of the starting puzzle and cannot be changed.";
  } else if (state.errors[sel.r][sel.c]) {
    messageEl.textContent =
      "Conflict: this digit appears more than once in its row, column, or 3x3 box.";
  } else if (state.grid[sel.r][sel.c] === EMPTY) {
    messageEl.textContent = "Enter a digit 1-9, or erase with Backspace.";
  }
}

// ---- Input wiring ----------------------------------------------------------

function handleGlobalKeydown(e) {
  if (/^[1-9]$/.test(e.key)) {
    inputDigit(parseInt(e.key, 10));
    return;
  }
  if (e.key === "Backspace" || e.key === "Delete" || e.key === "0") {
    e.preventDefault();
    eraseCell();
    return;
  }
  const dirs = {
    ArrowUp: [-1, 0],
    ArrowDown: [1, 0],
    ArrowLeft: [0, -1],
    ArrowRight: [0, 1],
  };
  if (dirs[e.key]) {
    e.preventDefault();
    moveSelection(dirs[e.key][0], dirs[e.key][1]);
  }
}

function resetGame() {
  state = createInitialState();
  renderBoard();
  renderStatus();
  updateMessage();
}

document.addEventListener("keydown", handleGlobalKeydown);
resetBtn.addEventListener("click", resetGame);

buildPad();
renderBoard();
renderStatus();
updateMessage();

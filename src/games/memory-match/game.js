"use strict";

const COLS = 4;
const ROWS = 4;
const TOTAL_CARDS = COLS * ROWS;
const TOTAL_PAIRS = TOTAL_CARDS / 2;
const MAX_FLIPPED = 2;
const MISMATCH_DELAY_MS = 900;

const STATUS_PLAYING = "PLAYING";
const STATUS_WON = "WON";

const SYMBOLS = [
  "\u2660", "\u2665", "\u2666", "\u2663",
  "\u2605", "\u263E", "\u2641", "\u2642"
];

function shuffle(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const temp = array[i];
    array[i] = array[j];
    array[j] = temp;
  }
  return array;
}

function createCards() {
  const symbols = SYMBOLS.slice(0, TOTAL_PAIRS);
  const deck = symbols.concat(symbols);
  shuffle(deck);

  const cards = [];
  for (let row = 0; row < ROWS; row++) {
    const rowArr = [];
    for (let col = 0; col < COLS; col++) {
      rowArr.push({
        symbol: deck[row * COLS + col],
        flipped: false,
        matched: false
      });
    }
    cards.push(rowArr);
  }
  return cards;
}

function createInitialState() {
  return {
    cards: createCards(),
    flippedCards: [],
    matchedPairs: 0,
    moves: 0,
    elapsedSeconds: 0,
    status: STATUS_PLAYING,
    locked: false
  };
}

let state = createInitialState();

function inBounds(row, col) {
  return (
    Number.isInteger(row) &&
    Number.isInteger(col) &&
    row >= 0 &&
    row < ROWS &&
    col >= 0 &&
    col < COLS
  );
}

// ---- Game flow logic -------------------------------------------------------

// Win condition detection: the game is won once every pair is matched.
function checkWin() {
  return state.matchedPairs === TOTAL_PAIRS;
}

// Move counting: a move is completed each time a second card is flipped.
function incrementMove() {
  state.moves += 1;
}

// Game completion handling: record a matched pair and, if that was the last
// pair, transition to the terminal WON state. Returns the outcome result.
function handleMatch() {
  const firstPos = state.flippedCards[0];
  const secondPos = state.flippedCards[1];
  const firstCard = state.cards[firstPos.row][firstPos.col];
  const secondCard = state.cards[secondPos.row][secondPos.col];

  firstCard.matched = true;
  secondCard.matched = true;
  state.matchedPairs += 1;
  state.flippedCards = [];

  if (checkWin()) {
    state.status = STATUS_WON;
    return "MATCH_WON";
  }
  return "MATCH";
}

// Terminal state locking: reject any interaction once the game is no longer
// PLAYING (for example after a win) or while the board is temporarily locked
// during a mismatch resolution.
function isTerminalLocked() {
  return state.status !== STATUS_PLAYING || state.locked;
}

// Core logic: attempt to flip the card at (row, col).
// Returns an object describing the outcome; returns {accepted:false, reason}
// for any invalid move, leaving the state untouched.
function flipCard(row, col) {
  if (isTerminalLocked()) {
    return {
      accepted: false,
      reason: state.status !== STATUS_PLAYING ? "NOT_PLAYING" : "LOCKED"
    };
  }
  if (!inBounds(row, col)) {
    return { accepted: false, reason: "OUT_OF_BOUNDS" };
  }

  const card = state.cards[row][col];
  if (card.matched) {
    return { accepted: false, reason: "ALREADY_MATCHED" };
  }
  if (card.flipped) {
    return { accepted: false, reason: "ALREADY_FLIPPED" };
  }

  card.flipped = true;
  state.flippedCards.push({ row: row, col: col });

  if (state.flippedCards.length < MAX_FLIPPED) {
    return { accepted: true, result: "FLIPPED" };
  }

  // Two cards are now face up: count the move and evaluate the pair.
  incrementMove();

  const firstPos = state.flippedCards[0];
  const firstCard = state.cards[firstPos.row][firstPos.col];

  if (firstCard.symbol === card.symbol) {
    return { accepted: true, result: handleMatch() };
  }

  // Mismatch: lock the board so no further cards can be flipped while the
  // mismatched cards are shown; the caller schedules resolveMismatch().
  state.locked = true;
  return { accepted: true, result: "MISMATCH" };
}

// Core logic: turn the pending mismatched cards back face down and unlock.
function resolveMismatch() {
  for (const pos of state.flippedCards) {
    state.cards[pos.row][pos.col].flipped = false;
  }
  state.flippedCards = [];
  state.locked = false;
}

// Timer for the mismatch resolution lives outside the core state so that reset
// can always clear a pending timer and never leave stale handlers fighting.
let mismatchTimer = null;

// ---- DOM wiring (runs only in a browser) ----------------------------------

const isBrowser =
  typeof document !== "undefined" && typeof window !== "undefined";

if (isBrowser) {
  const canvas = document.getElementById("board");
  const ctx = canvas.getContext("2d");
  const statusEl = document.getElementById("status");
  const pairsMatchedEl = document.getElementById("pairsMatched");
  const movesEl = document.getElementById("moves");
  const timerEl = document.getElementById("timer");
  const celebrationEl = document.getElementById("celebration");
  const resetBtn = document.getElementById("reset");

  const FACE = "#ecf0f1";
  const FACE_BORDER = "#bdc3c7";
  const BACK = "#34495e";
  const BACK_EDGE = "#2c3e50";
  const MATCHED = "#2ecc71";
  const CURSOR = "#e67e22";
  const TEXT = "#2c3e50";
  const SYMBOL_SIZE = 52;

  const CARD_MARGIN = 10;
  const CARD_GAP = 8;
  const CORNER_RADIUS = 8;

  let cursor = { row: 0, col: 0 };
  let hasCursor = false;
  let timerInterval = null;

  function cellGeometry() {
    const gap = CARD_GAP;
    const margin = CARD_MARGIN;
    const cellW = (canvas.width - margin * 2 - gap * (COLS - 1)) / COLS;
    const cellH = (canvas.height - margin * 2 - gap * (ROWS - 1)) / ROWS;
    return { gap, margin, cellW, cellH };
  }

  function cardRect(row, col) {
    const g = cellGeometry();
    const x = g.margin + col * (g.cellW + g.gap);
    const y = g.margin + row * (g.cellH + g.gap);
    return { x: x, y: y, w: g.cellW, h: g.cellH, r: CORNER_RADIUS };
  }

  function roundedRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawCard(row, col) {
    const card = state.cards[row][col];
    const rect = cardRect(row, col);

    if (card.matched) {
      roundedRect(rect.x, rect.y, rect.w, rect.h, rect.r);
      ctx.fillStyle = MATCHED;
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "600 " + SYMBOL_SIZE + "px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(card.symbol, rect.x + rect.w / 2, rect.y + rect.h / 2 + 4);
      return;
    }

    if (card.flipped) {
      roundedRect(rect.x, rect.y, rect.w, rect.h, rect.r);
      ctx.fillStyle = FACE;
      ctx.fill();
      ctx.strokeStyle = FACE_BORDER;
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = TEXT;
      ctx.font = "600 " + SYMBOL_SIZE + "px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(card.symbol, rect.x + rect.w / 2, rect.y + rect.h / 2 + 4);
      return;
    }

    // Face down.
    roundedRect(rect.x, rect.y, rect.w, rect.h, rect.r);
    ctx.fillStyle = BACK;
    ctx.fill();
    ctx.strokeStyle = BACK_EDGE;
    ctx.lineWidth = 3;
    ctx.stroke();

    // Inner decorative motif.
    const inner = rect.r * 0.7;
    roundedRect(
      rect.x + 6,
      rect.y + 6,
      rect.w - 12,
      rect.h - 12,
      inner
    );
    ctx.strokeStyle = "rgba(255,255,255,0.18)";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  function drawCursor() {
    if (!hasCursor) return;
    const rect = cardRect(cursor.row, cursor.col);
    ctx.strokeStyle = CURSOR;
    ctx.lineWidth = 4;
    roundedRect(
      rect.x - 3,
      rect.y - 3,
      rect.w + 6,
      rect.h + 6,
      rect.r + 3
    );
    ctx.stroke();
  }

  function renderBoard() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        drawCard(row, col);
      }
    }
    drawCursor();
  }

  function formatTime(totalSeconds) {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return mins + ":" + (secs < 10 ? "0" : "") + secs;
  }

  function renderStats() {
    pairsMatchedEl.textContent = "Pairs: " + state.matchedPairs;
    movesEl.textContent = "Moves: " + state.moves;
    timerEl.textContent = "Time: " + formatTime(state.elapsedSeconds);
  }

  function renderStatus() {
    if (state.status === STATUS_WON) {
      statusEl.textContent = "You matched all the pairs!";
      celebrationEl.textContent = "Congratulations, you win!";
      celebrationEl.classList.add("celebrate");
    } else {
      statusEl.textContent = "Find all matching pairs \u2014 flip two cards";
      celebrationEl.textContent = "";
      celebrationEl.classList.remove("celebrate");
    }
  }

  function renderAll() {
    renderBoard();
    renderStats();
    renderStatus();
  }

  function stopTimer() {
    if (timerInterval !== null) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  function startTimer() {
    if (timerInterval !== null) return;
    timerInterval = setInterval(() => {
      if (state.status === STATUS_PLAYING) {
        state.elapsedSeconds += 1;
        renderStats();
      }
    }, 1000);
  }

  function clearMismatchTimer() {
    if (mismatchTimer !== null) {
      clearTimeout(mismatchTimer);
      mismatchTimer = null;
    }
  }

  function resetGame() {
    clearMismatchTimer();
    stopTimer();
    state = createInitialState();
    cursor = { row: 0, col: 0 };
    hasCursor = false;
    renderAll();
    startTimer();
  }

  function onCardTouched(row, col) {
    const outcome = flipCard(row, col);
    if (!outcome.accepted) return;

    renderAll();

    if (outcome.result === "MATCH_WON") {
      stopTimer();
      return;
    }
    if (outcome.result === "MATCH") {
      return;
    }
    if (outcome.result === "MISMATCH") {
      clearMismatchTimer();
      mismatchTimer = setTimeout(() => {
        mismatchTimer = null;
        resolveMismatch();
        renderAll();
      }, MISMATCH_DELAY_MS);
    }
  }

  function hexToGrid(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (clientX - rect.left) * scaleX;
    const y = (clientY - rect.top) * scaleY;

    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        const r = cardRect(row, col);
        if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) {
          return { row: row, col: col };
        }
      }
    }
    return null;
  }

  canvas.addEventListener("mousedown", (event) => {
    const cell = hexToGrid(event.clientX, event.clientY);
    if (!cell) return;
    hasCursor = true;
    cursor = cell;
    onCardTouched(cell.row, cell.col);
  });

  canvas.addEventListener("touchstart", (event) => {
    event.preventDefault();
    const touch = event.touches[0];
    const cell = hexToGrid(touch.clientX, touch.clientY);
    if (!cell) return;
    hasCursor = true;
    cursor = cell;
    onCardTouched(cell.row, cell.col);
  }, { passive: false });

  canvas.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown" &&
        event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        hasCursor = true;
        onCardTouched(cursor.row, cursor.col);
      }
      return;
    }

    event.preventDefault();
    hasCursor = true;
    let nr = cursor.row;
    let nc = cursor.col;
    if (event.key === "ArrowUp") nr = cursor.row - 1;
    else if (event.key === "ArrowDown") nr = cursor.row + 1;
    else if (event.key === "ArrowLeft") nc = cursor.col - 1;
    else if (event.key === "ArrowRight") nc = cursor.col + 1;
    if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS) {
      cursor = { row: nr, col: nc };
      renderBoard();
    }
  });

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

  function sizeCanvas() {
    const displayed = Math.min(window.innerWidth - 32, 600);
    canvas.width = displayed;
    canvas.height = displayed;
    renderAll();
  }

  window.addEventListener("resize", sizeCanvas);

  canvas.setAttribute("tabindex", "0");
  canvas.setAttribute("role", "application");

  sizeCanvas();
  startTimer();
}

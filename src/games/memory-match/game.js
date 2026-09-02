"use strict";

const COLS = 4;
const ROWS = 4;
const TOTAL_CARDS = COLS * ROWS;
const TOTAL_PAIRS = TOTAL_CARDS / 2;
const MAX_FLIPPED = 2;

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

"use strict";

const WORD_LENGTH = 5;
const MAX_GUESSES = 6;

const FB_EMPTY = "empty";
const FB_CORRECT = "correct";
const FB_PRESENT = "present";
const FB_ABSENT = "absent";

const STATUS_PLAYING = "PLAYING";
const STATUS_WON = "WON";
const STATUS_LOST = "LOST";

const KEY_ENTER = "ENTER";
const KEY_BACKSPACE = "BACK";

// Section 6: a curated word list of valid 5-letter guesses. The answer words
// are a subset of the valid set so any answer is also a legal guess.
const ANSWERS = [
  "ABATE", "ABIDE", "ABOVE", "ABUSE", "ADMIT", "ADOBE", "ADOPT",
  "ADULT", "AFTER", "AGENT", "AGREE", "ALARM", "ALBUM", "ALIVE", "ALLOW",
  "ALONE", "ALOUD", "AMBER", "ANGRY", "APPLE", "APRON", "ARGUE", "ARISE",
  "AROMA", "ATLAS", "AUDIO", "AVOID", "AWAKE", "BAKER", "BEACH",
  "BEARD", "BEGIN", "BEING", "BELOW", "BENCH", "BERRY", "BLACK", "BLAZE",
  "BLEED", "BLOCK", "BOARD", "BONUS", "BRAIN", "BRAND", "BRAVE", "BREAD",
  "BRING", "BROOK", "BUILD", "BURNT", "CABIN", "CAMEL", "CARGO",
  "CARVE", "CAUSE", "CHAIR", "CHALK", "CHARM", "CHAOS", "CHEEK", "CHEST",
  "CHILD", "CHOIR", "CHORD", "CIDER", "CIGAR", "CIVIC", "CLASH", "CLEAN",
  "CLICK", "CLOUD", "COACH", "COBRA", "COLOR", "COUNT", "COUGH", "COURT",
  "CRISP", "CROSS", "CROWD", "CROWN", "CRUMB", "CRUST", "CURVE", "CYCLE",
  "DAILY", "DAISY", "DANCE",
  "DEATH", "DELAY", "DEPTH", "DIRTY", "DIZZY", "DOUBT", "DOZEN",
  "DRAFT", "DRAIN", "DRAMA", "DREAM", "DRIED", "DRIFT", "DRINK", "DRIVE",
  "DROWN", "DWARF", "EAGER", "EARTH", "EDICT", "ELDER", "EMPTY", "ENEMY",
  "ENJOY", "EPOCH", "ERROR", "ESSAY", "ETHIC", "EVENT", "EVERY", "EVOKE",
  "EXACT", "EXILE", "EXIST", "EXTRA", "FABLE", "FAITH", "FAULT", "FEAST",
  "FENCE", "FERAL", "FIERY", "FIFTH", "FIGHT", "FIRST", "FLESH", "FLOAT",
  "FLOOR", "FLOWER", "FOCUS", "FORCE", "FOUND", "FRAME", "FRANK",
  "FREED", "FRIED", "FROST", "FRONT", "FRUIT", "GAUGE", "GHOST", "GIANT",
  "GLASS", "GLOBE", "GLOSS", "GOODS", "GRACE",
  "GRADE", "GRAND", "GRAVE", "GREAT", "GREET", "GREEN", "GRIND", "GROUP",
  "GUARD", "GUESS", "GUEST", "GUILD", "HATCH", "HAUNT", "HEAVY",
  "HELLO", "HINGE", "HONOR", "HORDE", "HOUSE", "HUMOR",
  "IDEAL", "IMAGE", "INDEX", "INERT",
  "IRATE", "LIGHT", "LIMIT", "LINEN", "LOGIC", "LOOSE",
  "LOWER", "LUNAR", "LYRIC", "MAGIC", "MAJOR", "MANGO", "MARCH", "MASON",
  "MATCH", "MEDIA", "MEDAL", "METAL", "MODEL", "MOODY",
  "MOOSE", "MOTIF", "MOTOR", "MOUNT", "MOUTH", "NAIVE",
  "NAVAL", "NEXUS", "NIGHT", "NINTH", "NOBLE", "NORTH", "OASIS", "OCEAN",
  "OFFER", "OFTEN", "ONION", "OPERA", "ORBIT", "ORDER", "ORGAN", "OTHER",
  "OUTER", "OWNER", "OXIDE", "PANEL", "PARTY", "PATCH", "PAUSE",
  "PEACE", "PEDAL", "PHONE", "PIANO", "PIECE", "PILOT", "PINCH", "PIXEL",
  "PIZZA", "PLACE", "PLAIN", "PLANK", "PLANT", "PLATE", "POINT",
  "PORCH", "POUND", "POWER", "PRESS", "PRICE", "PRIDE", "PRIME", "PRINT",
  "PRIZE", "PROOF", "PROSE", "PROUD", "QUEEN", "QUICK", "QUIET", "QUOTA",
  "QUOTE", "RADIO", "RAINY", "RALLY", "REBEL", "REFER", "REIGN", "RELAX",
  "RHYME", "RIGHT", "RIPER", "RISEN", "ROBOT", "ROUGE", "ROUGH", "ROUND",
  "ROUTE", "RUSTY", "SAINT", "SALAD", "SALSA", "SAUCE", "SCALE",
  "SCAR", "SCARY", "SCENE", "SCORE", "SCOPE", "SCOUT", "SENSE", "SHAPE",
  "SHARE", "SHARP", "SHEEP", "SHINE", "SHIRT", "SHOCK", "SHOOT", "SHORT",
  "SIGHT", "SILLY", "SINCE", "SIXTH", "SKATE", "SKILL", "SLAVE", "SLEEP",
  "SLIDE", "SMART", "SMILE", "SMOKE", "SNACK", "SOLAR", "SOLID", "SORRY",
  "SOUND", "SOUTH", "SPACE", "SPARE", "SPEAK", "SPOON", "SPRAY", "SQUAD",
  "STACK", "STAGE", "STAKE", "STAMP", "STAND", "STARE", "STATE", "STEAK",
  "STEER", "STICK", "STILL", "STING", "STORE", "STORM", "STORY", "STOUT",
  "STRAP", "STRAY", "STUDY", "STUNT", "SUGAR", "SUITE", "SUNNY", "SUPER",
  "SURGE", "SWEAT", "SWORD", "SWING", "TABLE", "TASTE", "TEACH",
  "TERRA", "THANK", "THOSE", "THING", "THICK", "THIRD", "THROW",
  "TIGER", "TIGHT", "TITLE", "TODAY", "TOKEN", "TOOTH", "TOPIC", "TORCH",
  "TOTAL", "TOUCH", "TOUGH", "TOWEL", "TOWER", "TRACE", "TRACK", "TRADE",
  "TRAIN", "TREND", "TRIAL", "TRICK", "TROPE", "TRUCK", "TRULY", "TRUNK",
  "TRUST", "TRUTH", "TWIST", "UNCLE", "UNDER", "UNITE", "UNITY", "UPSET",
  "URBAN", "USAGE", "USUAL", "VAGUE", "VALID", "VALUE", "VAULT", "VEGAN",
  "VENUS", "VERSE", "VIDEO", "VIRUS", "VITAL", "VOICE", "VOTER",
  "WATER", "WAVES", "WATCH", "WEARY", "WEIGH", "WHEAT", "WHEEL", "WINDY",
  "WITCH", "WORST", "WOVEN", "WRIST", "WROTE", "YOUNG", "YOUTH", "ZEBRA",
  "ZERO"
];

const VALID_WORDS = new Set(ANSWERS);

function createInitialState() {
  const grid = [];
  const feedback = [];
  for (let r = 0; r < MAX_GUESSES; r++) {
    grid.push(new Array(WORD_LENGTH).fill(""));
    feedback.push(new Array(WORD_LENGTH).fill(FB_EMPTY));
  }
  const keyboard = {};
  for (let i = 0; i < 26; i++) {
    keyboard[String.fromCharCode(65 + i)] = FB_EMPTY;
  }
  const answer = ANSWERS[Math.floor(Math.random() * ANSWERS.length)];
  return {
    answer,
    grid,
    feedback,
    current_row: 0,
    current_col: 0,
    status: STATUS_PLAYING,
    keyboard,
  };
}

let state = createInitialState();

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const keyboardEl = document.getElementById("keyboard");
const resetBtn = document.getElementById("reset");

const isValidWord = (word) => word.length === WORD_LENGTH && VALID_WORDS.has(word);

// Section 4: two-pass feedback classification for the current (just-submitted)
// row, faithful to Wordle's duplicate-letter handling.
function classifyGuess() {
  const guess = state.grid[state.current_row];
  const answer = state.answer;
  const rowFeedback = state.feedback[state.current_row];

  const remaining = {};
  for (let i = 0; i < WORD_LENGTH; i++) {
    const ch = answer[i];
    remaining[ch] = (remaining[ch] || 0) + 1;
  }

  for (let c = 0; c < WORD_LENGTH; c++) {
    if (guess[c] === answer[c]) {
      rowFeedback[c] = FB_CORRECT;
      remaining[guess[c]] -= 1;
    }
  }

  for (let c = 0; c < WORD_LENGTH; c++) {
    if (rowFeedback[c] === FB_CORRECT) continue;
    const g = guess[c];
    if ((remaining[g] || 0) > 0) {
      rowFeedback[c] = FB_PRESENT;
      remaining[g] -= 1;
    } else {
      rowFeedback[c] = FB_ABSENT;
    }
  }
}

// Section 5: merge row feedback into the keyboard map using the hierarchy
// correct > present > absent (a guess may only improve a key's state).
function mergeKeyboardState() {
  const rank = { [FB_ABSENT]: 1, [FB_PRESENT]: 2, [FB_CORRECT]: 3 };
  for (let c = 0; c < WORD_LENGTH; c++) {
    const letter = state.grid[state.current_row][c];
    const fb = state.feedback[state.current_row][c];
    if ((rank[fb] || 0) > (rank[state.keyboard[letter]] || 0)) {
      state.keyboard[letter] = fb;
    }
  }
}

function inputLetter(letter) {
  if (state.status !== STATUS_PLAYING) return;
  if (state.current_col >= WORD_LENGTH) return;
  state.grid[state.current_row][state.current_col] = letter;
  state.current_col += 1;
  renderBoard();
}

function deleteLetter() {
  if (state.status !== STATUS_PLAYING) return;
  if (state.current_col <= 0) return;
  state.current_col -= 1;
  state.grid[state.current_row][state.current_col] = "";
  state.feedback[state.current_row][state.current_col] = FB_EMPTY;
  renderBoard();
}

function submitGuess() {
  if (state.status !== STATUS_PLAYING) return;
  if (state.current_col < WORD_LENGTH) {
    statusEl.textContent = "Not enough letters";
    return;
  }
  const guess = state.grid[state.current_row].join("");
  if (!isValidWord(guess)) {
    statusEl.textContent = "Not in word list";
    return;
  }

  classifyGuess();
  mergeKeyboardState();

  addReveal();

  const won = guess === state.answer;
  if (won) {
    state.status = STATUS_WON;
    renderBoard();
    renderKeyboard();
    statusEl.textContent = "You won! The word was " + state.answer;
    return;
  }

  renderBoard();
  renderKeyboard();

  if (state.current_row === MAX_GUESSES - 1) {
    state.status = STATUS_LOST;
    statusEl.textContent = "You lost! The word was " + state.answer;
    return;
  }

  state.current_row += 1;
  state.current_col = 0;
  statusEl.textContent = "Guesses remaining: " + (MAX_GUESSES - state.current_row);
}

function addReveal() {
  const rowEl = boardEl.children[state.current_row];
  if (!rowEl) return;
  const tiles = rowEl.children;
  for (let c = 0; c < WORD_LENGTH; c++) {
    tiles[c].style.animationDelay = c * 90 + "ms";
    tiles[c].classList.add("flip");
  }
}

function renderBoard() {
  boardEl.innerHTML = "";
  for (let r = 0; r < MAX_GUESSES; r++) {
    const row = document.createElement("div");
    row.className = "board-row";
    row.setAttribute("role", "row");
    for (let c = 0; c < WORD_LENGTH; c++) {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.setAttribute("role", "gridcell");
      tile.textContent = state.grid[r][c];
      const fb = state.feedback[r][c];
      if (fb !== FB_EMPTY) tile.classList.add(fb);
      row.appendChild(tile);
    }
    boardEl.appendChild(row);
  }
}

const KEYBOARD_ROWS = [
  ["Q","W","E","R","T","Y","U","I","O","P"],
  ["A","S","D","F","G","H","J","K","L"],
  [KEY_ENTER,"Z","X","C","V","B","N","M",KEY_BACKSPACE],
];

function buildKeyboard() {
  keyboardEl.innerHTML = "";
  for (const row of KEYBOARD_ROWS) {
    const rowEl = document.createElement("div");
    rowEl.className = "keyboard-row";
    for (const keyId of row) {
      const btn = document.createElement("button");
      btn.className = "key";
      if (keyId === KEY_ENTER || keyId === KEY_BACKSPACE) {
        btn.classList.add("wide");
        btn.textContent = keyId === KEY_ENTER ? "Enter" : "⌫";
        btn.addEventListener("click", () =>
          keyId === KEY_ENTER ? submitGuess() : deleteLetter()
        );
      } else {
        btn.textContent = keyId;
        btn.addEventListener("click", () => inputLetter(keyId));
      }
      rowEl.appendChild(btn);
    }
    keyboardEl.appendChild(rowEl);
  }
}

function renderKeyboard() {
  const keys = keyboardEl.querySelectorAll(".key");
  keys.forEach((key) => {
    const letterKey = key.textContent.trim().toUpperCase();
    if (!/^[A-Z]$/.test(letterKey)) return;
    key.className = "key";
    const fb = state.keyboard[letterKey];
    if (fb === FB_CORRECT || fb === FB_PRESENT || fb === FB_ABSENT) {
      key.classList.add(fb);
    }
  });
}

function handleGlobalKeydown(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    submitGuess();
    return;
  }
  if (e.key === "Backspace") {
    e.preventDefault();
    deleteLetter();
    return;
  }
  if (/^[a-zA-Z]$/.test(e.key)) {
    inputLetter(e.key.toUpperCase());
  }
}

function resetGame() {
  state = createInitialState();
  renderBoard();
  renderKeyboard();
  statusEl.textContent = "Type a 5-letter word to begin";
}

document.addEventListener("keydown", handleGlobalKeydown);
resetBtn.addEventListener("click", resetGame);

buildKeyboard();
renderBoard();
renderKeyboard();
statusEl.textContent = "Type a 5-letter word to begin";
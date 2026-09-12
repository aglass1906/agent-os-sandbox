"use strict";

// ---- Constants -------------------------------------------------------------
// Design Doc Section 5: statuses are mutually exclusive and drive input gating.
const STATUS_READY = "READY";
const STATUS_PLAYING = "PLAYING";
const STATUS_PAUSED = "PAUSED";
const STATUS_GAME_OVER = "GAME_OVER";

// Design Doc Section 2: logical canvas resolution; CSS scales responsively.
const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;

const START_LIVES = 3;
const START_WAVE = 1;

// Design Doc Section 3 (ship).
const SHIP_RADIUS = 12;
const SHIP_TURN_SPEED = 3.6;     // radians per second
const SHIP_ACCELERATION = 260;   // px per second squared
const SHIP_MAX_SPEED = 360;      // px per second
const SHIP_DRAG = 1.6;           // exponential drag coefficient per second
const SHIP_RESPAWN_INVULN = 3.0; // seconds of invulnerability after respawn

// Design Doc Section 4 (bullets).
const BULLET_SPEED = 520;        // px per second
const BULLET_LIFETIME = 1.1;     // seconds
const BULLET_COOLDOWN = 0.22;    // seconds between shots
const MAX_BULLETS = 6;

// Design Doc Section 6 (asteroids / waves).
const ASTEROID_SIZE_LARGE = 3;
const ASTEROID_SIZE_MEDIUM = 2;
const ASTEROID_SIZE_SMALL = 1;
const ASTEROID_RADIUS_LARGE = 46;
const ASTEROID_RADIUS_MEDIUM = 26;
const ASTEROID_RADIUS_SMALL = 14;
const ASTEROID_SPEED_MIN = 40;    // px per second
const ASTEROID_SPEED_MAX = 150;   // px per second
const ASTEROID_SPEED_SCALING = 8; // multiplier per extra wave beyond the first

const SCORE_LARGE = 20;
const SCORE_MEDIUM = 50;
const SCORE_SMALL = 100;

const SPAWN_SAFE_RADIUS = 150;    // margin around the ship for new asteroids
const MAX_PARTICLES = 260;

// Design Doc Section 8 (procedural audio feedback).
const EXPLOSION_NOISE_DURATION = 0.6;   // seconds — white noise buffer length
const EXPLOSION_VOLUME = 0.45;          // master gain for explosion playback
const EXPLOSION_CUTOFF_BASE = 400;      // Hz — low-pass cutoff for small asteroids
const EXPLOSION_CUTOFF_LARGE = 900;     // Hz — low-pass cutoff for large asteroids
const EXPLOSION_DECAY_BASE = 0.08;      // seconds — shortest exponential tail
const EXPLOSION_DECAY_LARGE = 0.32;     // seconds — longest exponential tail
const EXPLOSION_DURATION_BASE = 0.06;   // seconds — shortest envelope length
const EXPLOSION_DURATION_LARGE = 0.30;  // seconds — longest envelope length

// ---- Helpers ---------------------------------------------------------------

const TAU = Math.PI * 2;

function rand(min, max) {
  return min + Math.random() * (max - min);
}

function wrap(value, max) {
  return ((value % max) + max) % max;
}

function distanceSq(ax, ay, bx, by) {
  const dx = ax - bx;
  const dy = ay - by;
  return dx * dx + dy * dy;
}

// Deterministic pseudo-random for the static starfield so it does not change
// every frame and respects the canvas resolution.
function createStars() {
  const stars = [];
  let seed = 987654321;
  function next() {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  }
  const count = Math.round((CANVAS_WIDTH * CANVAS_HEIGHT) / 9000);
  for (let i = 0; i < count; i++) {
    stars.push({
      x: next() * CANVAS_WIDTH,
      y: next() * CANVAS_HEIGHT,
      r: 0.5 + next() * 1.3,
      a: 0.25 + next() * 0.5,
    });
  }
  return stars;
}

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

// ---- Audio ------------------------------------------------------------------
// Procedural explosion feedback (Design Doc Section 8): a shared AudioContext is
// created lazily on the first user gesture and every explosion is a filtered
// white-noise buffer shaped by an exponential decay envelope whose duration and
// cutoff scale with the destroyed asteroid's size.

let audioContext = null;
let audioMasterGain = null;
let noiseBuffer = null;

function audioSupported() {
  return !!(window.AudioContext || window.webkitAudioContext);
}

function createAudioContext() {
  try {
    const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextCtor) return null;
    const context = new AudioContextCtor();
    const masterGain = context.createGain();
    masterGain.gain.value = EXPLOSION_VOLUME;
    masterGain.connect(context.destination);
    audioContext = context;
    audioMasterGain = masterGain;
    return context;
  } catch (error) {
    audioContext = null;
    audioMasterGain = null;
    return null;
  }
}

function getAudioContext() {
  if (!audioContext && audioSupported()) {
    createAudioContext();
  }
  return audioContext;
}

// Autoplay-policy unlock: called from within a user gesture so the context is
// already running when the first explosion is scheduled.
function resumeAudio() {
  const context = getAudioContext();
  if (!context) return;
  if (context.state === "suspended" && typeof context.resume === "function") {
    const resumePromise = context.resume();
    if (resumePromise && typeof resumePromise.catch === "function") {
      resumePromise.catch(function () {});
    }
  }
}

// Release Web Audio resources on navigation so the page never leaks graph nodes.
function closeAudio() {
  resumeAudio();
  if (audioContext && typeof audioContext.close === "function") {
    try {
      audioContext.close();
    } catch (error) {
    }
  }
  audioContext = null;
  audioMasterGain = null;
  noiseBuffer = null;
}

// White-noise buffer is generated once and shared by every explosion so no
// per-shot buffer allocation is needed.
function getNoiseBuffer(context) {
  if (noiseBuffer) return noiseBuffer;
  const buffer = context.createBuffer(
    1,
    Math.max(1, Math.floor(context.sampleRate * EXPLOSION_NOISE_DURATION)),
    context.sampleRate
  );
  const channel = buffer.getChannelData(0);
  for (let i = 0; i < channel.length; i++) {
    channel[i] = Math.random() * 2 - 1;
  }
  noiseBuffer = buffer;
  return noiseBuffer;
}

// Normalized size drives every parameter: larger rocks boom lower and longer.
function explosionParameters(size) {
  const t = (size - ASTEROID_SIZE_SMALL) / (ASTEROID_SIZE_LARGE - ASTEROID_SIZE_SMALL);
  return {
    cutoff: EXPLOSION_CUTOFF_BASE + t * (EXPLOSION_CUTOFF_LARGE - EXPLOSION_CUTOFF_BASE),
    decay: EXPLOSION_DECAY_BASE + t * (EXPLOSION_DECAY_LARGE - EXPLOSION_DECAY_BASE),
    duration: EXPLOSION_DURATION_BASE + t * (EXPLOSION_DURATION_LARGE - EXPLOSION_DURATION_BASE),
  };
}

function playExplosionSound(size) {
  const context = getAudioContext();
  if (!context || !audioMasterGain || !audioSupported()) return;

  const now = context.currentTime;

  // Unlock a suspended context from within this user-gesture chain so the very
  // first explosion is audible instead of silently queued.
  if (context.state === "suspended" && typeof context.resume === "function") {
    const resumePromise = context.resume();
    if (resumePromise && typeof resumePromise.catch === "function") {
      resumePromise.catch(function () {});
    }
  }

  const source = context.createBufferSource();
  source.buffer = getNoiseBuffer(context);
  source.loop = true;

  // Low-pass filter turns broadband noise into a deep explosive rumble that
  // slides down as the blast dissipates.
  const filter = context.createBiquadFilter();
  filter.type = "lowpass";
  const params = explosionParameters(size);
  filter.frequency.setValueAtTime(params.cutoff, now);
  filter.frequency.exponentialRampToValueAtTime(80, now + params.duration);
  filter.Q.value = 0.8;

  // Exponential decay envelope: an instant attack snapping straight into a
  // size-scaled exponential tail so larger asteroids ring out longer.
  const envelope = context.createGain();
  envelope.gain.setValueAtTime(1.0, now);
  envelope.gain.exponentialRampToValueAtTime(0.001, now + params.decay);

  source.connect(filter);
  filter.connect(envelope);
  envelope.connect(audioMasterGain);

  source.start(now);
  source.stop(now + params.duration);
}

// ---- State -----------------------------------------------------------------
// Design Doc Section 5: every game property lives on this single object,
// initialized by createInitialState() so reset restores a clean slate.
function createShip() {
  return {
    x: CANVAS_WIDTH / 2,
    y: CANVAS_HEIGHT / 2,
    angle: -Math.PI / 2,
    vx: 0,
    vy: 0,
    thrusting: false,
    alive: true,
    invulnTimer: 0,
  };
}

// Design Doc Section 6: asteroid sizes map onto the same data shape.
function makeAsteroid(size, x, y, angle, speed) {
  const radiusBySize = {
    [ASTEROID_SIZE_LARGE]: ASTEROID_RADIUS_LARGE,
    [ASTEROID_SIZE_MEDIUM]: ASTEROID_RADIUS_MEDIUM,
    [ASTEROID_SIZE_SMALL]: ASTEROID_RADIUS_SMALL,
  };
  const vertices = [];
  const count = 9;
  for (let i = 0; i < count; i++) {
    vertices.push(rand(0.78, 1.25));
  }
  return {
    size,
    radius: radiusBySize[size],
    x,
    y,
    angle,
    speed,
    vertices,
  };
}

function createInitialState() {
  return {
    status: STATUS_READY,
    score: 0,
    lives: START_LIVES,
    wave: START_WAVE,
    ship: createShip(),
    bullets: [],
    asteroids: [],
    particles: [],
    stars: createStars(),
    keys: { left: false, right: false, thrust: false, fire: false },
    fireCooldown: 0,
  };
}

// ---- Game actions ----------------------------------------------------------

function announce(state, message) {
  if (!message) return;
  const announcementsEl = document.getElementById("announcements");
  if (announcementsEl) {
    announcementsEl.textContent = "";
    window.setTimeout(() => {
      if (announcementsEl) announcementsEl.textContent = message;
    }, 50);
  }
}

function setStatus(state, status) {
  state.status = status;
  renderStatus(state);
}

function renderStatus(state) {
  const statusEl = document.getElementById("status");
  if (!statusEl) return;
  switch (state.status) {
    case STATUS_READY:
      statusEl.textContent = "Press Start to pilot your ship";
      break;
    case STATUS_PLAYING:
      statusEl.textContent = "Wave " + state.wave + " — " + state.lives + " lives left";
      break;
    case STATUS_PAUSED:
      statusEl.textContent = "Paused — press Pause to resume";
      break;
    case STATUS_GAME_OVER:
      statusEl.textContent = "Game over — score " + state.score;
      break;
  }
}

function updateHUD(state) {
  const scoreEl = document.getElementById("score");
  const livesEl = document.getElementById("lives");
  const waveEl = document.getElementById("wave");
  if (scoreEl) scoreEl.textContent = String(state.score);
  if (livesEl) livesEl.textContent = String(state.lives);
  if (waveEl) waveEl.textContent = String(state.wave);
}

// Design Doc Section 4: fire a single bullet toward the ship's heading. Caps
// concurrent bullets so spamming cannot produce overwhelming firepower.
function fireBullet(state) {
  if (state.bullets.length >= MAX_BULLETS) return;
  const ship = state.ship;
  state.bullets.push({
    x: ship.x + Math.cos(ship.angle) * SHIP_RADIUS,
    y: ship.y + Math.sin(ship.angle) * SHIP_RADIUS,
    vx: Math.cos(ship.angle) * BULLET_SPEED,
    vy: Math.sin(ship.angle) * BULLET_SPEED,
    age: 0,
  });
  state.fireCooldown = BULLET_COOLDOWN;
}

// Design Doc Section 6: spawn a wave of asteroids, keeping large rocks clear of
// the ship's immediate area so a fresh wave is never a cheap kill.
function spawnWave(state) {
  const count = Math.min(3 + state.wave, 11);
  const clearance = SPAWN_SAFE_RADIUS
    + (ASTEROID_RADIUS_LARGE * state.wave) / 2;
  let attempts = 0;

  while (state.asteroids.length < count && attempts < 400) {
    attempts += 1;
    const x = rand(0, CANVAS_WIDTH);
    const y = rand(0, CANVAS_HEIGHT);
    const ship = state.ship;
    if (
      x > ship.x - clearance &&
      x < ship.x + clearance &&
      y > ship.y - clearance &&
      y < ship.y + clearance
    ) {
      continue;
    }
    const speed = rand(
      ASTEROID_SPEED_MIN,
      ASTEROID_SPEED_MAX +
        (state.wave - 1) * ASTEROID_SPEED_SCALING
    );
    state.asteroids.push(
      makeAsteroid(ASTEROID_SIZE_LARGE, x, y, rand(0, TAU), speed)
    );
  }
}

// Design Doc Section 6: large/medium asteroids split in two on destruction.
function splitAsteroid(state, asteroid) {
  const newSize = asteroid.size - 1;
  const speedBoost = 30;
  for (let i = 0; i < 2; i++) {
    const angle = rand(0, TAU);
    state.asteroids.push(
      makeAsteroid(
        newSize,
        asteroid.x,
        asteroid.y,
        angle,
        asteroid.speed * 1.15 + speedBoost
      )
    );
  }
}

// Design Doc Section 7: score value depends on the destroyed rock's size.
function scoreValue(size) {
  switch (size) {
    case ASTEROID_SIZE_LARGE:
      return SCORE_LARGE;
    case ASTEROID_SIZE_MEDIUM:
      return SCORE_MEDIUM;
    default:
      return SCORE_SMALL;
  }
}

function spawnParticles(state, x, y, color, count) {
  if (prefersReducedMotion()) return;
  const budget = MAX_PARTICLES - state.particles.length;
  const n = Math.min(count, budget);
  for (let i = 0; i < n; i++) {
    const angle = rand(0, TAU);
    const speed = rand(30, 220);
    state.particles.push({
      x,
      y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: rand(0.3, 0.9),
      maxLife: 0.9,
      color,
      size: rand(1.5, 3.5),
    });
  }
}

function destroyAsteroid(state, asteroid) {
  const idx = state.asteroids.indexOf(asteroid);
  if (idx !== -1) state.asteroids.splice(idx, 1);

  state.score += scoreValue(asteroid.size);
  playExplosionSound(asteroid.size);
  spawnParticles(
    state,
    asteroid.x,
    asteroid.y,
    asteroid.size === ASTEROID_SIZE_SMALL ? "#00ffa3" : "#ff9c3b",
    asteroid.size === ASTEROID_SIZE_SMALL ? 10 : 18
  );

  if (asteroid.size > ASTEROID_SIZE_SMALL) {
    splitAsteroid(state, asteroid);
  }
}

// Design Doc Section 7: a ship hit costs one life; the ship respawns in the
// center with temporary invulnerability, or the game ends at zero lives.
function damageShip(state) {
  state.lives -= 1;
  updateHUD(state);
  playExplosionSound(ASTEROID_SIZE_LARGE);
  spawnParticles(state, state.ship.x, state.ship.y, "#ff2e93", 40);
  if (state.lives <= 0) {
    state.ship.alive = false;
    setStatus(state, STATUS_GAME_OVER);
    announce(state, "Game over. Final score " + state.score + ".");
    return;
  }

  const ship = createShip();
  ship.invulnTimer = SHIP_RESPAWN_INVULN;
  state.ship = ship;
  announce(state, "Shields down. " + state.lives + " lives left.");
}

// Design Doc Section 5: full reset returns the object to its initial defaults.
function startNewGame(state) {
  resumeAudio();
  const fresh = createInitialState();
  fresh.status = STATUS_PLAYING;
  Object.assign(state, fresh, { keys: state.keys });
  spawnWave(state);
  updateHUD(state);
  setStatus(state, STATUS_PLAYING);
  announce(state, "Game started. Wave 1.");
}

function togglePause(state) {
  if (state.status === STATUS_PLAYING) {
    setStatus(state, STATUS_PAUSED);
    announce(state, "Game paused.");
  } else if (state.status === STATUS_PAUSED) {
    setStatus(state, STATUS_PLAYING);
    announce(state, "Game resumed.");
  }
}

// ---- Simulation ------------------------------------------------------------

function update(state, dt) {
  if (state.status !== STATUS_PLAYING) return;

  const ship = state.ship;

  // Ship rotation and thrust (Design Doc Section 3).
  if (ship.alive) {
    if (state.keys.left) ship.angle -= SHIP_TURN_SPEED * dt;
    if (state.keys.right) ship.angle += SHIP_TURN_SPEED * dt;
    ship.thrusting = state.keys.thrust;
    if (ship.thrusting) {
      ship.vx += Math.cos(ship.angle) * SHIP_ACCELERATION * dt;
      ship.vy += Math.sin(ship.angle) * SHIP_ACCELERATION * dt;
    }

    // Exponential drag so velocity never spins out of control.
    const drag = Math.exp(-SHIP_DRAG * dt);
    ship.vx *= drag;
    ship.vy *= drag;

    const speed = Math.hypot(ship.vx, ship.vy);
    if (speed > SHIP_MAX_SPEED) {
      const scale = SHIP_MAX_SPEED / speed;
      ship.vx *= scale;
      ship.vy *= scale;
    }

    ship.x = wrap(ship.x + ship.vx * dt, CANVAS_WIDTH);
    ship.y = wrap(ship.y + ship.vy * dt, CANVAS_HEIGHT);

    if (ship.invulnTimer > 0) ship.invulnTimer -= dt;

    if (state.keys.fire && state.fireCooldown <= 0) fireBullet(state);
    if (state.fireCooldown > 0) state.fireCooldown -= dt;
  }

  // Bullets (Design Doc Section 4).
  state.bullets = state.bullets.filter((bullet) => {
    bullet.x = wrap(bullet.x + bullet.vx * dt, CANVAS_WIDTH);
    bullet.y = wrap(bullet.y + bullet.vy * dt, CANVAS_HEIGHT);
    bullet.age += dt;
    return bullet.age < BULLET_LIFETIME;
  });

  // Asteroids (Design Doc Section 6).
  for (const asteroid of state.asteroids) {
    asteroid.x = wrap(asteroid.x + Math.cos(asteroid.angle) * asteroid.speed * dt, CANVAS_WIDTH);
    asteroid.y = wrap(asteroid.y + Math.sin(asteroid.angle) * asteroid.speed * dt, CANVAS_HEIGHT);
  }

  // Collisions (Design Doc Section 7).
  if (ship.alive) {
    // Bullet vs asteroid. A while loop over bullets is used so that after a
    // bullet is removed the next bullet shifts into its index and is still
    // examined; asteroids are re-found by search, never by stale index.
    let b = state.bullets.length - 1;
    while (b >= 0) {
      const bullet = state.bullets[b];
      if (!bullet) {
        b -= 1;
        continue;
      }
      const hitIndex = state.asteroids.findIndex((asteroid) => {
        const hitRadius = asteroid.radius + 3;
        return (
          distanceSq(bullet.x, bullet.y, asteroid.x, asteroid.y) <
          hitRadius * hitRadius
        );
      });

      if (hitIndex === -1) {
        b -= 1;
        continue;
      }

      state.bullets.splice(b, 1);
      destroyAsteroid(state, state.asteroids[hitIndex]);
      updateHUD(state);
    }

    // Ship vs asteroid.
    for (let i = state.asteroids.length - 1; i >= 0; i--) {
      const asteroid = state.asteroids[i];
      if (ship.invulnTimer > 0) break;
      const shipHitRadius = SHIP_RADIUS + asteroid.radius;
      if (distanceSq(ship.x, ship.y, asteroid.x, asteroid.y) < shipHitRadius * shipHitRadius) {
        damageShip(state);
        if (state.status !== STATUS_PLAYING) return;
        break;
      }
    }
  }

  // Particles (Design Doc Section 8).
  state.particles = state.particles.filter((particle) => {
    particle.x = wrap(particle.x + particle.vx * dt, CANVAS_WIDTH);
    particle.y = wrap(particle.y + particle.vy * dt, CANVAS_HEIGHT);
    particle.vx *= 0.96;
    particle.vy *= 0.96;
    particle.life -= dt;
    return particle.life > 0;
  });

  // Wave cleared -> advance to the next wave (Design Doc Section 6).
  if (state.asteroids.length === 0) {
    state.wave += 1;
    spawnWave(state);
    updateHUD(state);
    setStatus(state, STATUS_PLAYING);
    announce(state, "Wave " + state.wave + " incoming.");
  }
}

// ---- Rendering -------------------------------------------------------------

function drawWrapped(ctx, drawEntity) {
  for (const ox of [0, -CANVAS_WIDTH, CANVAS_WIDTH]) {
    for (const oy of [0, -CANVAS_HEIGHT, CANVAS_HEIGHT]) {
      drawEntity(ox, oy);
    }
  }
}

function drawShip(ctx, state) {
  const ship = state.ship;
  if (!ship.alive) return;

  // Blink while invulnerable so the state is visually and predictably readable.
  if (ship.invulnTimer > 0 && Math.floor(ship.invulnTimer * 8) % 2 === 0) return;

  ctx.save();
  ctx.translate(ship.x, ship.y);
  ctx.rotate(ship.angle);

  if (ship.thrusting) {
    ctx.beginPath();
    ctx.moveTo(-SHIP_RADIUS * 0.7, -SHIP_RADIUS * 0.4);
    ctx.lineTo(-SHIP_RADIUS - rand(4, 10), 0);
    ctx.lineTo(-SHIP_RADIUS * 0.7, SHIP_RADIUS * 0.4);
    ctx.closePath();
    ctx.fillStyle = "#ff9c3b";
    ctx.shadowColor = "#ff9c3b";
    ctx.shadowBlur = 12;
    ctx.fill();
  }

  ctx.beginPath();
  ctx.moveTo(SHIP_RADIUS, 0);
  ctx.lineTo(-SHIP_RADIUS * 0.7, -SHIP_RADIUS * 0.7);
  ctx.lineTo(-SHIP_RADIUS * 0.35, 0);
  ctx.lineTo(-SHIP_RADIUS * 0.7, SHIP_RADIUS * 0.7);
  ctx.closePath();
  ctx.strokeStyle = "#00f0ff";
  ctx.lineWidth = 2;
  ctx.shadowColor = "#00f0ff";
  ctx.shadowBlur = 14;
  ctx.stroke();
  ctx.restore();
}

function drawAsteroids(ctx, state) {
  for (const asteroid of state.asteroids) {
    drawWrapped(ctx, (ox, oy) => {
      ctx.beginPath();
      const count = asteroid.vertices.length;
      for (let i = 0; i < count; i++) {
        const a = (i / count) * TAU;
        const r = asteroid.radius * asteroid.vertices[i];
        const px = asteroid.x + ox + Math.cos(a) * r;
        const py = asteroid.y + oy + Math.sin(a) * r;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.strokeStyle = "#ff9c3b";
      ctx.lineWidth = 2;
      ctx.shadowColor = "#ff9c3b";
      ctx.shadowBlur = 12;
      ctx.stroke();
    });
  }
}

function drawBullets(ctx, state) {
  ctx.fillStyle = "#00ffa3";
  ctx.shadowColor = "#00ffa3";
  ctx.shadowBlur = 8;
  for (const bullet of state.bullets) {
    drawWrapped(ctx, (ox, oy) => {
      ctx.fillRect(bullet.x + ox - 2, bullet.y + oy - 2, 4, 4);
    });
  }
  ctx.shadowBlur = 0;
}

function drawParticles(ctx, state) {
  ctx.save();
  for (const particle of state.particles) {
    const alpha = Math.max(particle.life / particle.maxLife, 0);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = particle.color;
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.size, 0, TAU);
    ctx.fill();
  }
  ctx.restore();
}

function drawStarfield(ctx, state) {
  ctx.save();
  for (const star of state.stars) {
    ctx.globalAlpha = star.a;
    ctx.fillStyle = "#9db8e8";
    ctx.fillRect(star.x, star.y, star.r, star.r);
  }
  ctx.restore();
}

function renderFrame(ctx, state) {
  ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  drawStarfield(ctx, state);
  drawParticles(ctx, state);
  drawBullets(ctx, state);
  drawAsteroids(ctx, state);
  drawShip(ctx, state);

  if (state.status === STATUS_PAUSED) {
    drawOverlay(ctx, "Paused", "Press Pause to resume");
  } else if (state.status === STATUS_GAME_OVER) {
    drawOverlay(ctx, "Game Over", "Score " + state.score + " — press Start for a new game");
  } else if (state.status === STATUS_READY) {
    drawOverlay(ctx, "Asteroids Redux", "Press Start to pilot your ship");
  }
}

function drawOverlay(ctx, title, subtitle) {
  ctx.save();
  ctx.font = "600 44px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#00f0ff";
  ctx.shadowColor = "#00f0ff";
  ctx.shadowBlur = 24;
  ctx.fillText(title, CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2 - 40);
  ctx.font = "600 18px system-ui, sans-serif";
  ctx.fillStyle = "#e4f4ff";
  ctx.shadowColor = "transparent";
  ctx.shadowBlur = 0;
  ctx.fillText(subtitle, CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2 + 8);
  ctx.restore();
}

// ---- DOM wiring (browser only) ---------------------------------------------

const isBrowser =
  typeof document !== "undefined" && typeof window !== "undefined";

if (isBrowser) {
  const canvas = document.getElementById("board");
  const ctx = canvas.getContext("2d");
  canvas.width = CANVAS_WIDTH;
  canvas.height = CANVAS_HEIGHT;

  const state = createInitialState();

  const startBtn = document.getElementById("startBtn");
  const pauseBtn = document.getElementById("pauseBtn");
  const touchControls = document.getElementById("touchControls");

  startBtn.addEventListener("click", () => {
    startNewGame(state);
  });

  pauseBtn.addEventListener("click", () => {
    togglePause(state);
  });

  // Keyboard input (Design Doc Section 3).
  const KEY_LEFT = ["ArrowLeft", "KeyA"];
  const KEY_RIGHT = ["ArrowRight", "KeyD"];
  const KEY_THRUST = ["ArrowUp", "KeyW"];

  document.addEventListener("keydown", (event) => {
    const code = event.code;
    if (KEY_LEFT.includes(code)) {
      state.keys.left = true;
      event.preventDefault();
    } else if (KEY_RIGHT.includes(code)) {
      state.keys.right = true;
      event.preventDefault();
    } else if (KEY_THRUST.includes(code)) {
      state.keys.thrust = true;
      event.preventDefault();
    } else if (code === "Space") {
      state.keys.fire = true;
      if (state.status === STATUS_READY || state.status === STATUS_GAME_OVER) {
        startNewGame(state);
      }
      event.preventDefault();
    } else if (code === "KeyP") {
      togglePause(state);
      event.preventDefault();
    } else if (code === "Enter" && state.status === STATUS_READY) {
      startNewGame(state);
      event.preventDefault();
    }
  });

  document.addEventListener("keyup", (event) => {
    const code = event.code;
    if (KEY_LEFT.includes(code)) state.keys.left = false;
    else if (KEY_RIGHT.includes(code)) state.keys.right = false;
    else if (KEY_THRUST.includes(code)) state.keys.thrust = false;
    else if (code === "Space") state.keys.fire = false;
  });

  // Touch controls (Design Doc Section 3): pointer buttons feed the same key
  // flags, so keyboard and touch stay on one code path.
  function bindTouch(id, flag) {
    const button = document.getElementById(id);
    if (!button) return;
    const press = (event) => {
      event.preventDefault();
      state.keys[flag] = true;
    };
    const release = (event) => {
      event.preventDefault();
      state.keys[flag] = false;
    };
    button.addEventListener("pointerdown", press);
    button.addEventListener("pointerup", release);
    button.addEventListener("pointerleave", release);
    button.addEventListener("pointercancel", release);
  }

  bindTouch("touchLeft", "left");
  bindTouch("touchRight", "right");
  bindTouch("touchThrust", "thrust");
  bindTouch("touchFire", "fire");

  // Show touch controls on coarse pointers and the first real touch event.
  if (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(pointer: coarse)").matches
  ) {
    touchControls.hidden = false;
  }
  window.addEventListener("touchstart", () => {
    touchControls.hidden = false;
  }, { passive: true });

  // Auto-pause when the tab is hidden so the simulation never runs away.
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.status === STATUS_PLAYING) {
      setStatus(state, STATUS_PAUSED);
    }
  });

  // Release Web Audio graph nodes when the page is navigated away from.
  window.addEventListener("pagehide", closeAudio);

  // Main loop.
  let lastTime = performance.now();
  function frame(timestamp) {
    const dt = Math.min((timestamp - lastTime) / 1000, 0.05);
    lastTime = timestamp;

    if (state.status !== STATUS_PAUSED) {
      update(state, dt);
    }
    renderFrame(ctx, state);
    updateHUD(state);

    window.requestAnimationFrame(frame);
  }

  renderFrame(ctx, state);
  updateHUD(state);
  renderStatus(state);
  window.requestAnimationFrame(frame);
}
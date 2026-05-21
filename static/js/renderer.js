// ── Dungeon Defender – Canvas Renderer ─────────────────────────────────────
// Receives game state JSON from the server and renders every frame.

const W = 350, H = 700;
let socket = null;
let lastState = null;
let keysPressed = {};

// ── Canvas setup ────────────────────────────────────────────────────────────
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
canvas.width = W;
canvas.height = H;

// ── WebSocket ───────────────────────────────────────────────────────────────
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${proto}://${location.host}/ws`);

  socket.onmessage = (e) => {
    lastState = JSON.parse(e.data);
    renderFrame(lastState);
  };

  socket.onclose = () => {
    setTimeout(connect, 1000);
  };

  socket.onerror = () => socket.close();
}

function send(msg) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(msg));
  }
}

// ── Input ────────────────────────────────────────────────────────────────────
const KEY_MAP = {
  ArrowLeft: "left", ArrowRight: "right",
  ArrowUp: "up",    ArrowDown: "down",
  " ": "space",     Space: "space",
};

document.addEventListener("keydown", (e) => {
  const k = KEY_MAP[e.key] || KEY_MAP[e.code];
  if (!k) return;
  e.preventDefault();
  if (keysPressed[k]) return;
  keysPressed[k] = true;

  const st = lastState;
  if (st && st.phase === "title" && e.code === "Space") {
    send({ type: "start" });
    return;
  }
  if (st && st.phase === "gameover") {
    if (e.code === "KeyR" || e.code === "Space") { send({ type: "restart" }); return; }
  }
  if (e.code === "KeyQ") { send({ type: "ultimate" }); return; }

  send({ type: "keydown", key: k });
});

document.addEventListener("keyup", (e) => {
  const k = KEY_MAP[e.key] || KEY_MAP[e.code];
  if (!k) return;
  keysPressed[k] = false;
  send({ type: "keyup", key: k });
});

// Mobile buttons
document.querySelectorAll("[data-key]").forEach(btn => {
  const key = btn.dataset.key;
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    if (!keysPressed[key]) {
      keysPressed[key] = true;
      if (key === "ultimate") { send({ type: "ultimate" }); return; }
      if (key === "start") { send({ type: "start" }); return; }
      if (key === "restart") { send({ type: "restart" }); return; }
      send({ type: "keydown", key });
    }
  });
  btn.addEventListener("pointerup",   (e) => { e.preventDefault(); keysPressed[key] = false; send({ type: "keyup", key }); });
  btn.addEventListener("pointerleave",(e) => { e.preventDefault(); keysPressed[key] = false; send({ type: "keyup", key }); });
});

// ── Helpers ──────────────────────────────────────────────────────────────────
function rgb(c) { return `rgb(${c[0]},${c[1]},${c[2]})`; }

function fillCircle(x, y, r, color) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = color; ctx.fill();
}

function strokeCircle(x, y, r, color, lw = 2) {
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.stroke();
}

function fillRect(x, y, w, h, color) {
  ctx.fillStyle = color; ctx.fillRect(x, y, w, h);
}

function drawHpBar(x, y, w, hp, maxHp) {
  fillRect(x, y, w, 4, "#f00");
  fillRect(x, y, w * (hp / maxHp), 4, "#0f0");
}

// ── Entity renderers ─────────────────────────────────────────────────────────

function drawPlayer(p) {
  // Body
  ctx.fillStyle = "#6496ff";
  ctx.fillRect(p.x, p.y, p.sx, p.sy);
  // Helmet
  ctx.fillStyle = "#99aaff";
  ctx.fillRect(p.x + 5, p.y, p.sx - 10, 20);
  // Eye slit
  ctx.fillStyle = "#ffff00";
  ctx.fillRect(p.x + 8, p.y + 7, p.sx - 16, 5);
  // Cape
  ctx.fillStyle = "#3355cc";
  ctx.fillRect(p.x - 3, p.y + 20, p.sx + 6, p.sy - 25);
  // Cross on chest
  ctx.fillStyle = "#ffd700";
  ctx.fillRect(p.x + p.sx / 2 - 2, p.y + 25, 4, 14);
  ctx.fillRect(p.x + p.sx / 2 - 7, p.y + 30, 14, 4);
}

function drawGoblin(e) {
  const c = "#64c864";
  // body
  ctx.fillStyle = c;
  ctx.beginPath(); ctx.ellipse(e.x + 20, e.y + 24, 15, 14, 0, 0, Math.PI * 2); ctx.fill();
  // head
  fillCircle(e.x + 20, e.y + 8, 6, c);
  // eyes
  fillCircle(e.x + 16, e.y + 6, 2, "#000");
  fillCircle(e.x + 24, e.y + 6, 2, "#000");
  // mouth
  ctx.strokeStyle = "#000"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(e.x + 18, e.y + 10); ctx.lineTo(e.x + 22, e.y + 10); ctx.stroke();
}

function drawBat(e) {
  const c = "#323232";
  fillCircle(e.x + 20, e.y + 20, 5, c);
  ctx.fillStyle = c;
  ctx.beginPath(); ctx.moveTo(e.x + 15, e.y + 18); ctx.lineTo(e.x + 5, e.y + 10); ctx.lineTo(e.x + 8, e.y + 25); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(e.x + 25, e.y + 18); ctx.lineTo(e.x + 35, e.y + 10); ctx.lineTo(e.x + 32, e.y + 25); ctx.closePath(); ctx.fill();
  fillCircle(e.x + 20, e.y + 18, 2, "#f00");
}

function drawGhost(e) {
  const c = "#dcdcdc";
  ctx.fillStyle = c;
  ctx.beginPath(); ctx.ellipse(e.x + 20, e.y + 24, 15, 14, 0, 0, Math.PI * 2); ctx.fill();
  fillCircle(e.x + 20, e.y + 8, 8, c);
  fillCircle(e.x + 16, e.y + 6, 3, "#3296ff");
  fillCircle(e.x + 24, e.y + 6, 3, "#3296ff");
  ctx.strokeStyle = "#3296ff"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(e.x + 18, e.y + 12); ctx.lineTo(e.x + 22, e.y + 12); ctx.stroke();
}

function drawOrcArcher(e) {
  const c = "#966432";
  fillRect(e.x + 10, e.y + 15, 20, 18, c);
  fillCircle(e.x + 20, e.y + 10, 7, c);
  ctx.strokeStyle = "#644620"; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(e.x + 8, e.y + 18); ctx.lineTo(e.x + 2, e.y + 12); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(e.x + 32, e.y + 18); ctx.lineTo(e.x + 38, e.y + 12); ctx.stroke();
  fillCircle(e.x + 17, e.y + 8, 2, "#ff6400");
  fillCircle(e.x + 23, e.y + 8, 2, "#ff6400");
}

function drawSkeleton(e) {
  const c = "#c8c8c8";
  fillRect(e.x + 10, e.y + 18, 30, 25, c);
  fillCircle(e.x + 25, e.y + 12, 10, c);
  fillCircle(e.x + 21, e.y + 10, 3, "#000");
  fillCircle(e.x + 29, e.y + 10, 3, "#000");
  for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = "#000"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(e.x + 15 + i * 5, e.y + 18); ctx.lineTo(e.x + 15 + i * 5, e.y + 20); ctx.stroke();
  }
  ctx.strokeStyle = c; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(e.x + 10, e.y + 22); ctx.lineTo(e.x + 2, e.y + 22); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(e.x + 40, e.y + 22); ctx.lineTo(e.x + 48, e.y + 22); ctx.stroke();
  ctx.strokeStyle = "#969696"; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(e.x + 48, e.y + 22); ctx.lineTo(e.x + 50, e.y + 10); ctx.stroke();
}

function drawEnemy(e) {
  switch (e.type) {
    case "goblin":     drawGoblin(e);     break;
    case "bat":        drawBat(e);        break;
    case "ghost":      drawGhost(e);      break;
    case "orc_archer": drawOrcArcher(e);  break;
    case "skeleton":   drawSkeleton(e);   break;
  }
  if (e.max_hp > 1) drawHpBar(e.x, e.y - 8, e.sx, e.hp, e.max_hp);
}

function drawBoss(b) {
  // dark aura rings
  for (let ring = 3; ring >= 1; ring--) {
    const r = 60 + ring * 10 + Math.sin(b.dark_aura) * 5;
    strokeCircle(b.x + b.sx / 2, b.y + b.sy / 2, r, `rgba(80,0,80,0.4)`, 2);
  }
  // body
  fillRect(b.x + 20, b.y + 30, 80, 60, "#500064");
  ctx.fillStyle = "#1e0032";
  ctx.beginPath(); ctx.ellipse(b.x + 60, b.y + 30, 45, 20, 0, 0, Math.PI * 2); ctx.fill();
  // horns
  ctx.fillStyle = "#780096";
  fillCircle(b.x + 25, b.y + 35, 15, "#640078");
  fillCircle(b.x + 95, b.y + 35, 15, "#640078");
  // crown/cap
  ctx.beginPath();
  ctx.moveTo(b.x + 35, b.y + 15); ctx.lineTo(b.x + 65, b.y + 15);
  ctx.lineTo(b.x + 70, b.y + 30); ctx.lineTo(b.x + 30, b.y + 30);
  ctx.closePath(); ctx.fillStyle = "#780096"; ctx.fill();
  // eyes
  const glow = Math.floor(180 + Math.sin(b.dark_aura * 4) * 60);
  fillCircle(b.x + 42, b.y + 22, 8, "#ff0000");
  fillCircle(b.x + 58, b.y + 22, 8, "#ff0000");
  fillCircle(b.x + 42, b.y + 22, 5, `rgb(${glow},0,0)`);
  fillCircle(b.x + 58, b.y + 22, 5, `rgb(${glow},0,0)`);

  // sword
  const swordX = b.x + b.sx + 15;
  const swordY = b.y + b.sy / 2;
  const angle = b.sword_angle * 10 * Math.PI / 180;
  const ex = swordX + Math.cos(angle) * 40;
  const ey = swordY + Math.sin(angle) * 40;
  ctx.strokeStyle = "#c8c8c8"; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(swordX, swordY); ctx.lineTo(ex, ey); ctx.stroke();
  fillCircle(ex, ey, 5, "#ff3232");

  // phase 2 red rings
  if (b.phase === 2) {
    for (let i = 0; i < 2; i++) {
      const r = 75 + Math.sin(b.dark_aura * 6 + i) * 15;
      strokeCircle(b.x + b.sx / 2, b.y + b.sy / 2, r, "#ff0000", 2);
    }
  }

  // HP bar
  const bw = b.sx + 30;
  fillRect(b.x - 10, b.y - 35, bw, 20, "#320000");
  fillRect(b.x - 5,  b.y - 33, bw - 10, 16, "#640000");
  const ratio = b.hp / b.max_hp;
  const barColor = ratio > 0.5 ? "#00ff00" : ratio > 0.25 ? "#ffc800" : "#ff0000";
  fillRect(b.x - 5, b.y - 33, (bw - 10) * ratio, 16, barColor);

  ctx.fillStyle = "#fff";
  ctx.font = "bold 12px Arial";
  ctx.fillText(`DARK LORD: ${b.hp}/${b.max_hp}`, b.x - 10, b.y - 50);
}

function drawBullet(b) {
  fillRect(b.x, b.y, b.sx, b.sy, rgb(b.color));
}

function drawWave(w) {
  if (w.radius < w.max_radius) {
    strokeCircle(w.x, w.y, w.radius, rgb(w.color), 3);
  }
}

// ── HUD ──────────────────────────────────────────────────────────────────────
function drawHUD(s) {
  const p = s.player;

  ctx.font = "bold 16px Arial";
  ctx.fillStyle = "#ffc864";
  ctx.fillText(`Score: ${s.score} | Kills: ${s.kill}`, 10, 22);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(`Time: ${s.elapsed}s`, W - 110, 22);

  // HP hearts
  for (let i = 0; i < p.hp; i++) {
    fillCircle(15 + i * 25, 40, 8, "#ff0000");
    ctx.fillStyle = "#ff0000";
    ctx.beginPath();
    ctx.moveTo(15 + i * 25 - 5, 38); ctx.lineTo(15 + i * 25 + 5, 38); ctx.lineTo(15 + i * 25, 32);
    ctx.closePath(); ctx.fill();
  }

  // Ultimate gauge
  const gx = W - 150, gy = 35, gw = 140, gh = 16;
  fillRect(gx, gy, gw, gh, "#502864");
  const fillW = gw * (p.ultimate_charge / p.ultimate_max);
  fillRect(gx, gy, fillW, gh, p.ultimate_charge >= p.ultimate_max ? "#c8ff00" : "#96c8ff");
  ctx.font = "bold 11px Arial";
  ctx.fillStyle = "#fff";
  ctx.fillText("HOLY LIGHT [Q]", gx - 5, gy - 5);

  // Power-up timers
  let sy2 = 60;
  if (p.rapid_fire) {
    ctx.fillStyle = "#ffc800";
    ctx.font = "bold 11px Arial";
    ctx.fillText(`RAPID FIRE: ${Math.ceil(p.rapid_fire_timer / 60)}s`, 10, sy2);
    sy2 += 18;
  }
  if (p.shield) {
    ctx.fillStyle = "#64c8ff";
    ctx.fillText(`HOLY SHIELD: ${Math.ceil(p.shield_timer / 60)}s`, 10, sy2);
  }
}

// ── Screens ───────────────────────────────────────────────────────────────────
function drawTitle(s) {
  ctx.fillStyle = "#1a0a1e"; ctx.fillRect(0, 0, W, H);
  drawBgParticles(s.bg_particles);

  ctx.textAlign = "center";
  ctx.font = "bold 44px Arial";
  ctx.fillStyle = "#c864ff";
  ctx.fillText("DUNGEON", W / 2, 200);
  ctx.fillText("DEFENDER", W / 2, 250);

  ctx.font = "20px Arial";
  ctx.fillStyle = "#ffc864";
  ctx.fillText("PRESS SPACE TO START", W / 2, 330);

  ctx.fillStyle = "#c8c8c8";
  ctx.font = "18px Arial";
  ctx.fillText("← → : Move", W / 2, 390);
  ctx.fillText("↑ ↓ : Move Up/Down", W / 2, 418);
  ctx.fillText("SPACE : Holy Arrow", W / 2, 446);
  ctx.fillText("Q : Holy Light (Ultimate)", W / 2, 474);
  ctx.textAlign = "left";
}

function drawGameOver(s) {
  ctx.fillStyle = "#1a0a1e"; ctx.fillRect(0, 0, W, H);
  drawBgParticles(s.bg_particles);

  ctx.textAlign = "center";
  if (s.victory) {
    ctx.font = "bold 54px Arial";
    ctx.fillStyle = "#64ff64";
    ctx.fillText("VICTORY!", W / 2, 220);
    ctx.font = "24px Arial";
    ctx.fillStyle = "#c8ffc8";
    ctx.fillText("You saved the kingdom!", W / 2, 270);
  } else {
    ctx.font = "bold 48px Arial";
    ctx.fillStyle = "#ff6464";
    ctx.fillText("DEFEATED", W / 2, 220);
    ctx.font = "24px Arial";
    ctx.fillStyle = "#ff9696";
    ctx.fillText("by the Dark Lord...", W / 2, 270);
  }

  ctx.font = "24px Arial";
  ctx.fillStyle = "#ffc864";
  ctx.fillText(`Final Score: ${s.score}`, W / 2, 340);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(`Enemies Defeated: ${s.kill}`, W / 2, 380);
  ctx.fillText(`Survival Time: ${s.elapsed}s`, W / 2, 420);

  ctx.font = "20px Arial";
  ctx.fillStyle = "#64ff64";
  ctx.fillText("Press [SPACE] to Restart", W / 2, 500);
  ctx.textAlign = "left";
}

function drawBgParticles(bps) {
  for (const bp of bps) {
    const alpha = (bp.lifetime / bp.max_lifetime) * 0.6;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = "#963264";
    ctx.beginPath(); ctx.arc(bp.x, bp.y, bp.size, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = 1;
  }
}

// ── Main render ───────────────────────────────────────────────────────────────
function renderFrame(s) {
  if (s.phase === "title")    { drawTitle(s); return; }
  if (s.phase === "gameover") { drawGameOver(s); return; }

  // background
  ctx.fillStyle = "#140a1e"; ctx.fillRect(0, 0, W, H);
  drawBgParticles(s.bg_particles);

  // player
  drawPlayer(s.player);

  // shield ring
  if (s.player.shield) {
    strokeCircle(s.player.x + s.player.sx / 2, s.player.y + s.player.sy / 2, 50, "#64c8ff", 3);
  }
  // ultimate ring
  if (s.player.ultimate_active) {
    strokeCircle(s.player.x + s.player.sx / 2, s.player.y + s.player.sy / 2, 70, "#ffff64", 2);
  }

  // player bullets
  for (const b of s.bullets) drawBullet(b);

  // enemies
  for (const e of s.enemies) drawEnemy(e);

  // enemy bullets
  for (const b of s.enemy_bullets) drawBullet(b);

  // power-ups
  for (const pu of s.powerups) {
    ctx.fillStyle = pu.type === "rapid" ? "#ffc800" : "#64c8ff";
    ctx.fillRect(pu.x, pu.y, pu.sx, pu.sy);
    ctx.fillStyle = "#000";
    ctx.font = "bold 10px Arial";
    ctx.fillText(pu.type === "rapid" ? "R" : "S", pu.x + 6, pu.y + 14);
  }

  // boss bullets
  for (const b of s.boss_bullets) {
    if (b.type === "wave") drawWave(b);
    else drawBullet(b);
  }

  // boss
  if (s.boss) drawBoss(s.boss);

  // particles
  for (const pt of s.particles) {
    ctx.globalAlpha = Math.max(0, pt.lifetime / 30);
    fillCircle(pt.x, pt.y, pt.size, rgb(pt.color));
    ctx.globalAlpha = 1;
  }

  drawHUD(s);
}

// ── Boot ─────────────────────────────────────────────────────────────────────
connect();

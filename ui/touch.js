'use strict';
// =====================================================================
// ui/touch.js — controles de celular como no TCoM: joystick virtual à
// esquerda; à direita, atacar (segurar), pegar item e 4 magias da barra.
// Também: globos de vida e mana (D2), barra do alvo, avisos e tela de morte.
// =====================================================================
const Touch = {
  on: false, vec: [0, 0], atk: false,
  init() {
    this.on = matchMedia('(pointer: coarse)').matches || 'ontouchstart' in window && innerWidth < 1100;
    document.body.classList.toggle('touch', this.on);
    if (!this.on) return;
    // no celular os globos substituem a janela de status
    for (const id of ['status', 'minimap', 'journal']) Gumps.toggle(id, false);
    const ui = document.getElementById('ui');
    const pad = document.createElement('div'); pad.id = 'joy'; pad.innerHTML = '<i></i>'; ui.appendChild(pad);
    const knob = pad.querySelector('i'); let id = null, cx = 0, cy = 0;
    const R = 46;
    const move = (x, y) => { let dx = x - cx, dy = y - cy; const d = Math.hypot(dx, dy); if (d > R) { dx *= R / d; dy *= R / d; } knob.style.transform = `translate(${dx}px,${dy}px)`; this.vec = d > 8 ? [dx / R, dy / R] : [0, 0]; };
    pad.addEventListener('touchstart', e => { const t = e.changedTouches[0]; id = t.identifier; const r = pad.getBoundingClientRect(); cx = r.left + r.width / 2; cy = r.top + r.height / 2; move(t.clientX, t.clientY); e.preventDefault(); }, { passive: false });
    pad.addEventListener('touchmove', e => { for (const t of e.changedTouches) if (t.identifier === id) move(t.clientX, t.clientY); e.preventDefault(); }, { passive: false });
    const end = e => { for (const t of e.changedTouches) if (t.identifier === id) { id = null; this.vec = [0, 0]; knob.style.transform = ''; } };
    pad.addEventListener('touchend', end); pad.addEventListener('touchcancel', end);

    const acts = document.createElement('div'); acts.id = 'acts'; ui.appendChild(acts); this.acts = acts;
    this.render();
    // pinça para zoom
    const cv = Render.cv; let p0 = 0, z0 = 1;
    cv.addEventListener('touchstart', e => { if (e.touches.length === 2) { const [a, b] = e.touches; p0 = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY); z0 = Camera.zoom; } }, { passive: true });
    cv.addEventListener('touchmove', e => { if (e.touches.length === 2 && p0) { const [a, b] = e.touches; Game.setZoom(z0 * Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) / p0); } }, { passive: true });
    cv.addEventListener('touchend', e => { if (e.touches.length < 2) p0 = 0; if (e.changedTouches.length === 1 && !p0) this.tap(e.changedTouches[0]); }, { passive: true });
  },
  // toque rápido na tela: pega item, fala com jogador ou mira um monstro
  tap(t) {
    const it = Combat.labelAt(t.clientX, t.clientY);
    if (it) { Game.player.actor.moveTo(Game.map, it.x, it.y); Game.pickup = it; return; }
    const [wx, wy] = Camera.screenToWorld(t.clientX, t.clientY + 30 * Camera.zoom, Render.vw, Render.vh);
    const m = Combat.mobAt(wx, wy, 1.6); if (m) { Combat.engage(m); return; }
    const s = Game.pickSim && Game.pickSim(t.clientX, t.clientY); if (s && s.sim) Game.inspect(s.sim);
  },
  render() {
    if (!this.on) return;
    const spells = Magic.hotbar.slice(0, 4).map((id, i) => { const s = Magic.byId[id]; return s ? `<button class="sk s${i}" data-s="${id}">${Magic.name(s).split(' ').map(w => w[0]).join('').slice(0, 3)}</button>` : ''; }).join('');
    this.acts.innerHTML = `<button class="atk">⚔</button><button class="pick">✋</button>${spells}`;
    const atk = this.acts.querySelector('.atk');
    atk.addEventListener('touchstart', e => { this.atk = true; e.preventDefault(); }, { passive: false });
    atk.addEventListener('touchend', () => { this.atk = false; Combat.attacking = false; });
    this.acts.querySelector('.pick').addEventListener('touchstart', e => { e.preventDefault(); if (!Combat.pickNear()) HUD.toast('Nada para pegar'); }, { passive: false });
    this.acts.querySelectorAll('[data-s]').forEach(b => b.addEventListener('touchstart', e => { e.preventDefault(); Magic.cast(b.dataset.s, Combat.target || Combat.nearest(9), null); }, { passive: false }));
  },
  update(dt) {
    if (!this.on) return;
    const a = Game.player.actor, [jx, jy] = this.vec;
    if (jx || jy) {
      // direção da tela -> mundo isométrico
      const wx = (jx / ISO.HW + jy / ISO.HH) / 2, wy = (jy / ISO.HH - jx / ISO.HW) / 2, d = Math.hypot(wx, wy);
      const sp = a.speed * Math.min(1, Math.hypot(jx, jy)) * dt, nx = a.x + wx / d * sp, ny = a.y + wy / d * sp;
      a.path = null; Combat.attacking = false;
      if (Game.map.free(nx, ny)) { a.x = nx; a.y = ny; } else if (Game.map.free(nx, a.y)) a.x = nx; else if (Game.map.free(a.x, ny)) a.y = ny;
      a.dir = direcaoDoAngulo(Math.atan2(wy, wx)); a.setAnim('run'); this.moving = true;
    } else if (this.moving) { this.moving = false; if (!a.path) a.setAnim('stance'); }
    if (this.atk) {
      if (!Combat.target || Combat.target.dead) Combat.engage(Combat.nearest(8));
      Combat.attacking = !!Combat.target;
    }
  },
};

// ---------------------------------------------------------------------
// Globos de vida e mana (D2), aviso com botões (sem comandos digitados)
// ---------------------------------------------------------------------
const Orbs = {
  update(p) {
    if (!this.hp) { this.hp = document.querySelector('#orb-hp i'); this.mp = document.querySelector('#orb-mp i'); this.hpt = document.querySelector('#orb-hp b'); this.mpt = document.querySelector('#orb-mp b'); }
    this.hp.style.height = (100 * Math.max(0, p.hp) / p.hpMax) + '%'; this.mp.style.height = (100 * p.mp / p.mpMax) + '%';
    this.hpt.textContent = `${Math.max(0, Math.round(p.hp))}/${p.hpMax}`; this.mpt.textContent = `${Math.round(p.mp)}/${p.mpMax}`;
  },
};

const Prompt = {
  ask(text, buttons) {
    const el = document.getElementById('prompt');
    el.innerHTML = `<p>${text}</p><div>${buttons.map((b, i) => `<button data-i="${i}">${b[0]}</button>`).join('')}</div>`;
    el.classList.add('on');
    el.querySelectorAll('button').forEach(b => b.onclick = () => { el.classList.remove('on'); buttons[+b.dataset.i][1](); });
    clearTimeout(this._t); this._t = setTimeout(() => el.classList.remove('on'), 30000);
  },
};

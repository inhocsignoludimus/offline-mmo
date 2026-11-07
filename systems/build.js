'use strict';
// =====================================================================
// systems/build.js — coleta, construção e salvamento (estilo After Light, simples)
// - árvore dá logs, rocha dá stone (+ chance de minério): data/gathering.json
// - peças de data/building.json custam só logs, stone ou iron_ingot (sem tábua)
// - forja: na bigorna, 2 minérios viram 1 lingote
// - não se constrói em vila (área segura); tudo fica salvo no navegador
// =====================================================================
const Build = {
  pieces: {}, list: [], placed: [], mode: null, rot: 0, gather: null, hits: new Map(), regrow: [],
  init(data, map) {
    for (const p of data.building.pieces) if (map.build && map.build[p.id]) this.pieces[p.id] = p;
    this.nodes = {}; for (const [k, ids] of Object.entries(map.nodes || {})) for (const t of ids) this.nodes[t] = k;
    this.G = {}; for (const n of data.gathering.nodes) this.G[n.id] = n;
    this.forge = (data.gathering.stations || []).find(s => s.id === 'forge');
    this.anvil = (map.build && map.build.anvil || [])[0];
  },
  name(p) { return p.name[Chat.lang] || p.name.pt; },
  count(id) { return Game.player.bag.filter(i => i.id === id).reduce((n, i) => n + i.qty, 0); },
  take(id, n) { const bag = Game.player.bag; for (const it of bag.slice()) { if (it.id !== id || n <= 0) continue; const k = Math.min(n, it.qty); it.qty -= k; n -= k; if (it.qty <= 0) bag.splice(bag.indexOf(it), 1); } },
  canPay(p) { return Object.entries(p.cost).every(([id, n]) => this.count(id) >= n); },

  // ------------------------------------------------------------- coleta
  nodeAt(i, j) { const m = Game.map; if (!m.inBounds(i, j)) return null; const t = m.obj[j][i]; const k = t && this.nodes[t]; return k ? { kind: k, i, j, t } : null; },
  nodeNear(wx, wy, r = 1) {
    for (let d = 0; d <= r; d++) for (let j = Math.floor(wy) - d; j <= Math.floor(wy) + d; j++) for (let i = Math.floor(wx) - d; i <= Math.floor(wx) + d; i++) { const n = this.nodeAt(i, j); if (n) return n; }
    return null;
  },
  startGather(n) {
    if (World.safe(n.i, n.j)) { HUD.toast('Na vila não se corta nem se minera'); return; }
    const a = Game.player.actor;
    // vai até o lado da árvore/rocha
    const spot = [[1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, -1]].map(([dx, dy]) => [n.i + dx + 0.5, n.j + dy + 0.5]).filter(([x, y]) => !Game.map.blocked(Math.floor(x), Math.floor(y))).sort((p, q) => Math.hypot(p[0] - a.x, p[1] - a.y) - Math.hypot(q[0] - a.x, q[1] - a.y))[0];
    if (!spot) return;
    if (Math.hypot(spot[0] - a.x, spot[1] - a.y) > 0.4) a.moveTo(Game.map, spot[0], spot[1]);
    this.gather = { n, t: 0 }; Combat.attacking = false; Combat.target = null;
    this.holdTool(n.kind === 'tree' ? 'hand_axe' : 'picareta');
  },
  update(dt) {
    const a = Game.player.actor, g = this.gather;
    for (const r of this.regrow.slice()) if (Sim.t > r.at && Math.hypot(r.i - a.x, r.j - a.y) > 8) { this.setObj(r.i, r.j, r.t); this.regrow.splice(this.regrow.indexOf(r), 1); }
    if (!g) { if (Game.tool) this.holdTool(null); return; }
    if (a.path) return;
    if (this.nodeAt(g.n.i, g.n.j) === null) { this.gather = null; return; }
    if (Math.hypot(g.n.i + 0.5 - a.x, g.n.j + 0.5 - a.y) > 1.9) { this.gather = null; return; }
    const def = this.G[g.n.kind]; g.t += dt;
    a.dir = direcaoDoAngulo(Math.atan2(g.n.j + 0.5 - a.y, g.n.i + 0.5 - a.x));
    if (a.anim !== 'swing' || a.t > 0.45) a.setAnim('swing');
    if (g.t < (def.time_s || 1.5) * (1 - (Game.player.skills[def.skill] || 0) / 250)) return;
    g.t = 0;
    // rende
    const sk = Game.player.skills[def.skill] || 0, got = [];
    for (const y of def.yields) {
      let ch = y.always || !y.chance_by_skill ? 1 : 0;
      if (y.chance_by_skill) for (const [s, c] of y.chance_by_skill) if (sk >= s) ch = c;
      if (Math.random() > ch || sk < (y.min_skill || 0)) continue;
      const n = Math.round(Combat.rand(y.amount)); Game.give(y.item, n); got.push(`${n} ${Items.name(Items.def(y.item)).toLowerCase()}`);
    }
    Skills.use(def.skill, 0.4);
    Combat.float(a, got.join(', ') || 'nada', '#e8d8a0');
    Backpack.render();
    // esgota depois de algumas batidas e volta depois
    const k = g.n.i + ',' + g.n.j, h = (this.hits.get(k) || 0) + 1; this.hits.set(k, h);
    if (h >= (g.n.kind === 'tree' ? 4 : 5)) {
      this.hits.delete(k);
      this.regrow.push({ i: g.n.i, j: g.n.j, t: g.n.t, at: Sim.t + 300 });
      this.setObj(g.n.i, g.n.j, g.n.kind === 'tree' ? Game.map.build.stump[0] : 0, g.n.kind === 'tree');
      this.gather = null; HUD.toast(g.n.kind === 'tree' ? 'A árvore caiu' : 'A rocha acabou');
    }
  },
  holdTool(l) { if (Game.tool === l) return; Game.tool = l; Game.rebuildLook(); },
  // troca o objeto de um tile (e a colisão) e atualiza o índice de desenho
  setObj(i, j, t, solid) {
    const m = Game.map; m.obj[j][i] = t; m.col[j][i] = t ? (solid === false ? 0 : 1) : 0;
    const key = Math.floor(i / CHUNK) + ',' + Math.floor(j / CHUNK);
    let arr = m.objChunks.get(key); if (!arr) m.objChunks.set(key, arr = []);
    const k = arr.findIndex(o => o.i === i && o.j === j); if (k >= 0) arr.splice(k, 1);
    if (t && m.tiles[t]) arr.push({ i, j, t, key: i + j + 1 });
  },
  setFloor(i, j, t) { const m = Game.map; m.bg[j][i] = t; m.chunks.delete(Math.floor(i / CHUNK) + ',' + Math.floor(j / CHUNK)); },

  // ------------------------------------------------------------- forja
  smelt() {
    const f = this.forge; if (!f) return;
    const sk = Game.player.skills.blacksmithing || 0; let made = 0;
    for (const r of f.recipes) {
      if (sk < (r.min_skill || 0)) continue;
      const [[inId, inN]] = Object.entries(r.in), [[outId, outN]] = Object.entries(r.out);
      while (this.count(inId) >= inN) { this.take(inId, inN); Game.give(outId, outN); made += outN; Skills.use('blacksmithing', 0.3); }
    }
    Backpack.render();
    HUD.toast(made ? `Você fundiu ${made} lingote(s)` : 'Sem minério para fundir (2 minérios = 1 lingote)');
  },
  anvilNear() {
    const a = Game.player.actor;
    for (let j = Math.floor(a.y) - 2; j <= Math.floor(a.y) + 2; j++) for (let i = Math.floor(a.x) - 2; i <= Math.floor(a.x) + 2; i++) if (Game.map.inBounds(i, j) && Game.map.obj[j][i] === this.anvil) return true;
    return false;
  },

  // ------------------------------------------------------------- construção
  toggleMode(id) {
    this.armed = false;
    if (this.mode === id || !id) { this.mode = null; document.body.classList.remove('building'); BuildGump.render(); return; }
    this.mode = id; document.body.classList.add('building'); BuildGump.render();
    HUD.toast(Touch.on ? 'Toque para mirar e toque de novo para construir' : 'Clique para construir · R gira · Esc sai');
  },
  ghost(wx, wy) { const i = Math.floor(wx), j = Math.floor(wy); return { i, j, ok: this.okAt(i, j) }; },
  okAt(i, j) {
    const p = this.pieces[this.mode], m = Game.map, a = Game.player.actor; if (!p || !m.inBounds(i, j)) return false;
    if (World.safe(i + 0.5, j + 0.5)) return false;
    if (Math.hypot(i + 0.5 - a.x, j + 0.5 - a.y) > 7) return false;
    if (Math.floor(a.x) === i && Math.floor(a.y) === j && p.kind !== 'floor') return false;
    if (p.kind === 'floor') return m.col[j][i] !== 2 && !this.placed.some(b => b.i === i && b.j === j && this.pieces[b.id].kind === 'floor');
    return m.col[j][i] === 0 && !m.obj[j][i] && !Houses.list.some(h => i >= h.x && j >= h.y && i < h.x + h.w && j < h.y + h.h);
  },
  place(i, j) {
    const p = this.pieces[this.mode]; if (!p) return;
    if (!this.okAt(i, j)) { HUD.toast(World.safe(i + .5, j + .5) ? 'Não se constrói dentro da vila' : 'Não dá para construir aqui'); return; }
    if (!this.canPay(p)) { HUD.toast('Faltam: ' + Object.entries(p.cost).map(([id, n]) => `${n} ${Items.name(Items.def(id)).toLowerCase()}`).join(', ')); return; }
    for (const [id, n] of Object.entries(p.cost)) this.take(id, n);
    // paredes se alinham sozinhas com a vizinha (R/↻ só quando não há vizinha)
    let rot = this.rot;
    if (/wall|window|door/.test(p.kind)) {
      const lin = (a, b) => this.placed.some(x => x.i === a && x.j === b && /wall|window|door/.test(this.pieces[x.id].kind));
      if (lin(i - 1, j) || lin(i + 1, j)) rot = 0; else if (lin(i, j - 1) || lin(i, j + 1)) rot = 1;
    }
    this.apply({ id: p.id, i, j, rot, open: false });
    Skills.use(p.material === 'stone' ? 'mining' : 'carpentry', 0.3);
    Backpack.render(); BuildGump.render(); Save.soon();
  },
  apply(b) {
    const p = this.pieces[b.id], tiles = Game.map.build[b.id]; if (!p || !tiles) return;
    const t = tiles[b.rot % tiles.length];
    if (p.kind === 'floor') { if (b.prev == null) b.prev = Game.map.bg[b.j][b.i]; this.setFloor(b.i, b.j, t); }
    else this.setObj(b.i, b.j, b.open ? 0 : t, !(p.kind === 'door' || p.kind === 'gate') || !b.open);
    if ((p.kind === 'door' || p.kind === 'gate') && !b.open) Game.map.col[b.j][b.i] = 1;
    if (!this.placed.includes(b)) this.placed.push(b);
  },
  // portas e portões: abrem e fecham com um clique perto
  toggleDoor(i, j) {
    const b = this.placed.find(x => x.i === i && x.j === j && /door|gate/.test(this.pieces[x.id].kind)); if (!b) return false;
    const a = Game.player.actor; if (Math.hypot(i + .5 - a.x, j + .5 - a.y) > 2.2) return false;
    b.open = !b.open; this.apply(b); Save.soon(); return true;
  },
  // desmontar devolve metade do custo
  remove(i, j) {
    const k = this.placed.findIndex(x => x.i === i && x.j === j && this.pieces[x.id].kind !== 'floor');
    const k2 = k >= 0 ? k : this.placed.findIndex(x => x.i === i && x.j === j);
    if (k2 < 0) return false;
    const b = this.placed[k2], p = this.pieces[b.id]; this.placed.splice(k2, 1);
    if (p.kind === 'floor') this.setFloor(i, j, b.prev || Game.map.bg[j][i]); else this.setObj(i, j, 0);
    for (const [id, n] of Object.entries(p.cost)) if (Math.floor(n / 2)) Game.give(id, Math.floor(n / 2));
    Backpack.render(); Save.soon(); HUD.toast('Peça desmontada'); return true;
  },
  // clique/toque no mundo: devolve true se o sistema de construção/coleta usou o clique
  click(cx, cy) {
    const [wx, wy] = Camera.screenToWorld(cx, cy, Render.vw, Render.vh), i = Math.floor(wx), j = Math.floor(wy);
    if (this.mode === 'del') { if (!this.remove(i, j)) HUD.toast('Só dá para desmontar o que você construiu'); return true; }
    if (this.mode) { this.cursor = [cx, cy]; if (!Touch.on || this.armed) this.place(i, j); this.armed = Touch.on; return true; }
    this.gather = null;
    for (const [di, dj] of [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]]) if (this.toggleDoor(i + di, j + dj)) return true;
    if (Game.map.inBounds(i, j) && Game.map.obj[j][i] === this.anvil && Build.anvilNear()) { this.smelt(); return true; }
    const [wx2, wy2] = Camera.screenToWorld(cx, cy + 30 * Camera.zoom, Render.vw, Render.vh);
    const n = this.nodeAt(Math.floor(wx2), Math.floor(wy2)) || this.nodeAt(i, j);
    if (n) { this.startGather(n); return true; }
    return false;
  },
  // ✋ no celular: coleta o que estiver do lado
  gatherNear() { const a = Game.player.actor, n = this.nodeNear(a.x, a.y, 2); if (n) { this.startGather(n); return true; } if (this.anvilNear()) { this.smelt(); return true; } return false; },
  drawGhost(g) {
    if (!this.mode || this.mode === 'del') return;
    const [cx, cy] = (Touch.on ? this.cursor : Game.mouse) || [Render.vw / 2, Render.vh / 2 + 40];
    const [wx, wy] = Camera.screenToWorld(cx, cy, Render.vw, Render.vh), gh = this.ghost(wx, wy);
    const [sx, sy] = w2s(gh.i + 0.5, gh.j + 0.5), m = Game.map, t = m.build[this.mode][this.rot % m.build[this.mode].length];
    g.save(); g.globalAlpha = 0.6; m.drawTile(g, t, sx, sy); g.globalAlpha = 1;
    g.strokeStyle = gh.ok ? 'rgba(90,230,110,.9)' : 'rgba(240,80,60,.9)'; g.lineWidth = 2; g.beginPath();
    g.moveTo(sx, sy - ISO.HH); g.lineTo(sx + ISO.HW, sy); g.lineTo(sx, sy + ISO.HH); g.lineTo(sx - ISO.HW, sy); g.closePath(); g.stroke(); g.restore();
    this.hoverTile = [gh.i, gh.j];
  },
};

// ---------------------------------------------------------------------
// Janela de construção
// ---------------------------------------------------------------------
const BuildGump = {
  init() {
    this.g = Gumps.create('build', 'Construir', { pos: [-12, 214], posCompact: [-6, 50], w: 250, h: 300, cls: 'buildg', open: false, onOpen: () => this.render() });
  },
  render() {
    if (!this.g || !Gumps.isOpen('build')) return;
    const b = this.g.body;
    const mats = ['logs', 'stone', 'iron_ingot'].map(id => `${Items.name(Items.def(id))}: <b>${Build.count(id)}</b>`).join(' · ');
    b.innerHTML = `<div class="bmats">${mats}</div><div class="blist">` + Object.values(Build.pieces).map(p => {
      const cost = Object.entries(p.cost).map(([id, n]) => `${n} ${Items.name(Items.def(id)).toLowerCase()}`).join(', ');
      return `<button class="bp ${Build.mode === p.id ? 'on' : ''} ${Build.canPay(p) ? '' : 'poor'}" data-p="${p.id}"><span>${Build.name(p)}</span><em>${cost}</em></button>`;
    }).join('') + `</div><div class="bbar"><button data-a="rot">↻ Girar</button><button data-a="del" class="${Build.mode === 'del' ? 'on' : ''}">Desmontar</button><button data-a="forge">Forja</button><button data-a="off">Sair</button></div>`;
    b.querySelectorAll('[data-p]').forEach(x => x.onclick = () => Build.toggleMode(x.dataset.p));
    b.querySelector('[data-a=rot]').onclick = () => { Build.rot++; };
    b.querySelector('[data-a=del]').onclick = () => Build.toggleMode('del');
    b.querySelector('[data-a=off]').onclick = () => { Build.toggleMode(null); Gumps.toggle('build', false); };
    b.querySelector('[data-a=forge]').onclick = () => Build.anvilNear() ? Build.smelt() : HUD.toast('Vá até uma bigorna (na praça das vilas)');
  },
};

// ---------------------------------------------------------------------
// Salvamento no navegador: personagem, mochila, skills, posição e construções
// ---------------------------------------------------------------------
const Save = {
  key() { return 'save2.' + Game.player.name; },   // save2: começo só com roupa simples
  soon() { clearTimeout(this._t); this._t = setTimeout(() => this.write(), 1500); },
  item(i) { return { id: i.id, qty: i.qty, rarity: i.rarity, affixes: i.affixes, hue: i.hue, name: i.name, set: i.set, unique: i.unique, bx: i.bx, by: i.by }; },
  write() {
    const p = Game.player; if (!p) return;
    Store.set(this.key(), { v: 1, world: Game.map.w + 'x' + Game.map.h, x: p.actor.x, y: p.actor.y, gold: p.gold, skills: p.skills, locks: Skills.lock,
      bag: p.bag.map(i => this.item(i)), equip: Object.fromEntries(Object.entries(p.equip).map(([k, i]) => [k, this.item(i)])), builds: Build.placed, hotbar: Magic.hotbar });
  },
  restore(i) { const d = Items.def(i.id); return d ? { ...i, d, icon: d.icon, name: i.name || Items.name(d), affixes: i.affixes || [] } : null; },
  load() {
    const s = Store.get(this.key(), null), p = Game.player; if (!s) return false;
    p.gold = s.gold; Object.assign(p.skills, s.skills); Object.assign(Skills.lock, s.locks || {});
    p.bag = s.bag.map(i => this.restore(i)).filter(Boolean);
    p.equip = {}; for (const [k, i] of Object.entries(s.equip)) { const r = this.restore(i); if (r) p.equip[k] = r; }
    if (s.world === Game.map.w + 'x' + Game.map.h) { for (const b of s.builds || []) Build.apply(b); if (Game.map.free(s.x, s.y)) { p.actor.x = s.x; p.actor.y = s.y; } }
    if (s.hotbar) Magic.hotbar = s.hotbar;
    return true;
  },
};

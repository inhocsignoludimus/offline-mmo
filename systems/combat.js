'use strict';
// =====================================================================
// systems/combat.js — combate estilo Diablo 2 (sem PvP): monstros do
// data/monsters.json com folhas do Flare, ataque segurando o clique (ou o
// botão no celular), loot no chão com as 5 faixas do TCoM, afixos,
// conjuntos, únicos e cores (hues). Skills sobem lutando, como no UO.
// =====================================================================
const RARIDADE = {
  comum: { nome: 'Comum', cor: '#e8e2cf' }, refinado: { nome: 'Refinado', cor: '#6aa0ff' },
  raro: { nome: 'Raro', cor: '#ffd84a' }, conjunto: { nome: 'Conjunto', cor: '#5ee07a' }, lendario: { nome: 'Lendário', cor: '#ff9a2a' },
};
const ART_FALLBACK = { wyvern_air_boss: 'wyvern_air', necromancer: 'skeleton_mage_high_boss' };
const STAT_NOME = {
  dmg_pct: '% de dano', dmg_flat: 'de dano', armor_pct: '% de armadura', armor_flat: 'de armadura', str: 'de força', dex: 'de destreza', int: 'de inteligência',
  hp: 'de vida', mana: 'de mana', stam: 'de fôlego', regen_hp: 'de regeneração de vida', regen_mana: 'de regeneração de mana', regen_stam: 'de regeneração de fôlego',
  res_fire: '% de resistência a fogo', res_cold: '% de resistência a frio', res_poison: '% de resistência a veneno', res_energy: '% de resistência a energia',
  hit_chance: '% de chance de acerto', def_chance: '% de chance de defesa', swing_speed: '% de velocidade de ataque', luck: 'de sorte', durability: '% de durabilidade',
};

const Mons = {
  meta: null, imgs: {}, byId: {}, artMin: {},
  init(data) {
    this.meta = DATA.monArt;
    for (const m of data.monsters.monsters) {
      this.byId[m.id] = m;
      const a = this.art(m); this.artMin[a] = Math.min(this.artMin[a] || 9, m.scale || 1);
    }
  },
  art(m) { return this.meta[m.art] ? m.art : ART_FALLBACK[m.art] || 'skeleton'; },
  img(art) { let i = this.imgs[art]; if (!i) { i = new Image(); i.src = 'engine/dev_assets/monsters/' + art + '.webp'; this.imgs[art] = i; } return i; },
};

class Monster {
  constructor(def, x, y, home) {
    const r = (a, b) => a + Math.random() * (b - a);
    Object.assign(this, { def, x, y, home: home || [x, y], kind: 'mob', dir: Math.floor(Math.random() * 8), anim: 'stance', t: Math.random(), path: null });
    this.art = Mons.art(def); this.scale = (def.scale || 1) / (Mons.artMin[this.art] || 1);
    if (def.art === 'wyvern_air_boss') this.scale *= 1.3;
    this.hpMax = Math.round(r(def.hp[0], def.hp[1])); this.hp = this.hpMax; this.mp = def.mana || 0;
    this.speed = 2.6 * (def.speed || 1); this.cd = 0; this.state = 'idle'; this.next = Math.random() * 3;
    this.name = def.name[Chat.lang] || def.name.pt; this.nameColor = def.level >= 14 ? '#ff9a2a' : '#e0b0b0';
  }
  setAnim(a) { if (this.anim !== a) { this.anim = a; this.t = 0; } }
  get dead() { return this.hp <= 0; }
  update(dt, map) {
    this.t += dt;
    if (this.dead) { this.corpse -= dt; return; }
    this.cd -= dt; this.next -= dt;
    const P = Game.player, pa = P.actor, d = Math.hypot(pa.x - this.x, pa.y - this.y), def = this.def;
    if (this.hitStun > 0) { this.hitStun -= dt; return; }
    const alive = !P.dead && !World.safe(pa.x, pa.y);
    if (alive && (this.state === 'chase' || (d < (def.aggro || 6) && def.behavior !== 'passive'))) this.state = 'chase';
    if (this.state === 'chase' && (!alive || d > 16)) { this.state = 'home'; }
    if (this.state === 'chase') {
      const fleeing = def.flee_hp && this.hp < def.flee_hp;
      const range = Math.max(1, def.range || 1) * 0.9;
      if (fleeing) { this.step(this.x - (pa.x - this.x), this.y - (pa.y - this.y), dt, map); return; }
      if (d > range + 0.3) {
        // perseguir: anda reto; se travar, A*
        if (!this.path || this.next <= 0) { this.next = 0.8; this.path = map.free(this.x + (pa.x - this.x) / d * 0.6, this.y + (pa.y - this.y) / d * 0.6) ? null : map.path(this.x, this.y, pa.x, pa.y, 1500); }
        if (this.path && this.path.length) this.follow(dt); else this.step(pa.x, pa.y, dt, map);
      } else if (this.cd <= 0) this.attack(P, d);
      else if (this.anim !== 'swing' && this.anim !== 'shoot' && this.anim !== 'cast') this.setAnim('stance');
      this.face(pa);
    } else if (this.state === 'home') {
      const hd = Math.hypot(this.home[0] - this.x, this.home[1] - this.y);
      if (hd < 0.6) { this.state = 'idle'; this.hp = Math.min(this.hpMax, this.hp + this.hpMax * 0.5); } else this.step(this.home[0], this.home[1], dt, map);
    } else {
      if (this.next <= 0) { this.next = 2 + Math.random() * 5; const [x, y] = map.randomFree(Math.random, this.home, 3); this.path = map.path(this.x, this.y, x, y, 400); }
      if (this.path && this.path.length) this.follow(dt); else this.setAnim('stance');
    }
    if ((this.anim === 'swing' || this.anim === 'shoot' || this.anim === 'cast' || this.anim === 'hit') && this.t > 0.7) this.setAnim('stance');
  }
  face(t) { this.dir = direcaoDoAngulo(Math.atan2(t.y - this.y, t.x - this.x)); }
  step(tx, ty, dt, map) {
    const dx = tx - this.x, dy = ty - this.y, d = Math.hypot(dx, dy); if (d < 0.05) return;
    const s = Math.min(d, this.speed * dt), nx = this.x + dx / d * s, ny = this.y + dy / d * s;
    if (map.free(nx, ny, 0.25)) { this.x = nx; this.y = ny; } else if (map.free(nx, this.y, 0.25)) this.x = nx; else if (map.free(this.x, ny, 0.25)) this.y = ny;
    this.dir = direcaoDoAngulo(Math.atan2(dy, dx)); this.setAnim('run');
  }
  follow(dt) {
    const [tx, ty] = this.path[0], dx = tx - this.x, dy = ty - this.y, d = Math.hypot(dx, dy), s = this.speed * dt;
    if (d <= s) { this.x = tx; this.y = ty; this.path.shift(); } else { this.x += dx / d * s; this.y += dy / d * s; }
    if (d > 0.01) this.dir = direcaoDoAngulo(Math.atan2(dy, dx)); this.setAnim('run');
  }
  attack(P, d) {
    const def = this.def;
    const spells = (def.spells || []).map(id => Magic.byId[id]).filter(s => s && (s.effect.type === 'damage' || s.effect.type === 'debuff'));
    if (spells.length && Math.random() < 0.45 && d > 1.5) {
      const s = spells[Math.floor(Math.random() * spells.length)];
      this.setAnim(Mons.meta[this.art].cast ? 'cast' : 'swing'); this.cd = 2.2;
      Combat.projectile(this, P.actor, COR_ELEM[s.effect.element] || '#c080ff', () => Combat.hitPlayer(Math.round(Combat.rand(s.effect.base)), s.effect.element, this));
      return;
    }
    const ranged = (def.range || 1) > 2;
    this.setAnim(ranged && Mons.meta[this.art].shoot ? 'shoot' : 'swing');
    this.cd = 1.4 / Math.max(0.5, def.speed || 1);
    const dmg = Math.round(Combat.rand(def.dmg));
    const hit = () => { if (Math.random() < Math.max(0.25, 0.75 + (def.level * 2 - (P.skills.parrying || 0) * 0.3 - Combat.stats.def_chance) / 100)) Combat.hitPlayer(dmg, 'physical', this); else Combat.float(P.actor, 'esquivou', '#aaa'); };
    if (ranged) Combat.projectile(this, P.actor, '#d8c8a0', hit); else setTimeout(() => !this.dead && hit(), 250);
  }
  draw(g, sx, sy) {
    const a0 = Mons.meta[this.art]; if (!a0) return;
    const an = this.dead ? 'die' : this.anim, a = a0[an] || a0.stance;
    let f = quadroDaAnimacao(a, this.t);
    if (this.dead) f = Math.min(a.n - 1, Math.floor(this.t * 1000 / a.dur * a.n));
    const q = a.q[f] && a.q[f][this.dir]; if (!q || q[2] <= 0) return;
    const im = Mons.img(this.art); if (!im.complete || !im.naturalWidth) return;
    if (!this.dead) { g.fillStyle = 'rgba(0,0,0,0.28)'; g.beginPath(); g.ellipse(sx, sy, 16 * this.scale, 8 * this.scale, 0, 0, 7); g.fill(); }
    if (this.dead && this.corpse < 3) g.globalAlpha = Math.max(0, this.corpse / 3);
    if (this.flash > 0) { this.flash -= 0.016; g.filter = 'brightness(1.8)'; }
    const s = this.scale;
    g.drawImage(im, q[0], q[1], q[2], q[3], Math.round(sx - q[4] * s), Math.round(sy - q[5] * s), q[2] * s, q[3] * s);
    g.filter = 'none'; g.globalAlpha = 1;
  }
}

// ---------------------------------------------------------------------
// Itens gerados (faixas, afixos, conjuntos, únicos, cores)
// ---------------------------------------------------------------------
const Loot = {
  init(data) {
    this.hues = {}; for (const h of data.hues.hues) this.hues[h.id] = h;
    this.affix = [...data.affixes.prefix.map(a => ({ ...a, pre: 1 })), ...data.affixes.suffix];
    this.sets = data.sets.sets; this.uniques = data.uniques.uniques; this.rar = data.rarity; this.tables = data.loot.tables || data.loot;
    this.setPieces = []; for (const s of this.sets) for (const p of s.pieces) this.setPieces.push({ set: s, ...p });
  },
  pickW(list) { let t = 0; for (const [, w] of list) t += w; let r = Math.random() * t; for (const e of list) { r -= e[1]; if (r <= 0) return e[0]; } return list[0][0]; },
  rarity(level, bonus = 0) {
    const row = this.rar.drop.find(r => level >= r.level[0] && level <= r.level[1]) || this.rar.drop[0];
    const w = ['comum', 'refinado', 'raro', 'conjunto', 'lendario'].map((k, i) => [k, row[k] * (i ? 1 + bonus * 0.5 : 1)]);
    return this.pickW(w);
  },
  // cria a instância de um item; base = id do base.json
  make(base, rarity = 'comum', level = 1) {
    const d = Items.def(base); if (!d) return null;
    const it = { id: base, d, name: Items.name(d), icon: d.icon, qty: 1, rarity: 'comum', affixes: [], hue: null };
    const equip = d.slot && d.slot !== 'none';
    if (!equip) return it;
    if (rarity === 'lendario') {
      const u = this.uniques.filter(u => u.level <= level + 8);
      const pick = u.length ? u[Math.floor(Math.random() * u.length)] : null;
      if (pick) return this.fromUnique(pick);
      rarity = 'raro';
    }
    if (rarity === 'conjunto') {
      const ps = this.setPieces; const p = ps[Math.floor(Math.random() * ps.length)];
      const b = Items.def(p.base);
      return { id: p.base, d: b, name: `${Items.name(b)} (${p.set.name[Chat.lang] || p.set.name.pt})`, icon: b.icon, qty: 1, rarity: 'conjunto', set: p.set.id, affixes: p.affixes.map(a => [a[0], a[1]]), hue: p.hue };
    }
    it.rarity = rarity;
    const n = rarity === 'refinado' ? 1 + (Math.random() < 0.5 ? 1 : 0) : rarity === 'raro' ? 3 + (Math.random() < 0.5 ? 1 : 0) : 0;
    const kind = d.type === 'weapon' ? 'weapon' : d.type;
    const pool = this.affix.filter(a => a.applies.includes(kind) && (a.tier || 1) <= 1 + Math.ceil(level / 6));
    const used = new Set(); let pre = null, suf = null;
    for (let i = 0; i < n && pool.length; i++) {
      const a = pool[Math.floor(Math.random() * pool.length)]; if (used.has(a.stat)) continue; used.add(a.stat);
      it.affixes.push([a.stat, Math.round(a.range[0] + Math.random() * (a.range[1] - a.range[0]))]);
      if (a.pre && !pre) pre = a; else if (!a.pre && !suf) suf = a;
    }
    if (rarity === 'raro') { const rn = this.rar.rare_names, A = rn.first[Math.floor(Math.random() * rn.first.length)], B = rn.second[Math.floor(Math.random() * rn.second.length)]; it.name = `${A[Chat.lang] || A.pt} ${B[Chat.lang] || B.pt}`; it.baseName = Items.name(d); }
    else if (rarity === 'refinado') it.name = [pre && (pre.name[Chat.lang] || pre.name.pt), Items.name(d), suf && (suf.name[Chat.lang] || suf.name.pt)].filter(Boolean).join(' ');
    // cores: comuns às vezes vêm tingidas; raros com cor de loot
    const hs = Object.values(this.hues), g = rarity === 'raro' ? 'raro' : 'comum';
    if (Math.random() < (rarity === 'comum' ? 0.15 : 0.5)) { const c = hs.filter(h => h.group === g); it.hue = c[Math.floor(Math.random() * c.length)].id; }
    return it;
  },
  fromUnique(u) {
    const b = Items.def(u.base);
    return { id: u.base, d: b, name: u.name[Chat.lang] || u.name.pt, baseName: Items.name(b), icon: b.icon, qty: 1, rarity: 'lendario', unique: u.id, affixes: u.affixes.map(a => [a[0], a[1]]), hue: u.hue, lore: u.lore && (u.lore[Chat.lang] || u.lore.pt) };
  },
  // drops de um monstro morto
  drop(m) {
    const def = m.def, out = [], lv = def.level || 1, t = this.tables[def.loot && def.loot.table];
    const g = def.loot && def.loot.gold; if (g) out.push({ gold: Math.round(Combat.rand(g)) });
    if (t) {
      const n = Math.random() < 0.65 ? 1 + (Math.random() < 0.3 ? 1 : 0) + (lv >= 12 && Math.random() < 0.4 ? 1 : 0) : 0;
      for (let i = 0; i < n; i++) {
        const k = this.pickW(t);
        if (k === 'gold') out.push({ gold: Math.round(5 + lv * (2 + Math.random() * 4)) });
        else if (k === 'reagent') { const r = Object.keys(Items.byId).filter(id => Items.byId[id].type === 'reagent'); const it = Game.item(r[Math.floor(Math.random() * r.length)], 2 + Math.floor(Math.random() * 4)); it && out.push({ item: it }); }
        else { const id = k.replace(/^base:/, ''), d = Items.def(id); if (!d) continue;
          const it = d.slot && d.slot !== 'none' ? this.make(id, this.rarity(lv, (def.loot && def.loot.rarity_bonus) || 0), lv) : Game.item(id, 1); it && out.push({ item: it }); }
      }
    }
    return out;
  },
  color(it) { return (RARIDADE[it.rarity] || RARIDADE.comum).cor; },
  lines(it) {
    const out = [`<b style="color:${this.color(it)}">${it.name}</b>`];
    if (it.baseName) out.push(`<i>${it.baseName}</i>`);
    if (it.rarity && it.rarity !== 'comum') out.push(`<span style="color:${this.color(it)}">${RARIDADE[it.rarity].nome}</span>`);
    const d = it.d;
    if (d.dmg) out.push(`Dano ${d.dmg[0]}–${d.dmg[1]} · ${Chat.skills[d.skill] || d.skill || ''}`);
    if (d.armor) out.push(`Armadura ${d.armor}`);
    for (const [s, v] of it.affixes || []) out.push(`<span class="afx">+${v} ${s.startsWith('skill:') ? 'em ' + (Chat.skills[s.slice(6)] || s.slice(6)) : STAT_NOME[s] || s}</span>`);
    if (it.hue && this.hues[it.hue]) out.push(`<span style="color:${this.hues[it.hue].hex}">● ${this.hues[it.hue].name[Chat.lang] || this.hues[it.hue].name.pt}</span>`);
    if (it.set) { const s = this.sets.find(x => x.id === it.set); if (s) out.push(`<span style="color:#5ee07a">Conjunto: ${Object.entries(s.bonus).map(([n, b]) => `${n} peças: ${b.map(([k, v]) => '+' + v + ' ' + (STAT_NOME[k] || k)).join(', ')}`).join(' · ')}</span>`); }
    if (it.lore) out.push(`<i class="lore">${it.lore}</i>`);
    if (d.desc && !it.lore) out.push(`<i class="lore">${d.desc[Chat.lang] || d.desc.pt}</i>`);
    return out.join('<br>');
  },
};

// ---------------------------------------------------------------------
// Combate do jogador, chão com itens, números de dano
// ---------------------------------------------------------------------
const Combat = {
  mobs: [], ground: [], floats: [], shots: [], target: null, cd: 0, stats: {}, spawnT: 0,
  rand(r) { return r[0] + Math.random() * (r[1] - r[0]); },
  // soma dos itens equipados e dos conjuntos
  recompute() {
    const p = Game.player, st = { armor: 0, dmg_pct: 0, dmg_flat: 0, armor_pct: 0, armor_flat: 0, hp: 0, mana: 0, stam: 0, hit_chance: 0, def_chance: 0, swing_speed: 0, res_fire: 0, res_cold: 0, res_poison: 0, res_energy: 0, regen_hp: 0, regen_mana: 0, regen_stam: 0, skills: {} };
    const sets = {};
    for (const it of Object.values(p.equip)) {
      if (it.d.armor) st.armor += it.d.armor;
      for (const [k, v] of it.affixes || []) { if (k.startsWith('skill:')) st.skills[k.slice(6)] = (st.skills[k.slice(6)] || 0) + v; else st[k] = (st[k] || 0) + v; }
      if (it.set) sets[it.set] = (sets[it.set] || 0) + 1;
    }
    for (const [id, n] of Object.entries(sets)) { const s = Loot.sets.find(x => x.id === id); if (!s) continue; for (const [need, bs] of Object.entries(s.bonus)) if (n >= +need) for (const [k, v] of bs) { if (k.startsWith('skill:')) st.skills[k.slice(6)] = (st.skills[k.slice(6)] || 0) + v; else st[k] = (st[k] || 0) + v; } }
    st.armor = Math.round((st.armor + st.armor_flat) * (1 + st.armor_pct / 100));
    this.stats = st;
    const sk = id => (p.skills[id] || 0) + (st.skills[id] || 0);
    p.hpMax = Math.round(60 + sk('tactics') / 4 + sk('anatomy') / 4 + st.hp + (st.str || 0) * 0.5);
    p.mpMax = Math.round(30 + sk('magery') / 2 + sk('meditation') / 4 + st.mana + (st.int || 0) * 0.5);
    p.stMax = Math.round(50 + st.stam + (st.dex || 0) * 0.5);
    p.hp = Math.min(p.hp, p.hpMax); p.mp = Math.min(p.mp, p.mpMax);
  },
  skill(id) { return (Game.player.skills[id] || 0) + (this.stats.skills && this.stats.skills[id] || 0); },
  weapon() { const w = Game.player.equip.hand1; return w && w.d.type === 'weapon' ? w : null; },
  range() { const w = this.weapon(); if (!w) return 1.2; return /archery/.test(w.d.skill) ? 9 : /fencing/.test(w.d.skill) && /spear|lance|lanca|pike/.test(w.id) ? 1.9 : 1.4; },

  // alvo sob o cursor (ou perto dele)
  mobAt(wx, wy, r = 1.1) {
    let best = null, bd = r;
    for (const m of this.mobs) { if (m.dead) continue; const d = Math.hypot(m.x - wx, m.y - wy - 0.3); if (d < bd) { bd = d; best = m; } }
    return best;
  },
  nearest(r = 7) {
    const a = Game.player.actor; let best = null, bd = r;
    for (const m of this.mobs) { if (m.dead) continue; const d = Math.hypot(m.x - a.x, m.y - a.y); if (d < bd) { bd = d; best = m; } }
    return best;
  },
  // ataque do jogador (chamado enquanto o botão está apertado)
  engage(m) { if (m && !m.dead) this.target = m; },
  update(dt) {
    const p = Game.player, a = p.actor;
    this.cd -= dt;
    for (const m of this.mobs) m.update(dt, Game.map);
    this.mobs = this.mobs.filter(m => !m.dead || m.corpse > 0);
    if (p.dead) return;
    // regeneração
    const s = this.stats;
    p.hp = Math.min(p.hpMax, p.hp + (0.6 + (s.regen_hp || 0) * 0.5 + this.skill('healing') / 200) * dt);
    // atacar o alvo
    const t = this.target;
    if (t && (t.dead || Math.hypot(t.x - a.x, t.y - a.y) > 25)) this.target = null;
    if (this.target && this.attacking) {
      const d = Math.hypot(t.x - a.x, t.y - a.y), r = this.range();
      if (d > r) { if (!a.path || this._repath <= 0) { a.moveTo(Game.map, t.x, t.y); this._repath = 0.3; } this._repath -= dt; if (a.path && a.path.length) a.path[a.path.length - 1] = [t.x, t.y]; }
      else { a.path = null; a.dir = direcaoDoAngulo(Math.atan2(t.y - a.y, t.x - a.x)); if (this.cd <= 0) this.swing(t); }
    }
    // pegar ouro andando por cima
    for (const g of this.ground.slice()) if (g.gold && Math.hypot(g.x - a.x, g.y - a.y) < 0.8) this.pick(g);
    for (const f of this.floats) f.t += dt; this.floats = this.floats.filter(f => f.t < 1.1);
    for (const sh of this.shots) { sh.t += dt / sh.dur; if (sh.t >= 1 && !sh.done) { sh.done = true; sh.hit(); } } this.shots = this.shots.filter(s => !s.done);
    this.respawn(dt);
  },
  swing(t) {
    const p = Game.player, a = p.actor, w = this.weapon();
    const sk = w ? w.d.skill || 'wrestling' : 'wrestling';
    const spd = w ? w.d.speed || 2.5 : 2;
    this.cd = Math.max(0.3, (0.3 + spd * 0.18) * (1 - (this.stats.swing_speed || 0) / 100));
    a.setAnim('swing');
    const ranged = sk === 'archery';
    const go = () => {
      if (t.dead) return;
      const chance = Math.min(0.97, Math.max(0.3, 0.6 + (this.skill(sk) - t.def.level * 4) / 150 + (this.stats.hit_chance || 0) / 100));
      Skills.use(sk, Math.min(1, t.def.level / 15)); if (Math.random() < 0.4) Skills.use('tactics', Math.min(1, t.def.level / 15));
      if (Math.random() > chance) { this.float(t, 'errou', '#aaa'); return; }
      let dmg = this.rand(w ? w.d.dmg : [1, 4]) * 1.3 * (1 + this.skill('tactics') / 160 + this.skill('anatomy') / 320 + (this.stats.dmg_pct || 0) / 100) + (this.stats.dmg_flat || 0);
      dmg = dmg * 100 / (100 + (t.def.armor || 0) * 2);
      const crit = Math.random() < this.skill('anatomy') / 600; if (crit) dmg *= 1.8;
      this.damageMob(t, Math.max(1, Math.round(dmg)), crit);
    };
    if (ranged) { const ar = Game.player.bag.find(i => i.id === 'arrow'); if (!ar) { HUD.toast('Sem flechas'); this.cd = 0.6; return; } if (--ar.qty <= 0) p.bag.splice(p.bag.indexOf(ar), 1); this.projectile(a, t, '#e8dcb0', go); }
    else setTimeout(go, 180);
  },
  damageMob(m, n, crit, color) {
    if (m.dead) return;
    m.hp -= n; m.flash = 0.08; m.state = 'chase';
    this.float(m, String(n), color || (crit ? '#ffd84a' : '#ffffff'), crit);
    if (m.hp <= 0) this.kill(m); else if (n > m.hpMax * 0.15) { m.setAnim('hit'); m.hitStun = 0.15; }
  },
  kill(m) {
    m.hp = 0; m.t = 0; m.corpse = 12; m.path = null;
    if (this.target === m) this.target = null;
    for (const d of Loot.drop(m)) {
      const ang = Math.random() * 6.28, r = 0.3 + Math.random() * 0.8;
      const x = m.x + Math.cos(ang) * r, y = m.y + Math.sin(ang) * r;
      this.ground.push({ ...d, x: Game.map.free(x, y, 0.1) ? x : m.x, y: Game.map.free(x, y, 0.1) ? y : m.y, t: 0 });
    }
    if (m.spawn) m.spawn.dead = Sim.t;
    if (Math.random() < 0.12) { const s = Sim.speaker('loot_rare'); s && Sim.say(s, 'loot_rare', null, 'global'); }
  },
  hitPlayer(n, elem, from) {
    const p = Game.player; if (p.dead) return;
    const res = elem && elem !== 'physical' ? (this.stats['res_' + elem] || 0) : 0;
    let dmg = n * 100 / (100 + this.stats.armor * 1.5) * (1 - Math.min(70, res) / 100);
    dmg = Math.max(1, Math.round(dmg));
    p.hp -= dmg; this.float(p.actor, '-' + dmg, '#ff5a4a');
    if (Math.random() < 0.3) Skills.use('parrying', 0.3);
    if (p.hp <= 0) this.die();
  },
  die() {
    const p = Game.player; p.dead = true; p.hp = 0; p.actor.setAnim('die'); p.actor.path = null; this.target = null;
    document.getElementById('death').classList.add('on');
  },
  revive() {
    const p = Game.player; p.dead = false; p.hp = Math.round(p.hpMax * 0.6); p.mp = Math.round(p.mpMax * 0.5);
    document.getElementById('death').classList.remove('on');
    const [x, y] = Game.townCenter; p.actor.x = x; p.actor.y = y; p.actor.path = null; Camera.snap(x, y); p.actor.setAnim('stance');
    Journal.add('system', '', 'Você acorda no templo da vila. Nada foi perdido.');
  },
  pick(g) {
    const p = Game.player;
    if (g.gold) { p.gold += g.gold; this.float(p.actor, `+${g.gold} ouro`, '#ffd84a'); }
    else { const it = g.item; if (it.qty > 1 || Items.stackable(it.d)) { const same = p.bag.find(i => i.id === it.id && !i.rarity && Items.stackable(i.d)); if (same) same.qty += it.qty; else p.bag.push(it); } else p.bag.push(it);
      it.bx = 6 + Math.random() * 170; it.by = 6 + Math.random() * 120; Journal.add('system', '', `Você pegou: ${it.name}${it.qty > 1 ? ' ×' + it.qty : ''}.`); Backpack.render(); }
    this.ground.splice(this.ground.indexOf(g), 1);
  },
  pickNear() {
    const a = Game.player.actor; let best = null, bd = 1.8;
    for (const g of this.ground) { const d = Math.hypot(g.x - a.x, g.y - a.y); if (d < bd) { bd = d; best = g; } }
    if (best) this.pick(best); return !!best;
  },
  float(who, text, color, big) { this.floats.push({ x: who.x, y: who.y, text, color, big, t: 0 }); },
  projectile(from, to, color, hit) {
    const d = Math.hypot(to.x - from.x, to.y - from.y);
    this.shots.push({ x0: from.x, y0: from.y, to, color, t: 0, dur: Math.max(0.12, d / 14), hit });
  },
  // ------------------------------------------------------------
  // spawns da zona
  // mundo contínuo: spawns das regiões do data/zones.json
  spawnWorld() {
    this.mobs = []; this.ground = []; this.target = null;
    this.spawns = World.spawns().filter(s => Mons.byId[s.monster]).map(s => ({ ...s, dead: -999 }));
    for (const s of this.spawns) this.fill(s);
  },
  pickMonster(level, cat) {
    const pool = Object.values(Mons.byId).filter(m => Math.abs(m.level - level) <= 3 && !/boss/.test(m.id) && (!cat || this.catOk(m, cat)));
    return pool.length ? pool[Math.floor(Math.random() * pool.length)] : Mons.byId.skeleton;
  },
  catOk(m, cat) { return cat === 'undead' || cat === 'cursed_grave' ? /skeleton|zombie|necro/.test(m.id) : true; },
  fill(s) {
    const [x, y, w, h] = s.rect, def = s.monster ? Mons.byId[s.monster] : this.pickMonster(Math.max(1, s.level), s.cat);
    const n = s.count ? Math.round(this.rand(s.count)) : Math.max(1, Math.round(this.rand(def.pack || [1, 1]) * 0.6));
    if (n <= 0) { s.dead = null; return; }
    for (let i = 0; i < n; i++) {
      const [mx, my] = Game.map.randomFree(Math.random, [x + w / 2, y + h / 2], Math.max(1.5, Math.min(w, h) / 2 - 1));
      const m = new Monster(def, mx, my); m.spawn = s; this.mobs.push(m);
    }
    s.dead = null;
  },
  respawn(dt) {
    if (!this.spawns) return;
    const a = Game.player.actor;
    for (const s of this.spawns) {
      if (s.dead === null) { if (!this.mobs.some(m => m.spawn === s && !m.dead)) s.dead = Sim.t; continue; }
      if (Sim.t - s.dead > (s.boss ? 240 : 45) && Math.hypot(s.rect[0] + s.rect[2] / 2 - a.x, s.rect[1] + s.rect[3] / 2 - a.y) > 14) this.fill(s);
    }
  },
  // ------------------------------------------------------------
  drawWorld(g) {
    // itens no chão
    for (const it of this.ground) {
      const [sx, sy] = w2s(it.x, it.y);
      g.fillStyle = it.gold ? '#ffd84a' : Loot.color(it.item);
      g.beginPath(); g.ellipse(sx, sy, 5, 2.5, 0, 0, 7); g.fill();
    }
    for (const sh of this.shots) {
      const x = sh.x0 + (sh.to.x - sh.x0) * sh.t, y = sh.y0 + (sh.to.y - sh.y0) * sh.t, [sx, sy] = w2s(x, y);
      g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = sh.color; g.beginPath(); g.arc(sx, sy - 36, 4, 0, 7); g.fill(); g.restore();
    }
  },
  // rótulos, barras e números (em pixels de tela)
  drawScreen(g, now) {
    this.labels = [];
    const showAll = Game.altHeld || Render.showNames;
    g.font = '600 12px "Alegreya Sans", system-ui, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    for (const it of this.ground) {
      const [px, py] = Camera.worldToScreen(it.x, it.y, Render.vw, Render.vh);
      if (px < -50 || py < -50 || px > Render.vw + 50 || py > Render.vh + 50) continue;
      const near = Math.hypot(it.x - Game.player.actor.x, it.y - Game.player.actor.y) < 6;
      if (!showAll && !near && !it.gold) continue;
      const text = it.gold ? `${it.gold} ouro` : it.item.name + (it.item.qty > 1 ? ' ×' + it.item.qty : '');
      const w = g.measureText(text).width + 10, y = py - 12;
      g.fillStyle = 'rgba(0,0,0,0.72)'; g.fillRect(px - w / 2, y - 8, w, 16);
      g.fillStyle = it.gold ? '#ffd84a' : Loot.color(it.item); g.fillText(text, px, y);
      this.labels.push({ x: px - w / 2, y: y - 8, w, h: 16, it });
    }
    for (const m of this.mobs) {
      if (m.dead || m.hp >= m.hpMax && m !== this.target) continue;
      const [px, py] = Camera.worldToScreen(m.x, m.y, Render.vw, Render.vh), w = 34;
      const top = py - 70 * Camera.zoom * m.scale;
      g.fillStyle = 'rgba(0,0,0,0.7)'; g.fillRect(px - w / 2 - 1, top - 1, w + 2, 5);
      g.fillStyle = '#c0302a'; g.fillRect(px - w / 2, top, w * Math.max(0, m.hp / m.hpMax), 3);
    }
    for (const f of this.floats) {
      const [px, py] = Camera.worldToScreen(f.x, f.y, Render.vw, Render.vh);
      g.globalAlpha = 1 - f.t; g.font = `700 ${f.big ? 17 : 13}px "Alegreya Sans", sans-serif`;
      g.lineWidth = 3; g.strokeStyle = '#000'; const y = py - 60 * Camera.zoom - f.t * 30;
      g.strokeText(f.text, px, y); g.fillStyle = f.color; g.fillText(f.text, px, y);
    }
    g.globalAlpha = 1;
    // barra do alvo, no alto da tela (como no D2)
    const t = this.target || this.hover;
    const tb = document.getElementById('targetbar');
    if (t && !t.dead) { tb.style.display = ''; tb.querySelector('span').textContent = `${t.name} · nível ${t.def.level}`; tb.querySelector('i').style.width = (100 * t.hp / t.hpMax) + '%'; }
    else tb.style.display = 'none';
  },
  labelAt(x, y) { for (const l of this.labels || []) if (x >= l.x && x <= l.x + l.w && y >= l.y && y <= l.y + l.h) return l.it; return null; },
};

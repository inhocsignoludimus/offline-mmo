'use strict';
// =====================================================================
// src/main.js — liga tudo: carrega os dados, cria o personagem, trata a
// entrada (clique para andar, segurar para seguir o cursor) e roda o laço.
// DATA vem embutido pelo build/build.py (funciona em file:// no APK).
// =====================================================================
// Itens: data/items/base.json (Ludimus). sprite_layer = 'm/<camada do TCoM>' ou null.
const Items = {
  byId: {},
  init(data) { for (const it of data.items.items) this.byId[it.id] = it; },
  def(id) { return this.byId[id]; },
  name(d) { return (d.name && (d.name[Chat.lang] || d.name.pt)) || d.id; },
  layer(d) { return d.sprite_layer ? d.sprite_layer.split('/')[1] : null; },
  stackable(d) { return ['consumable', 'resource'].includes(d.type) || d.slot === 'none' && d.type === 'misc'; },
  twoHanded(d) { return ['arco', 'besta', 'lanca', 'infantry_axe'].includes(this.layer(d)) || /staff/.test(d.id); },
};
// ofícios iniciais: equipamento (ids de itens), camadas de base que não são itens, skills (ids de data/skills.json) e o que vai na mochila
const CLASSES = {
  guerreiro: { equip: ['gambeson', 'chain_greaves', 'leather_boots', 'leather_gloves', 'nasal_helm', 'longsword', 'buckler'], base: ['male_head1'], skills: { swordsmanship: 50, tactics: 45, healing: 30, anatomy: 25 }, bag: [['loriga'], ['round_shield'], ['mace'], ['bandage', 8], ['heal_potion', 2]] },
  cruzado: { equip: ['crusader_surcoat', 'chain_greaves', 'chain_boots', 'chain_gloves', 'chain_coif', 'longsword', 'crusader_shield'], base: ['male_head2'], skills: { swordsmanship: 45, tactics: 40, parrying: 35, healing: 30 }, bag: [['nasal_helm'], ['pilgrim_cross'], ['bandage', 6], ['bread', 4]] },
  beduino: { equip: ['bedouin_robe', 'cloth_sandals', 'turban', 'spear'], base: ['male_head1', 'beduino_saia', 'beduino_mangas'], skills: { fencing: 50, tactics: 35, tracking: 35, camping: 30 }, bag: [['dagger'], ['keffiyeh'], ['round_shield'], ['dried_meat', 6]] },
  artesao: { equip: ['cloth_pants', 'leather_boots', 'smith_hammer'], base: ['male_head2', 'ferreiro_tunica'], skills: { blacksmithing: 55, mining: 50, carpentry: 30, tinkering: 25 }, bag: [['pickaxe'], ['leather_gloves'], ['iron_ore', 12], ['iron_ingot', 6], ['logs', 10]] },
  peregrino: { equip: ['pilgrim_habit', 'cloth_pants', 'cloth_sandals', 'pilgrim_cross'], base: ['male_head1'], f: ['habito', 'head_long'], skills: { healing: 50, magery: 40, meditation: 40, resisting_spells: 30 }, bag: [['relicary'], ['heal_potion', 3], ['mana_potion', 2], ['bread', 5]] },
  aldea: { equip: ['cloth_pants', 'cloth_sandals', 'peasant_tunic', 'skinning_knife'], base: ['male_head1'], f: ['aldea_roupa2', 'head_long'], skills: { cooking: 45, fishing: 45, alchemy: 30, tailoring: 30 }, bag: [['fishing_pole'], ['sewing_kit'], ['cloth_bolt', 3], ['bread', 5]] },
};
const EFEITOS = { // consumíveis
  bandage: p => p.hp += 8, greater_bandage: p => p.hp += 18, heal_potion: p => p.hp += 20, greater_heal_potion: p => p.hp += 40,
  mana_potion: p => p.mp += 20, refresh_potion: p => p.st += 30, cure_potion: p => p.hp += 2, bread: p => p.st += 12, dried_meat: p => p.st += 15,
};

const Game = {
  actors: [], now: 0, t0: performance.now(), held: null, hover: null,
  clock() { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); },
  start(cfg) {
    this.map = new GameMap(DATA.map, this.atlas);
    this.townCenter = this.findCenter();
    Chat.init(DATA); TCOM.meta = DATA.tcom; Icons.meta = DATA.icons;
    // personagem
    Items.init(DATA);
    const cls = CLASSES[cfg.cls] || CLASSES.guerreiro, sexo = cfg.sexo === 'f' ? 'f' : 'm';
    const base = sexo === 'f' ? (cls.f || ['clothes', 'head_long']) : cls.base;
    const [x, y] = this.townCenter;
    const actor = new Actor({ x, y, ap: { sexo, layers: [] }, name: cfg.name, kind: 'me', nameColor: '#6ab0ff', speed: 4.2 });
    this.player = {
      name: cfg.name, guild: null, actor, base, gold: 120, hp: 70, hpMax: 70, mp: 40, mpMax: 40, st: 60, stMax: 60,
      skills: { ...cls.skills }, equip: {}, bag: [],
      weight() { let w = 0; for (const i of this.bag) w += (i.d.weight || 0) * i.qty; for (const k in this.equip) w += this.equip[k].d.weight || 0; return Math.round(w); },
    };
    for (const id of cls.equip) { const it = this.item(id); if (it) this.player.equip[it.d.slot] = it; }
    cls.bag.forEach(([id, n]) => this.give(id, n || 1));
    this.rebuildLook();
    this.playerSim = { name: cfg.name, online: true, near: true, pers: 'novato' };
    this.actors.push(actor);
    Camera.snap(x, y);
    // interface
    Journal.init(); StatusGump.init(); Backpack.init(); Paperdoll.init(); Minimap.init(); OnlineGump.init(); HUD.init();
    Minimap.build(this.map);
    Sim.init(DATA, this.map);
    Journal.add('system', '', `Bem-vindo a ${this.townName}, shard Outremer. ${Sim.online().length} jogadores online.`);
    Journal.add('system', '', 'Clique no chão para andar (segure para seguir o cursor). Enter para falar. /g global, /w Nome sussurro, /gu guilda, /aceitar, /sair, /quem.');
    this.bindInput();
    this.last = performance.now(); requestAnimationFrame(t => this.loop(t));
    setInterval(() => { OnlineGump.render(); }, 3000);
  },
  townName: 'Porto do Trigo',
  findCenter() {
    const m = this.map; let best = null, bd = 1e9;
    for (let j = 0; j < m.h; j++) for (let i = 0; i < m.w; i++) {
      if (m.blocked(i, j) || !m.bg[j][i]) continue;
      // perto do meio e com espaço livre em volta
      let free = 0; for (let dj = -2; dj <= 2; dj++) for (let di = -2; di <= 2; di++) if (!m.blocked(i + di, j + dj)) free++;
      const d = Math.hypot(i - m.w / 2, j - m.h / 2) - free * 0.6;
      if (d < bd) { bd = d; best = [i + 0.5, j + 0.5]; }
    }
    return best;
  },
  item(id, qty = 1) {
    const d = Items.def(id); if (!d) { console.warn('item desconhecido', id); return null; }
    return { id, d, name: Items.name(d), icon: d.icon, qty, bx: 6 + Math.random() * 170, by: 6 + Math.random() * 120 };
  },
  give(id, qty = 1) {
    const it = this.item(id, qty); if (!it) return;
    const same = Items.stackable(it.d) && this.player.bag.find(i => i.id === id);
    if (same) same.qty += qty; else this.player.bag.push(it);
  },
  useItem(it) {
    const p = this.player, d = it.d;
    if (EFEITOS[it.id]) {
      EFEITOS[it.id](p); p.hp = Math.min(p.hpMax, p.hp); p.mp = Math.min(p.mpMax, p.mp); p.st = Math.min(p.stMax, p.st);
      if (--it.qty <= 0) p.bag.splice(p.bag.indexOf(it), 1);
      Journal.add('system', '', `Você usa: ${it.name.toLowerCase()}.`); Backpack.render(); return;
    }
    if (!d.slot || d.slot === 'none') { Journal.add('system', '', (d.desc && (d.desc[Chat.lang] || d.desc.pt)) || it.name); return; }
    p.bag.splice(p.bag.indexOf(it), 1);
    const back = s => { const o = p.equip[s]; if (o) { delete p.equip[s]; p.bag.push({ ...o, bx: it.bx, by: it.by }); } };
    back(d.slot);
    if (d.slot === 'hand2') { const m = p.equip.hand1; if (m && Items.twoHanded(m.d)) back('hand1'); }
    if (d.slot === 'hand1' && Items.twoHanded(d)) back('hand2');
    p.equip[d.slot] = it;
    this.rebuildLook(); Backpack.render(); Paperdoll.render();
  },
  unequip(slot) {
    const p = this.player, it = p.equip[slot]; if (!it) return;
    delete p.equip[slot]; p.bag.push({ ...it, bx: 10 + Math.random() * 150, by: 10 + Math.random() * 100 });
    this.rebuildLook(); Backpack.render(); Paperdoll.render();
  },
  // camadas = base (cabeça, roupa de baixo) + itens equipados; armadura de tronco esconde a túnica de base
  rebuildLook() {
    const p = this.player, a = p.actor;
    const eq = Object.values(p.equip).map(i => Items.layer(i.d)).filter(Boolean);
    const hasChest = eq.some(l => TCOM.slot[l] === 'tronco');
    a.ap.layers = p.base.filter(l => !(hasChest && TCOM.slot[l] === 'tronco')).concat(eq);
    a.camadas = montarCamadas(a.ap);
  },

  // ------------------------------------------------------------------
  // fala do jogador e comandos
  // ------------------------------------------------------------------
  playerSays(text, ch) {
    const p = this.player;
    let m;
    if ((m = text.match(/^\/w\s+(\S+)\s+(.+)/i))) { Journal.add('whisper', `você → ${m[1]}`, m[2], { me: true }); Sim.hear(m[2], 'whisper', m[1]); return; }
    if ((m = text.match(/^\/g\s+(.+)/i))) { ch = 'global'; text = m[1]; }
    else if ((m = text.match(/^\/gu\s+(.+)/i))) { ch = 'guild'; text = m[1]; }
    else if (/^\/aceitar\b/i.test(text)) { Sim.accept(); return; }
    else if (/^\/sair\b/i.test(text)) { Sim.leave(); return; }
    else if (/^\/quem\b/i.test(text)) { Gumps.toggle('online', true); OnlineGump.render(); return; }
    else if (text.startsWith('/')) { Journal.add('system', '', 'Comando desconhecido.'); return; }
    if (ch === 'guild' && !p.guild) { Journal.add('system', '', 'Você não está em uma guilda.'); return; }
    const who = p.guild && ch !== 'guild' ? `${p.name} [${p.guild.tag}]` : p.name;
    Journal.add(ch, who, text, { me: true });
    if (ch === 'local') p.actor.say = { text, until: this.now + 3500 + text.length * 70 };
    Sim.hear(text, ch);
  },

  // ------------------------------------------------------------------
  // entrada
  // ------------------------------------------------------------------
  bindInput() {
    const cv = Render.cv;
    const pick = (cx, cy) => {
      let best = null, bd = 26;
      for (const a of this.actors) {
        if (a === this.player.actor) continue;
        const [sx, sy] = Camera.worldToScreen(a.x, a.y, Render.vw, Render.vh);
        const d = Math.hypot(cx - sx, (cy - (sy - 32 * Camera.zoom)) * 0.6);
        if (d < bd) { bd = d; best = a; }
      }
      return best;
    };
    const go = (cx, cy) => {
      const [wx, wy] = Camera.screenToWorld(cx, cy, Render.vw, Render.vh);
      this.hover = [wx, wy];
      const a = this.player.actor;
      if (!a.moveTo(this.map, wx, wy)) {
        // destino bloqueado: anda até o ponto livre mais perto na direção
        for (let k = 1; k <= 6; k++) { const t = k / 7, x = wx + (a.x - wx) * t, y = wy + (a.y - wy) * t; if (!this.map.blocked(Math.floor(x), Math.floor(y)) && a.moveTo(this.map, x, y)) break; }
      }
    };
    let downAt = 0, lastRepath = 0;
    cv.addEventListener('pointerdown', e => {
      document.activeElement && document.activeElement.blur && document.activeElement.blur();
      const s = pick(e.clientX, e.clientY);
      if (s && s.sim) { this.inspect(s.sim); return; }
      this.held = [e.clientX, e.clientY]; downAt = performance.now(); go(e.clientX, e.clientY); cv.setPointerCapture(e.pointerId);
    });
    cv.addEventListener('pointermove', e => {
      if (!this.held) return; this.held = [e.clientX, e.clientY];
      const n = performance.now(); if (n - lastRepath > 180) { lastRepath = n; go(e.clientX, e.clientY); }
    });
    const up = () => { this.held = null; setTimeout(() => { if (!this.held) this.hover = null; }, 600); };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    cv.addEventListener('contextmenu', e => e.preventDefault());
    cv.addEventListener('wheel', e => { Camera.zoom = Math.max(0.5, Math.min(2, Camera.zoom * (e.deltaY < 0 ? 1.1 : 0.9))); }, { passive: true });
    addEventListener('keydown', e => {
      const typing = document.activeElement && /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
      if (e.key === 'Enter' && !typing) { e.preventDefault(); Journal.focus(); return; }
      if (e.key === 'Escape' && typing) { document.activeElement.blur(); return; }
      if (typing) return;
      const k = e.key.toLowerCase(), map = { s: 'status', p: 'paperdoll', b: 'backpack', j: 'journal', o: 'online', m: 'minimap' };
      if (map[k] && !e.ctrlKey && !e.metaKey) { Gumps.toggle(map[k]); e.preventDefault(); }
    });
  },
  inspect(s) {
    // como no UO: clique num jogador mostra o nome e a guilda
    const g = s.guild ? ` — ${s.guild.name} [${s.guild.tag}]` : '';
    Journal.add('system', '', `${s.name}${g}${s.murderer ? ' (assassino)' : ''}`);
    s.actor.say = { text: s.guild ? `[${s.guild.tag}] ${s.name}` : s.name, until: this.now + 1800, color: s.actor.nameColor };
    Journal.input.value = `/w ${s.name} `;
  },

  loop(t) {
    const dt = Math.min(0.05, Math.max(0, (t - this.last) / 1000)); this.last = t; this.now = t;
    const p = this.player, a = p.actor;
    for (const x of this.actors) x.update(dt, this.map);
    Sim.update(dt);
    // fôlego cai correndo e volta parado
    p.st = Math.max(0, Math.min(p.stMax, p.st + (a.path ? -0.4 : 2) * dt));
    p.mp = Math.min(p.mpMax, p.mp + 0.5 * dt);
    Camera.follow(a.x, a.y, dt);
    Render.frame(this.map, this.actors, this.hover, t);
    if (!this._ui || t - this._ui > 200) { this._ui = t; StatusGump.update(p); Minimap.tick(this.map, this.actors, a); }
    Paperdoll.tick(dt);
    requestAnimationFrame(n => this.loop(n));
  },
};

// ---------------------------------------------------------------------
// tela de criação do personagem
// ---------------------------------------------------------------------
function boot() {
  Render.init(document.getElementById('cv'));
  const atlas = new Image(); atlas.src = DATA.map.atlasFile; Game.atlas = atlas;
  const fonts = document.fonts ? document.fonts.ready : Promise.resolve();
  const saved = Store.get('char', null);
  const el = document.getElementById('create');
  const f = el.querySelector('form');
  if (saved) { f.nome.value = saved.name; f.sexo.value = saved.sexo; f.cls.value = saved.cls; }
  else f.nome.value = rnd(['Tomás', 'Godofredo', 'Balduíno', 'Onofre', 'Raimundo', 'Hugo']) + Math.floor(10 + Math.random() * 89);
  f.onsubmit = e => {
    e.preventDefault();
    const cfg = { name: f.nome.value.trim().slice(0, 16) || 'Andarilho', sexo: f.sexo.value, cls: f.cls.value };
    Store.set('char', cfg);
    el.classList.add('off');
    const go = () => Promise.all([fonts, new Promise(r => atlas.complete ? r() : (atlas.onload = r))]).then(() => Game.start(cfg));
    go();
  };
}
addEventListener('DOMContentLoaded', boot);

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
// Não há classe fixa, como no UO: o kit inicial só decide por onde você começa
// (4 skills e o equipamento). Qualquer skill sobe com o uso (systems/skills.js).
const ROUPA = ['cloth_shirt', 'cloth_pants', 'cloth_sandals'];
const KITS = {
  guerreiro: { nome: 'Guerreiro', equip: ['gambeson', 'chain_greaves', 'leather_boots', 'leather_gloves', 'nasal_helm', 'longsword', 'buckler'], base: ['male_head1'], skills: { swordsmanship: 50, tactics: 45, parrying: 30, anatomy: 25 }, bag: [['bandage', 8], ['heal_potion', 2]] },
  cruzado: { nome: 'Cruzado', equip: ['crusader_surcoat', 'chain_greaves', 'chain_boots', 'chain_gloves', 'chain_coif', 'longsword', 'crusader_shield'], base: ['male_head2'], skills: { swordsmanship: 45, tactics: 40, parrying: 35, healing: 30 }, bag: [['pilgrim_cross'], ['bandage', 6], ['bread', 4]] },
  lanceiro: { nome: 'Lanceiro beduíno', equip: ['bedouin_robe', 'cloth_sandals', 'turban', 'spear'], base: ['male_head1', 'beduino_saia', 'beduino_mangas'], skills: { fencing: 50, tactics: 40, tracking: 35, camping: 25 }, bag: [['dagger'], ['dried_meat', 6]] },
  arqueiro: { nome: 'Arqueiro', equip: ['leather_armor', 'cloth_pants', 'leather_boots', 'leather_hood', 'longbow'], base: ['male_head2'], skills: { archery: 50, tactics: 40, bowcraft_fletching: 35, tracking: 25 }, bag: [['arrow', 60], ['hatchet'], ['bread', 4]] },
  mago: { nome: 'Mago', equip: ['pilgrim_habit', 'cloth_sandals', 'travel_cloak', 'staff'], base: ['male_head1'], f: ['habito', 'head_long'], skills: { magery: 50, evaluating_intelligence: 40, meditation: 40, resisting_spells: 20 }, bag: [['mana_potion', 3], ['bread', 4], ['incense', 20], ['saltpeter', 20], ['myrrh', 20], ['quicklime', 20]] },
  curandeiro: { nome: 'Curandeiro', equip: ['pilgrim_habit', 'cloth_pants', 'cloth_sandals', 'pilgrim_cross'], base: ['male_head1'], f: ['habito', 'head_long'], skills: { healing: 50, anatomy: 40, veterinary: 30, meditation: 30 }, bag: [['bandage', 20], ['heal_potion', 3], ['bread', 4]] },
  gatuno: { nome: 'Gatuno', equip: ['leather_armor', 'cloth_pants', 'leather_boots', 'leather_gloves', 'leather_hood', 'dagger'], base: ['male_head2'], skills: { stealth: 45, hiding: 45, snooping: 35, lockpicking: 25 }, bag: [['bread', 3]] },
  ferreiro: { nome: 'Ferreiro', equip: ['cloth_pants', 'leather_boots', 'smith_hammer'], base: ['male_head2', 'ferreiro_tunica'], skills: { blacksmithing: 55, mining: 50, tinkering: 25, mace_fighting: 20 }, bag: [['pickaxe'], ['iron_ore', 12], ['iron_ingot', 6]] },
  lenhador: { nome: 'Lenhador e carpinteiro', equip: [...ROUPA, 'leather_boots', 'hatchet'], base: ['male_head1'], skills: { lumberjacking: 50, carpentry: 45, bowcraft_fletching: 25, tactics: 30 }, bag: [['logs', 15], ['boards', 10]] },
  pescador: { nome: 'Pescador e cozinheiro', equip: ['cloth_pants', 'cloth_sandals', 'peasant_tunic', 'skinning_knife'], base: ['male_head1'], f: ['aldea_roupa2', 'head_long'], skills: { fishing: 50, cooking: 45, camping: 30, tailoring: 25 }, bag: [['fishing_pole'], ['bread', 6]] },
  alfaiate: { nome: 'Alfaiate', equip: [...ROUPA], base: ['male_head2'], f: ['clothes', 'head_long'], skills: { tailoring: 55, herding: 30, cooking: 30, musicianship: 35 }, bag: [['sewing_kit'], ['cloth_bolt', 4], ['cut_leather', 6]] },
  domador: { nome: 'Domador', equip: ['leather_armor', 'cloth_pants', 'leather_boots', 'skinning_knife'], base: ['male_head1'], skills: { animal_taming: 50, veterinary: 40, herding: 35, tracking: 25 }, bag: [['bandage', 10], ['dried_meat', 6]] },
  bardo: { nome: 'Bardo', equip: [...ROUPA, 'travel_cloak', 'dagger'], base: ['male_head2'], f: ['aldea_roupa2', 'head_long'], skills: { musicianship: 50, peacemaking: 40, provocation: 35, fencing: 25 }, bag: [['bread', 4]] },
  alquimista: { nome: 'Alquimista', equip: [...ROUPA, 'wool_cloak'], base: ['male_head1'], f: ['clothes', 'head_long'], skills: { alchemy: 50, poisoning: 35, healing: 35, inscription: 30 }, bag: [['mortar_pestle'], ['heal_potion', 4], ['cure_potion', 2]] },
  livre: { nome: 'Do seu jeito (escolha 3 skills)', equip: [...ROUPA, 'dagger'], base: ['male_head1'], f: ['clothes', 'head_long'], skills: {}, bag: [['bandage', 6], ['bread', 4]] },
};
const EFEITOS = { // consumíveis
  bandage: p => p.hp += 8, greater_bandage: p => p.hp += 18, heal_potion: p => p.hp += 20, greater_heal_potion: p => p.hp += 40,
  mana_potion: p => p.mp += 20, refresh_potion: p => p.st += 30, cure_potion: p => p.hp += 2, bread: p => p.st += 12, dried_meat: p => p.st += 15,
};

// zonas: a vila é segura; as saídas do Flare levam às áreas de caça (PvE, sem PvP)
const ZONES = {
  lochport: { name: 'Porto do Trigo', pve: false },
  lochport_cemetery: { name: 'Cemitério de Porto do Trigo · área de caça', pve: true },
};

const Game = {
  actors: [], now: 0, t0: performance.now(), held: null, hover: null,
  clock() { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); },
  start(cfg) {
    this.zone = ZONES.lochport; this.zoneId = 'lochport';
    this.map = new GameMap(DATA.maps.lochport, this.atlasOf('lochport'));
    this.townMap = this.map;
    this.townCenter = this.findCenter();
    Chat.init(DATA); TCOM.meta = DATA.tcom; Icons.meta = DATA.icons;
    // personagem
    Items.init(DATA); Magic.init(DATA); Mons.init(DATA); Loot.init(DATA);
    const cls = KITS[cfg.cls] || KITS.guerreiro, sexo = cfg.sexo === 'f' ? 'f' : 'm';
    const base = sexo === 'f' ? (cls.f || ['clothes', 'head_long']) : cls.base;
    const [x, y] = this.townCenter;
    const actor = new Actor({ x, y, ap: { sexo, layers: [] }, name: cfg.name, kind: 'me', nameColor: '#6ab0ff', speed: 4.2 });
    this.player = {
      name: cfg.name, guild: null, actor, base, gold: 120, hp: 70, hpMax: 70, mp: 40, mpMax: 40, st: 60, stMax: 60,
      skills: Skills.start(cfg.cls === 'livre' ? cfg.free : cls.skills), equip: {}, bag: [],
      weight() { let w = 0; for (const i of this.bag) w += (i.d.weight || 0) * i.qty; for (const k in this.equip) w += this.equip[k].d.weight || 0; return Math.round(w); },
    };
    for (const id of cls.equip) { const it = this.item(id); if (it) this.player.equip[it.d.slot] = it; }
    cls.bag.forEach(([id, n]) => this.give(id, n || 1));
    this.rebuildLook(); Combat.recompute(); this.player.hp = this.player.hpMax; this.player.mp = this.player.mpMax;
    this.playerSim = { name: cfg.name, online: true, near: true, pers: 'novato' };
    this.actors.push(actor);
    Camera.snap(x, y);
    // interface
    Journal.init(); StatusGump.init(); Backpack.init(); Paperdoll.init(); SkillsGump.init(); Spellbook.init(); Minimap.init(); OnlineGump.init(); HUD.init();
    Minimap.build(this.map);
    Sim.init(DATA, this.map);
    Journal.add('system', '', `Bem-vindo a ${this.townName}, shard Outremer. ${Sim.online().length} jogadores online.`);
    Journal.add('system', '', Touch.on ? 'Joystick para andar, ⚔ para atacar, botões de magia à direita, ✋ para pegar itens. A saída para o cemitério fica ao norte da vila.'
      : 'Segure o clique num monstro para atacar e no chão para andar. Magias nas teclas 1–9. Alt mostra os itens no chão. A saída para o cemitério fica ao norte da vila.');
    this.bindInput(); Touch.init();
    this.last = performance.now(); requestAnimationFrame(t => this.loop(t));
    setInterval(() => { OnlineGump.render(); }, 3000);
  },
  townName: 'Porto do Trigo',
  atlases: {},
  atlasOf(id) { let a = this.atlases[id]; if (!a) { a = new Image(); a.src = DATA.maps[id].atlasFile; this.atlases[id] = a; } return a; },
  // troca de mapa (saídas do Flare); a vila é segura, o resto é PvE
  loadZone(id, at) {
    if (!DATA.maps[id]) { HUD.toast('Caminho fechado por enquanto'); return false; }
    const p = this.player, a = p.actor, z = ZONES[id] || { name: id, pve: true };
    this.map = id === 'lochport' ? this.townMap : new GameMap(DATA.maps[id], this.atlasOf(id));
    this.zone = z; this.zoneId = id;
    if (id === 'lochport') { Sim.enterTown(); } else Sim.leaveTown();
    const [x, y] = at ? this.map.randomFree(Math.random, [at[0] + 0.5, at[1] + 0.5], 1.5) : this.townCenter;
    a.x = x; a.y = y; a.path = null; Camera.snap(x, y);
    this.actors = [a, ...Sim.near().map(s => s.actor)];
    Combat.spawnZone(z); Minimap.build(this.map);
    HUD.toast(z.name); this.exitCooldown = 1.5;
    return true;
  },
  checkExit(dt) {
    this.exitCooldown = (this.exitCooldown || 0) - dt; if (this.exitCooldown > 0) return;
    const a = this.player.actor, i = Math.floor(a.x), j = Math.floor(a.y);
    for (const e of this.map.exits || []) {
      const [x, y, w, h] = e.rect;
      if (i >= x - 1 && i <= x + w && j >= y - 1 && j <= y + h) { if (!this.loadZone(e.to, e.at)) { this.exitCooldown = 2; a.path = null; } return; }
    }
  },
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
      EFEITOS[it.id](p);
      if (/bandage/.test(it.id)) { Skills.use('healing', 0.3); Skills.use('anatomy', 0.2); }
      if (/potion/.test(it.id)) Skills.use('alchemy', 0.1); p.hp = Math.min(p.hpMax, p.hp); p.mp = Math.min(p.mpMax, p.mp); p.st = Math.min(p.stMax, p.st);
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
    this.rebuildLook(); Combat.recompute(); Backpack.render(); Paperdoll.render();
  },
  unequip(slot) {
    const p = this.player, it = p.equip[slot]; if (!it) return;
    delete p.equip[slot]; p.bag.push({ ...it, bx: 10 + Math.random() * 150, by: 10 + Math.random() * 100 });
    this.rebuildLook(); Combat.recompute(); Backpack.render(); Paperdoll.render();
  },
  // camadas = base (cabeça, roupa de baixo) + itens equipados; armadura de tronco esconde a túnica de base
  rebuildLook() {
    const p = this.player, a = p.actor;
    const eq = Object.values(p.equip).map(i => Items.layer(i.d)).filter(Boolean);
    a.hues = {}; for (const i of Object.values(p.equip)) { const l = Items.layer(i.d); if (l && i.hue && Loot.hues[i.hue]) a.hues[l] = Loot.hues[i.hue].hex; }
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
    else if (text.startsWith('/')) { Journal.add('system', '', 'Não precisa de comandos: use os botões.'); return; }
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
    this.pickSim = pick;
    const world = (cx, cy) => Camera.screenToWorld(cx, cy + 30 * Camera.zoom, Render.vw, Render.vh);
    const go = (cx, cy) => {
      const [wx, wy] = Camera.screenToWorld(cx, cy, Render.vw, Render.vh);
      this.hover = [wx, wy];
      const a = this.player.actor;
      if (!a.moveTo(this.map, wx, wy)) {
        for (let k = 1; k <= 6; k++) { const t = k / 7, x = wx + (a.x - wx) * t, y = wy + (a.y - wy) * t; if (!this.map.blocked(Math.floor(x), Math.floor(y)) && a.moveTo(this.map, x, y)) break; }
      }
    };
    // Diablo 2: segurar o clique ataca o monstro sob o cursor ou anda até o cursor
    let lastRepath = 0;
    const press = (cx, cy) => {
      if (this.player.dead) return;
      const lab = Combat.labelAt(cx, cy);
      if (lab) { const a = this.player.actor; a.moveTo(this.map, lab.x, lab.y); this.pickup = lab; return; }
      const [wx, wy] = world(cx, cy), m = Combat.mobAt(wx, wy);
      if (m) { Combat.engage(m); Combat.attacking = true; this.held = null; return; }
      const s = pick(cx, cy);
      if (s && s.sim) { this.inspect(s.sim); return; }
      Combat.attacking = false; Combat.target = null; this.held = [cx, cy]; go(cx, cy);
    };
    cv.addEventListener('pointerdown', e => {
      if (e.pointerType === 'touch') return; // no celular quem manda é o joystick (ui/touch.js)
      document.activeElement && document.activeElement.blur && document.activeElement.blur();
      if (e.button === 2) { this.castAt(Magic.hotbar[0], e.clientX, e.clientY); return; }
      press(e.clientX, e.clientY); cv.setPointerCapture(e.pointerId);
    });
    cv.addEventListener('pointermove', e => {
      if (e.pointerType === 'touch') return;
      this.mouse = [e.clientX, e.clientY];
      const [wx, wy] = world(e.clientX, e.clientY);
      Combat.hover = Combat.mobAt(wx, wy);
      const h = pick(e.clientX, e.clientY); this.hoverActor = h; cv.style.cursor = Combat.hover ? 'crosshair' : h ? 'pointer' : 'default';
      if (this.held) { this.held = [e.clientX, e.clientY]; const n = performance.now(); if (n - lastRepath > 180) { lastRepath = n; go(e.clientX, e.clientY); } }
    });
    const up = e => { if (e && e.pointerType === 'touch') return; this.held = null; Combat.attacking = false; setTimeout(() => { if (!this.held) this.hover = null; }, 600); };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    cv.addEventListener('contextmenu', e => e.preventDefault());
    const setZoom = z => { Camera.zoom = Math.max(0.4, Math.min(1.5, z)); Store.set('zoom', Camera.zoom); };
    this.setZoom = setZoom;
    cv.addEventListener('wheel', e => setZoom(Camera.zoom * (e.deltaY < 0 ? 1.1 : 0.9)), { passive: true });
    addEventListener('keydown', e => {
      const typing = document.activeElement && /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
      if (e.key === 'Alt') { this.altHeld = true; e.preventDefault(); }
      if (e.key === 'Enter' && !typing) { e.preventDefault(); Journal.focus(); return; }
      if (e.key === 'Escape' && typing) { document.activeElement.blur(); return; }
      if (typing) return;
      const k = e.key.toLowerCase(), map = { s: 'status', p: 'paperdoll', b: 'backpack', i: 'backpack', j: 'journal', o: 'online', m: 'minimap', k: 'skills', l: 'spellbook' };
      if (/^[1-9]$/.test(k)) { const id = Magic.hotbar[+k - 1]; if (id) this.castAt(id, ...(this.mouse || [Render.vw / 2, Render.vh / 2])); return; }
      if (k === ' ') { Combat.pickNear(); e.preventDefault(); return; }
      if (k === 'n' && !e.ctrlKey) { Render.toggleNames(); e.preventDefault(); return; }
      if (map[k] && !e.ctrlKey && !e.metaKey) { Gumps.toggle(map[k]); e.preventDefault(); }
    });
    addEventListener('keyup', e => { if (e.key === 'Alt') this.altHeld = false; });
  },
  // lança a magia no que está sob o cursor (monstro, chão) ou em si mesmo
  castAt(id, cx, cy) {
    if (!id || this.player.dead) return;
    const s = Magic.byId[id]; if (!s) return;
    const [wx, wy] = Camera.screenToWorld(cx, cy + 30 * Camera.zoom, Render.vw, Render.vh);
    const m = Combat.mobAt(wx, wy, 2) || Combat.target || Combat.nearest(9);
    Magic.cast(id, m, [wx, wy]);
  },
  inspect(s) {
    // como no UO: clique num jogador mostra o nome e a guilda
    const g = s.guild ? ` — ${s.guild.name} [${s.guild.tag}]` : '';
    Journal.add('system', '', `${s.name}${g}`);
    s.actor.say = { text: s.guild ? `[${s.guild.tag}] ${s.name}` : s.name, until: this.now + 1800, color: s.actor.nameColor };
  },

  loop(t) {
    const dt = Math.min(0.05, Math.max(0, (t - this.last) / 1000)); this.last = t; this.now = t;
    const p = this.player, a = p.actor;
    if (!p.dead) Touch.update(dt);
    for (const x of this.actors) if (x !== a || !p.dead) x.update(dt, this.map);
    Sim.update(dt); Combat.update(dt); this.checkExit(dt);
    if (this.pickup && !a.path) { if (Combat.ground.includes(this.pickup) && Math.hypot(this.pickup.x - a.x, this.pickup.y - a.y) < 1.6) Combat.pick(this.pickup); this.pickup = null; }
    // fôlego cai correndo e volta parado
    p.st = Math.max(0, Math.min(p.stMax, p.st + (a.path ? -0.4 : 2) * dt));
    p.mp = Math.min(p.mpMax, p.mp + (0.5 + (p.skills.meditation || 0) / 40) * dt); // Meditação acelera a mana
    Magic.update(dt);
    Camera.follow(a.x, a.y, dt);
    Render.frame(this.map, this.actors.concat(Combat.mobs), this.hover, t);
    Orbs.update(p);
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
  const atlas = Game.atlasOf('lochport');
  const fonts = document.fonts ? document.fonts.ready : Promise.resolve();
  const saved = Store.get('char', null);
  const el = document.getElementById('create');
  const f = el.querySelector('form');
  f.cls.innerHTML = Object.entries(KITS).map(([k, v]) => `<option value="${k}">${v.nome}</option>`).join('');
  const sk = DATA.skills.skills.map(x => `<option value="${x.id}">${x.name.pt}</option>`).join('');
  f.querySelectorAll('.free select').forEach((s, i) => { s.innerHTML = sk; s.selectedIndex = [0, 4, 26][i]; });
  const kitInfo = () => {
    const k = KITS[f.cls.value], free = f.cls.value === 'livre';
    f.querySelector('.free').style.display = free ? '' : 'none';
    f.querySelector('.kitinfo').textContent = free ? 'Escolha 3 skills: começam em 50, 30 e 20.' :
      Object.entries(k.skills).map(([id, v]) => `${(DATA.skills.skills.find(x => x.id === id) || { name: { pt: id } }).name.pt} ${v}`).join(' · ');
  };
  f.cls.onchange = kitInfo;
  if (saved && KITS[saved.cls]) { f.nome.value = saved.name; f.sexo.value = saved.sexo; f.cls.value = saved.cls; }
  else f.nome.value = rnd(['Tomás', 'Godofredo', 'Balduíno', 'Onofre', 'Raimundo', 'Hugo']) + Math.floor(10 + Math.random() * 89);
  kitInfo();
  f.onsubmit = e => {
    e.preventDefault();
    const fs = [...f.querySelectorAll('.free select')].map(x => x.value), free = {};
    [50, 30, 20].forEach((v, i) => { if (fs[i] && !free[fs[i]]) free[fs[i]] = v; });
    const cfg = { name: f.nome.value.trim().slice(0, 16) || 'Andarilho', sexo: f.sexo.value, cls: f.cls.value, free };
    Store.set('char', cfg);
    el.classList.add('off');
    const go = () => Promise.all([fonts, new Promise(r => atlas.complete ? r() : (atlas.onload = r))]).then(() => Game.start(cfg));
    go();
  };
}
addEventListener('DOMContentLoaded', boot);

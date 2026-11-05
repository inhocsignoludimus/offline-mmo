'use strict';
// =====================================================================
// src/main.js — liga tudo: carrega os dados, cria o personagem, trata a
// entrada (clique para andar, segurar para seguir o cursor) e roda o laço.
// DATA vem embutido pelo build/build.py (funciona em file:// no APK).
// =====================================================================
const ITENS_DEV = {
  espada: { name: 'Espada longa', icon: 'espada_1', layer: 'longsword' },
  maca: { name: 'Maça', icon: 'maca_0', layer: 'mace' },
  machado: { name: 'Machadinha', icon: 'machado', layer: 'hand_axe' },
  faca: { name: 'Adaga', icon: 'faca_0', layer: 'dagger' },
  lanca: { name: 'Lança', icon: 'lanca_0', layer: 'lanca' },
  martelo: { name: 'Martelo', icon: 'martelo', layer: 'martelo' },
  escudoCruz: { name: 'Escudo da cruz', icon: 'escudoCruz', layer: 'escudo_cruz' },
  escudoRedondo: { name: 'Escudo redondo', icon: 'escudoRedondo', layer: 'escudo_redondo' },
  broquel: { name: 'Broquel', icon: 'broquel', layer: 'buckler' },
  elmoNasal: { name: 'Elmo nasal', icon: 'elmoNasal', layer: 'elmo_nasal' },
  turbante: { name: 'Turbante', icon: 'turbante', layer: 'turbante' },
  capuz: { name: 'Capuz de couro', icon: 'capuz', layer: 'leather_hood' },
  loriga: { name: 'Loriga', icon: 'loriga', layer: 'loriga' },
  lamelar: { name: 'Armadura lamelar', icon: 'lamelar', layer: 'lamelar' },
  gambesao: { name: 'Gambesão', icon: 'gambesao', layer: 'gambesao' },
  jaque: { name: 'Jaque de couro', icon: 'jaque', layer: 'jaque_couro' },
  habito: { name: 'Hábito de peregrino', icon: 'habito', layer: 'habito_peregrino' },
  sobrevesteCruzado: { name: 'Sobreveste de cruzado', icon: 'sobreveste', layer: 'armadura_cruzado' },
  sobrevesteTemplario: { name: 'Manto do Templo', icon: 'sobreveste', layer: 'armadura_templario' },
  gibao: { name: 'Gibão de sargento', icon: 'gibao', layer: 'armadura_sargento' },
  lorigao: { name: 'Lorigão', icon: 'cota', layer: 'lorigao' },
  coifa: { name: 'Coifa de malha', icon: 'capelo', layer: 'chain_coif' },
  grevas: { name: 'Grevas de malha', icon: 'cotaSemMangas', layer: 'chain_greaves' },
  botasCano: { name: 'Botas de cano', icon: 'botasCano', layer: 'chain_boots' },
  luvas: { name: 'Luvas de couro', icon: 'luvasCouro', layer: 'leather_gloves' },
  manoplas: { name: 'Manoplas de malha', icon: 'manoplas', layer: 'chain_gloves' },
  botas: { name: 'Botas de couro', icon: 'botasCouro', layer: 'leather_boots' },
  amendoa: { name: 'Amêndoas', icon: 'amendoa_0', food: 1 },
  relicario: { name: 'Relicário', icon: 'relicario' },
  anel: { name: 'Anel de prata', icon: 'anelPrata' },
};
const CLASSES = {
  guerreiro: { nome: 'Guerreiro', m: ['chain_greaves', 'leather_boots', 'gambesao', 'leather_gloves', 'male_head1', 'elmo_nasal', 'longsword', 'buckler'], skills: { Espadas: 50, Táticas: 45, Cura: 30, Anatomia: 25 }, bag: ['loriga', 'escudoRedondo', 'maca'] },
  cruzado: { nome: 'Cruzado', m: ['chain_greaves', 'chain_boots', 'chain_gloves', 'armadura_cruzado', 'male_head2', 'chain_coif', 'longsword', 'escudo_cruz'], skills: { Espadas: 45, Táticas: 40, Cavalgar: 35, Piedade: 30 }, bag: ['elmoNasal', 'relicario'] },
  beduino: { nome: 'Beduíno', m: ['beduino_saia', 'beduino_veste', 'beduino_mangas', 'cloth_sandals', 'male_head1', 'turbante', 'lanca', 'escudo_redondo'], skills: { Lanças: 50, Táticas: 35, Rastrear: 35, Cavalgar: 30 }, bag: ['faca', 'amendoa'] },
  artesao: { nome: 'Artesão', m: ['cloth_pants', 'leather_boots', 'ferreiro_tunica', 'male_head2', 'martelo'], skills: { Ferraria: 55, Mineração: 50, Carpintaria: 30, Comércio: 25 }, bag: ['machado', 'luvas', 'anel'] },
  peregrino: { nome: 'Peregrino', m: ['cloth_pants', 'cloth_sandals', 'habito_peregrino', 'male_head1'], f: ['habito', 'head_long'], skills: { Cura: 50, Magia: 40, Meditação: 40, Piedade: 30 }, bag: ['relicario', 'amendoa'] },
  aldea: { nome: 'Aldeã(o)', m: ['cloth_pants', 'cloth_sandals', 'aldeao_tunica1', 'male_head1', 'dagger'], f: ['aldea_roupa2', 'head_long'], skills: { Culinária: 45, Pesca: 45, Alquimia: 30, Comércio: 30 }, bag: ['faca', 'amendoa', 'capuz'] },
};

const Game = {
  actors: [], now: 0, t0: performance.now(), held: null, hover: null,
  clock() { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); },
  start(cfg) {
    this.map = new GameMap(DATA.map, this.atlas);
    this.townCenter = this.findCenter();
    Chat.init(DATA); TCOM.meta = DATA.tcom; Icons.meta = DATA.icons;
    // personagem
    const cls = CLASSES[cfg.cls] || CLASSES.guerreiro, sexo = cfg.sexo === 'f' ? 'f' : 'm';
    const layers = sexo === 'f' ? (cls.f || ['clothes', 'head_long']) : cls.m;
    const [x, y] = this.townCenter;
    const actor = new Actor({ x, y, ap: { sexo, layers: layers.slice() }, name: cfg.name, kind: 'me', nameColor: '#6ab0ff', speed: 4.2 });
    this.player = {
      name: cfg.name, guild: null, actor, gold: 120, hp: 70, hpMax: 70, mp: 40, mpMax: 40, st: 60, stMax: 60,
      skills: { ...cls.skills }, equip: {}, bag: [],
      weight() { return 8 + this.bag.length * 3 + Object.keys(this.equip).length * 4; },
    };
    // o que já veste vira item equipado no paperdoll
    const byLayer = {}; for (const k in ITENS_DEV) if (ITENS_DEV[k].layer) byLayer[ITENS_DEV[k].layer] = k;
    for (const l of layers) if (byLayer[l]) this.player.equip[TCOM.slot[l]] = this.item(byLayer[l]);
    cls.bag.forEach(k => this.give(k));
    this.give('amendoa'); this.player.bag.find(i => i.icon === 'amendoa_0').qty = 5;
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
  item(k) { const d = ITENS_DEV[k]; return { k, ...d, qty: 1, bx: 6 + Math.random() * 170, by: 6 + Math.random() * 120 }; },
  give(k) { const it = this.item(k); const same = it.food && this.player.bag.find(i => i.k === k); if (same) same.qty++; else this.player.bag.push(it); },
  useItem(it) {
    const p = this.player;
    if (it.food) { it.qty--; if (it.qty <= 0) p.bag.splice(p.bag.indexOf(it), 1); p.st = Math.min(p.stMax, p.st + 10); Journal.add('system', '', `Você come ${it.name.toLowerCase()}.`); Backpack.render(); return; }
    if (!it.layer) { Journal.add('system', '', it.name); return; }
    const slot = TCOM.slot[it.layer];
    const old = p.equip[slot];
    p.bag.splice(p.bag.indexOf(it), 1);
    if (old) p.bag.push({ ...old, bx: it.bx, by: it.by });
    p.equip[slot] = it;
    this.rebuildLook();
    Backpack.render(); Paperdoll.render();
  },
  unequip(slot) {
    const p = this.player, it = p.equip[slot]; if (!it) return;
    delete p.equip[slot]; p.bag.push({ ...it, bx: 10 + Math.random() * 150, by: 10 + Math.random() * 100 });
    this.rebuildLook(); Backpack.render(); Paperdoll.render();
  },
  rebuildLook() {
    const a = this.player.actor, p = this.player;
    // mantém o que não é item (cabeça, roupa de baixo) e troca o resto pelo equipado
    const itemLayers = new Set(Object.values(ITENS_DEV).map(i => i.layer).filter(Boolean));
    const base = a.ap.layers.filter(l => !itemLayers.has(l));
    const eq = Object.values(p.equip).map(i => i.layer);
    // armadura de tronco esconde a túnica de baixo
    const hasChest = eq.some(l => TCOM.slot[l] === 'tronco');
    a.ap.layers = base.filter(l => !(hasChest && TCOM.slot[l] === 'tronco')).concat(eq);
    if (!hasChest && !a.ap.layers.some(l => TCOM.slot[l] === 'tronco')) a.ap.layers.push(a.ap.sexo === 'f' ? 'clothes' : 'aldeao_tunica1');
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

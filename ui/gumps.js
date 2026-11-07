'use strict';
// =====================================================================
// ui/gumps.js — janelas arrastáveis no estilo do UO ("gumps"):
// status, mochila, paperdoll, diário/chat, minimapa, jogadores online.
// Posição e quais estão abertas ficam guardadas no navegador.
// =====================================================================
const Store = {
  get(k, d) { try { const v = localStorage.getItem('omm.' + k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('omm.' + k, JSON.stringify(v)); } catch (e) { } },
};

const Gumps = {
  all: {}, z: 10, layout: Store.get('gumps', {}),
  create(id, title, opts = {}) {
    const el = document.createElement('div');
    el.className = 'gump ' + (opts.cls || ''); el.id = 'g-' + id;
    el.innerHTML = `<div class="gbar"><span class="gtitle">${title}</span><button class="gx" title="Fechar">×</button></div><div class="gbody"></div>`;
    document.getElementById('ui').appendChild(el);
    const L = this.layout[id] || {};
    const compact = innerWidth < 900 || innerHeight < 520;
    const pos = (compact && opts.posCompact) || opts.pos || [40, 40];
    el.style.left = (L.x ?? this.resolveX(pos[0], opts.w)) + 'px';
    el.style.top = (L.y ?? this.resolveY(pos[1], opts.h)) + 'px';
    if (opts.w) el.style.width = opts.w + 'px';
    if (opts.h) el.style.height = opts.h + 'px';
    const open = L.open ?? (compact ? opts.openCompact ?? opts.open : opts.open) ?? false;
    el.style.display = open ? '' : 'none';
    const g = { id, el, body: el.querySelector('.gbody'), onOpen: opts.onOpen };
    this.all[id] = g;
    el.querySelector('.gx').onclick = e => { e.stopPropagation(); this.toggle(id, false); };
    el.addEventListener('pointerdown', () => this.front(id));
    this.drag(el, el.querySelector('.gbar'), id);
    return g;
  },
  resolveX(x, w = 260) { return x < 0 ? innerWidth + x - w : x; },
  resolveY(y, h = 200) { return y < 0 ? innerHeight + y - h : y; },
  front(id) { this.all[id].el.style.zIndex = ++this.z; },
  isOpen(id) { return this.all[id] && this.all[id].el.style.display !== 'none'; },
  toggle(id, force) {
    const g = this.all[id]; if (!g) return;
    const open = force ?? !this.isOpen(id);
    g.el.style.display = open ? '' : 'none';
    if (open) { this.front(id); this.clamp(g.el); g.onOpen && g.onOpen(); }
    this.save(id);
  },
  clamp(el) {
    const r = el.getBoundingClientRect();
    el.style.left = Math.max(0, Math.min(innerWidth - Math.min(r.width, 120), r.left)) + 'px';
    el.style.top = Math.max(0, Math.min(innerHeight - 30, r.top)) + 'px';
  },
  save(id) {
    const el = this.all[id].el;
    this.layout[id] = { x: parseInt(el.style.left), y: parseInt(el.style.top), open: el.style.display !== 'none' };
    Store.set('gumps', this.layout);
  },
  drag(el, handle, id) {
    let sx, sy, ox, oy, on = false;
    handle.addEventListener('pointerdown', e => {
      if (e.target.closest('button')) return;
      on = true; sx = e.clientX; sy = e.clientY; ox = el.offsetLeft; oy = el.offsetTop; handle.setPointerCapture(e.pointerId); e.preventDefault();
    });
    handle.addEventListener('pointermove', e => {
      if (!on) return;
      el.style.left = Math.max(-el.offsetWidth + 60, Math.min(innerWidth - 60, ox + e.clientX - sx)) + 'px';
      el.style.top = Math.max(0, Math.min(innerHeight - 24, oy + e.clientY - sy)) + 'px';
    });
    const end = () => { if (on) { on = false; this.save(id); } };
    handle.addEventListener('pointerup', end); handle.addEventListener('pointercancel', end);
  },
};

// ---------------------------------------------------------------------
// Diário / chat
// ---------------------------------------------------------------------
const CANAIS = {
  local: { nome: 'Local', cor: '#e8e2cf' },
  global: { nome: 'Global', cor: '#f0c060' },
  guild: { nome: 'Guilda', cor: '#7fe08a' },
  party: { nome: 'Grupo', cor: '#7fd0ff' },
  whisper: { nome: 'Sussurro', cor: '#e48ae0' },
  system: { nome: 'Sistema', cor: '#b0a890' },
};

const Journal = {
  g: null, log: [], filter: 'all', max: 300, unread: 0,
  init() {
    this.g = Gumps.create('journal', 'Diário', { pos: [12, -12], posCompact: [6, -6], w: 380, h: 230, open: true, openCompact: false, cls: 'journal', onOpen: () => { this.unread = 0; HUD.badge(); } });
    const b = this.g.body;
    b.innerHTML = `<div class="tabs">${['all', 'local', 'global', 'guild', 'whisper'].map(k => `<button data-f="${k}" class="${k === 'all' ? 'on' : ''}">${k === 'all' ? 'Tudo' : CANAIS[k].nome}</button>`).join('')}</div>
      <div class="jlog"></div>
      <form class="jform"><select class="jch"><option value="local">Local</option><option value="global">Global</option><option value="guild">Guilda</option><option value="party">Grupo</option></select><input class="jin" maxlength="120" placeholder="Digite e Enter… (/w Nome msg)" autocomplete="off"></form>`;
    b.querySelectorAll('.tabs button').forEach(bt => bt.onclick = () => { this.filter = bt.dataset.f; b.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === bt)); this.redraw(); });
    this.logEl = b.querySelector('.jlog'); this.input = b.querySelector('.jin'); this.chSel = b.querySelector('.jch');
    b.querySelector('.jform').onsubmit = e => { e.preventDefault(); const t = this.input.value.trim(); this.input.value = ''; if (t) Game.playerSays(t, this.chSel.value); this.input.blur(); };
  },
  add(ch, from, text, opts = {}) {
    const e = { ch, from, text, t: Game.clock(), me: opts.me };
    this.log.push(e); if (this.log.length > this.max) this.log.shift();
    if (this.pass(e)) this.append(e);
    if (!Gumps.isOpen('journal') && ch !== 'local' && ch !== 'system') { this.unread++; HUD.badge(); }
  },
  pass(e) { return this.filter === 'all' || e.ch === this.filter || e.ch === 'system'; },
  line(e) {
    const c = CANAIS[e.ch] || CANAIS.local, d = document.createElement('div');
    d.className = 'jl'; d.style.color = c.cor;
    const pre = e.ch === 'local' || e.ch === 'system' ? '' : `[${c.nome}] `;
    d.textContent = e.from ? `${pre}${e.from}: ${e.text}` : `${pre}${e.text}`;
    if (e.from && !e.me) { d.dataset.who = e.from; d.title = 'Clique para sussurrar'; }
    d.onclick = () => { if (d.dataset.who) { this.input.value = `/w ${e.from.split(' [')[0]} `; this.input.focus(); } };
    return d;
  },
  append(e) {
    const el = this.logEl, stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 8;
    el.appendChild(this.line(e)); while (el.children.length > this.max) el.firstChild.remove();
    if (stick) el.scrollTop = el.scrollHeight;
  },
  redraw() { this.logEl.innerHTML = ''; for (const e of this.log) if (this.pass(e)) this.logEl.appendChild(this.line(e)); this.logEl.scrollTop = this.logEl.scrollHeight; },
  focus() { Gumps.toggle('journal', true); this.input.focus(); },
};

// ---------------------------------------------------------------------
// Status (barras de vida, mana e fôlego)
// ---------------------------------------------------------------------
const StatusGump = {
  init() {
    this.g = Gumps.create('status', 'Status', { pos: [12, 12], posCompact: [6, 6], w: 210, open: true, cls: 'status' });
    this.g.body.innerHTML = `<div class="sname"></div><div class="sguild"></div>
      ${['hp', 'mp', 'st'].map(k => `<div class="bar ${k}"><i></i><span></span></div>`).join('')}
      <div class="srow"><span>Ouro <b class="sgold">0</b></span><span>Peso <b class="sw">0</b></span></div>`;
  },
  update(p) {
    const b = this.g.body;
    b.querySelector('.sname').textContent = p.name;
    const sg = b.querySelector('.sguild'), gtxt = p.guild ? `${p.guild.name} [${p.guild.tag}]` : 'Sem guilda';
    if (sg.dataset.t !== gtxt) { sg.dataset.t = gtxt; sg.innerHTML = gtxt + (p.guild ? ' <button class="gleave">sair</button>' : ''); const bt = sg.querySelector('.gleave'); if (bt) bt.onclick = () => Prompt.ask(`Sair da guilda ${p.guild.name}?`, [['Sair', () => Sim.leave()], ['Ficar', () => {}]]); }
    for (const [k, v, m] of [['hp', p.hp, p.hpMax], ['mp', p.mp, p.mpMax], ['st', p.st, p.stMax]]) {
      const el = b.querySelector('.bar.' + k); el.querySelector('i').style.width = (100 * v / m) + '%'; el.querySelector('span').textContent = `${Math.round(v)} / ${m}`;
    }
    b.querySelector('.sgold').textContent = p.gold; b.querySelector('.sw').textContent = p.weight();
    const bf = b.querySelector('.sbuffs') || b.appendChild(Object.assign(document.createElement('div'), { className: 'sbuffs' }));
    bf.textContent = Magic.buffs.map(x => `${x.name} ${Math.ceil((x.until - Game.now) / 1000)}s`).join(' · ');
  },
};

// ---------------------------------------------------------------------
// Ícones dos itens (folha do TCoM)
// ---------------------------------------------------------------------
const COR_TIPO = { consumable: '#7a3030', resource: '#5a4a2a', tool: '#3a4a5a', furniture: '#5a3a1a', deed: '#6a5a2a', jewelry: '#5a4a6a', misc: '#444' };
const Icons = {
  // quadrado com as iniciais, para os itens que ainda não têm ícone desenhado
  fallback(it, size) {
    const n = it.name.split(/\s+/).filter(w => w.length > 2).map(w => w[0]).join('').slice(0, 2).toUpperCase() || it.name.slice(0, 2);
    return { style: `background:${COR_TIPO[it.d.type] || '#444'};border:1px solid #000;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.15);display:flex;align-items:center;justify-content:center;font:700 ${Math.round(size * 0.36)}px 'Alegreya SC',serif;color:#f0e0c0`, label: n };
  },
  style(it, size) { const c = this.css(it.icon, size); return c ? { style: c, label: '' } : this.fallback(it, size); },
  img: null, meta: null,
  // ícone da folha do TCoM; sem ícone na folha, devolve '' e quem chama usa fallback()
  css(key, size) {
    const m = this.meta && this.meta.mapa[key]; if (!m) return '';
    const s = size / this.meta.tam;
    const sw = (this.meta.w || 1024), sh = (this.meta.h || 896);
    return `background-image:url(engine/dev_assets/tcom/icons.webp);background-size:${sw * s}px ${sh * s}px;background-position:-${m[0] * size}px -${m[1] * size}px`;
  },
};

// ---------------------------------------------------------------------
// Mochila: itens soltos, arrastáveis dentro da bolsa (como no UO)
// ---------------------------------------------------------------------
const Backpack = {
  init() {
    this.g = Gumps.create('backpack', 'Mochila', { pos: [-12, 220], posCompact: [-6, 60], w: 250, h: 210, cls: 'backpack', open: false, onOpen: () => this.render() });
  },
  render() {
    const p = Game.player, b = this.g.body; b.innerHTML = '';
    for (const it of p.bag) {
      const d = document.createElement('div'); d.className = 'bitem';
      const ic = Icons.style(it, 44);
      d.style.cssText = ic.style + `;left:${it.bx}px;top:${it.by}px`;
      d.onmouseenter = () => Tip.show(d, Loot.lines(it)); d.onmouseleave = () => Tip.hide();
      if (it.rarity && it.rarity !== 'comum') d.style.boxShadow = `0 0 0 1px ${Loot.color(it)}, 0 0 8px ${Loot.color(it)}`;
      d.innerHTML = ic.label + (it.qty > 1 ? `<b>${it.qty}</b>` : '');
      let sx, sy, ox, oy, moved = false;
      d.onpointerdown = e => { e.stopPropagation(); sx = e.clientX; sy = e.clientY; ox = it.bx; oy = it.by; moved = false; d.setPointerCapture(e.pointerId); };
      d.onpointermove = e => { if (sx === undefined) return; const dx = e.clientX - sx, dy = e.clientY - sy; if (Math.abs(dx) + Math.abs(dy) > 4) moved = true; it.bx = Math.max(0, Math.min(b.clientWidth - 44, ox + dx)); it.by = Math.max(0, Math.min(b.clientHeight - 44, oy + dy)); d.style.left = it.bx + 'px'; d.style.top = it.by + 'px'; };
      d.onpointerup = () => { sx = undefined; if (!moved) Game.useItem(it); };
      b.appendChild(d);
    }
    if (!p.bag.length) b.innerHTML = '<p class="empty">Vazia</p>';
  },
};

// ---------------------------------------------------------------------
// Paperdoll: o boneco grande com os espaços equipados
// ---------------------------------------------------------------------
const Paperdoll = {
  init() {
    this.g = Gumps.create('paperdoll', 'Paperdoll', { pos: [240, 12], posCompact: [6, 6], w: 340, h: 360, cls: 'paperdoll', open: false, onOpen: () => this.render() });
    this.g.body.innerHTML = `<canvas width="150" height="240"></canvas><div class="pslots"></div><div class="pinfo"></div>`;
    this.cv = this.g.body.querySelector('canvas'); this.t = 0;
  },
  render() {
    this.dirty = true;
    const p = Game.player, s = this.g.body.querySelector('.pslots');
    s.innerHTML = '';
    for (const [slot, nome] of [['head', 'Cabeça'], ['neck', 'Pescoço'], ['torso', 'Tronco'], ['cloak', 'Manto'], ['arms', 'Braços'], ['hands', 'Mãos'], ['legs', 'Pernas'], ['feet', 'Pés'], ['hand1', 'Arma'], ['hand2', 'Escudo'], ['ring', 'Anel']]) {
      const it = p.equip[slot], d = document.createElement('div'); d.className = 'pslot';
      const ic = it ? Icons.style(it, 22) : { style: '', label: '' };
      d.innerHTML = `<i style="${ic.style}">${ic.label}</i><span>${it ? it.name : '<em>' + nome + '</em>'}</span>`;
      if (it) { d.onclick = () => { Tip.hide(); Game.unequip(slot); }; d.onmouseenter = () => Tip.show(d, Loot.lines(it) + '<br><i>clique para tirar</i>'); d.onmouseleave = () => Tip.hide(); d.querySelector('span').style.color = Loot.color(it); }
      s.appendChild(d);
    }
    const sk = p.skills;
    this.g.body.querySelector('.pinfo').innerHTML = `<b>${p.name}</b>${p.guild ? ` <span>[${p.guild.tag}]</span>` : ''}<br>${Object.entries(sk).filter(e => e[1] > 0).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([k, v]) => `${Chat.skills[k] || k} ${v.toFixed(1)}`).join('<br>')}`;
  },
  // o próprio boneco do jogo, ampliado: mostra exatamente as armas, armaduras e cores equipadas
  tick(dt) {
    if (!Gumps.isOpen('paperdoll')) return;
    this.t = (this.t || 0) + dt;
    const g = this.cv.getContext('2d'); g.clearRect(0, 0, 150, 240); g.imageSmoothingEnabled = true;
    const a = Game.player.actor, keep = [a.dir, a.anim, a.t];
    a.dir = 7; a.anim = 'stance'; a.t = this.t;
    g.save(); g.translate(75, 205); g.scale(2.3, 2.3); a.draw(g, 0, 0); g.restore();
    [a.dir, a.anim, a.t] = keep;
  },
};

// ---------------------------------------------------------------------
// Minimapa
// ---------------------------------------------------------------------
const Minimap = {
  init() {
    this.g = Gumps.create('minimap', 'Mapa', { pos: [-12, 12], posCompact: [-6, 6], w: 196, h: 196, cls: 'minimap', open: true, openCompact: false });
    this.g.body.innerHTML = '<canvas width="180" height="160"></canvas>';
    this.cv = this.g.body.querySelector('canvas');
  },
  build(map) {
    const c = document.createElement('canvas'); c.width = map.w + map.h; c.height = (map.w + map.h) / 2 + 2;
    const g = c.getContext('2d'), col = { 0: '#5d6b3a', 1: '#3a3a3a', 2: '#2d4f73', 3: '#22301c', 4: '#444' };
    for (let j = 0; j < map.h; j++) for (let i = 0; i < map.w; i++) {
      if (!map.bg[j][i]) continue;
      g.fillStyle = col[map.col[j][i]] || '#555';
      if (map.obj[j][i] && map.col[j][i] === 1) g.fillStyle = '#8a6a4a';
      g.fillRect(i - j + map.h, (i + j) / 2, 2, 1.2);
    }
    this.base = c;
  },
  tick(map, actors, player) {
    if (!Gumps.isOpen('minimap') || !this.base) return;
    const g = this.cv.getContext('2d'), W = this.cv.width, H = this.cv.height, k = 2.2;
    const px = (player.x - player.y + map.h), py = (player.x + player.y) / 2;
    g.fillStyle = '#0b0d10'; g.fillRect(0, 0, W, H);
    g.save(); g.translate(W / 2, H / 2); g.scale(k, k); g.translate(-px, -py);
    g.imageSmoothingEnabled = false; g.drawImage(this.base, 0, 0);
    for (const a of actors) {
      g.fillStyle = a === player ? '#fff' : a.kind === 'sim' ? (a.sim && a.sim.guild && a.sim.guild.align === 'caos' ? '#ff6a5a' : '#6ab0ff') : '#ffcc55';
      g.fillRect(a.x - a.y + map.h - 0.8, (a.x + a.y) / 2 - 0.8, 1.6, 1.6);
    }
    g.restore();
  },
};

// ---------------------------------------------------------------------
// Jogadores online e guildas
// ---------------------------------------------------------------------
const OnlineGump = {
  init() {
    this.g = Gumps.create('online', 'Jogadores', { pos: [-220, 220], posCompact: [-6, 60], w: 240, h: 260, cls: 'online', open: false, onOpen: () => this.render() });
  },
  render() {
    if (!Gumps.isOpen('online')) return;
    const on = Sim.online(), b = this.g.body;
    const wars = Sim.wars.map(w => `<div class="war">⚔ [${w.a.tag}] × [${w.b.tag}]</div>`).join('');
    b.innerHTML = `<div class="ohead">${on.length} online · shard Outremer</div>${wars}` +
      on.slice().sort((a, b) => (b.near - a.near) || a.name.localeCompare(b.name)).map(s =>
        `<div class="orow ${s.near ? 'near' : ''}" data-n="${s.name}"><span>${s.name}</span>${s.guild ? `<i class="${s.guild.align}">${s.guild.tag}</i>` : ''}<em>${s.near ? 'aqui' : s.where}</em></div>`).join('');
    b.querySelectorAll('.orow').forEach(r => r.onclick = () => { Journal.focus(); Journal.input.value = `/w ${r.dataset.n} `; });
  },
};

// ---------------------------------------------------------------------
// Barra de botões (abre/fecha janelas) e avisos curtos
// ---------------------------------------------------------------------
const HUD = {
  init() {
    const bar = document.createElement('div'); bar.id = 'menubar';
    bar.innerHTML = [['status', 'Status', 'S'], ['paperdoll', 'Paperdoll', 'P'], ['backpack', 'Mochila', 'B'], ['skills', 'Skills', 'K'], ['spellbook', 'Magias', 'L'], ['journal', 'Diário', 'J'], ['online', 'Online', 'O'], ['minimap', 'Mapa', 'M']]
      .map(([id, n, k]) => `<button data-g="${id}" title="${n} (${k})">${n}${id === 'journal' ? '<b class="badge"></b>' : ''}</button>`).join('') + '<button data-act="names" title="Mostrar nomes (N)">Nomes</button><button data-act="chat" class="chatbtn" title="Falar (Enter)">Falar</button>';
    document.getElementById('ui').appendChild(bar);
    bar.querySelectorAll('button[data-g]').forEach(b => b.onclick = () => Gumps.toggle(b.dataset.g));
    bar.querySelector('[data-act=chat]').onclick = () => Journal.focus();
    bar.querySelector('[data-act=names]').onclick = () => Render.toggleNames();
    this.toastEl = document.createElement('div'); this.toastEl.id = 'toast'; document.getElementById('ui').appendChild(this.toastEl);
  },
  badge() { const b = document.querySelector('#menubar .badge'); if (b) b.textContent = Journal.unread ? (Journal.unread > 99 ? '99+' : Journal.unread) : ''; },
  toast(t) { this.toastEl.textContent = t; this.toastEl.classList.add('on'); clearTimeout(this._t); this._t = setTimeout(() => this.toastEl.classList.remove('on'), 2600); },
};

// dica flutuante dos itens (nome na cor da faixa, afixos, conjunto, lore)
const Tip = {
  show(el, html) { const t = document.getElementById('tip'); t.innerHTML = html; t.style.display = 'block'; const r = el.getBoundingClientRect(); t.style.left = Math.min(innerWidth - t.offsetWidth - 6, r.right + 6) + 'px'; t.style.top = Math.max(6, Math.min(innerHeight - t.offsetHeight - 6, r.top)) + 'px'; },
  hide() { document.getElementById('tip').style.display = 'none'; },
};

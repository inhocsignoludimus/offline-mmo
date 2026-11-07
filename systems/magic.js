'use strict';
// =====================================================================
// systems/magic.js — livro de magias, barra de atalhos, lançamento com alvo,
// efeitos e ganho de skill. Regras: docs/SKILLS_MAGIA.md (versão casual do UO).
// Dados: data/magic/spells.json e reagents.json (Ludimus).
// Sem combate ainda: dano e debuff em outros jogadores só têm o efeito visual
// e a reação deles; invocação espera os monstros.
// =====================================================================
const CIRCULO_MIN = [0, 0, 10, 20, 30, 45, 60, 75, 90]; // índice = círculo
const COR_ELEM = { fire: '#ff8a3a', energy: '#9ad0ff', physical: '#e0d0b0', poison: '#7ee05a', cold: '#a0e8ff' };
const COR_TIPO_FX = { heal: '#ffe680', buff: '#c0a0ff', debuff: '#b060d0', teleport: '#80c0ff', field: '#ff9a50', summon: '#b0b0b0', create_item: '#ffd890', reveal: '#ffffff', damage: '#ff6040' };

const FX_CEU = new Set(['storm_nail', 'nail_chain']);
const FX_CAMPO = { fire: 'blast', poison: 'dark_mist', energy: 'lightning', paralyze: 'status_freeze', wall: 'spikes', dispel: 'sparkle' };

const Magic = {
  byId: {}, list: [], casting: null, targeting: null, buffs: [], fx: [], hotbar: Store.get('hotbar', []),
  init(data) {
    this.list = data.spells.spells; for (const s of this.list) this.byId[s.id] = s;
    for (const r of data.reagents.reagents) Items.byId[r.id] = r; // reagentes são itens
  },
  name(s) { return s.name[Chat.lang] || s.name.pt; },
  min(s) { return CIRCULO_MIN[s.circle]; },
  // chance de sucesso: 50% no mínimo do círculo, sem falha 20 pontos acima
  chance(s) { const v = Game.player.skills.magery || 0; return Math.max(0, Math.min(1, 0.5 + (v - this.min(s)) / 40)); },
  open(s) { return (Game.player.skills.magery || 0) >= this.min(s) || s.circle === 1; },
  hasReagents(s) {
    const bag = Game.player.bag;
    return Object.entries(s.reagents || {}).every(([id, n]) => { const it = bag.find(i => i.id === id); return it && it.qty >= n; });
  },
  useReagents(s) {
    const bag = Game.player.bag;
    for (const [id, n] of Object.entries(s.reagents || {})) { const it = bag.find(i => i.id === id); it.qty -= n; if (it.qty <= 0) bag.splice(bag.indexOf(it), 1); }
  },
  roll(s) {
    const [a, b] = s.effect.base || [0, 0], v = Game.player.skills.magery || 0, ev = Game.player.skills.evaluating_intelligence || 0;
    return Math.round((a + Math.random() * (b - a)) * (0.8 + v / 250 + ev / 400));
  },

  // ---------------------------------------------------------------
  // estilo Diablo: sem palavras e sem modo de mira; o alvo vem do cursor (ou do mais próximo)
  cast(id, mob, at) {
    const s = this.byId[id], p = Game.player; if (!s) return;
    if (this.casting || p.dead) return;
    if (!this.open(s)) { HUD.toast(`Precisa de Magia ${this.min(s)}`); return; }
    if (p.mp < s.mana) { Journal.add('system', '', 'Mana insuficiente.'); return; }
    if (!this.hasReagents(s)) { Journal.add('system', '', `Faltam reagentes: ${Object.keys(s.reagents).map(r => Items.name(Items.byId[r])).join(', ')}.`); return; }
    const a = p.actor;
    a.path = null; a.setAnim('swing'); FX.play('channel', a.x, a.y, { follow: a, life: 0.35 });
    const hostile = s.effect.type === 'damage' || s.effect.type === 'debuff';
    if (hostile && !mob) { HUD.toast('Nenhum monstro por perto'); return; }
    if (mob) a.dir = direcaoDoAngulo(Math.atan2(mob.y - a.y, mob.x - a.x));
    this.casting = { s, mob, at, until: Game.now + 200 + s.circle * 60 };
  },
  update(dt) {
    const p = Game.player;
    if (this.casting && Game.now >= this.casting.until) {
      const { s, mob, at } = this.casting; this.casting = null;
      const t = s.effect.type, P = p.actor;
      if (t === 'damage' || t === 'debuff') this.resolve(s, mob, [mob.x, mob.y]);
      else if (t === 'teleport') { const ang = DIRECOES.length && (P.dir - 6) * Math.PI / 4; const tgt = at && !Touch.on ? at : [P.x + Math.cos(ang) * 5, P.y + Math.sin(ang) * 5]; this.resolve(s, null, tgt); }
      else if (t === 'field') this.resolve(s, null, mob ? [mob.x, mob.y] : at || [P.x, P.y]);
      else this.resolve(s, P, [P.x, P.y]);
    }
    // buffs com duração
    for (const b of this.buffs.slice()) if (Game.now > b.until) { this.buffs.splice(this.buffs.indexOf(b), 1); b.end && b.end(); Journal.add('system', '', `${b.name} acabou.`); }
    for (const f of this.fx) { f.t += dt;
      if (f.kind === 'field' && f.spr) { f.st = (f.st || 0) - dt; if (f.st <= 0) { f.st = 0.22; const a = Math.random() * 6.28, r = Math.sqrt(Math.random()) * f.r; FX.play(f.spr, f.x + Math.cos(a) * r, f.y + Math.sin(a) * r * 0.9, { scale: f.spr === 'blast' ? 0.2 : 0.6, life: f.spr === 'blast' ? undefined : 0.9 }); } }
      if (f.kind === 'field' && f.stop) for (const m of Combat.mobs) if (!m.dead && Math.hypot(m.x - f.x, m.y - f.y) < f.r) m.stun = Game.now + 300;
      if (f.kind === 'field' && f.dps) { f.tick = (f.tick || 0) - dt; if (f.tick <= 0) { f.tick = 1; for (const m of Combat.mobs) if (!m.dead && Math.hypot(m.x - f.x, m.y - f.y) < f.r) Combat.damageMob(m, Math.round(f.dps), false, f.col); } } }
    this.fx = this.fx.filter(f => f.t < f.life);
  },
  // clique no mundo enquanto mira; devolve true se usou o clique
  click(actor, wx, wy) {
    const s = this.targeting; if (!s) return false;
    this.targeting = null; document.body.classList.remove('targeting');
    if (s.target === 'mobile' && !actor) { Journal.add('system', '', 'Alvo inválido.'); return true; }
    const P = Game.player.actor, tx = actor ? actor.x : wx, ty = actor ? actor.y : wy;
    if (Math.hypot(tx - P.x, ty - P.y) > 12) { Journal.add('system', '', 'Longe demais.'); return true; }
    this.resolve(s, actor, [tx, ty]);
    return true;
  },
  cancel() { if (this.targeting) { this.targeting = null; document.body.classList.remove('targeting'); Journal.add('system', '', 'Magia cancelada.'); } },

  resolve(s, actor, at) {
    const p = Game.player, e = s.effect;
    const ok = Math.random() < this.chance(s);
    Skills.use('magery', Math.min(1, 0.3 + s.circle * 0.08)); // treina tentando, como no UO
    if (!ok) { p.mp -= Math.ceil(s.mana / 2); Journal.add('system', '', 'A magia falhou.'); FX.play('spark_blue', p.actor.x, p.actor.y) || this.burst(p.actor.x, p.actor.y, '#666', 0.6); return; }
    p.mp -= s.mana; this.useReagents(s);
    if (Math.random() < 0.5) Skills.use('evaluating_intelligence', 0.3);
    const col = COR_ELEM[e.element] || COR_TIPO_FX[e.type] || '#fff';
    const me = !actor || actor === p.actor, sim = actor && actor.sim;
    switch (e.type) {
      case 'heal': {
        const n = this.roll(s);
        FX.play('heal', (actor || p.actor).x, (actor || p.actor).y, { follow: actor || p.actor });
        if (e.radius) for (const x of [p.actor]) FX.play('heal', x.x, x.y, { follow: x });
        if (me) { p.hp = Math.min(p.hpMax, p.hp + n); Journal.add('system', '', `Você recupera ${n} de vida.`); }
        else if (sim && chance(0.6)) setTimeout(() => Sim.say(sim, 'thanks', { target: p.name }, 'local'), 900);
        break;
      }
      case 'damage': {
        const n = this.roll(s), el = e.element || 'physical', R = e.radius || 0;
        const hurt = (m, k = 1) => !m.dead && Combat.damageMob(m, Math.max(1, Math.round(n * k * (1 - ((m.def.resist || {})[el] || 0) / 100))), false, col);
        const area = (x, y, r) => { for (const m of Combat.mobs) if (!m.dead && Math.hypot(m.x - x, m.y - y) <= r + 0.3) hurt(m, m === actor ? 1 : 0.75); };
        const tx = actor ? actor.x : at[0], ty = actor ? actor.y : at[1];
        if (s.id === 'falling_stars') {   // chuva de fogo em volta do alvo
          for (let i = 0; i < 8; i++) { const a = Math.random() * 6.28, r = Math.random() * R; FX.play('blast', tx + Math.cos(a) * r, ty + Math.sin(a) * r, { delay: i * 0.15, scale: 0.4 }); }
          setTimeout(() => area(tx, ty, R), 600); break;
        }
        if (s.id === 'split_ground') { FX.play('quake', tx, ty, { scale: 1.7 }); FX.play('rupture', tx, ty); setTimeout(() => area(tx, ty, R), 250); break; }
        if (FX_CEU.has(s.id)) {          // raio que cai do céu, e pula de monstro em monstro
          FX.play('thunderstrike', tx, ty); if (actor) setTimeout(() => hurt(actor), 150);
          let last = actor; const done = new Set([actor]);
          for (let c = 0; c < (e.chains || 0) && last; c++) {
            const nx = Combat.mobs.filter(m => !m.dead && !done.has(m) && Math.hypot(m.x - last.x, m.y - last.y) < 5).sort((a, b) => Math.hypot(a.x - last.x, a.y - last.y) - Math.hypot(b.x - last.x, b.y - last.y))[0];
            if (!nx) break; done.add(nx); last = nx;
            FX.play('thunderstrike', nx.x, nx.y, { delay: (c + 1) * 0.2 }); setTimeout(() => hurt(nx, 0.7), (c + 1) * 200 + 150);
          }
          break;
        }
        if (actor && actor.kind === 'mob') {
          const m = actor;
          Combat.projectile(p.actor, m, col, () => {
            FX.play(R ? FX_AREA[el] : FX_HIT[el], m.x, m.y, { scale: R ? (el === 'fire' ? 0.35 + R * 0.12 : 0.6 + R * 0.3) : 1, dir: direcaoDoAngulo(Math.atan2(m.y - p.actor.y, m.x - p.actor.x)) });
            if (R) area(m.x, m.y, R); else hurt(m);
          }, FX_PROJ[el]);
        }
        break;
      }
      case 'buff': case 'debuff': {
        const n = this.roll(s), dur = (e.duration || 60) * 1000;
        if (me || e.type === 'buff' && !actor) { this.addBuff(s, n, dur); if (e.type === 'buff') FX.play(e.stat === 'invisible' ? 'immunity' : (e.stats || []).some(x => /res_/.test(x)) ? 'shield_orange' : 'shield', p.actor.x, p.actor.y, { follow: p.actor, life: 1.4 }); }
        else if (actor && actor.kind === 'mob' && e.type === 'debuff' && e.stat === 'paralyze') { actor.stun = Game.now + Math.min(8000, dur); FX.play('status_freeze', actor.x, actor.y, { follow: actor, life: Math.min(8, dur / 1000) }); }
        else if (actor && actor.kind === 'mob' && e.type === 'debuff') { FX.play('dark_mist', actor.x, actor.y, { follow: actor, scale: 0.7 }); actor.speed *= 0.6; actor.cd += 1.5; Combat.float(actor, this.name(s), col); setTimeout(() => { actor.speed /= 0.6; }, dur); }
        break;
      }
      case 'teleport': {
        const [x, y] = at;
        if (Game.map.blocked(Math.floor(x), Math.floor(y))) { Journal.add('system', '', 'Não dá para ir até lá.'); return; }
        FX.play('runes_blue', p.actor.x, p.actor.y, { life: 0.8 }); p.actor.x = x; p.actor.y = y; p.actor.path = null; FX.play('runes_blue', x, y, { life: 0.8 });
        break;
      }
      case 'create_item': { const n = Math.max(1, Math.round(((e.base || [1, 1])[0] + (e.base || [1, 1])[1]) / 2)); Game.give(e.id, n); Backpack.render(); FX.play('sparkle', p.actor.x, p.actor.y, { scale: 0.6, life: 1 }); Journal.add('system', '', `Você cria ${Items.name(Items.byId[e.id])}.`); break; }
      case 'field': this.fx.push({ kind: 'field', x: at[0], y: at[1], r: e.radius || 1.5, col, t: 0, life: Math.max(1.5, Math.min(20, e.duration || 10)), dps: e.base && e.base[1] ? Math.max(2, this.roll(s) / 3) : 0, spr: FX_CAMPO[e.kind] || 'sparkle', stop: e.kind === 'paralyze' }); break;
      case 'summon': FX.play('runes_orange', p.actor.x, p.actor.y, { life: 1.2 }); Journal.add('system', '', `${this.name(s)}: as invocações chegam junto com os monstros.`); break;
      case 'reveal': FX.play('sparkle', p.actor.x, p.actor.y, { life: 1 }); Journal.add('system', '', 'Nada escondido por perto.'); break;
    }
    const tgt = actor || { x: at[0], y: at[1] };
    if (!FX.has('heal') && e.type !== 'field') this.burst(tgt.x, tgt.y, col, 1);
  },
  addBuff(s, n, dur) {
    const p = Game.player, e = s.effect, b = { id: s.id, name: this.name(s), until: Game.now + dur };
    const old = this.buffs.find(x => x.id === s.id); if (old) { old.end && old.end(); this.buffs.splice(this.buffs.indexOf(old), 1); }
    if (e.stat === 'mana') { p.mpMax += n; b.end = () => { p.mpMax -= n; p.mp = Math.min(p.mp, p.mpMax); }; }
    if (e.stat === 'invisible') { p.actor.alpha = 0.35; b.end = () => { p.actor.alpha = 1; }; }
    this.buffs.push(b); Journal.add('system', '', `${b.name} (${Math.round(dur / 1000)}s).`);
  },
  burst(x, y, col, life) { this.fx.push({ kind: 'burst', x, y, col, t: 0, life }); },
  // efeitos visuais, no espaço do mundo (chamado pelo Render)
  draw(g) {
    for (const f of this.fx) {
      const [sx, sy] = w2s(f.x, f.y), k = f.t / f.life;
      g.save(); g.globalCompositeOperation = 'lighter';
      if (f.kind === 'burst') {
        g.globalAlpha = 1 - k;
        const r = 10 + k * 34, gr = g.createRadialGradient(sx, sy - 35, 0, sx, sy - 35, r);
        gr.addColorStop(0, f.col); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr;
        g.beginPath(); g.arc(sx, sy - 35, r, 0, 7); g.fill();
        for (let i = 0; i < 10; i++) { const a = i * 0.63 + f.t * 3, d = 8 + k * 30; g.fillStyle = f.col; g.fillRect(sx + Math.cos(a) * d, sy - 35 + Math.sin(a) * d * 0.6 - k * 25, 2, 2); }
      } else {
        g.globalAlpha = (f.spr ? 0.12 : 0.45) * Math.min(1, (f.life - f.t) / 1.5) * (0.8 + 0.2 * Math.sin(f.t * 8));
        g.fillStyle = f.col; g.beginPath(); g.ellipse(sx, sy, f.r * ISO.HW, f.r * ISO.HH, 0, 0, 7); g.fill();
      }
      g.restore();
    }
  },
};

// ---------------------------------------------------------------------
// Livro de magias e barra de atalhos
// ---------------------------------------------------------------------
const Spellbook = {
  circle: 1,
  init() {
    this.g = Gumps.create('spellbook', 'Livro de magias', { pos: [520, 60], posCompact: [6, 6], w: 300, h: 340, cls: 'spellbook', open: false, onOpen: () => this.render() });
    const bar = document.createElement('div'); bar.id = 'hotbar'; document.getElementById('ui').appendChild(bar); this.bar = bar;
    this.renderBar();
  },
  render() {
    if (!Gumps.isOpen('spellbook')) return;
    const b = this.g.body, v = Game.player.skills.magery || 0;
    const tabs = [1, 2, 3, 4, 5, 6, 7, 8].map(c => `<button data-c="${c}" class="${c === this.circle ? 'on' : ''} ${v >= CIRCULO_MIN[c] || c === 1 ? '' : 'shut'}">${['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][c - 1]}</button>`).join('');
    const rows = Magic.list.filter(s => s.circle === this.circle).map(s => {
      const reag = Object.entries(s.reagents || {}).map(([r, n]) => `${n}× ${Items.name(Items.byId[r])}`).join(', ') || 'sem reagente';
      const on = Magic.open(s), inBar = Magic.hotbar.includes(s.id);
      return `<div class="sp ${on ? '' : 'shut'}" title="${(s.desc[Chat.lang] || s.desc.pt).replace(/"/g, '')}"><button class="spc" data-s="${s.id}" ${on ? '' : 'disabled'}>${Magic.name(s)}</button><span>${s.mana} mana · ${reag}</span><button class="spb ${inBar ? 'on' : ''}" data-b="${s.id}" title="Pôr/tirar da barra (1–9)">★</button></div>`;
    }).join('');
    b.innerHTML = `<div class="sptabs">${tabs}</div><div class="sphead">Círculo ${this.circle} · precisa de Magia ${CIRCULO_MIN[this.circle]} · sua: ${v.toFixed(1)}</div><div class="splist">${rows}</div>`;
    b.querySelectorAll('[data-c]').forEach(x => x.onclick = () => { this.circle = +x.dataset.c; this.render(); });
    b.querySelectorAll('[data-s]').forEach(x => x.onclick = () => Magic.cast(x.dataset.s, Combat.target || Combat.nearest(9), null));
    b.querySelectorAll('[data-b]').forEach(x => x.onclick = () => {
      const id = x.dataset.b, h = Magic.hotbar, i = h.indexOf(id);
      if (i >= 0) h.splice(i, 1); else if (h.length < 9) h.push(id); else HUD.toast('Barra cheia (9)');
      Store.set('hotbar', h); this.render(); this.renderBar();
    });
  },
  renderBar() {
    const h = Magic.hotbar.filter(id => Magic.byId[id]);
    this.bar.style.display = h.length ? '' : 'none';
    this.bar.innerHTML = h.map((id, i) => { const s = Magic.byId[id]; return `<button data-s="${id}" title="${Magic.name(s)} (${s.mana} mana)"><b>${i + 1}</b>${Magic.name(s).split(' ').map(w => w[0]).join('').slice(0, 3)}</button>`; }).join('');
    this.bar.querySelectorAll('[data-s]').forEach(x => x.onclick = () => Game.castAt(x.dataset.s, ...(Game.mouse || [Render.vw / 2, Render.vh / 2])));
    Touch.render();
  },
};

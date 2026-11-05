'use strict';
// =====================================================================
// systems/skills.js — skills sem classe, como no UO: sobem com o uso.
// Versão casual: chance de subir alta, passos grandes no começo, teto de
// 100 por skill e 700 no total. Cada skill pode estar em subir (▲),
// baixar (▼) ou travada (■); no teto total, só sobe tirando de uma em ▼.
// Nomes: data/skills.json (Ludimus).
// =====================================================================
const Skills = {
  CAP: 100, TOTAL: 700, lock: {},
  start(given) {
    const out = {};
    for (const s of DATA.skills.skills) out[s.id] = 0;
    for (const k in given || {}) if (k in out) out[k] = given[k];
    return out;
  },
  total(p = Game.player) { let t = 0; for (const k in p.skills) t += p.skills[k]; return t; },
  name(id) { return Chat.skills[id] || id; },
  // chance de subir: alta no começo, cai perto do 100; diff 0..1 (quanto mais difícil a ação, mais ensina)
  use(id, diff = 0.5) {
    const p = Game.player; if (!(id in p.skills)) return false;
    const v = p.skills[id];
    if (v >= this.CAP || this.lock[id] === 'lock' || this.lock[id] === 'down') return false;
    const chance = Math.max(0.12, (1 - v / 100) * 0.85) * (0.6 + diff * 0.8);
    if (Math.random() > chance) return false;
    let step = v < 30 ? 1.0 : v < 60 ? 0.5 : v < 85 ? 0.2 : 0.1;
    step = Math.min(step, this.CAP - v);
    if (this.total(p) + step > this.TOTAL) {
      // teto total: tira de uma skill marcada para baixar
      const down = Object.keys(p.skills).find(k => this.lock[k] === 'down' && p.skills[k] >= step);
      if (!down) return false;
      p.skills[down] = Math.round((p.skills[down] - step) * 10) / 10;
    }
    p.skills[id] = Math.round((v + step) * 10) / 10;
    if (Math.floor(p.skills[id]) > Math.floor(v)) Journal.add('system', '', `Sua habilidade em ${this.name(id)} subiu para ${p.skills[id].toFixed(1)}.`);
    SkillsGump.render();
    return true;
  },
  // sucesso de uma ação contra a dificuldade (0..100), e já treina a skill
  check(id, difficulty) {
    const v = Game.player.skills[id] || 0;
    const ok = Math.random() < Math.min(0.98, Math.max(0.05, 0.5 + (v - difficulty) / 50));
    this.use(id, Math.min(1, Math.max(0, difficulty / 100)));
    return ok;
  },
};

const SkillsGump = {
  init() {
    this.g = Gumps.create('skills', 'Skills', { pos: [240, 60], posCompact: [6, 6], w: 270, h: 360, cls: 'skillsg', open: false, onOpen: () => this.render() });
  },
  render() {
    if (!this.g || !Gumps.isOpen('skills')) return;
    const p = Game.player, b = this.g.body;
    const sym = { up: '▲', down: '▼', lock: '■' };
    const rows = DATA.skills.skills.slice().sort((a, c) => (p.skills[c.id] - p.skills[a.id]) || a.name.pt.localeCompare(c.name.pt));
    b.innerHTML = `<div class="sktot">Total ${Skills.total().toFixed(1)} / ${Skills.TOTAL}</div><div class="sklist">` +
      rows.map(s => { const v = p.skills[s.id], l = Skills.lock[s.id] || 'up';
        return `<div class="skrow ${v > 0 ? '' : 'zero'}"><span>${s.name[Chat.lang] || s.name.pt}</span><b>${v.toFixed(1)}</b><button data-k="${s.id}" class="${l}" title="subir / baixar / travar">${sym[l]}</button></div>`; }).join('') + '</div>';
    b.querySelectorAll('button[data-k]').forEach(bt => bt.onclick = () => {
      const k = bt.dataset.k, o = ['up', 'down', 'lock'], c = Skills.lock[k] || 'up';
      Skills.lock[k] = o[(o.indexOf(c) + 1) % 3]; this.render();
    });
  },
};

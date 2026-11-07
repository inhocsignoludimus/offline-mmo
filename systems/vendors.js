'use strict';
// =====================================================================
// systems/vendors.js — comércio: vendedores nas vilas (data/npcs/vendors.json)
// Clique/toque no vendedor: Comprar, Vender e Treinar (como no UO, treino pago até 30).
// =====================================================================
const LOJAS_POR_PAPEL = {
  capital: ['ferreiro', 'alfaiate', 'mago', 'alquimista', 'estalajadeiro', 'carpinteiro', 'arqueiro', 'acougueiro'],
  castelo: ['ferreiro', 'arqueiro', 'alquimista', 'estalajadeiro'],
  fort: ['ferreiro', 'arqueiro', 'alquimista', 'estalajadeiro'],
  mosteiro: ['mago', 'alquimista', 'estalajadeiro', 'alfaiate'],
  templo: ['mago', 'alquimista', 'estalajadeiro', 'alfaiate'],
  acampamento: ['acougueiro', 'carpinteiro', 'estalajadeiro', 'arqueiro'],
  porto: ['acougueiro', 'estalajadeiro', 'alfaiate', 'carpinteiro', 'ferreiro'],
  mina: ['ferreiro', 'carpinteiro', 'estalajadeiro', 'alquimista'],
  vila: ['ferreiro', 'alfaiate', 'alquimista', 'estalajadeiro', 'carpinteiro', 'mago'],
};
const FEM = { mago: 'Maga', estalajadeiro: 'Estalajadeira', banqueiro: 'Banqueira', alfaiate: 'Alfaiata' };
const NOMES_NPC = { m: ['Anselmo', 'Bertrand', 'Caio', 'Dario', 'Elias', 'Fulco', 'Gaspar', 'Henrique', 'Isaac', 'Jaime', 'Lucas', 'Martim', 'Nuno', 'Odo', 'Pedro', 'Rui', 'Simão', 'Tancredo'],
  f: ['Adela', 'Beatriz', 'Clara', 'Dulce', 'Ermesinda', 'Filipa', 'Guiomar', 'Helena', 'Inês', 'Joana', 'Leonor', 'Mafalda', 'Sancha', 'Teresa'] };

const Vendors = {
  defs: {}, npcs: [], open: null, tab: 'buy',
  init(data, map) {
    for (const v of (data.vendors && data.vendors.vendors) || []) this.defs[v.id] = v;
    const capital = (map.home || [0, 0]).join();
    let seed = 7; const rnd = n => { seed = (seed * 9301 + 49297) % 233280; return Math.floor(seed / 233280 * n); };
    for (const z of World.zones) {
      if (!z.center || !(z.kind === 'village' || z.kind === 'city')) continue;
      const papel = z.center.join() === capital || z.id === 'aurelia' ? 'capital' : Object.keys(LOJAS_POR_PAPEL).find(p => z.id.startsWith(p)) || 'vila';
      const ids = LOJAS_POR_PAPEL[papel].filter(id => this.defs[id]);
      // cada loja na porta de uma casa da vila; o que sobrar fica na praça
      const [ox, oy] = z.origin || [z.center[0] - 20, z.center[1] - 20], [zw, zh] = z.size || [40, 40];
      const portas = Houses.list.filter(o => o.x >= ox && o.y >= oy && o.x < ox + zw && o.y < oy + zh)
        .map(o => { const [di, dj] = o.d.doors[0]; return [o.x + di + 1.5, o.y + dj + 1.5]; });
      ids.forEach((id, k) => {
        const v = this.defs[id], ang = k / ids.length * Math.PI * 2 + 0.4, r = 4 + (k % 2) * 2;
        let [x, y] = portas[k] || [z.center[0] + Math.cos(ang) * r, z.center[1] + Math.sin(ang) * r];
        for (let t = 0; t < 30 && !map.free(x, y); t++) { x += rnd(3) - 1; y += rnd(3) - 1; }
        if (!map.free(x, y)) return;
        const sexo = v.sex || 'm', nome = NOMES_NPC[sexo][rnd(NOMES_NPC[sexo].length)];
        const layers = v.look.filter(l => TCOM.slot[l] || /head/.test(l));
        const a = new Actor({ x: Math.floor(x) + 0.5, y: Math.floor(y) + 0.5, ap: { sexo, layers }, name: `${nome}, ${(sexo === 'f' && FEM[id] || v.name[Chat.lang] || v.name.pt).toLowerCase()}`, kind: 'npc', nameColor: '#f0d070', speed: 0, dir: portas[k] ? 7 : rnd(8) });
        a.vendor = v; a.home = [a.x, a.y]; this.npcs.push(a); Game.actors.push(a);
      });
    }
    this.g = Gumps.create('shop', 'Comércio', { pos: [300, 70], posCompact: [6, 40], w: 340, h: 420, cls: 'shopg', open: false });
  },
  // vendedor sob o cursor (o pick do jogo já acha atores; aqui só filtra os vendedores)
  near(a, r = 2.4) { const P = Game.player.actor; return Math.hypot(a.x - P.x, a.y - P.y) <= r; },
  click(a) {
    if (!a || !a.vendor) return false;
    const P = Game.player.actor;
    if (!this.near(a)) { P.moveTo(Game.map, a.x + 0.8, a.y + 0.8); this.pending = a; return true; }
    this.show(a); return true;
  },
  update() {
    if (this.pending && !Game.player.actor.path) { const a = this.pending; this.pending = null; if (this.near(a, 3)) this.show(a); }
    if (this.open && !this.near(this.open, 5)) { Gumps.toggle('shop', false); this.open = null; }
  },
  show(a) {
    this.open = a; this.tab = 'buy';
    const P = Game.player.actor; a.dir = direcaoDoAngulo(Math.atan2(P.y - a.y, P.x - a.x));
    const ls = a.vendor.lines[Chat.lang] || a.vendor.lines.pt; a.say = { text: ls[Math.floor(Math.random() * ls.length)].replace('{player}', Game.player.name), until: Game.now + 4000, color: '#f0d070' };
    Gumps.toggle('shop', true); this.render();
  },
  priceBuy(id, mult) { const d = Items.def(id); return Math.max(1, Math.round((d.value || 5) * mult)); },
  priceSell(it) {
    const r = { comum: 1, magico: 1.8, raro: 3, conjunto: 4, lendario: 6 }[it.rarity] || 1;
    return Math.max(1, Math.round((it.d.value || 2) * 0.35 * r * (1 + (it.affixes || []).length * 0.25)));
  },
  buys(v, it) {
    const d = it.d; if (Object.values(Game.player.equip).includes(it)) return false;
    return v.buys.some(b => b === d.type || b === it.id || (b === 'bow' && /bow/.test(it.id)) || (b === 'staff' && /staff/.test(it.id)));
  },
  icon(it, size = 30) { const s = Icons.style(it, size); return `<span class="ic" style="width:${size}px;height:${size}px;${s.style}">${s.label}</span>`; },
  render() {
    const a = this.open; if (!a || !this.g) return;
    const v = a.vendor, p = Game.player, b = this.g.body, nm = v.name[Chat.lang] || v.name.pt;
    this.g.el.querySelector('.title, h3, .gtitle') && (this.g.el.querySelector('.title, h3, .gtitle').textContent = a.name);
    let rows = '';
    if (this.tab === 'buy') {
      rows = v.sells.map(([id, m]) => { const d = Items.def(id); if (!d) return ''; const it = { id, d, name: Items.name(d), icon: d.icon }, pr = this.priceBuy(id, m);
        return `<div class="srow">${this.icon(it)}<span class="sn">${it.name}</span><b class="${p.gold < pr ? 'poor' : ''}">${pr}</b><button data-buy="${id}" data-pr="${pr}">Comprar</button></div>`; }).join('') || '<p class="se">Não vende nada.</p>';
    } else if (this.tab === 'sell') {
      const list = p.bag.filter(it => this.buys(v, it));
      rows = list.map(it => `<div class="srow">${this.icon(it)}<span class="sn" style="color:${Loot.color ? Loot.color(it) : '#eee'}">${it.name}${it.qty > 1 ? ' ×' + it.qty : ''}</span><b>${this.priceSell(it)}</b><button data-sell="${p.bag.indexOf(it)}">Vender</button></div>`).join('')
        || `<p class="se">${nm} não compra nada do que está na sua mochila.<br><small>Compra: ${v.buys.map(x => x.replace(/_/g, ' ')).join(', ')}.</small></p>`;
    } else {
      rows = (v.trains || []).map(s => { const cur = p.skills[s] || 0, pr = Math.round(Math.max(0, 30 - cur) * 12);
        return `<div class="srow"><span class="sn">${Skills.name(s)} <small>${cur.toFixed(1)}</small></span>${cur >= 30 ? '<em>já sabe o que eu ensino</em>' : `<b class="${p.gold < pr ? 'poor' : ''}">${pr}</b><button data-train="${s}" data-pr="${pr}">Treinar até 30</button>`}</div>`; }).join('') || '<p class="se">Não ensina nada.</p>';
    }
    b.innerHTML = `<div class="stabs"><button data-t="buy" class="${this.tab === 'buy' ? 'on' : ''}">Comprar</button><button data-t="sell" class="${this.tab === 'sell' ? 'on' : ''}">Vender</button><button data-t="train" class="${this.tab === 'train' ? 'on' : ''}">Treinar</button><span class="sgold">Ouro: <b>${p.gold}</b></span></div><div class="slist">${rows}</div>`;
    b.querySelectorAll('[data-t]').forEach(x => x.onclick = () => { this.tab = x.dataset.t; this.render(); });
    b.querySelectorAll('[data-buy]').forEach(x => x.onclick = () => this.buy(x.dataset.buy, +x.dataset.pr));
    b.querySelectorAll('[data-sell]').forEach(x => x.onclick = () => this.sell(+x.dataset.sell));
    b.querySelectorAll('[data-train]').forEach(x => x.onclick = () => this.train(x.dataset.train, +x.dataset.pr));
  },
  buy(id, pr) {
    const p = Game.player; if (p.gold < pr) { HUD.toast('Ouro insuficiente'); return; }
    const d = Items.def(id); p.gold -= pr;
    if (d.slot && d.slot !== 'none' && Loot.make) { const it = Loot.make(id, 'comum', 1); it ? p.bag.push(it) : Game.give(id, 1); } else Game.give(id, Items.stackable(d) ? 1 : 1);
    Journal.add('system', '', `Você comprou ${Items.name(d)} por ${pr} de ouro.`);
    Backpack.render(); this.render(); Save.soon();
  },
  sell(i) {
    const p = Game.player, it = p.bag[i]; if (!it) return;
    const pr = this.priceSell(it);
    if (it.qty > 1) it.qty--; else p.bag.splice(i, 1);
    p.gold += pr; Journal.add('system', '', `Você vendeu ${it.name} por ${pr} de ouro.`);
    Backpack.render(); this.render(); Save.soon();
  },
  train(s, pr) {
    const p = Game.player; if (p.gold < pr) { HUD.toast('Ouro insuficiente'); return; }
    if (Skills.total() >= (Skills.cap || 700)) { HUD.toast('Você já está no limite de skills'); return; }
    p.gold -= pr; p.skills[s] = Math.max(p.skills[s] || 0, 30);
    Journal.add('system', '', `${this.open.name} ensina ${Skills.name(s)}. Agora em 30.`);
    SkillsGump.render && SkillsGump.render(); this.render(); Save.soon();
  },
};

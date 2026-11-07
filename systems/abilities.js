'use strict';
// =====================================================================
// systems/abilities.js — habilidades de arma (data/abilities.json), estilo Diablo 2
// Q e E no PC, botões ao lado do ⚔ no celular. Gastam fôlego e têm recarga.
// Quais aparecem depende da arma na mão e da skill dela.
// =====================================================================
const ARMA_TIPO = { swordsmanship: 'sword', archery: 'bow', mace_fighting: 'mace', fencing: 'spear', axe_fighting: 'axe' };

const Abilities = {
  list: [], cd: {}, dash: null,
  init(data) {
    this.list = (data.abilities && data.abilities.abilities) || [];
    const el = document.createElement('div'); el.id = 'abil'; document.body.appendChild(el); this.el = el;
    this.render();
  },
  name(a) { return a.name[Chat.lang] || a.name.pt; },
  available() {
    const w = Combat.weapon(), k = w && ARMA_TIPO[w.d.skill];
    return k ? this.list.filter(a => a.weapon === k) : [];
  },
  render() {
    const av = this.available(), keys = ['Q', 'E'];
    this.el.innerHTML = av.slice(0, 2).map((a, i) => {
      const lock = (Combat.skill(a.skill) || 0) < a.min_level;
      return `<button data-i="${i}" class="${lock ? 'lock' : ''}" title="${this.name(a)} — ${a.desc.pt} (${a.stamina} fôlego, ${a.cooldown_s}s)${lock ? ' · precisa ' + a.min_level : ''}">
        <b>${this.name(a).split(' ').map(w => w[0]).join('').slice(0, 2)}</b>${Touch.on ? '' : `<i>${keys[i]}</i>`}<s></s></button>`;
    }).join('');
    this.el.querySelectorAll('button').forEach(b => {
      const go = e => { e.preventDefault(); this.use(+b.dataset.i); };
      b.addEventListener(Touch.on ? 'touchstart' : 'click', go, { passive: false });
    });
    this._sig = av.map(a => a.id).join();
  },
  // recarga desenhada nos botões
  tick() {
    const av = this.available(); if (av.map(a => a.id).join() !== this._sig) this.render();
    this.el.querySelectorAll('button').forEach(b => {
      const a = av[+b.dataset.i], left = a ? Math.max(0, (this.cd[a.id] || 0) - Game.now) : 0;
      b.querySelector('s').style.height = left ? Math.min(100, left / (a.cooldown_s * 10)) + '%' : '0';
    });
  },
  dmg(a, k = 1) {
    const [lo, hi] = a.effect.base, sk = Combat.skill(a.skill) || 0;
    return Math.max(1, Math.round((lo + Math.random() * (hi - lo)) * (0.7 + sk / 120) * (1 + (Combat.skill('tactics') || 0) / 250) * (1 + (Combat.stats.dmg_pct || 0) / 100) * k));
  },
  hit(m, n) { if (!m || m.dead) return; Combat.damageMob(m, Math.round(n * 100 / (100 + (m.def.armor || 0) * 2))); },
  use(i) {
    const a = this.available()[i], p = Game.player, me = p.actor;
    if (!a || p.dead) return;
    if ((Combat.skill(a.skill) || 0) < a.min_level) { HUD.toast(`${this.name(a)}: precisa de ${a.min_level} em ${Skills.name(a.skill)}`); return; }
    if (Game.now < (this.cd[a.id] || 0)) return;
    if (p.st < a.stamina) { HUD.toast('Fôlego insuficiente'); return; }
    const e = a.effect, reach = e.range || (a.weapon === 'bow' ? 9 : a.id === 'charge' ? 7 : Combat.range() + 0.6);
    let t = Combat.target && !Combat.target.dead ? Combat.target : Combat.nearest(reach);
    if (a.target !== 'self' && !t) { HUD.toast('Nenhum monstro por perto'); return; }
    if (t && a.target !== 'self' && Math.hypot(t.x - me.x, t.y - me.y) > reach + 0.4) { HUD.toast('Longe demais'); return; }
    if (a.weapon === 'bow') { const ar = p.bag.find(x => x.id === 'arrow'); if (!ar) { HUD.toast('Sem flechas'); return; } if (--ar.qty <= 0) p.bag.splice(p.bag.indexOf(ar), 1); }
    p.st -= a.stamina; this.cd[a.id] = Game.now + a.cooldown_s * 1000;
    me.path = null; me.setAnim('swing'); Combat.cd = Math.max(Combat.cd, 0.5);
    if (t) { me.dir = direcaoDoAngulo(Math.atan2(t.y - me.y, t.x - me.x)); Combat.engage(t); }
    Skills.use(a.skill, 0.5);
    const dirTo = m => direcaoDoAngulo(Math.atan2(m.y - me.y, m.x - me.x));
    switch (a.id) {
      case 'whirlwind_strike':
        for (let d = 0; d < 8; d++) FX.play('cleave', me.x, me.y, { dir: d, delay: d * 0.035 });
        setTimeout(() => { for (const m of Combat.mobs) if (!m.dead && Math.hypot(m.x - me.x, m.y - me.y) <= (e.aoe || 2) + 0.4) this.hit(m, this.dmg(a)); }, 160);
        break;
      case 'charge': {
        const d = Math.hypot(t.x - me.x, t.y - me.y), k = Math.max(0, (d - 0.9) / d);
        const x1 = me.x + (t.x - me.x) * k, y1 = me.y + (t.y - me.y) * k;
        if (Game.map.los(me.x, me.y, x1, y1)) this.dash = { x0: me.x, y0: me.y, x1, y1, t: 0, dur: Math.max(0.1, d / 22), done: () => { FX.play('spark_red', t.x, t.y, { dir: dirTo(t) }); this.hit(t, this.dmg(a)); } };
        else { FX.play('spark_red', t.x, t.y); this.hit(t, this.dmg(a, 0.7)); }
        break;
      }
      case 'multishot': {
        const base = Math.atan2(t.y - me.y, t.x - me.x);
        for (const off of [-0.32, 0, 0.32]) {
          const ang = base + off;
          const m = Combat.mobs.filter(x => !x.dead && Math.hypot(x.x - me.x, x.y - me.y) < 9)
            .map(x => [x, Math.abs(Math.atan2(Math.sin(Math.atan2(x.y - me.y, x.x - me.x) - ang), Math.cos(Math.atan2(x.y - me.y, x.x - me.x) - ang)))])
            .filter(([, da]) => da < 0.2).sort((p1, p2) => p1[1] - p2[1])[0];
          const to = m ? m[0] : { x: me.x + Math.cos(ang) * 8, y: me.y + Math.sin(ang) * 8 };
          Combat.projectile(me, to, '#e8dcb0', () => m && this.hit(m[0], this.dmg(a)), 'arrows');
        }
        break;
      }
      case 'piercing_arrow': {
        const ang = Math.atan2(t.y - me.y, t.x - me.x), far = { x: me.x + Math.cos(ang) * 11, y: me.y + Math.sin(ang) * 11 };
        Combat.projectile(me, far, '#e8dcb0', () => {}, 'arrows');
        for (const m of Combat.mobs) {
          if (m.dead) continue;
          const dx = m.x - me.x, dy = m.y - me.y, along = dx * Math.cos(ang) + dy * Math.sin(ang), side = Math.abs(-dx * Math.sin(ang) + dy * Math.cos(ang));
          if (along > 0 && along < 11 && side < 0.8) setTimeout(() => this.hit(m, this.dmg(a)), along / 14 * 1000);
        }
        break;
      }
      case 'stun_blow':
        setTimeout(() => {
          if (t.dead) return; this.hit(t, this.dmg({ effect: { base: [4, 8] }, skill: a.skill }));
          t.stun = Game.now + (e.duration || 2) * 1000; FX.play('sparkle', t.x, t.y, { follow: t, life: e.duration || 2, scale: 0.6 }); Combat.float(t, 'atordoado', '#ffe080');
        }, 180);
        break;
      case 'long_thrust':
        FX.play('spear', me.x, me.y, { dir: dirTo(t) });
        setTimeout(() => this.hit(t, this.dmg(a)), 200);
        break;
      case 'heavy_blow':
        setTimeout(() => { FX.play('rupture', t.x, t.y); this.hit(t, this.dmg(a)); }, 220);
        break;
      default:
        setTimeout(() => this.hit(t, this.dmg(a)), 200);
    }
  },
  update(dt) {
    const d = this.dash; if (!d) return;
    const me = Game.player.actor; d.t += dt / d.dur;
    const k = Math.min(1, d.t); me.x = d.x0 + (d.x1 - d.x0) * k; me.y = d.y0 + (d.y1 - d.y0) * k; me.path = null; me.setAnim('run');
    if (k >= 1) { this.dash = null; me.setAnim('swing'); d.done(); }
  },
};

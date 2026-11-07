'use strict';
// =====================================================================
// systems/fx.js — efeitos de magia e habilidades com os sprites do Flare (images/powers, CC-BY-SA)
// FX.play(nome, x, y, {dir, scale, life, follow, loop})  efeito parado ou seguindo alguém
// FX.frame(...) desenha um quadro (os projéteis em Combat.shots também usam)
// =====================================================================
const FX_ADD = new Set(['fireball', 'plasmaball', 'blast', 'lightning', 'thunderstrike', 'spark_red', 'spark_orange', 'spark_green',
  'spark_blue', 'heal', 'shield', 'shield_orange', 'immunity', 'runes', 'runes_blue', 'runes_orange', 'sparkle', 'channel', 'icicle']);
const FX_PROJ = { fire: 'fireball', cold: 'icicle', energy: 'plasmaball', poison: 'spit', physical: 'stone' };
const FX_HIT = { fire: 'spark_orange', cold: 'freeze', energy: 'lightning', poison: 'spark_green', physical: 'spark_red' };
const FX_AREA = { fire: 'blast', cold: 'freeze', energy: 'thunderstrike', poison: 'dark_mist', physical: 'quake' };

const FX_VEL = { thunderstrike: 0.45, lightning: 0.6, blast: 0.8 };   // mais lentos que no Flare, para dar tempo de ver

const FX = {
  list: [],
  init(meta) { this.meta = meta || {}; this.img = new Image(); this.img.src = 'engine/dev_assets/powers/powers.webp'; },
  has(n) { return !!(this.meta && this.meta[n]); },
  len(n) { const m = this.meta[n]; return m ? m.dur / 1000 : 0.4; },
  play(name, x, y, o = {}) {
    const m = this.meta[name]; if (!m) return null;
    const e = { name, x, y, t: 0, dir: o.dir || 0, v: Math.floor(Math.random() * 8), scale: o.scale || 1, follow: o.follow || null,
      life: o.life || (m.tipo === 'looped' || m.tipo === 'back_forth' ? 1 : m.dur / 1000 / (o.speed || FX_VEL[name] || 1)), delay: o.delay || 0, alpha: o.alpha || 1, speed: o.speed || FX_VEL[name] || 1 };
    this.list.push(e); return e;
  },
  update(dt) {
    for (const e of this.list) { if (e.delay > 0) { e.delay -= dt; continue; } e.t += dt; if (e.follow) { e.x = e.follow.x; e.y = e.follow.y; } }
    this.list = this.list.filter(e => e.t < e.life && !(e.follow && e.follow.dead));
  },
  // quadro do efeito no tempo t (segundos)
  frame(g, name, t, dir, v, x, y, scale = 1, alpha = 1) {
    const m = this.meta[name]; if (!m || !this.img.complete || !this.img.naturalWidth) return false;
    const n = m.n, k = t * 1000 / m.dur * n;
    let f = m.tipo === 'play_once' ? Math.min(n - 1, Math.floor(k)) : Math.floor(k) % n;
    if (m.tipo === 'back_forth') { const p = Math.floor(k) % (2 * n - 2 || 1); f = p < n ? p : 2 * n - 2 - p; }
    const row = m.q[f], dirs = row.length, q = row[dirs === 8 ? (dir + 7) % 8 : v % dirs];   // Flare começa no oeste; o TCoM, no sudoeste
    if (!q || !q[2]) return false;
    const [sx, sy] = w2s(x, y);
    g.save(); g.globalAlpha = alpha;
    if (FX_ADD.has(name)) g.globalCompositeOperation = 'lighter';
    g.drawImage(this.img, q[0], q[1], q[2], q[3], sx - q[4] * scale, sy - q[5] * scale, q[2] * scale, q[3] * scale);
    g.restore(); return true;
  },
  draw(g) {
    for (const e of this.list) {
      if (e.delay > 0) continue;
      const fade = Math.min(1, (e.life - e.t) / 0.25);
      this.frame(g, e.name, e.t * e.speed, e.dir, e.v, e.x, e.y, e.scale, e.alpha * fade);
    }
  },
};

'use strict';
// =====================================================================
// systems/chat.js — escolhe e monta as frases dos jogadores simulados.
// Frases e personalidades: data/chat (Ludimus). Esquema: docs/DATA_SCHEMA.md.
// =====================================================================
const Chat = {
  lang: 'pt', byKey: {}, pers: {}, recent: [],
  // {skill} ainda não tem arquivo de dados: lista provisória
  DEV: { skill: ['Espadas', 'Táticas', 'Cura', 'Magia', 'Arquearia', 'Ferraria', 'Mineração', 'Pesca', 'Furtividade', 'Domar Animais', 'Alquimia', 'Carpintaria'] },
  init(data) {
    for (const p of data.personalities.personalities) this.pers[p.id] = p;
    for (const l of data.lines.lines) for (const p of l.p) (this.byKey[p + '|' + l.ctx] ||= []).push(l);
    this.places = [];
    for (const b of data.biomes.biomes) for (const c of b.cities) this.places.push(c.name[this.lang] || c.name.pt);
    // itens que valem a pena anunciar (nada de pão e minério nas falas de loot e comércio)
    this.items = data.items.items.filter(i => ['weapon', 'armor', 'shield', 'jewelry', 'clothing'].includes(i.type)).map(i => (i.name[this.lang] || i.name.pt).toLowerCase());
    this.bosses = data.bosses.bosses.map(b => b.name[this.lang] || b.name.pt);
  },
  has(pers, ctx) { return !!this.byKey[pers + '|' + ctx]; },
  // devolve { text, ch } ou null
  pick(pers, ctx, vars) {
    const pool = this.byKey[pers + '|' + ctx]; if (!pool) return null;
    let l, tries = 0;
    do { l = pool[Math.floor(Math.random() * pool.length)]; } while (this.recent.includes(l.id) && tries++ < 6);
    this.recent.push(l.id); if (this.recent.length > 40) this.recent.shift();
    let t = l.text[this.lang] || l.text.pt;
    t = t.replace(/\{(\w+)\}/g, (m, k) => this.fill(k, vars));
    return { text: this.noise(t, this.pers[pers]), ch: l.ch };
  },
  fill(k, v) {
    if (v && v[k] != null) return v[k];
    const r = a => a[Math.floor(Math.random() * a.length)];
    switch (k) {
      case 'place': return r(this.places);
      case 'item': return r(this.items);
      case 'skill': return r(this.DEV.skill);
      case 'boss': return r(this.bosses);
      case 'price': return String((1 + Math.floor(Math.random() * 40)) * 50);
      case 'n': return String(2 + Math.floor(Math.random() * 8));
      default: return '?';
    }
  },
  // erros de digitação, CAIXA ALTA e emoticons conforme a personalidade
  noise(t, p) {
    if (!p) return t;
    if (Math.random() < p.typo) {
      const w = t.split(' '), i = Math.floor(Math.random() * w.length), s = w[i];
      if (s.length > 3 && !s.includes('{')) {
        const k = 1 + Math.floor(Math.random() * (s.length - 2)), r = Math.random();
        w[i] = r < 0.4 ? s.slice(0, k) + s[k + 1] + s[k] + s.slice(k + 2) : r < 0.75 ? s.slice(0, k) + s.slice(k + 1) : s.slice(0, k) + s[k] + s.slice(k);
      }
      t = w.join(' ');
    }
    if (Math.random() < p.caps) t = t.toUpperCase();
    if (Math.random() < p.emoji) t += ' ' + [':)', ':P', 'xD', '^^', ':D', 'kkk', ';)', ':('][Math.floor(Math.random() * 8)];
    return t;
  },
};

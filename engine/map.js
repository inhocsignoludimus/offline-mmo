'use strict';
// =====================================================================
// engine/map.js — mapa em tiles: chão pré-desenhado em pedaços (chunks),
// objetos ordenados por profundidade junto com os personagens, colisão e A*.
// Lê o formato gerado por build/import_dev_assets.py a partir do .txt do Flare.
// =====================================================================
const CHUNK = 16;

class GameMap {
  constructor(data, atlas) {
    Object.assign(this, { id: data.id, w: data.w, h: data.h, hero: data.hero, tiles: data.tiles, atlas });
    this.bg = data.background; this.obj = data.object; this.col = data.collision;
    this.chunks = new Map();
    // lista de objetos por linha, para achar rápido os que estão na tela
    this.objects = [];
    for (let j = 0; j < this.h; j++) for (let i = 0; i < this.w; i++) {
      const t = this.obj[j] && this.obj[j][i];
      if (t && this.tiles[t]) this.objects.push({ i, j, t, key: i + j + 1 });
    }
  }
  inBounds(i, j) { return i >= 0 && j >= 0 && i < this.w && j < this.h; }
  blocked(i, j) { if (!this.inBounds(i, j)) return true; const c = this.col[j][i]; return c !== 0; }
  // posição livre para um círculo de raio r (em tiles)
  free(x, y, r = 0.22) {
    for (const [dx, dy] of [[-r, -r], [r, -r], [-r, r], [r, r], [0, 0]]) if (this.blocked(Math.floor(x + dx), Math.floor(y + dy))) return false;
    return true;
  }
  drawTile(g, t, sx, sy) {
    const d = this.tiles[t]; if (!d) return;
    g.drawImage(this.atlas, d[0], d[1], d[2], d[3], Math.round(sx - d[4]), Math.round(sy - d[5]), d[2], d[3]);
  }
  // pedaço de chão de CHUNK x CHUNK tiles, desenhado uma vez num canvas
  chunk(ci, cj) {
    const k = ci + ',' + cj; let c = this.chunks.get(k);
    if (c) return c;
    const [ox, oy] = w2s(ci * CHUNK, cj * CHUNK);
    const left = ox - CHUNK * ISO.HW - 64, top = oy - 64;
    const cv = document.createElement('canvas'); cv.width = CHUNK * ISO.TW + 128; cv.height = CHUNK * ISO.TH + 160;
    const g = cv.getContext('2d');
    for (let s = 0; s < CHUNK * 2; s++) for (let a = 0; a <= s; a++) {
      const i = ci * CHUNK + a, j = cj * CHUNK + (s - a);
      if (a >= CHUNK || s - a >= CHUNK || !this.inBounds(i, j)) continue;
      const t = this.bg[j][i]; if (!t) continue;
      const [sx, sy] = w2s(i + 0.5, j + 0.5);
      this.drawTile(g, t, sx - left, sy - top);
    }
    c = { cv, left, top }; this.chunks.set(k, c);
    if (this.chunks.size > 64) this.chunks.delete(this.chunks.keys().next().value);
    return c;
  }
  // A* em 8 direções, sem cortar quina
  path(sx, sy, gx, gy, maxNodes = 6000) {
    const W = this.w, H = this.h, idx = (i, j) => j * W + i;
    sx = Math.floor(sx); sy = Math.floor(sy); gx = Math.floor(gx); gy = Math.floor(gy);
    if (!this.inBounds(gx, gy) || this.blocked(gx, gy)) return null;
    const open = [[0, sx, sy]], g = new Map([[idx(sx, sy), 0]]), prev = new Map();
    const h = (i, j) => { const dx = Math.abs(i - gx), dy = Math.abs(j - gy); return Math.max(dx, dy) + 0.41 * Math.min(dx, dy); };
    let n = 0;
    while (open.length && n++ < maxNodes) {
      let bi = 0; for (let k = 1; k < open.length; k++) if (open[k][0] < open[bi][0]) bi = k;
      const [, i, j] = open.splice(bi, 1)[0];
      if (i === gx && j === gy) {
        const out = []; let c = idx(i, j);
        while (prev.has(c)) { out.push([c % W + 0.5, Math.floor(c / W) + 0.5]); c = prev.get(c); }
        return out.reverse();
      }
      const gc = g.get(idx(i, j));
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
        const ni = i + dx, nj = j + dy;
        if (this.blocked(ni, nj)) continue;
        if (dx && dy && (this.blocked(i + dx, j) || this.blocked(i, j + dy))) continue;
        const ng = gc + (dx && dy ? 1.41 : 1), k = idx(ni, nj);
        if (g.has(k) && g.get(k) <= ng) continue;
        g.set(k, ng); prev.set(k, idx(i, j)); open.push([ng + h(ni, nj), ni, nj]);
      }
    }
    return null;
  }
  randomFree(rng = Math.random, near = null, radius = 12) {
    for (let k = 0; k < 400; k++) {
      const i = near ? Math.floor(near[0] + (rng() * 2 - 1) * radius) : Math.floor(rng() * this.w);
      const j = near ? Math.floor(near[1] + (rng() * 2 - 1) * radius) : Math.floor(rng() * this.h);
      if (this.inBounds(i, j) && !this.blocked(i, j) && this.bg[j][i]) return [i + 0.5, j + 0.5];
    }
    return [this.hero[0] + 0.5, this.hero[1] + 0.5];
  }
}

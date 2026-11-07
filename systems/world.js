'use strict';
// =====================================================================
// systems/world.js — mundo único e contínuo (estilo After Light):
// zonas e regiões de data/zones.json (vila segura, áreas de caça),
// spawns por região e casas em camadas em que se entra (ART_SPEC §5).
// Coordenadas do zones.json são "legadas"; somamos o offset do mapa.
// =====================================================================
const World = {
  zones: [], cur: null,
  init(data, map) {
    const [ox, oy] = map.offset || [0, 0];
    this.off = [ox, oy];
    this.zones = (map.zones || data.zones.zones).map(z => ({ ...z, rect: [z.origin[0] + ox, z.origin[1] + oy, z.size[0], z.size[1]],
      chunks: (z.chunks || []).map(c => ({ ...c, rect: [c.rect[0] + ox, c.rect[1] + oy, c.rect[2], c.rect[3]] })) }));
  },
  name(z) { return z.name[Chat.lang] || z.name.pt; },
  zoneAt(x, y) { for (const z of this.zones) { const [a, b, w, h] = z.rect; if (x >= a && y >= b && x < a + w && y < b + h) return z; } return null; },
  safe(x, y) { const z = this.zoneAt(x, y); return !!z && (z.kind === 'village' || z.kind === 'city'); },
  // todos os pontos de spawn do mundo (regiões das zonas de caça)
  spawns() {
    const out = [];
    for (const z of this.zones) for (const c of z.chunks) for (const s of c.spawns || [])
      out.push({ rect: c.rect, monster: s.monster, count: s.count, level: s.level, boss: c.boss === s.monster, region: c, zone: z });
    return out;
  },
  update() {
    const a = Game.player.actor, z = this.zoneAt(a.x, a.y);
    const region = z && z.chunks.find(c => { const [x, y, w, h] = c.rect; return a.x >= x && a.y >= y && a.x < x + w && a.y < y + h; });
    const key = (z && z.id) + '/' + (region && region.id);
    if (key !== this.key) {
      this.key = key; this.cur = z;
      if (z) HUD.toast(region ? `${this.name(z)} · ${region.name[Chat.lang] || region.name.pt}` : this.name(z) + (this.safe(a.x, a.y) ? ' · área segura' : ''));
    }
  },
};

// ---------------------------------------------------------------------
// Casas em camadas: back / front / front_low / roof / door_*, uma âncora só.
// A ordem com os personagens sai da planta (retângulo), não de um valor fixo.
// ---------------------------------------------------------------------
const Houses = {
  list: [], imgs: {},
  img(id, k) { const key = id + '/' + k; let i = this.imgs[key]; if (!i) { i = new Image(); i.src = `engine/dev_assets/houses/${id}/${k}.webp`; this.imgs[key] = i; } return i; },
  // procura um lugar livre do tamanho da planta (dev: até o mapa ter lotes de casa)
  place(id, near, map) {
    const d = DATA.houses[id]; if (!d) return;
    const [w, h] = d.size;
    for (let r = 2; r < 30; r++) for (let k = 0; k < 60; k++) {
      const x = Math.floor(near[0] + (Math.random() * 2 - 1) * r), y = Math.floor(near[1] + (Math.random() * 2 - 1) * r);
      let ok = true;
      for (let j = -1; j <= h && ok; j++) for (let i = -1; i <= w && ok; i++) if (map.blocked(x + i, y + j) || !map.bg[y + j] || !map.bg[y + j][x + i] || (map.obj[y + j] && map.obj[y + j][x + i]) || this.list.some(o => x + i >= o.x - 1 && x + i <= o.x + o.w && y + j >= o.y - 1 && y + j <= o.y + o.h)) ok = false;
      if (ok) return this.add(id, x, y, map);
    }
  },
  add(id, x, y, map, tint) {
    const d = DATA.houses[id]; if (!d) return; const [w, h] = d.size;
    const o = { id, d, x, y, w, h, inside: false, door: false, fade: 1, tint };
    for (let j = -1; j <= h; j++) for (let i = -1; i <= w; i++) if (map.inBounds(x + i, y + j)) { map.obj[y + j][x + i] = 0; map.col[y + j][x + i] = 0; }
    for (const [i, j] of d.walls) map.col[y + j][x + i] = 1;
    for (const [i, j] of d.doors) map.col[y + j][x + i] = 0;      // porta abre sozinha ao chegar perto
    const [[ix0, iy0], [ix1, iy1]] = d.interior || [[1, 1], [w - 2, h - 2]];
    o.interior = [x + ix0, y + iy0, x + ix1 + 1, y + iy1 + 1];
    o.props = (d.props || []).map(([i, j, p]) => ({ x: x + i + 0.5, y: y + j + 0.5, p }));
    for (const pr of o.props) map.col[Math.floor(pr.y)][Math.floor(pr.x)] = 1;
    this.list.push(o); return o;
  },
  update(dt) {
    const a = Game.player.actor;
    for (const o of this.list) {
      const [x0, y0, x1, y1] = o.interior;
      o.inside = a.x >= x0 && a.y >= y0 && a.x < x1 && a.y < y1;
      o.door = o.d.doors.some(([i, j]) => Math.hypot(o.x + i + 0.5 - a.x, o.y + j + 0.5 - a.y) < 1.6) || o.inside;
      o.fade += ((o.inside ? 0 : 1) - o.fade) * Math.min(1, dt * 8);
    }
  },
  // põe as camadas na lista de desenho com a ordem certa para os personagens por perto
  addToList(list, actors) {
    for (const o of this.list) {
      const near = actors.filter(a => a.x > o.x - 3 && a.y > o.y - 3 && a.x < o.x + o.w + 3 && a.y < o.y + o.h + 3);
      const behind = near.filter(a => a.x < o.x || a.y < o.y), front = near.filter(a => a.x >= o.x + o.w || a.y >= o.y + o.h);
      const mid = near.filter(a => !behind.includes(a) && !front.includes(a));
      const k = a => a.x + a.y;
      // valor padrão da camada, empurrado só o necessário para ficar entre quem está atrás e quem está na frente
      const between = (lo, hi, def) => { const L = lo.length ? Math.max(...lo.map(k)) : -1e9, H = hi.length ? Math.min(...hi.map(k)) : 1e9; let v = def; if (v <= L) v = L + 0.01; if (v >= H) v = H - 0.01; return L < H ? v : def; };
      const kBack = between(behind, mid.concat(front), o.x + o.y + 1);
      const kFront = Math.max(kBack + 0.02, between(behind.concat(mid), front, o.x + o.w + o.y + o.h - 1));
      const [sx, sy] = w2s(o.x + 0.5, o.y + 0.5);
      list.push({ k: kBack, house: o, layer: 'back', sx, sy });
      for (const pr of o.props) { const [px, py] = w2s(pr.x, pr.y); list.push({ k: kBack + 0.001 + (pr.x + pr.y) * 1e-6, prop: pr, house: o, sx: px, sy: py }); }
      list.push({ k: kFront, house: o, layer: o.inside ? 'front_low' : 'front', sx, sy });
      list.push({ k: kFront + 0.0005, house: o, layer: o.door ? 'door_open' : 'door_closed', sx, sy });
      list.push({ k: kFront + 0.001, house: o, layer: 'roof', sx, sy });
    }
  },
  // telhado de cada casa num tom próprio (o mesmo modelo não parece repetido)
  tinted(id, hex, im) {
    const k = id + '/roof' + hex; let c = this.imgs[k]; if (c) return c;
    c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight; const g = c.getContext('2d');
    g.drawImage(im, 0, 0); g.globalCompositeOperation = 'color'; g.fillStyle = hex; g.globalAlpha = 0.55; g.fillRect(0, 0, c.width, c.height);
    g.globalAlpha = 1; g.globalCompositeOperation = 'destination-in'; g.drawImage(im, 0, 0); c.complete = true; c.naturalWidth = c.width;
    this.imgs[k] = c; return c;
  },
  draw(g, e) {
    const o = e.house;
    if (e.prop) { const im = this.img(o.id, 'props/' + e.prop.p); if (im.complete && im.naturalWidth) g.drawImage(im, Math.round(e.sx - im.naturalWidth / 2), Math.round(e.sy - im.naturalHeight * 0.83)); return; }
    let im = this.img(o.id, e.layer); if (!im.complete || !im.naturalWidth) return;
    if (e.layer === 'roof' && o.tint) im = this.tinted(o.id, o.tint, im);
    if (e.layer === 'roof') { if (o.fade < 0.02) return; g.globalAlpha = o.fade; }
    g.drawImage(im, Math.round(e.sx - o.d.anchor[0]), Math.round(e.sy - o.d.anchor[1]));
    g.globalAlpha = 1;
  },
};

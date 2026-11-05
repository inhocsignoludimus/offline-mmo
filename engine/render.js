'use strict';
// =====================================================================
// engine/render.js — desenha chão (em pedaços), depois objetos do mapa e
// personagens juntos, ordenados por profundidade (x+y), e por cima os nomes
// e as falas em balão, como no UO.
// =====================================================================
const Render = {
  cv: null, g: null, vw: 0, vh: 0, dpr: 1, showNames: false, labels: new Map(),
  init(cv) { this.cv = cv; this.g = cv.getContext('2d'); this.resize(); addEventListener('resize', () => this.resize()); },
  resize() {
    // resolução do mundo: no celular 1:1 (a tela ampliada pelo navegador), no PC até 1,5x.
    // É o que mais pesa no FPS; Store 'hq' liga a resolução cheia.
    const mobile = matchMedia('(pointer: coarse)').matches || innerWidth < 900;
    this.dpr = Math.min(devicePixelRatio || 1, Store.get('hq', false) ? 2 : mobile ? 1 : 1.5);
    this.labels.clear();
    this.vw = innerWidth; this.vh = innerHeight;
    this.cv.width = Math.round(this.vw * this.dpr); this.cv.height = Math.round(this.vh * this.dpr);
    this.cv.style.width = this.vw + 'px'; this.cv.style.height = this.vh + 'px';
    Camera.zoom = this.vw < 700 || this.vh < 500 ? 0.75 : 1;
  },
  frame(map, actors, hover, now) {
    const g = this.g, z = Camera.zoom * this.dpr;
    g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#05070a'; g.fillRect(0, 0, this.cv.width, this.cv.height);
    g.imageSmoothingEnabled = Camera.zoom < 1;
    g.setTransform(z, 0, 0, z, Math.round(this.vw * this.dpr / 2 - Camera.x * z), Math.round(this.vh * this.dpr / 2 - Camera.y * z));
    // área visível em coordenadas de tela do mundo
    const hw = this.vw / 2 / Camera.zoom, hh = this.vh / 2 / Camera.zoom;
    const L = Camera.x - hw - 200, R = Camera.x + hw + 200, T = Camera.y - hh - 300, B = Camera.y + hh + 200;
    // chão
    const corners = [s2w(L, T), s2w(R, T), s2w(L, B), s2w(R, B)];
    const minI = Math.floor(Math.min(...corners.map(c => c[0])) / CHUNK), maxI = Math.floor(Math.max(...corners.map(c => c[0])) / CHUNK);
    const minJ = Math.floor(Math.min(...corners.map(c => c[1])) / CHUNK), maxJ = Math.floor(Math.max(...corners.map(c => c[1])) / CHUNK);
    for (let cj = Math.max(0, minJ); cj <= Math.min(Math.floor((map.h - 1) / CHUNK), maxJ); cj++)
      for (let ci = Math.max(0, minI); ci <= Math.min(Math.floor((map.w - 1) / CHUNK), maxI); ci++) {
        const c = map.chunk(ci, cj); g.drawImage(c.cv, c.left, c.top);
      }
    // marcador do destino
    if (hover) {
      const [hx, hy] = w2s(Math.floor(hover[0]) + 0.5, Math.floor(hover[1]) + 0.5);
      g.strokeStyle = 'rgba(255,230,150,0.55)'; g.lineWidth = 1.5; g.beginPath();
      g.moveTo(hx, hy - ISO.HH); g.lineTo(hx + ISO.HW, hy); g.lineTo(hx, hy + ISO.HH); g.lineTo(hx - ISO.HW, hy); g.closePath(); g.stroke();
    }
    // objetos + personagens
    const list = [];
    for (const o of map.objects) {
      const [sx, sy] = w2s(o.i + 0.5, o.j + 0.5);
      if (sx < L || sx > R || sy < T || sy > B + 300) continue;
      list.push({ k: o.key, o, sx, sy });
    }
    for (const a of actors) {
      const [sx, sy] = w2s(a.x, a.y);
      if (sx < L || sx > R || sy < T || sy > B + 200) continue;
      list.push({ k: a.x + a.y, a, sx, sy });
    }
    list.sort((p, q) => p.k - q.k);
    for (const e of list) {
      if (e.o) map.drawTile(g, e.o.t, e.sx, e.sy);
      else e.a.draw(g, e.sx, e.sy);
    }
    // nomes e falas, em pixels de tela (texto nítido)
    g.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    for (const e of list) if (e.a) this.overhead(e.a, now);
  },
  toggleNames() {
    this.showNames = !this.showNames;
    const b = document.querySelector('#menubar [data-act=names]'); if (b) b.classList.toggle('on', this.showNames);
    HUD.toast(this.showNames ? 'Nomes visíveis' : 'Nomes só ao passar o mouse');
  },
  // texto com contorno pré-desenhado num canvas pequeno (strokeText a cada quadro pesa muito)
  label(text, color, size) {
    const k = size + '|' + color + '|' + text; let c = this.labels.get(k);
    if (c) return c;
    const d = this.dpr, font = `600 ${size}px "Alegreya Sans", system-ui, sans-serif`;
    const m = this.g; m.font = font;
    const w = Math.ceil(m.measureText(text).width) + 8, h = size + 8;
    c = document.createElement('canvas'); c.width = Math.ceil(w * d); c.height = Math.ceil(h * d); c.w = w; c.h = h;
    const g = c.getContext('2d'); g.scale(d, d); g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.lineJoin = 'round'; g.lineWidth = 3; g.strokeStyle = 'rgba(0,0,0,0.88)'; g.strokeText(text, w / 2, h / 2);
    g.fillStyle = color; g.fillText(text, w / 2, h / 2);
    if (this.labels.size > 400) this.labels.delete(this.labels.keys().next().value);
    this.labels.set(k, c); return c;
  },
  overhead(a, now) {
    const g = this.g, [px, py] = Camera.worldToScreen(a.x, a.y, this.vw, this.vh);
    const talking = a.say && a.say.until > now;
    // como no UO: nomes só ao passar o mouse, ao clicar, ou com N ligado; o seu sempre
    const named = a.kind === 'me' || this.showNames || a === Game.hoverActor || talking;
    if (!named) return;
    let y = py - 78 * Camera.zoom - 10;
    const put = c => { g.drawImage(c, Math.round(px - c.w / 2), Math.round(y - c.h / 2), c.w, c.h); y -= 15; };
    if (a.showName !== false) put(this.label(a.tag ? `${a.name} [${a.tag}]` : a.name, a.nameColor, 12));
    if (talking) {
      g.font = '600 13px "Alegreya Sans", system-ui, sans-serif';
      const lines = a.say.lines || (a.say.lines = wrapText(g, a.say.text, 220));
      for (let i = lines.length - 1; i >= 0; i--) put(this.label(lines[i], a.say.color || '#f2ede0', 13));
    }
  },
};

function wrapText(g, text, max) {
  const words = text.split(' '), out = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (g.measureText(t).width > max && cur) { out.push(cur); cur = w; } else cur = t; }
  if (cur) out.push(cur);
  return out.slice(0, 4);
}

'use strict';
// =====================================================================
// engine/iso.js — projeção isométrica 2:1 (ART_SPEC: tile de runtime 96x48)
// Mundo em unidades de tile: o tile (i, j) ocupa [i, i+1) x [j, j+1).
// x+ aparece na tela como sudeste, y+ como sudoeste (igual ao TCoM e ao Flare).
// =====================================================================
const ISO = { TW: 96, TH: 48, HW: 48, HH: 24 };

function w2s(x, y) { return [(x - y) * ISO.HW, (x + y) * ISO.HH]; }
function s2w(sx, sy) { const a = sx / ISO.HW, b = sy / ISO.HH; return [(a + b) / 2, (b - a) / 2]; }

// direções do TCoM: índice 0..7 = SW, W, NW, N, NE, E, SE, S
const DIRECOES = ['SW', 'W', 'NW', 'N', 'NE', 'E', 'SE', 'S'];
function direcaoDoAngulo(angulo) { const passo = Math.round(angulo / (Math.PI / 4)); return ((6 + passo) % 8 + 8) % 8; }

const Camera = {
  x: 0, y: 0,          // centro, em coordenadas de tela do mundo (px)
  zoom: 1,             // px de tela (CSS) por px do mundo
  follow(wx, wy, dt) { const [sx, sy] = w2s(wx, wy); const k = Math.min(1, dt * 8); this.x += (sx - this.x) * k; this.y += (sy - 40 - this.y) * k; },
  snap(wx, wy) { const [sx, sy] = w2s(wx, wy); this.x = sx; this.y = sy - 40; },
  // tela (CSS px) -> mundo (tiles)
  screenToWorld(px, py, vw, vh) { const sx = (px - vw / 2) / this.zoom + this.x, sy = (py - vh / 2) / this.zoom + this.y; return s2w(sx, sy); },
  worldToScreen(wx, wy, vw, vh) { const [sx, sy] = w2s(wx, wy); return [(sx - this.x) * this.zoom + vw / 2, (sy - this.y) * this.zoom + vh / 2]; },
};

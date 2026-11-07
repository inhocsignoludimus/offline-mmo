'use strict';
// =====================================================================
// engine/actor.js — personagem em camadas do TCoM (8 direções, animações)
// As folhas vêm de engine/dev_assets/tcom (build/import_dev_assets.py).
// Ordem das camadas por direção copiada do TCoM (CAMADAS.ordem).
// =====================================================================
const TCOM = {
  base: 'engine/dev_assets/tcom/',
  meta: null, imgs: {},
  ordem: {
    SW: ['main', 'pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca'],
    W: ['main', 'pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca'],
    NW: ['main', 'pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca'],
    N: ['pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca', 'main'],
    NE: ['pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca', 'main'],
    E: ['pes', 'pernas', 'maos', 'tronco', 'off', 'cabeca', 'main'],
    SE: ['pes', 'pernas', 'maos', 'main', 'tronco', 'cabeca', 'off'],
    S: ['main', 'pes', 'pernas', 'maos', 'tronco', 'cabeca', 'off'],
  },
  corpo: { pes: 'default_feet', pernas: 'default_legs', maos: 'default_hands', tronco: 'default_chest' },
  // em que espaço do corpo cada camada é desenhada
  slot: {},
  // camada pintada com a cor (hue) do item: troca matiz/saturação, mantém luz e sombra
  tinted(key, hex) {
    const k = key + hex; let c = this.imgs[k];
    if (c) return c;
    const im = this.img(key); if (!im.complete || !im.naturalWidth) return im;
    c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
    const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    g.globalCompositeOperation = 'color'; g.fillStyle = hex; g.fillRect(0, 0, c.width, c.height);
    g.globalCompositeOperation = 'destination-in'; g.drawImage(im, 0, 0);
    c.complete = true; c.naturalWidth = c.width; this.imgs[k] = c; return c;
  },
  img(key) {
    let im = this.imgs[key];
    if (!im) { im = new Image(); im.src = this.base + key + '.webp'; this.imgs[key] = im; }
    return im;
  },
};
(function () {
  const S = {
    pes: 'default_feet cloth_sandals leather_boots chain_boots',
    pernas: 'default_legs cloth_pants calca_branca chain_greaves beduino_saia',
    maos: 'default_hands leather_gloves chain_gloves beduino_mangas',
    tronco: 'default_chest aldeao_tunica1 aldeao_tunica2 cloth_shirt gambesao jaque_couro loriga lorigao lamelar ferreiro_tunica armadura_templario armadura_cruzado armadura_sargento beduino_veste habito_peregrino clothes aldea_roupa2 camisa_freira habito cazagante chain_cuirass couraca_turca gibao_egipcio leather_armor',
    cabeca: 'male_head1 male_head2 head_long leather_hood chain_coif elmo_nasal turbante elmo_grande elmo_pontudo elmo_rosto keffiyeh',
    main: 'longsword mace hand_axe dagger lanca martelo infantry_axe',
    off: 'shield buckler escudo_cruz escudo_redondo arco besta besta_mao', // arcos e bestas vão na ordem da mão de trás, como no TCoM
  };
  for (const k in S) for (const n of S[k].split(' ')) TCOM.slot[n] = k;
})();

function quadroDaAnimacao(anim, tempo) {
  const n = anim.n, t = (tempo * 1000) / anim.dur;
  if (anim.tipo === 'play_once') return Math.min(n - 1, Math.floor(t * n));
  if (anim.tipo === 'back_forth') { const c = Math.floor(t * (2 * n - 2)) % (2 * n - 2); return c < n ? c : 2 * n - 2 - c; }
  return Math.floor(t * n) % n;
}

// aparência: { sexo:'m'|'f', layers:['cloth_pants', 'aldeao_tunica1', 'male_head1', ...] }
// o corpo nu (default_*) entra sozinho por baixo de cada espaço.
function montarCamadas(ap) {
  const porSlot = { pes: [], pernas: [], maos: [], tronco: [], cabeca: [], main: [], off: [] };
  for (const s in TCOM.corpo) porSlot[s].push(ap.sexo + '/' + TCOM.corpo[s]);
  for (const n of ap.layers) { const s = TCOM.slot[n]; if (s && !n.startsWith('default_')) porSlot[s].push(ap.sexo + '/' + n); }
  const out = {};
  for (const d of DIRECOES) { const l = []; for (const s of TCOM.ordem[d]) l.push(...porSlot[s]); out[d] = l; }
  return out;
}

class Actor {
  constructor(o) {
    Object.assign(this, { x: 0, y: 0, dir: 7, anim: 'stance', t: Math.random() * 3, speed: 3.6, path: null, name: '', tag: '', kind: 'player', hp: 50, hpMax: 50, nameColor: '#7fb3ff' }, o);
    this.camadas = montarCamadas(this.ap);
    this.say = null; // { text, until }
  }
  setAnim(a) { if (this.anim !== a) { this.anim = a; this.t = 0; } }
  moveTo(map, gx, gy) {
    // em linha reta quando dá; A* só quando há obstáculo no caminho
    if (map.free(gx, gy) && map.los(this.x, this.y, gx, gy)) { this.path = [[gx, gy]]; return true; }
    const p = map.path(this.x, this.y, gx, gy);
    if (p) { if (p.length) p[p.length - 1] = [gx, gy]; this.path = p; }
    return !!p;
  }
  update(dt, map) {
    // a corrida do TCoM foi feita para 2,2 tiles/s em tile de 64 px (= 1,47 tile/s aqui):
    // acelera os passos na mesma proporção da velocidade, senão o pé "desliza"
    this.t += dt * (this.anim === 'run' ? this.speed / 1.47 : 1);
    if (this.path && this.path.length) {
      const [tx, ty] = this.path[0], dx = tx - this.x, dy = ty - this.y, d = Math.hypot(dx, dy);
      const step = this.speed * dt;
      if (d <= step) { this.x = tx; this.y = ty; this.path.shift(); }
      else { this.x += dx / d * step; this.y += dy / d * step; }
      if (d > 0.01) this.dir = direcaoDoAngulo(Math.atan2(dy, dx)); // ângulo no mundo, como no TCoM
      this.setAnim('run');
      if (!this.path.length) this.path = null;
    } else if (this.manualMove) this.manualMove = false; // andando pelo joystick: mantém a corrida
    else if (this.anim === 'run') this.setAnim('stance');
    if (this.anim === 'swing' && this.t > 0.45) this.setAnim('stance');
  }
  draw(g, sx, sy) {
    const meta = TCOM.meta, dn = DIRECOES[this.dir];
    if (this.alpha != null && this.alpha < 1) g.globalAlpha = this.alpha;
    // sombra
    g.fillStyle = 'rgba(0,0,0,0.28)'; g.beginPath(); g.ellipse(sx, sy, 15, 7, 0, 0, Math.PI * 2); g.fill();
    for (const key of this.camadas[dn]) {
      const m = meta[key]; if (!m) continue;
      const a = m[this.anim] || m.stance; if (!a) continue;
      const q = a.q[quadroDaAnimacao(a, this.t)][this.dir];
      if (!q || q[2] <= 0) continue;
      const hue = this.hues && this.hues[key.slice(2)];
      const im = hue ? TCOM.tinted(key, hue) : TCOM.img(key); if (!im.complete || !im.naturalWidth) continue;
      g.drawImage(im, q[0], q[1], q[2], q[3], Math.round(sx - q[4]), Math.round(sy - q[5]), q[2], q[3]);
    }
    g.globalAlpha = 1;
  }
}

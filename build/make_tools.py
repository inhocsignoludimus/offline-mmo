#!/usr/bin/env python3
"""Cria camadas de arma/ferramenta que o TCoM não tem, a partir das que tem:
  m/cajado   — cajado de mago: a lança sem a ponta de ferro e com uma gema que brilha
  m/bastao   — bastão (quarterstaff): a lança sem a ponta
  m/picareta — picareta: o machado de mão com a lâmina trocada por um bico de ferro
Rodar depois de build/import_dev_assets.py (que regrava layers.json):
  python3 build/make_tools.py
"""
import colorsys, json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TC = os.path.join(ROOT, 'engine', 'dev_assets', 'tcom')


def masks(a):
    """separa ferro (cinza) de madeira (marrom) num recorte RGBA"""
    rgb, al = a[..., :3] / 255.0, a[..., 3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    on = al > 20
    metal = on & (sat < 0.22) & (mx > 0.28)
    return metal, on & ~metal


def staff(fr, gem):
    """a ponta da lança é a ponta mais larga do eixo; some com ela e põe a gema no lugar"""
    a = np.array(fr)
    on = a[..., 3] > 20
    ys, xs = np.nonzero(on)
    if len(xs) < 6:
        return fr
    pts = np.stack([xs - xs.mean(), ys - ys.mean()], 1).astype(float)
    _, _, vt = np.linalg.svd(pts, full_matrices=False)
    ax, perp = pts @ vt[0], pts @ vt[1]
    lo, hi = ax.min(), ax.max(); L = hi - lo
    if L < 10:
        return fr
    seg = max(4.0, L * 0.12)
    wide = lambda m: (np.ptp(perp[m]) if m.sum() > 1 else 0) + m.sum() * 0.02
    m_hi, m_lo = ax > hi - seg, ax < lo + seg
    head = m_hi if wide(m_hi) >= wide(m_lo) else m_lo
    # só corta se a ponta for de fato mais larga que o cabo
    if np.ptp(perp[head]) < 1.6:
        return fr
    hx, hy = xs[head].mean(), ys[head].mean()
    a[ys[head], xs[head]] = 0
    im = Image.fromarray(a)
    if gem:
        d = ImageDraw.Draw(im)
        for r, c in ((3.0, (110, 190, 255, 90)), (2.0, (150, 220, 255, 210)), (1.0, (240, 252, 255, 255))):
            d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=c)
    return im


def pick(fr):
    a = np.array(fr)
    metal, wood = masks(a)
    if metal.sum() < 2 or wood.sum() < 3:
        return fr
    ys, xs = np.nonzero(metal); hx, hy = xs.mean(), ys.mean()
    wy, wx = np.nonzero(wood)
    pts = np.stack([wx - wx.mean(), wy - wy.mean()], 1)
    _, _, vt = np.linalg.svd(pts, full_matrices=False)
    ux, uy = vt[0]                       # direção do cabo
    px, py = -uy, ux                     # perpendicular: o bico
    L = max(4.5, np.sqrt(metal.sum()) * 1.6)
    a[metal] = 0
    # a lâmina do machado fica de um lado; o bico da picareta vai para os dois, um pouco curvo
    big = Image.fromarray(a).resize((fr.width * 4, fr.height * 4), Image.NEAREST)
    d = ImageDraw.Draw(big)
    pts = [((hx + px * L * t + ux * abs(t) * L * 0.25) * 4, (hy + py * L * t + uy * abs(t) * L * 0.25) * 4) for t in np.linspace(-1, 1, 9)]
    d.line(pts, fill=(70, 72, 78, 255), width=7)
    d.line(pts, fill=(150, 152, 160, 255), width=3)
    return big.resize(fr.size, Image.LANCZOS)


def derive(src, dst, fn):
    lj = os.path.join(TC, 'layers.json')
    meta = json.load(open(lj))
    m = meta['m/' + src]
    sheet = Image.open(os.path.join(TC, 'm', src + '.webp')).convert('RGBA')
    out = sheet.copy()
    out.paste((0, 0, 0, 0), (0, 0, out.width, out.height))
    # cada quadro é pintado em cima do próprio lugar na folha; a ponta pode crescer um pouco, então
    # quadros com margem ganham 4px de folga desenhados na mesma posição
    done = set()
    for anim in m.values():
        for row in anim['q']:
            for q in row:
                x, y, w, h = q[:4]
                if not w or (x, y) in done:
                    continue
                done.add((x, y))
                fr = sheet.crop((x, y, x + w, y + h))
                out.paste(fn(fr), (x, y))
    out.save(os.path.join(TC, 'm', dst + '.webp'), 'WEBP', quality=90, method=6)
    meta['m/' + dst] = m
    json.dump(meta, open(lj, 'w'), separators=(',', ':'))
    print('ok', dst)


if __name__ == '__main__':
    derive('lanca', 'cajado', lambda f: staff(f, True))
    derive('lanca', 'bastao', lambda f: staff(f, False))
    derive('hand_axe', 'picareta', pick)

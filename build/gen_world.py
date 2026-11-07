#!/usr/bin/env python3
"""Gera o mundo contínuo a partir do mapa-guia data/world_layout.json, com os
tiles do Flare (grassland, snowplains, ruins) usados do jeito certo.

    python3 build/gen_world.py --flare <flare-game> [--cells 8,3,20,21] [--cell 32] [--seed 7]

Saída: engine/dev_assets/flare/mundo.json + mundo_tiles.webp. As camadas vão
compactadas (Uint16 em base64). Além do mapa: zones (vilas e lugares de caça
com spawns pelo bioma e pela distância), houses (casas em camadas) e towns.
Ids dos tiles: grassland = id, snowplains = 1000 + id, ruins = 2000 + id.
"""
import argparse, base64, json, math, os, random, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_dev_assets import load_tileset, pack, SCALE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S, R = 1000, 2000  # deslocamento dos ids de neve e de ruínas

G = dict(grass=list(range(16, 32)), cobble=list(range(32, 48)), water=list(range(176, 192)), tent=[72, 73, 74, 75], crate=[96, 97, 98, 99],
         logs=[100, 101], fire=[102], anvil=[103], fence_a=[104], fence_b=[105], bush=[112, 113], reed=[114, 115], plant=[116, 117],
         flower=[118, 119], shrub=[120, 121, 122, 123], tall=[124, 125, 126, 127], rock=[128, 129, 130, 131], pillar=[132, 133, 134, 135],
         stump=[136], sign=[138, 139], grave=[140, 141, 142, 143], birch=[240, 241, 242, 243], dead=[244, 245, 246, 247],
         pine=[248, 249, 250, 251], oak=[252, 253, 254, 255], circle=[264])
N = dict(snow=[S + i for i in range(16, 34)], snow2=[S + i for i in range(34, 48)], mix=[S + i for i in range(568, 624)], ice=[S + i for i in (344, 345, 348, 349, 350, 352, 353, 356, 357)],
         tent=[S + i for i in (72, 73, 74, 75)], fire=[S + 102], crate=[S + i for i in (96, 97, 98, 99)], logs=[S + 100, S + 101],
         shrub=[S + i for i in (112, 113, 120, 121, 122, 123)], grass=[S + i for i in (124, 125, 126, 127)], rock=[S + i for i in (128, 129, 130, 131)],
         boulder=[S + i for i in range(552, 568)], dead=[S + i for i in (244, 245, 246, 247)], stump=[S + 136, S + 137], grave=[S + i for i in (140, 141, 142, 143)],
         snowman=[S + 532, S + 533, S + 534], cart=[S + 540, S + 541], pillar=[S + i for i in (132, 133, 134, 135)])
RU = dict(dirt=[R + i for i in range(97, 120)], floor=[R + i for i in list(range(24, 32)) + list(range(38, 44)) + list(range(72, 80))], rubble=[R + i for i in range(187, 195)],
          pillar=[R + i for i in range(223, 234)], statue=[R + i for i in range(241, 247)], urn=[R + 268, R + 269], sword=[R + i for i in (270, 271, 272, 273)],
          shrine=[R + i for i in (291, 292, 293, 294)], well=[R + 289, R + 290], barrel=[R + 287, R + 288], crate=[R + 285, R + 286], autumn=[R + 314, R + 315],
          plant=[R + 312, R + 313, R + 316, R + 317], circle=[R + 380])
WALKABLE = set(G['grass'] + G['cobble'] + G['flower'] + G['tall'] + G['plant'] + G['reed'] + G['shrub'] + N['snow'] + N['snow2'] + N['mix'] + N['ice'] + N['grass']
               + RU['dirt'] + RU['floor'] + RU['plant'] + G['circle'] + RU['circle'] + N['shrub'])


D = 3000  # ids do deserto (gerados a partir da arte do TCoM)
TCOM = '/home/claude/ihsl/tcom'


def desert_assets(tcom):
    """areia (losangos recortados do chão pintado das Dunas do TCoM) e objetos
    (palmeiras, pedras, arbustos) das fatias de tile das Dunas. Escala TCoM 2x de 64 px -> 0,75."""
    import re as _re
    js = open(os.path.join(tcom, 'js', 'jogo.js'), encoding='utf-8').read()
    m = _re.search(r'const CENARIO_DADOS = (\{.*?\});\n', js, _re.S)
    dados = json.loads(m.group(1))['dunas']
    chao = Image.open(os.path.join(tcom, 'assets', 'cenario', 'dunas', 'chao_0_0.webp')).convert('RGBA')
    folha = Image.open(os.path.join(tcom, 'assets', 'cenario', 'dunas', 'folha0.webp')).convert('RGBA')
    out, kinds = {}, {'sand': [], 'palm': [], 'rock': [], 'bush': []}
    mask = Image.new('L', (128, 64), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(mask).polygon([(64, 0), (127, 32), (64, 63), (0, 32)], fill=255)
    rr = random.Random(3); cand = []
    for k in range(3000):
        x, y = rr.randint(0, chao.width - 129), rr.randint(0, chao.height - 65)
        c = chao.crop((x, y, x + 128, y + 64)); arr = np.array(c)
        px = arr[..., :3].reshape(-1, 3).astype(float); m_ = px.mean(axis=0)
        if arr[..., 3].min() < 250 or px.std(axis=0).mean() > 18: continue
        if not (m_[0] > 150 and m_[0] > m_[1] + 8 and m_[1] > m_[2] + 15): continue   # tom de areia
        cand.append((m_, c))
    med = np.median(np.array([m_ for m_, _ in cand]), axis=0)
    cand.sort(key=lambda t: np.abs(t[0] - med).sum())                                 # areias do mesmo tom
    for m_, c in cand[:16]:
        c = c.copy(); c.putalpha(mask); tid = D + len(kinds['sand'])
        out[tid] = (c.resize((100, 50), Image.LANCZOS), (50, 25)); kinds['sand'].append(tid)   # 2 px de sobra: sem emenda entre losangos
    for key, f in dados['fatias'].items():
        sh, x, y, w, h, ax, ay = f
        if sh != 0 or w < 40: continue
        im = folha.crop((x, y, x + w, y + h)); arr = np.array(im).astype(int); al = arr[..., 3] > 30
        if al.sum() < 300: continue
        ys_ = np.where(al.any(axis=1))[0]
        if ys_.max() < h - 6 or ys_.min() > 6: continue   # fatia cortada (pedaço de algo maior): pula
        r_, g_, b_ = arr[..., 0][al], arr[..., 1][al], arr[..., 2][al]
        green = ((g_ > r_ + 8) & (g_ > b_)).mean()
        sandy = ((r_ > 150) & (g_ > 120) & (b_ < 120)).mean()
        kind = 'palm' if green > .25 and h > 260 else 'bush' if green > .25 else 'rock' if sandy < .3 and h < 230 else None
        if not kind or len(kinds[kind]) >= 14: continue
        tid = D + 100 * (1 + ['palm', 'rock', 'bush'].index(kind)) + len(kinds[kind])
        out[tid] = (im.resize((max(1, round(w * .75)), max(1, round(h * .75))), Image.LANCZOS), (ax * .75, ay * .75)); kinds[kind].append(tid)
    return out, kinds


def noise(w, h, scale, rng):
    gw, gh = w // scale + 2, h // scale + 2
    g = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / scale
    x0, y0 = xs.astype(int), ys.astype(int); fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = g[y0, x0], g[y0, x0 + 1], g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def iso_wall(tex, H, mirror=False, hole=None, cap=(70, 52, 34), dark=1.0):
    """parede isométrica de 1 tile, sintetizada a partir de uma textura (sem desenho do Flare para isso)"""
    from PIL import ImageDraw, ImageEnhance
    L, t = 48, 6
    tw, th = tex.size; k = H / th
    tx = tex.resize((max(1, round(tw * k)), H), Image.LANCZOS)
    face = Image.new('RGBA', (L, H))
    for x0 in range(0, L, tx.width): face.paste(tx, (x0, 0))
    dr = ImageDraw.Draw(face)
    if hole == 'window':
        dr.rectangle((14, H * .25, 34, H * .55), fill=(18, 14, 10, 255), outline=(60, 44, 26, 255), width=3)
        dr.line((24, H * .25, 24, H * .55), fill=(60, 44, 26, 255), width=2)
    elif hole == 'door':
        dr.rectangle((12, H * .18, 36, H), fill=(74, 50, 28, 255), outline=(40, 26, 14, 255), width=3)
        for xx in (18, 24, 30): dr.line((xx, H * .18 + 3, xx, H), fill=(52, 34, 18, 255), width=1)
        dr.ellipse((31, H * .6, 34, H * .6 + 3), fill=(190, 160, 90, 255))
    if dark != 1.0: face = ImageEnhance.Brightness(face).enhance(dark)
    out = face.transform((L, H + 24 + t), Image.AFFINE, (1, 0, 0, -0.5, 1, -t), Image.BICUBIC)
    d2 = ImageDraw.Draw(out)
    d2.polygon([(0, t), (L, t + 24), (L - 5, t + 24 - 5), (-5, t - 5)], fill=cap + (255,))
    d2.line([(0, t), (L, t + 24)], fill=tuple(max(0, c - 25) for c in cap) + (255,), width=1)
    if mirror: out = out.transpose(Image.FLIP_LEFT_RIGHT)
    return out, (24, t + H + 12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flare', required=True); ap.add_argument('--cells', default='8,3,22,23'); ap.add_argument('--cell', type=int, default=32)
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    CELL = a.cell
    cx0, cy0, cw, ch = [int(v) for v in a.cells.split(',')]
    L = json.load(open(os.path.join(ROOT, 'data', 'world_layout.json'), encoding='utf-8'))
    mons = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))['monsters']}
    W, H = cw * CELL, ch * CELL
    rng = random.Random(a.seed); nrng = np.random.default_rng(a.seed)
    rows = L['rows']
    DIMG, DS = desert_assets(TCOM)
    print('deserto:', {k: len(v) for k, v in DS.items()})

    jx, jy = (noise(W, H, 28, nrng) - .5) * CELL * 1.1, (noise(W, H, 28, nrng) - .5) * CELL * 1.1
    ys, xs = np.mgrid[0:H, 0:W]
    sx = np.clip(xs + jx, 0, W - 1).astype(int) // CELL + cx0; sy = np.clip(ys + jy, 0, H - 1).astype(int) // CELL + cy0
    bnames = sorted({c['biome'] for r in rows for c in r} | {'water'})
    bidx = {b: i for i, b in enumerate(bnames)}
    cellb = np.array([[bidx['water'] if c.get('water') else bidx[c['biome']] for c in r] for r in rows])
    biome_i = cellb[sy, sx]
    biome = lambda x, y: bnames[biome_i[min(H - 1, max(0, y)), min(W - 1, max(0, x))]]
    forest = noise(W, H, 18, nrng); detail = noise(W, H, 5, nrng); patch = noise(W, H, 9, nrng)

    bg = np.zeros((H, W), np.uint16); obj = np.zeros((H, W), np.uint16); col = np.zeros((H, W), np.uint16)
    for y in range(H):
        for x in range(W):
            b = biome(x, y)
            if b == 'water': bg[y, x] = rng.choice(G['water']); col[y, x] = 2
            elif b == 'north': bg[y, x] = rng.choice(N['snow2'] if patch[y, x] > .62 else N['snow'])
            elif b == 'ruins': bg[y, x] = rng.choice(RU['floor'] if patch[y, x] > .66 else RU['dirt'])
            elif b == 'outremer': bg[y, x] = rng.choice(DS['sand'])
            else: bg[y, x] = rng.choice(G['grass'])
    # borda neve/grama com tiles de neve rala, para a transição não ser uma linha seca
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if biome(x, y) == 'north' and any(biome(x + dx, y + dy) not in ('north', 'water') for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))):
                bg[y, x] = rng.choice(N['mix'])
    clear = np.zeros((H, W), bool)

    def put(x, y, t):
        if 0 <= x < W and 0 <= y < H and col[y, x] != 2:
            obj[y, x] = t; col[y, x] = 0 if t in WALKABLE else 1

    def carve(x, y, r, paint=None):
        for j in range(-r, r + 1):
            for i in range(-r, r + 1):
                X, Y = x + i, y + j
                if 0 <= X < W and 0 <= Y < H and i * i + j * j <= r * r:
                    clear[Y, X] = True
                    if col[Y, X] == 2: continue
                    if paint: bg[Y, X] = rng.choice(paint(X, Y))

    def road_tiles(X, Y):
        b = biome(X, Y)
        return N['snow2'] if b == 'north' else RU['floor'] if b == 'ruins' else RU['dirt'] if b == 'outremer' else G['cobble']

    center = lambda c: ((c[0] - cx0) * CELL + CELL // 2, (c[1] - cy0) * CELL + CELL // 2)
    inside = lambda c: cx0 <= c[0] < cx0 + cw and cy0 <= c[1] < cy0 + ch
    for r in L['roads']:
        cs = r['cells']
        for p, q in zip(cs, cs[1:]):
            if not (inside(p) or inside(q)): continue
            (x0, y0), (x1, y1) = center(p), center(q)
            n = int(math.hypot(x1 - x0, y1 - y0))
            for k in range(n + 1):
                t = k / max(1, n)
                x = int(x0 + (x1 - x0) * t + math.sin(t * 6.283 + x0) * 3); y = int(y0 + (y1 - y0) * t + math.cos(t * 6.283 + y0) * 3)
                carve(x, y, 1, road_tiles); carve(x, y, 3)

    zones, houses, towns = [], [], []
    for s in L['settlements']:
        if not inside(s['cell']): continue
        tx, ty = center(s['cell']); b = biome(tx, ty)
        Rr = 20 if s.get('capital') else 14
        carve(tx, ty, Rr + 5)
        floor = road_tiles
        def pave(X, Y):
            if 0 <= X < W and 0 <= Y < H and col[Y, X] != 2: bg[Y, X] = rng.choice(floor(X, Y))
        for j in range(-5, 6):
            for i in range(-5, 6): pave(tx + i, ty + j)
        for i in range(-Rr, Rr + 1):
            for k in (-1, 0, 1): pave(tx + i, ty + k); pave(tx + k, ty + i)
        put(tx, ty, RU['well'][0]) if 'camp' not in s.get('role', '') else None
        tints = ['#6b4a2e', '#4a3a2a', '#7a5a3a', '#55402c', '#5e5040', '#6a3e2a', '#3e3a36']
        role = s.get('role', '')
        style = ('acampamento' if 'camp' in role or 'watch' in role else 'forte' if 'keep' in role or 'fort' in role
                 else 'mosteiro' if 'abbey' in role else 'vila')
        snow = b == 'north'
        crate, logs, fire, tent = (N['crate'], N['logs'], N['fire'], N['tent']) if snow else (G['crate'], G['logs'], G['fire'], G['tent'])
        spots = [(tx - 13, ty - 13), (tx + 7, ty - 13), (tx - 13, ty + 7), (tx + 7, ty + 7), (tx - 20, ty - 3), (tx + 14, ty - 3), (tx - 3, ty - 20), (tx - 3, ty + 14)]
        rng.shuffle(spots)
        CASAS = {'north': ['north_log_01', 'north_stone_01'], 'outremer': ['desert_adobe_01', 'desert_adobe_02'],
                 'ruins': ['ruins_chapel_01', 'plains_stone_01', 'plains_timber_02']}.get(b, ['plains_timber_01', 'plains_timber_02', 'plains_cabin_01', 'plains_cabin_02', 'plains_stone_01'])
        if b == 'outremer':   # no deserto: casas de adobe entre palmeiras
            for k in range(8):
                an = k / 8 * 6.283; put(int(tx + math.cos(an) * (Rr - 2)), int(ty + math.sin(an) * (Rr - 2)), rng.choice(DS['palm']))
        if style == 'vila':
            for k, (hx, hy) in enumerate(spots[:6 if s.get('capital') else 3]):
                houses.append([CASAS[(k + len(houses)) % len(CASAS)], hx, hy, rng.choice(tints) if 'cabin' in CASAS[(k + len(houses)) % len(CASAS)] else None])
            for k in range(5): put(tx - 4 + (k % 3) * 2, ty + 4 + (k // 3) * 2, rng.choice(crate + logs + RU['barrel']))
            put(tx + 4, ty - 4, G['anvil'][0]); put(tx + 4, ty + 4, fire[0]); put(tx + 6, ty + 1, rng.choice(G['sign']))
            if snow:
                for k in range(3): put(tx + rng.randint(-Rr, Rr), ty + rng.randint(-Rr, Rr), rng.choice(N['snowman'] + N['cart']))
            else:
                fx, fy = tx + Rr - 3, ty - Rr + 1
                for i in range(7):
                    put(fx + i, fy, G['fence_a'][0]); put(fx + i, fy + 6, G['fence_a'][0]); put(fx, fy + i, G['fence_b'][0]); put(fx + 6, fy + i, G['fence_b'][0])
                for j in range(2, 5):
                    for i in range(2, 5): put(fx + i, fy + j, rng.choice(G['plant']))
        elif style == 'acampamento':   # barracas em roda, fogueira, lenha e caixotes
            for k in range(7):
                an = k / 7 * 6.283; put(int(tx + math.cos(an) * 7), int(ty + math.sin(an) * 7), rng.choice(tent))
            put(tx, ty, fire[0])
            for k in range(6): put(tx + rng.randint(-4, 4), ty + rng.randint(-4, 4), rng.choice(crate + logs + (RU['urn'] + RU['sword'] if 'relic' in role else G['stump'])))
        elif style == 'forte':         # muralha de pedra em anel com portões nas estradas
            for k in range(44):
                an = k / 44 * 6.283; x, y = int(tx + math.cos(an) * 12), int(ty + math.sin(an) * 12)
                if abs(x - tx) > 2 and abs(y - ty) > 2: put(x, y, rng.choice(RU['pillar']))
            for j in range(-8, 9):
                for i in range(-8, 9):
                    if i * i + j * j < 70: pave(tx + i, ty + j) if False else None
            for k in range(4): put(tx + rng.choice([-5, 5]), ty + rng.choice([-5, 5]), rng.choice(RU['statue'] + RU['barrel']))
            put(tx + 3, ty + 3, fire[0])
            houses.append([{'north': 'north_stone_01', 'outremer': 'desert_adobe_02'}.get(b, 'plains_stone_01'), tx - 9, ty - 9, None])
        else:                          # mosteiro: pátio de pedra, santuário, horta de ervas
            for j in range(-7, 8):
                for i in range(-7, 8):
                    if 0 <= ty + j < H and 0 <= tx + i < W and col[ty + j, tx + i] != 2: bg[ty + j, tx + i] = rng.choice(RU['floor'])
            put(tx, ty, rng.choice(RU['shrine'])); put(tx - 3, ty, rng.choice(RU['statue'])); put(tx + 3, ty, rng.choice(RU['statue']))
            for j in range(3):
                for i in range(4): put(tx + 9 + i, ty - 2 + j, rng.choice(RU['plant']))
            houses.append(['ruins_chapel_01' if b != 'north' else 'north_stone_01', tx - 14, ty - 11, None])
        z = {'id': s['id'], 'name': s['name'], 'kind': 'village', 'biome': b, 'origin': [tx - Rr - 5, ty - Rr - 5], 'size': [2 * Rr + 10, 2 * Rr + 10], 'chunks': [], 'center': [tx, ty]}
        zones.append(z); towns.append({'id': s['id'], 'name': s['name'], 'center': [tx, ty]})

    # --- lugares de caça: cena e monstros pelo bioma e pela distância da vila mais próxima
    towns_xy = [t['center'] for t in towns]

    def monsters_for(b, lv, n=3):
        bb = {'forest': 'forest', 'north': 'north', 'ruins': 'ruins', 'mountains': 'mountains', 'swamp': 'swamp', 'outremer': 'outremer'}.get(b, 'plains')
        ok = sorted([m for m in mons.values() if bb in m['biomes'] and 'boss' not in m['id']], key=lambda m: abs(m['level'] - lv))
        return [m['id'] for m in ok[:n]] or ['goblin']

    def scene(x, y, b, lv):
        r = 7; carve(x, y, r)
        if b == 'north':
            kind = rng.choice(['acampamento', 'cemiterio', 'pedras'])
            if kind == 'acampamento':
                for _ in range(4): put(x + rng.randint(-5, 5), y + rng.randint(-5, 5), rng.choice(N['tent']))
                put(x, y, N['fire'][0]); put(x + 2, y + 1, rng.choice(N['crate']))
            elif kind == 'cemiterio':
                for j in range(-4, 5, 2):
                    for i in range(-5, 6, 2): put(x + i, y + j, rng.choice(N['grave']))
            else:
                for _ in range(12):
                    an = rng.random() * 6.283; d = rng.uniform(3, 7); put(int(x + math.cos(an) * d), int(y + math.sin(an) * d), rng.choice(N['boulder']))
            name = {'acampamento': ('Acampamento na Neve', 'Snow Camp'), 'cemiterio': ('Túmulos Gelados', 'Frozen Graves'), 'pedras': ('Pedras do Gelo', 'Ice Stones')}[kind]
        elif b == 'ruins':
            kind = rng.choice(['templo', 'estatuas', 'altar'])
            for j in range(-6, 7):
                for i in range(-6, 7):
                    if i * i + j * j < 30 and 0 <= y + j < H and 0 <= x + i < W and col[y + j, x + i] != 2: bg[y + j, x + i] = rng.choice(RU['floor'])
            for k in range(10):
                an = k / 10 * 6.283; put(int(x + math.cos(an) * 6), int(y + math.sin(an) * 6), rng.choice(RU['pillar'] + RU['rubble']))
            if kind == 'templo': put(x, y, RU['circle'][0])
            elif kind == 'estatuas':
                for k in range(4): put(x + rng.choice([-3, 3]), y + rng.choice([-3, 3]), rng.choice(RU['statue']))
            else: put(x, y, rng.choice(RU['shrine'])); put(x + 2, y, rng.choice(RU['urn'])); put(x - 2, y, rng.choice(RU['sword']))
            name = {'templo': ('Templo Caído', 'Fallen Temple'), 'estatuas': ('Jardim das Estátuas', 'Statue Garden'), 'altar': ('Altar Profanado', 'Defiled Altar')}[kind]
        elif b == 'outremer':
            kind = rng.choice(['oasis', 'ninho', 'ruina'])
            if kind == 'oasis':
                for k in range(6):
                    an = k / 6 * 6.283; put(int(x + math.cos(an) * 5), int(y + math.sin(an) * 5), rng.choice(DS['palm']))
                put(x, y, RU['well'][0])
            elif kind == 'ninho':
                for _ in range(12):
                    an = rng.random() * 6.283; d = rng.uniform(3, 7); put(int(x + math.cos(an) * d), int(y + math.sin(an) * d), rng.choice(DS['rock']))
            else:
                for k in range(8):
                    an = k / 8 * 6.283; put(int(x + math.cos(an) * 6), int(y + math.sin(an) * 6), rng.choice(RU['pillar'] + RU['rubble']))
                put(x, y, rng.choice(RU['statue']))
            name = {'oasis': ('Oásis Perdido', 'Lost Oasis'), 'ninho': ('Ninho nas Dunas', 'Dune Nest'), 'ruina': ('Ruína nas Areias', 'Ruin in the Sands')}[kind]
        elif b == 'mountains':
            for _ in range(14):
                an = rng.random() * 6.283; d = rng.uniform(3, 7); put(int(x + math.cos(an) * d), int(y + math.sin(an) * d), rng.choice(G['rock'] + G['pillar']))
            put(x, y, G['fire'][0]); name = ('Covil nas Pedras', 'Rock Den')
        else:
            kind = rng.choice(['goblins', 'goblins', 'cemiterio', 'ruina'])
            if kind == 'goblins':
                for _ in range(4): put(x + rng.randint(-5, 5), y + rng.randint(-5, 5), rng.choice(G['tent']))
                put(x, y, G['fire'][0]); put(x + 2, y + 1, rng.choice(G['crate'])); put(x - 2, y + 2, rng.choice(G['logs']))
            elif kind == 'cemiterio':
                for j in range(-4, 5, 2):
                    for i in range(-5, 6, 2): put(x + i, y + j, rng.choice(G['grave']))
                for i in (-6, 6): put(x + i, y - 5, rng.choice(G['dead']))
            else:
                for k in range(8):
                    an = k / 8 * 6.283; put(int(x + math.cos(an) * 5), int(y + math.sin(an) * 5), rng.choice(G['pillar']))
                put(x, y, G['circle'][0])
            name = {'goblins': ('Acampamento Goblin', 'Goblin Camp'), 'cemiterio': ('Cemitério Antigo', 'Old Graveyard'), 'ruina': ('Círculo de Pedra', 'Stone Circle')}[kind]
        mlist = monsters_for(b, lv)
        sp = [{'monster': m, 'count': [2, 4] if i == 0 else [1, 2], 'level': lv} for i, m in enumerate(mlist)]
        return {'id': f'poi_{x}_{y}', 'name': {'pt': name[0], 'en': name[1]}, 'rect': [x - r, y - r, 2 * r, 2 * r], 'spawns': sp, 'biome': b}

    chunks = []
    target = int(W * H / 5200)
    for _ in range(target * 30):
        if len(chunks) >= target: break
        x, y = rng.randint(14, W - 15), rng.randint(14, H - 15)
        b = biome(x, y)
        if b == 'water' or clear[y, x] or any(col[y + j, x + i] == 2 for j in (-7, 0, 7) for i in (-7, 0, 7)): continue
        dmin = min(math.hypot(x - p, y - q) for p, q in towns_xy) if towns_xy else 999
        if dmin < 34 or any(math.hypot(x - c['rect'][0] - 7, y - c['rect'][1] - 7) < 30 for c in chunks): continue
        lv = max(1, min(18, int(dmin / 26) + 1 + {'north': 4, 'ruins': 4, 'mountains': 3, 'outremer': 6}.get(b, 0)))
        chunks.append(scene(x, y, b, lv))
    # chefes do mapa-guia que caem na região
    for bo in L['bosses']:
        if inside(bo['cell']) and bo.get('monster_in_data') in mons:
            x, y = center(bo['cell'])
            if col[y, x] == 2: continue
            carve(x, y, 6)
            for _ in range(10):
                an = rng.random() * 6.283; d = rng.uniform(4, 6); put(int(x + math.cos(an) * d), int(y + math.sin(an) * d), rng.choice(G['rock'] + RU['pillar']))
            chunks.append({'id': 'chefe_' + bo['id'], 'name': bo['name'], 'rect': [x - 6, y - 6, 12, 12], 'boss': bo['monster_in_data'],
                           'spawns': [{'monster': bo['monster_in_data'], 'count': [1, 1], 'level': bo.get('level', 10)}]})
    zones.append({'id': 'ermos', 'name': {'pt': 'Ermos de Aelória', 'en': 'Aeloria Wilds'}, 'kind': 'hunt', 'origin': [0, 0], 'size': [W, H], 'chunks': chunks})

    # --- vegetação por bioma
    for y in range(H):
        for x in range(W):
            if obj[y, x] or clear[y, x] or col[y, x] == 2: continue
            b, f, d, r = biome(x, y), forest[y, x], detail[y, x], rng.random()
            if x < 2 or y < 2 or x >= W - 2 or y >= H - 2:
                put(x, y, rng.choice(N['dead'] if b == 'north' else G['pine'])); continue
            if b == 'forest':
                dens = 0.08 + max(0, f - 0.35) * 0.9
                if r < dens: put(x, y, rng.choice(G['pine'] * 2 + G['oak']))
                elif r < dens + 0.05: put(x, y, rng.choice(G['shrub'] + G['bush'] + G['stump']))
            elif b == 'north':
                if r < 0.02 + max(0, f - 0.5) * 0.25: put(x, y, rng.choice(N['dead'] + G['pine']))
                elif r < 0.05: put(x, y, rng.choice(N['shrub'] + N['grass']))
                elif r < 0.058: put(x, y, rng.choice(N['rock'] + N['boulder']))
            elif b == 'ruins':
                if r < 0.012: put(x, y, rng.choice(RU['rubble']))
                elif r < 0.016: put(x, y, rng.choice(RU['pillar']))
                elif r < 0.03: put(x, y, rng.choice(G['dead'] + RU['autumn']))
                elif r < 0.07: put(x, y, rng.choice(RU['plant'] + G['tall']))
            elif b == 'mountains':
                if r < 0.03 + max(0, patch[y, x] - .55) * .3: put(x, y, rng.choice(G['rock']))
                elif r < 0.05: put(x, y, rng.choice(G['pine'] + G['pillar']))
                elif r < 0.08: put(x, y, rng.choice(G['tall'] + G['shrub']))
            elif b == 'outremer':
                if r < 0.004 + max(0, f - 0.6) * 0.12: put(x, y, rng.choice(DS['palm']))
                elif r < 0.02: put(x, y, rng.choice(DS['rock'] + DS['bush']))
            elif b in ('swamp',):
                if r < 0.05: put(x, y, rng.choice(G['dead']))
                elif r < 0.16: put(x, y, rng.choice(G['reed'] + G['shrub']))
            else:
                dens = 0.006 + max(0, f - 0.55) * 0.5
                if r < dens: put(x, y, rng.choice(G['oak'] * 2 + G['birch']))
                elif r < dens + 0.06 * d: put(x, y, rng.choice(G['tall'] * 2 + G['flower'] + G['bush'] + G['shrub']))
                elif r < dens + 0.065 * d + 0.002: put(x, y, rng.choice(G['rock']))

    # --- atlas com os tiles usados dos três tilesets
    sets = {0: load_tileset(a.flare, 'tilesetdefs/tileset_grassland.txt'), S: load_tileset(a.flare, 'tilesetdefs/tileset_snowplains.txt'),
            R: load_tileset(a.flare, 'tilesetdefs/tileset_ruins.txt')}
    used = set(np.unique(bg).tolist()) | set(np.unique(obj).tolist()) - {0}
    imgs, meta = {}, {}
    for t in sorted(used):
        if not t: continue
        if t >= D:
            im, (ox, oy) = DIMG[t]; imgs[t] = im; meta[t] = (ox, oy); continue
        base = R if t >= R else S if t >= S else 0
        src, x, y, w, h, ox, oy = sets[base][t - base]
        imgs[t] = src.crop((x, y, x + w, y + h)).resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS)
        meta[t] = (ox * SCALE, oy * SCALE)
    # peças de construção (sempre no atlas): ids do Flare + piso de tábua recortado do cais
    BUILD = {'floor_wood': [D + 900], 'floor_stone': [R + 24, R + 25], 'wall_wood': [208, 215], 'wall_stone': [R + 223, R + 227],
             'door_wood': [212, 212], 'door_iron': [R + 364, R + 364], 'window_wood': [210, 211], 'window_iron': [R + 360, R + 365],
             'fence_wood': [104, 105], 'fence_stone': [R + 48, R + 49], 'gate_wood': [110, 111], 'gate_iron': [R + 361, R + 361],
             'stump': G['stump'], 'anvil': G['anvil']}
    src, x, y, w, h, ox, oy = sets[0][200]
    plank = src.crop((x, y, x + w, y + 96)).resize((96, 48), Image.LANCZOS)
    DIMG[D + 900] = (plank, (48, 24))
    def crop_full(base, tid, fx0, fy0, fx1, fy1):
        src, x, y, w, h, ox, oy = sets[base][tid]
        return src.crop((x + int(w * fx0), y + int(h * fy0), x + int(w * fx1), y + int(h * fy1)))
    wood = crop_full(0, 215, .12, .3, .8, .92); stone = crop_full(R, 228, .2, .35, .8, .8)
    for n, (tex, wh, cap, hole) in enumerate([(wood, 62, (92, 66, 40), None), (stone, 68, (150, 146, 138), None),
                                             (wood, 62, (92, 66, 40), 'window'), (stone, 68, (150, 146, 138), 'window'),
                                             (wood, 62, (92, 66, 40), 'door')]):
        for m in (0, 1): DIMG[D + 910 + n * 2 + m] = iso_wall(tex, wh, mirror=bool(m), hole=hole, cap=cap, dark=0.82 if m else 1.0)
    BUILD.update({'wall_wood': [D + 910, D + 911], 'wall_stone': [D + 912, D + 913], 'window_wood': [D + 914, D + 915],
                  'window_iron': [D + 916, D + 917], 'door_wood': [D + 918, D + 919], 'door_iron': [R + 364, R + 361]})
    for ids in BUILD.values():
        for t in ids:
            if t in imgs: continue
            if t >= D: im, (ox, oy) = DIMG[t]; imgs[t] = im; meta[t] = (ox, oy); continue
            base = R if t >= R else S if t >= S else 0
            src, x, y, w, h, ox, oy = sets[base][t - base]
            imgs[t] = src.crop((x, y, x + w, y + h)).resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS); meta[t] = (ox * SCALE, oy * SCALE)
    NODES = {'tree': G['oak'] + G['birch'] + G['pine'] + G['dead'] + N['dead'] + DS['palm'] + RU['autumn'],
             'rock': G['rock'] + N['rock'] + N['boulder'] + DS['rock'] + RU['rubble']}
    atlas, pos = pack(imgs)
    d = os.path.join(ROOT, 'engine', 'dev_assets', 'flare'); os.makedirs(d, exist_ok=True)
    atlas.save(os.path.join(d, 'mundo_tiles.webp'), 'WEBP', quality=90, method=6)
    home = next((t['center'] for t in towns if 'trigo' in t['id']), towns[0]['center'] if towns else [W // 2, H // 2])
    enc = lambda m: base64.b64encode(m.astype('<u2').tobytes()).decode()
    data = {'version': 3, 'id': 'mundo', 'source': f'build/gen_world.py células {a.cells} x{CELL} semente {a.seed}', 'w': W, 'h': H, 'tile': [96, 48],
            'offset': [0, 0], 'hero': home, 'atlas': 'mundo_tiles.webp', 'enc': 'u16b64',
            'tiles': {str(t): [*pos[t], round(meta[t][0], 2), round(meta[t][1], 2)] for t in pos},
            'background': enc(bg), 'object': enc(obj), 'collision': enc(col), 'exits': [], 'spawns': [],
            'zones': zones, 'houses': houses, 'towns': towns, 'home': home, 'build': BUILD, 'nodes': NODES}
    json.dump(data, open(os.path.join(d, 'mundo.json'), 'w'), separators=(',', ':'))
    cnt = {}
    for y in range(0, H, 4):
        for x in range(0, W, 4): cnt[biome(x, y)] = cnt.get(biome(x, y), 0) + 1
    print(f'mundo {W}x{H}: vilas {[t["name"]["pt"] for t in towns]}, {len(houses)} casas, {len(chunks)} lugares, biomas {cnt}, atlas {atlas.size}')


if __name__ == '__main__':
    main()

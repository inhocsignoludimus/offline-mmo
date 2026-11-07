#!/usr/bin/env python3
"""Gera o mundo contínuo a partir do mapa-guia data/world_layout.json, com os
tiles de grassland do Flare usados do jeito certo (sem penhasco solto).

    python3 build/gen_world.py --flare <flare-game> [--cells 9,18,6,6] [--seed 7]

Saída: engine/dev_assets/flare/mundo.json + mundo_tiles.webp (mesmo formato dos
mapas importados) com, a mais: zones (vilas e áreas de caça com spawns),
houses (casas em camadas com posição e cor do telhado) e towns.
Cada célula do mapa-guia = 64x64 tiles.
"""
import argparse, json, math, os, random, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_dev_assets import load_tileset, pack, SCALE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL = 64

# --- catálogo dos tiles de grassland do Flare (ids do tileset_grassland.txt)
GRASS = list(range(16, 32)); COBBLE = list(range(32, 48)); WATER = list(range(176, 192))
TENT = [72, 73, 74, 75]; CRATE = [96, 97, 98, 99]; LOGPILE = [100, 101]; FIRE = 102; ANVIL = 103
FENCE_A, FENCE_B = [104, 107], [105, 106]   # cerca nas duas diagonais
BUSH = [112, 113]; REED = [114, 115]; PLANT = [116, 117]; FLOWER = [118, 119]; SHRUB = [120, 121, 122, 123]; TALLGRASS = [124, 125, 126, 127]
ROCK = [128, 129, 130, 131]; PILLAR = [132, 133, 134, 135]; STUMP = [136]; AXESTUMP = 137; SIGN = [138, 139]; GRAVE = [140, 141, 142, 143]
BIRCH = [240, 241, 242, 243]; DEAD = [244, 245, 246, 247]; PINE = [248, 249, 250, 251]; OAK = [252, 253, 254, 255]; CIRCLE = 264
BLOCKS = set(TENT + CRATE + LOGPILE + [FIRE, ANVIL] + FENCE_A + FENCE_B + ROCK + PILLAR + STUMP + [AXESTUMP] + SIGN + GRAVE + BIRCH + DEAD + PINE + OAK)


def noise(w, h, scale, rng):
    """ruído de valor suave (bilinear entre pontos aleatórios)"""
    gw, gh = w // scale + 2, h // scale + 2
    g = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / scale
    x0, y0 = xs.astype(int), ys.astype(int); fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = g[y0, x0], g[y0, x0 + 1], g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flare', required=True); ap.add_argument('--cells', default='9,18,6,6'); ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()
    cx0, cy0, cw, ch = [int(v) for v in a.cells.split(',')]
    L = json.load(open(os.path.join(ROOT, 'data', 'world_layout.json'), encoding='utf-8'))
    mons = {m['id']: m for m in json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))['monsters']}
    W, H = cw * CELL, ch * CELL
    rng = random.Random(a.seed); nrng = np.random.default_rng(a.seed)
    cell = lambda x, y: L['rows'][cy0 + y // CELL][cx0 + x // CELL]

    # bioma por tile, com a fronteira das células deformada por ruído (nada de bloco quadrado)
    jx, jy = (noise(W, H, 40, nrng) - .5) * 70, (noise(W, H, 40, nrng) - .5) * 70
    biome = np.empty((H, W), dtype=object); level = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            sx, sy = int(min(W - 1, max(0, x + jx[y, x]))), int(min(H - 1, max(0, y + jy[y, x])))
            c = cell(sx, sy); biome[y, x] = 'water' if c.get('water') else c['biome']; level[y, x] = c.get('level', 1)
    forest = noise(W, H, 22, nrng); detail = noise(W, H, 6, nrng); rocks = noise(W, H, 14, nrng)

    bg = [[rng.choice(GRASS) for _ in range(W)] for _ in range(H)]
    obj = [[0] * W for _ in range(H)]
    col = [[0] * W for _ in range(H)]
    clear = np.zeros((H, W), bool)   # onde não pode nascer mato (estrada, vila, acampamento)

    def put(x, y, t):
        if 0 <= x < W and 0 <= y < H:
            obj[y][x] = t; col[y][x] = 1 if t in BLOCKS else 0

    def carve(x, y, r, cobble=False):
        for j in range(-r, r + 1):
            for i in range(-r, r + 1):
                X, Y = x + i, y + j
                if 0 <= X < W and 0 <= Y < H and i * i + j * j <= r * r:
                    clear[Y, X] = True
                    if cobble: bg[Y][X] = rng.choice(COBBLE)

    # --- estradas do mapa-guia (centro de célula a centro de célula, com curvas)
    def road(p, q):
        (x0, y0), (x1, y1) = p, q
        n = int(math.hypot(x1 - x0, y1 - y0))
        for k in range(n + 1):
            t = k / max(1, n)
            x = x0 + (x1 - x0) * t + math.sin(t * math.pi * 2 + x0) * 4
            y = y0 + (y1 - y0) * t + math.cos(t * math.pi * 2 + y0) * 4
            carve(int(x), int(y), 1, cobble=True); carve(int(x), int(y), 3)
    center = lambda c: ((c[0] - cx0) * CELL + CELL // 2, (c[1] - cy0) * CELL + CELL // 2)
    inside = lambda c: cx0 <= c[0] < cx0 + cw and cy0 <= c[1] < cy0 + ch
    for r in L['roads']:
        cs = r['cells']
        for p, q in zip(cs, cs[1:]):
            if inside(p) or inside(q):
                road(center(p), center(q))

    zones, houses, towns = [], [], []
    # --- vilas: praça, ruas, casas viradas para a praça, horta cercada, poço, mercado, cemitério
    for s in L['settlements']:
        if not inside(s['cell']):
            continue
        tx, ty = center(s['cell'])
        R = 22 if s.get('capital') else 16
        carve(tx, ty, R + 6)
        for j in range(-6, 7):
            for i in range(-6, 7):
                bg[ty + j][tx + i] = rng.choice(COBBLE)
        put(tx, ty + 2, rng.choice(SIGN))                  # placa no meio da praça
        for i in range(-R, R + 1, 1):                      # ruas em cruz
            for k in (-1, 0, 1):
                bg[ty + k][tx + i] = rng.choice(COBBLE); bg[ty + i][tx + k] = rng.choice(COBBLE)
        # casas: em volta da praça, nos 4 quadrantes, com tamanhos e telhados variados
        tints = ['#6b4a2e', '#4a3a2a', '#7a5a3a', '#55402c', '#5e5040', '#6a3e2a']
        spots = [(tx - 14, ty - 14), (tx + 8, ty - 14), (tx - 14, ty + 8), (tx + 8, ty + 8), (tx - 22, ty - 4), (tx + 16, ty - 4), (tx - 4, ty - 22), (tx - 4, ty + 16)]
        rng.shuffle(spots)
        nh = 6 if s.get('capital') else 4
        for k, (hx, hy) in enumerate(spots[:nh]):
            hid = ['plains_cabin_01', 'plains_cabin_02'][k % 2]
            houses.append([hid, hx, hy, tints[rng.randrange(len(tints))]])
        # mercado: caixotes, lenha, bigorna do ferreiro, fogueira
        for k, t in enumerate(CRATE + LOGPILE):
            put(tx - 5 + (k % 3) * 2, ty + 5 + (k // 3) * 2, t)
        put(tx + 5, ty - 5, ANVIL); put(tx + 5, ty + 5, FIRE); put(tx + 7, ty + 1, rng.choice(SIGN))
        # horta cercada fora da praça
        fx, fy = tx + R - 4, ty - R + 2
        for i in range(8):
            put(fx + i, fy, FENCE_A[0]); put(fx + i, fy + 7, FENCE_A[0]); put(fx, fy + i, FENCE_B[0]); put(fx + 7, fy + i, FENCE_B[0])
        for j in range(2, 6):
            for i in range(2, 6):
                put(fx + i, fy + j, rng.choice(PLANT))
        # cemitério pequeno na saída
        gx, gy = tx - R + 2, ty + R - 6
        for j in range(0, 6, 2):
            for i in range(0, 8, 2):
                put(gx + i, gy + j, rng.choice(GRAVE))
        zones.append({'id': s['id'], 'name': s['name'], 'kind': 'village', 'biome': s['biome'], 'origin': [tx - R - 6, ty - R - 6], 'size': [2 * R + 12, 2 * R + 12], 'chunks': [], 'center': [tx, ty]})
        towns.append({'id': s['id'], 'name': s['name'], 'center': [tx, ty]})

    # --- lugares de caça: acampamento goblin, cemitério antigo, ruínas, ninho de wyvern, poleiro do grifo
    def pick(ids, lv):
        ok = [m for m in ids if m in mons]
        return ok or ['goblin']

    def poi(kind, x, y, lv):
        r = 7
        carve(x, y, r)
        if kind == 'goblins':
            for k in range(4): put(x + rng.randint(-5, 5), y + rng.randint(-5, 5), rng.choice(TENT))
            put(x, y, FIRE); put(x + 2, y + 1, rng.choice(CRATE)); put(x - 2, y + 2, rng.choice(LOGPILE))
            sp = [('goblin', [3, 5]), ('goblin_spearman', [1, 2]), ('goblin_runner', [1, 2])] if lv < 6 else [('goblin_elite', [2, 4]), ('hobgoblin', [1, 2]), ('hobgoblin_archer', [1, 2])]
            name = {'pt': 'Acampamento Goblin', 'en': 'Goblin Camp'}
        elif kind == 'cemiterio':
            for j in range(-4, 5, 2):
                for i in range(-5, 6, 2): put(x + i, y + j, rng.choice(GRAVE))
            for i in (-6, 6): put(x + i, y - 5, rng.choice(DEAD))
            sp = [('skeleton', [2, 4]), ('zombie', [2, 3]), ('skeleton_archer', [1, 2])] if lv < 7 else [('skeleton_knight', [1, 3]), ('zombie_rotting', [2, 3]), ('skeleton_mage', [1, 2])]
            name = {'pt': 'Cemitério Antigo', 'en': 'Old Graveyard'}
        elif kind == 'ruinas':
            for k in range(10):
                ang = k / 10 * 6.283; put(int(x + math.cos(ang) * 6), int(y + math.sin(ang) * 6), rng.choice(PILLAR))
            put(x, y, CIRCLE)
            sp = [('skeleton_mage', [1, 3]), ('skeleton_knight', [1, 2]), ('necromancer', [0, 1])]
            name = {'pt': 'Ruínas do Círculo', 'en': 'Circle Ruins'}
        elif kind == 'wyvern':
            for k in range(12):
                ang = rng.random() * 6.283; d = rng.uniform(4, 7); put(int(x + math.cos(ang) * d), int(y + math.sin(ang) * d), rng.choice(ROCK))
            sp = [('wyvern', [1, 1])]
            name = {'pt': 'Ninho da Wyvern', 'en': 'Wyvern Nest'}
        else:  # grifo
            for k in range(8):
                ang = rng.random() * 6.283; d = rng.uniform(4, 7); put(int(x + math.cos(ang) * d), int(y + math.sin(ang) * d), rng.choice(ROCK + PILLAR))
            sp = [('griffin', [1, 1])] if 'griffin' in mons else [('wyvern_air', [1, 1])]
            name = {'pt': 'Poleiro do Grifo', 'en': 'Griffin Roost'}
        spawns = [{'monster': m, 'count': c, 'level': lv} for m, c in sp if m in mons]
        return {'id': f'{kind}_{x}_{y}', 'name': name, 'rect': [x - r, y - r, 2 * r, 2 * r], 'spawns': spawns, 'boss': spawns[0]['monster'] if kind in ('wyvern', 'grifo') and spawns else None}

    chunks = []
    towns_xy = [t['center'] for t in towns]
    tries = 0
    plan = ['goblins'] * 7 + ['cemiterio'] * 4 + ['ruinas'] * 3 + ['wyvern'] * 2 + ['grifo'] * 1
    for kind in plan:
        for _ in range(200):
            tries += 1
            x, y = rng.randint(20, W - 21), rng.randint(20, H - 21)
            if biome[y, x] == 'water': continue
            dmin = min(math.hypot(x - a, y - b) for a, b in towns_xy) if towns_xy else 999
            need = {'goblins': 40, 'cemiterio': 60, 'ruinas': 90, 'wyvern': 120, 'grifo': 110}[kind]
            if dmin < need or any(math.hypot(x - c['rect'][0] - 7, y - c['rect'][1] - 7) < 40 for c in chunks): continue
            lv = max(1, min(18, int(dmin / 22) + 1))
            chunks.append(poi(kind, x, y, lv)); break
    zones.append({'id': 'ermos', 'name': {'pt': 'Ermos de Aelória', 'en': 'Aeloria Wilds'}, 'kind': 'hunt', 'origin': [0, 0], 'size': [W, H], 'chunks': chunks})

    # --- vegetação por bioma (fora de estradas, vilas e acampamentos)
    for y in range(H):
        for x in range(W):
            if obj[y][x] or clear[y, x]:
                continue
            b, f, d, r = biome[y, x], forest[y, x], detail[y, x], rng.random()
            if b == 'water':
                bg[y][x] = rng.choice(WATER); col[y][x] = 2; continue
            edge = x < 3 or y < 3 or x >= W - 3 or y >= H - 3
            if edge:
                put(x, y, rng.choice(PINE)); continue
            if b in ('forest',):
                dens = 0.08 + max(0, f - 0.35) * 0.9
                if r < dens: put(x, y, rng.choice(PINE + PINE + OAK))
                elif r < dens + 0.05: put(x, y, rng.choice(SHRUB + BUSH + STUMP))
            elif b in ('swamp', 'miasma'):
                if r < 0.05: put(x, y, rng.choice(DEAD))
                elif r < 0.16: put(x, y, rng.choice(REED + SHRUB))
            elif b in ('mountains', 'ruins'):
                if r < 0.04 + max(0, rocks[y, x] - .6) * .4: put(x, y, rng.choice(ROCK))
                elif r < 0.07: put(x, y, rng.choice(PINE + DEAD))
            elif b in ('north',):
                if r < 0.06 * f: put(x, y, rng.choice(PINE))
            else:  # planícies, costa e o resto
                dens = 0.006 + max(0, f - 0.55) * 0.5
                if r < dens: put(x, y, rng.choice(OAK + BIRCH + OAK))
                elif r < dens + 0.06 * d: put(x, y, rng.choice(TALLGRASS + TALLGRASS + FLOWER + BUSH + SHRUB))
                elif r < dens + 0.065 * d + 0.002: put(x, y, rng.choice(ROCK))

    # --- atlas só com os tiles usados
    tiles = load_tileset(a.flare, 'tilesetdefs/tileset_grassland.txt')
    used = {t for row in bg for t in row} | {t for row in obj for t in row if t}
    imgs, meta = {}, {}
    for t in sorted(used):
        src, x, y, w, h, ox, oy = tiles[t]
        imgs[t] = src.crop((x, y, x + w, y + h)).resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS)
        meta[t] = (ox * SCALE, oy * SCALE)
    atlas, pos = pack(imgs)
    d = os.path.join(ROOT, 'engine', 'dev_assets', 'flare'); os.makedirs(d, exist_ok=True)
    atlas.save(os.path.join(d, 'mundo_tiles.webp'), 'WEBP', quality=92, method=6)
    home = towns[0]['center'] if towns else [W // 2, H // 2]
    for t in towns:
        if t['id'] == 'porto_do_trigo' or 'Trigo' in t['name']['pt']: home = t['center']
    data = {'version': 2, 'id': 'mundo', 'source': f'build/gen_world.py células {a.cells} semente {a.seed}', 'w': W, 'h': H, 'tile': [96, 48],
            'offset': [0, 0], 'hero': home, 'atlas': 'mundo_tiles.webp',
            'tiles': {str(t): [*pos[t], round(meta[t][0], 2), round(meta[t][1], 2)] for t in pos},
            'background': bg, 'object': obj, 'collision': col, 'exits': [], 'spawns': [],
            'zones': zones, 'houses': houses, 'towns': towns, 'home': home}
    json.dump(data, open(os.path.join(d, 'mundo.json'), 'w'), separators=(',', ':'))
    print(f'mundo {W}x{H}: {len(towns)} vilas {[t["name"]["pt"] for t in towns]}, {len(houses)} casas, {len(chunks)} lugares de caça, atlas {atlas.size}')


if __name__ == '__main__':
    main()

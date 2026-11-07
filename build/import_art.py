#!/usr/bin/env python3
"""Converte a arte do Ludimus (art/) para o formato da engine (engine/dev_assets/).

    python3 build/import_art.py --flare <flare-game>

- mundo: compõe as peças de data/zones.json (world.pieces) num mapa só
  -> engine/dev_assets/flare/mundo.json + mundo_tiles.webp
- casas: art/buildings/<bioma>/<id>/ -> engine/dev_assets/houses/<id>/ (metade do master, webp)
- paperdoll: art/paperdoll/<m|f>/*.png -> engine/dev_assets/paperdoll/<m|f>/*.webp (150x240)
- monstros novos: art/monsters/<id>/<id>.png + .json -> engine/dev_assets/monsters/ (metade, webp)
"""
import argparse, glob, json, os, re, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_dev_assets import load_tileset, pack, SCALE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'engine', 'dev_assets')


def load_txt(path):
    txt = open(path, encoding='utf-8').read()
    hdr = lambda k: re.search(r'^%s=(.+)$' % k, txt, re.M).group(1).strip()
    W, H = int(hdr('width')), int(hdr('height'))
    layers = {}
    for m in re.finditer(r'\[layer\]\s*\ntype=(\w+)\s*\ndata=\s*\n(.*?)(?=\n\s*\n|\n\[|\Z)', txt, re.S):
        rows = [[int(v) for v in r.strip().rstrip(',').split(',') if v != ''] for r in m.group(2).strip().split('\n')]
        layers.setdefault(m.group(1), rows)
    return W, H, hdr('tileset'), layers


def world(flare):
    z = json.load(open(os.path.join(ROOT, 'data', 'zones.json'), encoding='utf-8'))
    pieces = z['world']['pieces']
    loaded = []
    for p in pieces:
        W, H, ts, L = load_txt(os.path.join(ROOT, p['file']))
        loaded.append((p, W, H, ts, L))
    minx = min(p['legacy_origin'][0] for p, *_ in loaded); miny = min(p['legacy_origin'][1] for p, *_ in loaded)
    maxx = max(p['legacy_origin'][0] + W for p, W, *_ in loaded); maxy = max(p['legacy_origin'][1] + H for p, W, H, *_ in loaded)
    GW, GH = maxx - minx, maxy - miny
    grid = {k: [[0] * GW for _ in range(GH)] for k in ('background', 'object', 'collision')}
    for p, W, H, ts, L in loaded:
        ox, oy = p['legacy_origin'][0] - minx, p['legacy_origin'][1] - miny
        for k in grid:
            for j, row in enumerate(L.get(k, [])):
                for i, t in enumerate(row):
                    if t or k == 'collision':
                        if t or not grid['background'][oy + j][ox + i]:
                            grid[k][oy + j][ox + i] = t
    tiles = load_tileset(flare, loaded[0][3])
    used = {t for k in ('background', 'object') for r in grid[k] for t in r if t}
    imgs, meta = {}, {}
    for t in sorted(used):
        if t not in tiles:
            continue
        src, x, y, w, h, ox, oy = tiles[t]
        imgs[t] = src.crop((x, y, x + w, y + h)).resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS)
        meta[t] = (ox * SCALE, oy * SCALE)
    atlas, pos = pack(imgs)
    d = os.path.join(OUT, 'flare'); os.makedirs(d, exist_ok=True)
    atlas.save(os.path.join(d, 'mundo_tiles.webp'), 'WEBP', quality=92, method=6)
    data = {'version': 1, 'id': 'mundo', 'source': 'art/maps (data/zones.json world.pieces)', 'w': GW, 'h': GH, 'tile': [96, 48],
            'offset': [-minx, -miny], 'hero': [43 - minx, 1 - miny], 'atlas': 'mundo_tiles.webp',
            'tiles': {str(t): [*pos[t], round(meta[t][0], 2), round(meta[t][1], 2)] for t in pos},
            'background': grid['background'], 'object': grid['object'], 'collision': grid['collision'], 'exits': [], 'spawns': []}
    json.dump(data, open(os.path.join(d, 'mundo.json'), 'w'), separators=(',', ':'))
    print(f'mundo: {GW}x{GH}, deslocamento {data["offset"]}, {len(pos)} tiles, atlas {atlas.size}')


def half(src, dst, size=None):
    im = Image.open(src).convert('RGBA')
    im = im.resize(size or (max(1, im.width // 2), max(1, im.height // 2)), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, 'WEBP', quality=90, method=4)
    return im


def houses():
    index = {}
    for hj in sorted(glob.glob(os.path.join(ROOT, 'art', 'buildings', '*', '*', 'house.json'))):
        h = json.load(open(hj, encoding='utf-8')); src = os.path.dirname(hj); dst = os.path.join(OUT, 'houses', h['id'])
        for k, f in h['layers'].items():
            half(os.path.join(src, f), os.path.join(dst, k + '.webp'))
        props = {}
        for f in glob.glob(os.path.join(src, 'props', '*.png')):
            n = os.path.basename(f)[:-4]; im = Image.open(f).convert('RGBA')
            half(f, os.path.join(dst, 'props', n + '.webp'))
            bb = im.getbbox() or (0, 0, im.width, im.height)
            props[n] = [im.width // 2, im.height // 2]
        index[h['id']] = {**{k: v for k, v in h.items() if k != 'layers'}, 'layers': sorted(h['layers']), 'anchor': [h['anchor'][0] / 2, h['anchor'][1] / 2], 'propsize': props}
        print('casa', h['id'], h['size'])
    json.dump(index, open(os.path.join(OUT, 'houses', 'houses.json'), 'w'), separators=(',', ':'))


def paperdoll():
    have = {}
    for sx in ('m', 'f'):
        files = sorted(glob.glob(os.path.join(ROOT, 'art', 'paperdoll', sx, '*.png')))
        for f in files:
            half(f, os.path.join(OUT, 'paperdoll', sx, os.path.basename(f)[:-4] + '.webp'), (150, 240))
        have[sx] = [os.path.basename(f)[:-4] for f in files]
        print('paperdoll', sx, len(files))
    json.dump(have, open(os.path.join(OUT, 'paperdoll', 'paperdoll.json'), 'w'))


def monsters():
    mp = os.path.join(OUT, 'monsters', 'monsters.json')
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    for jf in glob.glob(os.path.join(ROOT, 'art', 'monsters', '*', '*.json')):
        art = os.path.basename(jf)[:-5]; png = jf[:-5] + '.png'
        if not os.path.exists(png):
            continue
        half(png, os.path.join(OUT, 'monsters', art + '.webp'))
        A = json.load(open(jf))
        for an in A.values():
            an['q'] = [[[round(v / 2, 1) for v in q] for q in row] for row in an['q']]
        meta[art] = A
        print('monstro', art, list(A))
    json.dump(meta, open(mp, 'w'), separators=(',', ':'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--flare', required=True); ap.add_argument('--only', default='world,houses,paperdoll,monsters')
    a = ap.parse_args()
    for step in a.only.split(','):
        {'world': lambda: world(a.flare), 'houses': houses, 'paperdoll': paperdoll, 'monsters': monsters}[step]()

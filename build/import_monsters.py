#!/usr/bin/env python3
"""Importa as folhas de monstros do Flare (CC-BY-SA) para a escala do jogo.

    python3 build/import_monsters.py --flare <flare-game> --out engine/dev_assets/monsters

Lê o campo `art` de data/monsters.json, acha o .txt de animação no Flare, reduz
a 1/2 (master 2x -> jogo 1x), reempacota só os quadros usados e grava
<art>.webp e um monsters.json com {art: {anim: {n, dur, tipo, q[quadro][dir]}}},
o mesmo formato das camadas do TCoM.
"""
import argparse, json, os, re
from PIL import Image

SCALE = 0.5
MODS = ['fantasycore', 'empyrean_campaign', 'minicore', 'alpha_demo', 'minicore_alpha']
KEEP = {'stance', 'run', 'swing', 'hit', 'die'}
RANGED = {'shoot', 'cast'}  # só para quem ataca à distância (folhas grandes demais com tudo)


def find_anim(flare, art):
    for m in MODS:
        p = os.path.join(flare, 'mods', m, 'animations', 'enemies', art + '.txt')
        if os.path.exists(p):
            return m, p
    return None, None


def find_img(flare, mod, rel):
    for m in [mod] + MODS:
        p = os.path.join(flare, 'mods', m, rel)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(rel)


def parse(flare, mod, path):
    anims, img, cur, named = {}, None, None, {}
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line.startswith('image='):
            v = line.split('=', 1)[1]
            if ',' in v:  # image=arquivo.png,nome  (várias folhas, citadas por nome nos quadros)
                f, n = v.split(',', 1); named[n] = f
                continue
            img = v
            if cur:
                cur['img'] = img
        elif line.startswith('['):
            name = line[1:-1]
            cur = {'img': img, 'frames': {}, 'n': 1, 'dur': 800, 'tipo': 'looped'}
            anims[name] = cur
        elif cur is not None and '=' in line:
            k, v = line.split('=', 1)
            if k == 'frames': cur['n'] = int(v)
            elif k == 'duration': cur['dur'] = int(re.sub(r'\D', '', v)) * (1000 if v.endswith('s') and not v.endswith('ms') else 1)
            elif k == 'type': cur['tipo'] = v
            elif k == 'image': cur['img'] = v
            elif k == 'frame':
                t = v.split(',')
                if len(t) == 9:  # frame=i,d,x,y,w,h,ox,oy,folha
                    cur['img'] = named.get(t[8], cur['img']); t = t[:8]
                f, d, x, y, w, h, ox, oy = [int(z) for z in t]
                cur['frames'][(f, d)] = (x, y, w, h, ox, oy)
    return anims


def pack(images, max_w=8192):
    order = sorted(images, key=lambda k: -images[k].height)
    x = y = shelf = 0
    pos = {}
    for k in order:
        im = images[k]
        if x + im.width > max_w:
            x, y, shelf = 0, y + shelf + 1, 0
        pos[k] = (x, y, im.width, im.height)
        x += im.width + 1
        shelf = max(shelf, im.height)
    atlas = Image.new('RGBA', (max_w, y + shelf + 1), (0, 0, 0, 0))
    for k, (px, py, w, h) in pos.items():
        atlas.paste(images[k], (px, py))
    bb = atlas.getbbox()
    return atlas.crop((0, 0, bb[2] if bb else 1, atlas.height)), pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flare', required=True)
    ap.add_argument('--data', default='data/monsters.json')
    ap.add_argument('--out', default='engine/dev_assets/monsters')
    ap.add_argument('--ranged', default='hobgoblin_archer,skeleton_archer,skeleton_mage,skeleton_mage_boss,skeleton_mage_high_boss,necromancer,fire_ant,antlion,wyvern_fire,wyvern_water,wyvern_air,wyvern')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    arts = sorted({m['art'] for m in json.load(open(a.data, encoding='utf-8'))['monsters']})
    meta_path = os.path.join(a.out, 'monsters.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for art in arts:
        if art in meta and os.path.exists(os.path.join(a.out, art + '.webp')):
            continue
        mod, path = find_anim(a.flare, art)
        if not path:
            print('sem animação no Flare:', art)
            continue
        ranged = art in a.ranged.split(',')
        anims = {k: v for k, v in parse(a.flare, mod, path).items() if v['frames'] and (k in KEEP or (ranged and k in RANGED))}
        sheets, crops = {}, {}
        for an, A in anims.items():
            src = sheets.setdefault(A['img'], Image.open(find_img(a.flare, mod, A['img'])).convert('RGBA'))
            for (f, d), (x, y, w, h, ox, oy) in A['frames'].items():
                if w <= 0 or h <= 0:
                    continue
                key = (an, f, d)
                im = src.crop((x, y, x + w, y + h))
                crops[key] = im.resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS)
        atlas, pos = pack(crops)
        atlas.save(os.path.join(a.out, art + '.webp'), 'WEBP', quality=88, method=4)
        out = {}
        for an, A in anims.items():
            q = []
            for f in range(A['n']):
                row = []
                for d in range(8):
                    k = (an, f, d)
                    if k in pos:
                        x, y, w, h = pos[k]
                        ox, oy = A['frames'][(f, d)][4:6]
                        row.append([x, y, w, h, round(ox * SCALE, 1), round(oy * SCALE, 1)])
                    else:
                        row.append([0, 0, 0, 0, 0, 0])
                q.append(row)
            out[an] = {'n': A['n'], 'dur': A['dur'], 'tipo': A['tipo'], 'q': q}
        meta[art] = out
        print(f'{art}: {list(out)} atlas {atlas.size}')
        json.dump(meta, open(meta_path, 'w'), separators=(',', ':'))


if __name__ == '__main__':
    main()

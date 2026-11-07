#!/usr/bin/env python3
"""Importa os efeitos de magia/habilidade do Flare (images/powers, CC-BY-SA) para uma folha só.
    python3 build/import_powers.py --flare <flare-game>
Saída: engine/dev_assets/powers/powers.webp + powers.json
  {nome: {n, dur, tipo, q: [quadro][direção] = [x, y, w, h, ox, oy]}}
Direções na mesma ordem do Flare/TCoM (DIRECOES em engine/actor.js); efeitos sem direção têm só uma.
"""
import argparse, json, os, re, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_dev_assets import pack

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 0.5
USE = ['fireball', 'icicle', 'plasmaball', 'spit', 'stone', 'arrows', 'spear', 'throw_axe',
       'blast', 'freeze', 'lightning', 'thunderstrike', 'spark_red', 'spark_orange', 'spark_green', 'spark_blue',
       'heal', 'shield', 'shield_orange', 'immunity', 'dark_mist', 'status_freeze', 'runes', 'runes_blue', 'runes_orange',
       'quake', 'rupture', 'cleave', 'sparkle', 'spikes', 'channel']


def parse(path):
    t = open(path, encoding='utf-8').read()
    img = re.search(r'^image=(\S+)', t, re.M).group(1)
    sec = re.split(r'\n\[', t)[1]
    n = int(re.search(r'frames=(\d+)', sec).group(1))
    dur = int(re.search(r'duration=(\d+)', sec).group(1))
    tipo = (re.search(r'type=(\w+)', sec) or [None, 'play_once'])[1]
    fr = [tuple(map(int, l.split('=')[1].split(','))) for l in sec.splitlines() if l.startswith('frame=')]
    return img, n, dur, tipo, fr


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--flare', required=True); a = ap.parse_args()
    core = os.path.join(a.flare, 'mods', 'fantasycore')
    frames, info = {}, {}
    for name in USE:
        img, n, dur, tipo, fr = parse(os.path.join(core, 'animations', 'powers', name + '.txt'))
        sheet = Image.open(os.path.join(core, img)).convert('RGBA')
        # direções sem desenho (quadros de 1px) ficam de fora: o efeito passa a ser sem direção
        real = sorted({f[1] for f in fr if f[4] > 2 and f[5] > 2})
        remap = {d: k for k, d in enumerate(real)}
        fr = [(f, remap[d], *rest) for f, d, *rest in fr if d in remap]
        dirs = len(real)
        info[name] = (n, dur, tipo, dirs, {})
        for f, d, x, y, w, h, ox, oy in fr:
            im = sheet.crop((x, y, x + w, y + h))
            im = im.resize((max(1, round(w * SCALE)), max(1, round(h * SCALE))), Image.LANCZOS)
            frames[(name, f, d)] = im
            info[name][4][(f, d)] = (ox * SCALE, oy * SCALE)
    atlas, pos = pack(frames, 2048)
    meta = {}
    for name, (n, dur, tipo, dirs, off) in info.items():
        q = [[([*pos[(name, f, d)], round(off[(f, d)][0], 1), round(off[(f, d)][1], 1)] if (name, f, d) in pos else [0, 0, 0, 0, 0, 0])
              for d in range(dirs)] for f in range(n)]
        meta[name] = {'n': n, 'dur': dur, 'tipo': tipo, 'q': q}
    out = os.path.join(ROOT, 'engine', 'dev_assets', 'powers'); os.makedirs(out, exist_ok=True)
    atlas.save(os.path.join(out, 'powers.webp'), 'WEBP', quality=88, method=6)
    json.dump(meta, open(os.path.join(out, 'powers.json'), 'w'), separators=(',', ':'))
    print(f'efeitos: {len(meta)}, folha {atlas.size}, {os.path.getsize(os.path.join(out, "powers.webp")) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()

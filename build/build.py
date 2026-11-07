#!/usr/bin/env python3
"""Monta dist/: um game.js só (scripts + dados embutidos), o index.html, o CSS
e os assets. Assim o jogo abre por file:// (APK) e por http (itch.io, artifact).

    python3 build/build.py            # gera dist/
    python3 build/build.py --zip      # e também dist.zip para o itch.io
"""
import argparse, json, os, shutil, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = ['engine/iso.js', 'engine/map.js', 'engine/actor.js', 'engine/render.js',
           'ui/gumps.js', 'ui/touch.js', 'systems/chat.js', 'systems/skills.js', 'systems/magic.js', 'systems/combat.js', 'systems/world.js', 'systems/sim.js', 'systems/build.js', 'systems/fx.js', 'systems/vendors.js', 'systems/abilities.js', 'src/main.js']
MAPS = ['mundo']


def load(p, default=None):
    p = os.path.join(ROOT, p)
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zip', action='store_true')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    a = ap.parse_args()
    out = a.out
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, 'ui'))

    maps = {}
    for mid in MAPS:
        m = load(f'engine/dev_assets/flare/{mid}.json')
        m['atlasFile'] = f'engine/dev_assets/flare/{m["atlas"]}'
        maps[mid] = m
    data = {
        'maps': maps,
        'monsters': load('data/monsters.json'), 'monArt': load('engine/dev_assets/monsters/monsters.json'),
        'zones': load('data/zones.json'), 'houses': load('engine/dev_assets/houses/houses.json'),
        'loot': load('data/loot.json'), 'affixes': load('data/items/affixes.json'), 'sets': load('data/items/sets.json'),
        'uniques': load('data/items/uniques.json'), 'rarity': load('data/items/rarity.json'), 'hues': load('data/hues.json'),
        'tcom': load('engine/dev_assets/tcom/layers.json'),
        'icons': load('engine/dev_assets/tcom/icons.json'),
        'personalities': load('data/chat/personalities.json'),
        'lines': load('data/chat/lines.json'),
        'players': load('data/names/players.json'),
        'guilds': load('data/names/guilds.json'),
        'biomes': load('data/lore/biomes.json'),
        'items': load('data/items/base.json'),
        'bosses': load('data/names/bosses.json'),
        'skills': load('data/skills.json'),
        'spells': load('data/magic/spells.json'),
        'reagents': load('data/magic/reagents.json'),
        'building': load('data/building.json'), 'abilities': load('data/abilities.json'), 'vendors': load('data/npcs/vendors.json'), 'powers': load('engine/dev_assets/powers/powers.json'), 'gathering': load('data/gathering.json'),
    }
    js = ['// gerado por build/build.py — não editar à mão',
          'const DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';']
    for s in SCRIPTS:
        with open(os.path.join(ROOT, s), encoding='utf-8') as f:
            js.append(f'\n// ===== {s} =====\n' + f.read().replace("'use strict';", ''))
    with open(os.path.join(out, 'game.js'), 'w', encoding='utf-8') as f:
        f.write("'use strict';\n" + '\n'.join(js))
    shutil.copy(os.path.join(ROOT, 'ui/index.html'), os.path.join(out, 'index.html'))
    shutil.copy(os.path.join(ROOT, 'ui/style.css'), os.path.join(out, 'ui/style.css'))
    # só as imagens e fontes (os .json já foram embutidos)
    src = os.path.join(ROOT, 'engine/dev_assets')
    for d, _, files in os.walk(src):
        for fn in files:
            if fn.endswith(('.webp', '.png', '.woff2', '.txt')):
                rel = os.path.relpath(os.path.join(d, fn), ROOT)
                os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
                shutil.copy(os.path.join(ROOT, rel), os.path.join(out, rel))
    shutil.copy(os.path.join(ROOT, 'CREDITOS.txt'), os.path.join(out, 'CREDITOS.txt'))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print(f'dist/: {size / 1e6:.1f} MB')
    if a.zip:
        z = out + '.zip'
        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
            for d, _, fs in os.walk(out):
                for f in fs:
                    p = os.path.join(d, f)
                    zf.write(p, os.path.relpath(p, out))
        print('zip:', z)


if __name__ == '__main__':
    main()

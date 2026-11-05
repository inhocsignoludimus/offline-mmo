#!/usr/bin/env python3
"""
Importa os assets PROVISÓRIOS da engine (até a arte do Ludimus chegar em art/):

  * um mapa do Flare (formato .txt do Tiled/Flare) + só os tiles que ele usa,
    reduzidos de 192x96 (master do Flare) para 96x48 (runtime), num atlas;
  * as camadas dos personagens do TCoM (folhas + metadados de animação).

Uso:
  python3 build/import_dev_assets.py --flare ../flare-game --tcom ../the-cross-of-montgisard \
         --map lochport --out engine/dev_assets

Licenças: arte do Flare e dos personagens do TCoM = CC-BY-SA 3.0 (ver CREDITOS.txt).
"""
import argparse, json, os, re, shutil
from PIL import Image

SCALE = 0.5  # master 192x96 -> runtime 96x48


def find(flare, rel):
    for mod in ('empyrean_campaign', 'fantasycore'):
        p = os.path.join(flare, 'mods', mod, rel)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(rel)


def load_tileset(flare, rel):
    tiles, img, imgs = {}, None, {}
    for line in open(find(flare, rel), encoding='utf-8'):
        line = line.strip()
        if line.startswith('img='):
            p = line[4:]
            if p not in imgs:
                imgs[p] = Image.open(find(flare, p)).convert('RGBA')
            img = imgs[p]
        elif line.startswith('tile='):
            a = [int(v) for v in line[5:].split(',')[:7]]
            tiles[a[0]] = (img,) + tuple(a[1:])
    return tiles


def load_map(flare, name):
    txt = open(os.path.join(flare, 'mods', 'empyrean_campaign', 'maps', name + '.txt'), encoding='utf-8').read()
    hdr = lambda k: re.search(r'^%s=(.+)$' % k, txt, re.M).group(1).strip()
    W, H = int(hdr('width')), int(hdr('height'))
    hero = [int(v) for v in hdr('hero_pos').split(',')] if re.search(r'^hero_pos=', txt, re.M) else [W // 2, H // 2]
    layers = {}
    for m in re.finditer(r'\[layer\]\s*\ntype=(\w+)\s*\ndata=\s*\n(.*?)(?=\n\s*\n|\n\[|\Z)', txt, re.S):
        rows = [[int(v) for v in r.strip().rstrip(',').split(',') if v != ''] for r in m.group(2).strip().split('\n')]
        layers.setdefault(m.group(1), rows)
    return W, H, hdr('tileset'), hero, layers


def pack(images, max_w=2048):
    """Empacotamento em prateleiras. images: {id: Image}. Devolve (atlas, {id: (x,y,w,h)})."""
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
    return atlas, pos


def import_map(flare, name, out):
    W, H, ts, hero, L = load_map(flare, name)
    tiles = load_tileset(flare, ts)
    used = set()
    for lname in ('background', 'object'):
        for row in L.get(lname, []):
            used.update(t for t in row if t)
    imgs, meta = {}, {}
    for t in sorted(used):
        if t not in tiles:
            continue
        src, x, y, w, h, ox, oy = tiles[t]
        im = src.crop((x, y, x + w, y + h))
        nw, nh = max(1, round(w * SCALE)), max(1, round(h * SCALE))
        imgs[t] = im.resize((nw, nh), Image.LANCZOS)
        meta[t] = (ox * SCALE, oy * SCALE)
    atlas, pos = pack(imgs)
    os.makedirs(out, exist_ok=True)
    atlas.save(os.path.join(out, f'{name}_tiles.webp'), 'WEBP', quality=92, method=6)
    tdef = {str(t): [*pos[t], round(meta[t][0], 2), round(meta[t][1], 2)] for t in pos}
    col = L.get('collision', [[0] * W for _ in range(H)])
    data = {
        'version': 1, 'id': name, 'source': 'flare-game/empyrean_campaign/maps/' + name + '.txt',
        'w': W, 'h': H, 'tile': [96, 48], 'hero': hero,
        'atlas': f'{name}_tiles.webp', 'tiles': tdef,
        'background': L['background'], 'object': L.get('object', []), 'collision': col,
    }
    json.dump(data, open(os.path.join(out, f'{name}.json'), 'w'), separators=(',', ':'))
    print(f'mapa {name}: {W}x{H}, {len(pos)} tiles, atlas {atlas.size}')


TCOM_LAYERS_M = ['default_chest', 'default_legs', 'default_hands', 'default_feet', 'male_head1', 'male_head2',
                 'aldeao_tunica1', 'aldeao_tunica2', 'cloth_shirt', 'cloth_pants', 'calca_branca', 'cloth_sandals',
                 'leather_boots', 'leather_gloves', 'leather_hood', 'gambesao', 'jaque_couro', 'loriga', 'lorigao',
                 'lamelar', 'ferreiro_tunica', 'armadura_templario', 'armadura_cruzado', 'armadura_sargento',
                 'chain_coif', 'chain_boots', 'chain_gloves', 'chain_greaves', 'elmo_nasal', 'turbante',
                 'beduino_veste', 'beduino_mangas', 'beduino_saia', 'longsword', 'mace', 'hand_axe', 'dagger',
                 'lanca', 'martelo', 'shield', 'buckler', 'escudo_cruz', 'escudo_redondo', 'habito_peregrino']
TCOM_LAYERS_F = ['default_chest', 'default_legs', 'default_hands', 'default_feet', 'head_long', 'clothes',
                 'aldea_roupa2', 'camisa_freira', 'habito']
KEEP_ANIMS = ('stance', 'run', 'swing', 'hit', 'die', 'idle')


def import_tcom(tcom, out):
    s = open(os.path.join(tcom, 'js', 'jogo.js'), encoding='utf-8').read()
    i = s.index('const CAMADAS_ANIM = ') + len('const CAMADAS_ANIM = ')
    depth = 0
    for k in range(i, len(s)):
        if s[k] == '{':
            depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0:
                break
    anim = json.loads(s[i:k + 1])
    os.makedirs(os.path.join(out, 'm'), exist_ok=True)
    os.makedirs(os.path.join(out, 'f'), exist_ok=True)
    meta = {}
    total = 0
    for sex, names in (('m', TCOM_LAYERS_M), ('f', TCOM_LAYERS_F)):
        for n in names:
            key = f'{sex}/{n}'
            if key not in anim:
                print('  (falta no TCoM)', key)
                continue
            # re-empacota só as animações que a engine usa, para a folha ficar menor
            sheet = Image.open(os.path.join(tcom, 'assets', 'personagens', key + '.webp')).convert('RGBA')
            frames, newq = {}, {}
            for a in KEEP_ANIMS:
                if a not in anim[key]:
                    continue
                for fi, fr in enumerate(anim[key][a]['q']):
                    for di, q in enumerate(fr):
                        if q[2] > 0:
                            frames[(a, fi, di)] = sheet.crop((q[0], q[1], q[0] + q[2], q[1] + q[3]))
            atlas, pos = pack(frames, 2048)
            m = {}
            for a in KEEP_ANIMS:
                if a not in anim[key]:
                    continue
                src = anim[key][a]
                q2 = []
                for fi, fr in enumerate(src['q']):
                    row = []
                    for di, q in enumerate(fr):
                        if q[2] > 0:
                            x, y, w, h = pos[(a, fi, di)]
                            row.append([x, y, w, h, q[4], q[5]])
                        else:
                            row.append([0, 0, 0, 0, 0, 0])
                    q2.append(row)
                m[a] = {'n': src['n'], 'dur': src['dur'], 'tipo': src.get('tipo', 'looped'), 'q': q2}
            meta[key] = m
            p = os.path.join(out, key + '.webp')
            atlas.save(p, 'WEBP', quality=90, method=6)
            total += os.path.getsize(p)
    json.dump(meta, open(os.path.join(out, 'layers.json'), 'w'), separators=(',', ':'))
    print(f'TCoM: {len(meta)} camadas, {total / 1e6:.1f} MB')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--flare', required=True)
    ap.add_argument('--tcom', required=True)
    ap.add_argument('--map', action='append', default=[])
    ap.add_argument('--out', default='engine/dev_assets')
    a = ap.parse_args()
    for m in a.map or ['lochport']:
        import_map(a.flare, m, os.path.join(a.out, 'flare'))
    import_tcom(a.tcom, os.path.join(a.out, 'tcom'))

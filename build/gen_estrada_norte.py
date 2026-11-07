#!/usr/bin/env python3
"""Estrada Real para o norte, sem mover a fatia já desenhada.

O arquivo mundo.txt fica 146×60. A peça nova senta em coordenadas
legadas negativas: o portão norte de Porto do Trigo (x=41..44, y=0)
continua no mesmo tile. Folhaverde segue a noroeste; isto é só o
primeiro lance da estrada.

    python3 build/gen_estrada_norte.py
"""
import json
import os
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUNDO = os.path.join(ROOT, 'art', 'maps', 'mundo.txt')
PIECE = os.path.join(ROOT, 'art', 'maps', 'estrada_norte.txt')
PIECE_TMX = os.path.join(ROOT, 'art', 'maps', 'src', 'estrada_norte.tmx')
ZONES = os.path.join(ROOT, 'data', 'zones.json')
PREVIEW = os.path.join(ROOT, 'docs', 'estrada_norte.png')

# Peça em espaço legado. y negativo = norte do y=0 de mundo.txt.
LEG_X, LEG_Y = 32, -72
PW, PH = 64, 72
ROAD_X = range(9, 13)          # legado 41..44, o portão
HUNT = (32, 64, 0, 8)          # px0, px1, py0, py1 — célula (13, 20)
GRASS = list(range(16, 32))
DIRT = list(range(32, 38))
TREES = [48, 49, 50, 51, 52, 53, 54, 55, 56, 58, 62]
SHRUBS = [66, 69, 70, 75]


def noise(x, y, salt=0):
    n = (x * 374761393 + y * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFF


def pick(seq, x, y, salt=0):
    return seq[noise(x, y, salt) % len(seq)]


def load_layer(path, kind):
    raw = open(path, encoding='utf-8').read()
    for part in raw.split('[layer]')[1:]:
        meta, data = part.split('data=', 1)
        got = None
        for line in meta.splitlines():
            if line.startswith('type='):
                got = line.split('=', 1)[1].strip()
        if got != kind:
            continue
        rows = []
        for line in data.strip().splitlines():
            line = line.strip().rstrip(',')
            if not line or line.startswith('['):
                break
            rows.append([int(v) for v in line.split(',') if v != ''])
        return rows
    raise SystemExit(f'sem camada {kind}')


def build():
    bg = [[0] * PW for _ in range(PH)]
    ob = [[0] * PW for _ in range(PH)]
    col = [[2] * PW for _ in range(PH)]
    hx0, hx1, hy0, hy1 = HUNT
    camp = {(x, y) for x in range(40, 53) for y in range(1, 7)}
    spur = {(x, y) for x in range(13, 40) for y in (3, 4)}
    marco = {(x, y) for x in range(6, 16) for y in range(34, 42)}

    def dirt(x, y):
        bg[y][x] = pick(DIRT, x, y, 1)
        ob[y][x] = 0
        col[y][x] = 0

    def grass(x, y):
        bg[y][x] = pick(GRASS, x, y, 2)
        col[y][x] = 0
        ob[y][x] = pick(SHRUBS, x, y, 3) if noise(x, y, 4) % 13 == 0 else 0

    def tree(x, y):
        bg[y][x] = pick(GRASS, x, y, 5)
        ob[y][x] = pick(TREES, x, y, 6)
        col[y][x] = 2

    for y in range(PH):
        for x in range(PW):
            on_road = x in ROAD_X
            on_open = hx0 <= x < hx1 and hy0 <= y < hy1
            if on_road or (x, y) in spur or (x, y) in marco or (x, y) in camp:
                dirt(x, y)
            elif on_open:
                # Campo aberto: pouca árvore, para a caça ter chão.
                if noise(x, y, 8) % 14 == 0 and (x, y) not in camp:
                    tree(x, y)
                else:
                    grass(x, y)
            else:
                # Fronteira da estrada: arvoredo de coleta, sem virar muralha.
                if noise(x, y, 8) % 4 == 0:
                    tree(x, y)
                else:
                    grass(x, y)
    # A estrada e o portão ganham por último.
    for y in range(PH):
        for x in ROAD_X:
            dirt(x, y)
    for x, y in spur | marco | camp:
        dirt(x, y)
    return bg, ob, col


def write_txt(path, layers, title, hero):
    w, h = len(layers['background'][0]), len(layers['background'])
    lines = [
        '[header]',
        f'width={w}',
        f'height={h}',
        'tilewidth=192',
        'tileheight=96',
        'orientation=isometric',
        'background_color=20,24,18,255',
        f'hero_pos={hero}',
        'music=music/forest_theme.ogg',
        'tileset=tilesetdefs/tileset_grassland.txt',
        f'title={title}',
        '',
        '[tilesets]',
        'tileset=../../../tiled/tilesheets/tiled_collision.png,192,96,0,0',
        'tileset=../../../tiled/tilesheets/grassland.png,192,384,0,0',
        'tileset=../../../tiled/tilesheets/grassland_water.png,192,192,0,96',
        'tileset=../../../tiled/tilesheets/grassland_structures.png,192,768,0,0',
        'tileset=../../../tiled/tilesheets/grassland_trees.png,384,768,-96,0',
        '',
    ]
    for kind in ('background', 'object', 'collision'):
        lines += ['[layer]', f'type={kind}', 'data=']
        for row in layers[kind]:
            lines.append(','.join(str(v) for v in row) + ',')
        lines.append('')
    open(path, 'w', encoding='utf-8').write('\n'.join(lines).rstrip('\n') + '\n')


def write_tmx(path, layers, title, hero):
    w, h = len(layers['background'][0]), len(layers['background'])

    def csv(rows):
        out = []
        for i, row in enumerate(rows):
            end = ',' if i < len(rows) - 1 else ''
            out.append(','.join(str(v) for v in row) + end)
        return '\n'.join(out)

    parts = [f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="isometric" renderorder="right-down"
 width="{w}" height="{h}" tilewidth="192" tileheight="96" infinite="0" backgroundcolor="#141812">
 <properties>
  <property name="hero_pos" value="{hero}"/>
  <property name="title" value="{title}"/>
  <property name="tileset_flare" value="tilesetdefs/tileset_grassland.txt"/>
  <property name="legacy_origin" value="{LEG_X},{LEG_Y}"/>
 </properties>
 <tileset firstgid="1" name="grassland" tilewidth="192" tileheight="96" tilecount="1" columns="1">
  <image source="../../../../flare-game/mods/fantasycore/images/tilesets/tileset_grassland.png" width="1" height="1"/>
 </tileset>''']
    for i, kind in enumerate(('background', 'object', 'collision'), 1):
        parts.append(f' <layer id="{i}" name="{kind}" width="{w}" height="{h}">\n  <data encoding="csv">')
        parts.append(csv(layers[kind]))
        parts.append('  </data>\n </layer>')
    parts.append('</map>\n')
    open(path, 'w', encoding='utf-8').write('\n'.join(parts))


def update_zones():
    z = json.load(open(ZONES, encoding='utf-8'))
    z['world']['pieces'] = [
        {
            'id': 'mundo',
            'file': 'art/maps/mundo.txt',
            'legacy_origin': [0, 0],
            'size': [146, 60],
            'note': {
                'pt': 'Coordenada legada = tile do arquivo. Lochport segue em [0, 0].',
                'en': 'Legacy coordinate = file tile. Lochport stays at [0, 0].',
            },
        },
        {
            'id': 'estrada_norte',
            'file': 'art/maps/estrada_norte.txt',
            'legacy_origin': [LEG_X, LEG_Y],
            'size': [PW, PH],
            'abuts': {'piece': 'mundo', 'side': 'north', 'legacy_y': 0},
            'note': {
                'pt': 'Norte de mundo.txt. Tile legado (x, y) = origem + tile do arquivo. y negativo não desloca o que já está desenhado.',
                'en': 'North of mundo.txt. Legacy tile (x, y) = origin + file tile. Negative y does not move what is already drawn.',
            },
        },
    ]
    common = ['logs', 'stone', 'iron_ore', 'copper_ore']
    zones = [zz for zz in z['zones'] if zz['id'] not in ('estrada_real_norte', 'acostamento_norte', 'campo_do_marco')]
    zones.append({
        'id': 'estrada_real_norte',
        'name': {'pt': 'Estrada Real ao Norte', 'en': 'North Royal Road'},
        'map': 'mundo',
        'piece': 'estrada_norte',
        'kind': 'road',
        'biome': 'plains',
        'level': [1, 1],
        'origin': [32, -72],
        'size': [32, 72],
        'build': 'fronteira',
        'danger': 1,
        'invasion': False,
        'resources': {'common': common, 'rare': []},
        'layout_cells': [[12, 20], [12, 21]],
        'world_origin': [768 + 32, 1408 - 72],
        'unlock': {'kind': 'always'},
        'note': {
            'pt': 'Portão norte de Porto do Trigo (legado x=41..44, y=0) e o primeiro lance da Estrada Real. Fronteira: sem monstro e sem invasão. Folhaverde continua a noroeste, depois deste lance.',
            'en': 'North gate of Wheatport (legacy x=41..44, y=0) and the first stretch of the Royal Road. Frontier: no monsters and no invasion. Folhaverde stays northwest, beyond this stretch.',
        },
        'chunks': [{
            'id': 'portao_norte',
            'name': {'pt': 'Portão Norte', 'en': 'North Gate'},
            'rect': [32, -72, 32, 72],
            'build': 'fronteira',
            'danger': 1,
            'invasion': False,
            'spawns': [],
        }],
    })
    zones.append({
        'id': 'acostamento_norte',
        'name': {'pt': 'Acostamento Norte', 'en': 'North Roadside'},
        'map': 'mundo',
        'piece': 'estrada_norte',
        'kind': 'road',
        'biome': 'plains',
        'level': [1, 1],
        'origin': [64, -64],
        'size': [32, 64],
        'build': 'fronteira',
        'danger': 1,
        'invasion': False,
        'resources': {'common': common, 'rare': []},
        'layout_cells': [[13, 21]],
        'world_origin': [768 + 64, 1408 - 64],
        'unlock': {'kind': 'always'},
        'chunks': [{
            'id': 'acostamento',
            'name': {'pt': 'Acostamento', 'en': 'Roadside'},
            'rect': [64, -64, 32, 64],
            'build': 'fronteira',
            'danger': 1,
            'invasion': False,
            'spawns': [],
        }],
    })
    zones.append({
        'id': 'campo_do_marco',
        'name': {'pt': 'Campo do Marco', 'en': 'Milestone Field'},
        'map': 'mundo',
        'piece': 'estrada_norte',
        'kind': 'hunt',
        'biome': 'plains',
        'level': [6, 6],
        'origin': [64, -72],
        'size': [32, 8],
        'build': 'aberta',
        'danger': 2,
        'invasion': True,
        'resources': {'common': common, 'rare': ['silver_ore', 'leather_hide']},
        'layout_cells': [[13, 20]],
        'world_origin': [768 + 64, 1408 - 72],
        'unlock': {'kind': 'always'},
        'note': {
            'pt': 'Primeira faixa aberta ao lado da Estrada Real, célula (13, 20). Sem chefe. Não é Folhaverde.',
            'en': 'First open strip beside the Royal Road, cell (13, 20). No boss. This is not Folhaverde.',
        },
        'chunks': [{
            'id': 'campo',
            'name': {'pt': 'Campo', 'en': 'Field'},
            'rect': [64, -72, 32, 8],
            'build': 'aberta',
            'danger': 2,
            'invasion': True,
            'spawns': [
                {'monster': 'goblin', 'count': [3, 5], 'level': 6},
                {'monster': 'goblin_spearman', 'count': [2, 3], 'level': 6},
            ],
        }],
    })
    z['zones'] = zones
    with open(ZONES, 'w', encoding='utf-8') as f:
        json.dump(z, f, ensure_ascii=False, indent=2)
        f.write('\n')


def connects(col):
    """O portão do mundo entra na estrada, e a estrada chega ao campo e ao norte."""
    start = [(x, PH - 1) for x in ROAD_X]
    q = deque(start)
    seen = set(start)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < PW and 0 <= yy < PH and (xx, yy) not in seen and col[yy][xx] == 0:
                seen.add((xx, yy))
                q.append((xx, yy))
    north = sum(1 for x in ROAD_X if (x, 0) in seen)
    camp = sum(1 for x in range(40, 53) for y in range(1, 7) if (x, y) in seen)
    if north != len(list(ROAD_X)) or camp < 20:
        raise SystemExit(f'estrada não liga: norte {north}, campo {camp}')


def preview(layers, mundo_col, mundo_bg):
    from PIL import Image, ImageDraw, ImageFont
    bg, col = layers['background'], layers['collision']
    tw = 8
    pad = 16
    # Peça em cima, 12 linhas do mundo embaixo, alinhadas no x legado.
    top_h = PH * tw
    bot_h = 12 * tw
    w = PW * tw + pad * 2
    h = 52 + top_h + 8 + bot_h + 24
    im = Image.new('RGB', (w, h), (22, 24, 28))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf', 15)
    font_s = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-Regular.ttf', 12)

    def paint(x, y, blocked, dirt, ox, oy):
        if blocked:
            color = (42, 86, 48)
        elif dirt:
            color = (176, 142, 86)
        else:
            color = (116, 164, 82)
        d.rectangle([ox + x * tw, oy + y * tw, ox + (x + 1) * tw - 1, oy + (y + 1) * tw - 1], fill=color)

    oy = 48
    for y in range(PH):
        for x in range(PW):
            paint(x, y, col[y][x] != 0, 32 <= bg[y][x] <= 37, pad, oy)
    oy2 = oy + top_h + 8
    for y in range(12):
        for x in range(PW):
            lx = LEG_X + x
            blocked = mundo_col[y][lx] != 0
            dirt = 32 <= mundo_bg[y][lx] <= 47
            paint(x, y, blocked, dirt, pad, oy2)
    d.text((pad, 8), 'Estrada Real ao norte — y legado negativo, fatia antiga parada', fill=(236, 232, 220), font=font)
    d.text((pad, 28), 'Cima: peça nova. Baixo: y=0..11 de mundo.txt, o portão em x=41..44.', fill=(180, 176, 164), font=font_s)
    im.save(PREVIEW)


def main():
    layers = {
        'background': None,
        'object': None,
        'collision': None,
    }
    bg, ob, col = build()
    layers = {'background': bg, 'object': ob, 'collision': col}
    connects(col)
    # O portão do arquivo antigo tem de encontrar chão andável.
    mundo_col = load_layer(MUNDO, 'collision')
    mundo_bg = load_layer(MUNDO, 'background')
    assert len(mundo_col[0]) == 146 and len(mundo_col) == 60
    for x in ROAD_X:
        assert mundo_col[0][LEG_X + x] == 0, (x, LEG_X + x)
        assert col[PH - 1][x] == 0
    write_txt(PIECE, layers, 'Estrada Real ao Norte', '10,70')
    write_tmx(PIECE_TMX, layers, 'Estrada Real ao Norte', '10,70')
    update_zones()
    preview(layers, mundo_col, mundo_bg)
    print('piece', PW, PH, 'legacy', [LEG_X, LEG_Y])
    print('preview', PREVIEW)


if __name__ == '__main__':
    main()

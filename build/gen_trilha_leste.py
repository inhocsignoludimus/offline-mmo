#!/usr/bin/env python3
"""Acrescenta a trilha leste ao mapa contínuo, sem mexer na fatia 98×60.

A estrada sai pelas duas brechas já andáveis da coluna x=97 (y=15 e y=17).
Os 98 tiles de largura e os rects de Lochport e do Bosque da Vila ficam.
Não cria chefe. Não edita engine/.

    python3 build/gen_trilha_leste.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'art', 'maps', 'mundo.txt')
TMX = os.path.join(ROOT, 'art', 'maps', 'src', 'mundo.tmx')
PIECE_TXT = os.path.join(ROOT, 'art', 'maps', 'trilha_leste.txt')
PIECE_TMX = os.path.join(ROOT, 'art', 'maps', 'src', 'trilha_leste.tmx')
ZONES = os.path.join(ROOT, 'data', 'zones.json')
PREVIEW = os.path.join(ROOT, 'docs', 'trilha_leste.png')

KEEP_W = 98
ADD_W = 48
H = 60
# Peça alinhada ao Bosque (y 12–47). px 0–29 ainda é a célula floresta (13,22).
# px 30–47 entra na célula de planície (14,22).
ZONE_Y0 = 12
ZONE_H = 36
FOREST_W = 30
GRASS = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
DIRT = [32, 33, 34, 35, 36, 37]
TREES = [48, 49, 50, 51, 52, 53, 54, 55, 56, 58, 62]
SHRUBS = [66, 69, 70, 75]


def noise(x, y, salt=0):
    n = (x * 374761393 + y * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n ^ (n >> 16)) & 0xFF


def pick(seq, x, y, salt=0):
    return seq[noise(x, y, salt) % len(seq)]


def load_txt(path):
    raw = open(path, encoding='utf-8').read()
    head, rest = raw.split('[layer]', 1)
    # header is everything before the first [layer]; we reattach layers below
    parts = raw.split('[layer]')
    header = parts[0]
    layers = {}
    order = []
    for part in parts[1:]:
        meta, data = part.split('data=', 1)
        kind = None
        for line in meta.splitlines():
            if line.startswith('type='):
                kind = line.split('=', 1)[1].strip()
        rows = []
        for line in data.strip().splitlines():
            line = line.strip().rstrip(',')
            if not line or line.startswith('['):
                break
            rows.append([int(x) for x in line.split(',') if x != ''])
        layers[kind] = rows
        order.append(kind)
    return header, layers, order


def write_txt(path, header, layers, order, title=None):
    h = header
    if title:
        lines = []
        for line in h.splitlines(True):
            if line.startswith('title='):
                lines.append(f'title={title}\n')
            elif line.startswith('width='):
                lines.append(f'width={len(layers["background"][0])}\n')
            elif line.startswith('height='):
                lines.append(f'height={len(layers["background"])}\n')
            else:
                lines.append(line)
        h = ''.join(lines)
    else:
        lines = []
        for line in h.splitlines(True):
            if line.startswith('width='):
                lines.append(f'width={len(layers["background"][0])}\n')
            elif line.startswith('height='):
                lines.append(f'height={len(layers["background"])}\n')
            else:
                lines.append(line)
        h = ''.join(lines)
    if not h.endswith('\n'):
        h += '\n'
    out = [h.rstrip('\n'), '']
    for kind in order:
        out.append('[layer]')
        out.append(f'type={kind}')
        out.append('data=')
        for row in layers[kind]:
            out.append(','.join(str(v) for v in row) + ',')
        out.append('')
    open(path, 'w', encoding='utf-8').write('\n'.join(out).rstrip('\n') + '\n')


def build_extension():
    """48 colunas. Devolve bg, obj, col de altura 60."""
    bg = [[0] * ADD_W for _ in range(H)]
    ob = [[0] * ADD_W for _ in range(H)]
    col = [[0] * ADD_W for _ in range(H)]

    def tree(x, y):
        bg[y][x] = pick(GRASS, x, y)
        ob[y][x] = pick(TREES, x, y, 1)
        col[y][x] = 2

    def grass(x, y, shrub=True):
        bg[y][x] = pick(GRASS, x, y, 2)
        col[y][x] = 0
        if shrub and (x * 3 + y * 5) % 11 == 0:
            ob[y][x] = pick(SHRUBS, x, y, 3)
        else:
            ob[y][x] = 0

    def dirt(x, y):
        bg[y][x] = pick(DIRT, x, y, 4)
        ob[y][x] = 0
        col[y][x] = 0

    road_rows = {3, 4, 5}  # py dentro da peça; mundo y = 15, 16, 17
    # Campinho de goblin na seara, fora da estrada. Sem chefe.
    camp = {(x, y) for x in range(36, 42) for y in range(12, 17)}
    spur = {(x, y) for x in range(38, 40) for y in range(6, 12)}

    for y in range(H):
        py = y - ZONE_Y0
        in_zone = ZONE_Y0 <= y < ZONE_Y0 + ZONE_H
        for x in range(ADD_W):
            if not in_zone:
                tree(x, y)
                continue
            on_road = py in road_rows
            on_camp = (x, py) in camp or (x, py) in spur
            if on_road or on_camp:
                dirt(x, y)
                continue
            if x < FOREST_W:
                # Mata densa, irregular, no mesmo espírito do Bosque.
                if noise(x, py, 9) % 5 == 0:
                    grass(x, y)
                else:
                    tree(x, y)
            else:
                # Seara: grama aberta, árvore rara.
                if noise(x, py, 9) % 11 == 0:
                    tree(x, y)
                else:
                    grass(x, y, shrub=True)
    # As brechas do mapa antigo são grama andável. Os primeiros tiles
    # continuam grama, para a emenda não virar terra do nada.
    for x in range(3):
        for py in (2, 3, 4, 5, 6):
            grass(x, ZONE_Y0 + py, shrub=False)
    return bg, ob, col


def stitch(layers, ext):
    bg, ob, col = ext
    for kind, grid in (('background', bg), ('object', ob), ('collision', col)):
        rows = layers[kind]
        assert len(rows) == H and len(rows[0]) >= KEEP_W
        for y in range(H):
            rows[y] = rows[y][:KEEP_W] + grid[y]
    return layers


def write_piece(ext):
    bg, ob, col = ext
    # só as 36 linhas da peça
    piece = {
        'background': [row[:] for row in bg[ZONE_Y0:ZONE_Y0 + ZONE_H]],
        'object': [row[:] for row in ob[ZONE_Y0:ZONE_Y0 + ZONE_H]],
        'collision': [row[:] for row in col[ZONE_Y0:ZONE_Y0 + ZONE_H]],
    }
    header = """[header]
width=48
height=36
tilewidth=192
tileheight=96
orientation=isometric
background_color=20,24,18,255
hero_pos=0,3
music=music/forest_theme.ogg
tileset=tilesetdefs/tileset_grassland.txt
title=Trilha Leste

[tilesets]
tileset=../../../tiled/tilesheets/tiled_collision.png,192,96,0,0
tileset=../../../tiled/tilesheets/grassland.png,192,384,0,0
tileset=../../../tiled/tilesheets/grassland_water.png,192,192,0,96
tileset=../../../tiled/tilesheets/grassland_structures.png,192,768,0,0
tileset=../../../tiled/tilesheets/grassland_trees.png,384,768,-96,0

"""
    write_txt(PIECE_TXT, header, piece, ['background', 'object', 'collision'], title='Trilha Leste')
    write_tmx(PIECE_TMX, piece, ['background', 'object', 'collision'], 48, 36,
              'Trilha Leste', '0,3', continuous=False)


def write_tmx(path, layers, order, width, height, title, hero, continuous):
    def csv(rows):
        lines = []
        for i, row in enumerate(rows):
            comma = ',' if i < len(rows) - 1 else ''
            lines.append(','.join(str(v) for v in row) + comma)
        return '\n'.join(lines)

    props = f""" <properties>
  <property name="hero_pos" value="{hero}"/>
  <property name="title" value="{title}"/>
  <property name="tileset_flare" value="tilesetdefs/tileset_grassland.txt"/>
"""
    if continuous:
        props += '  <property name="continuous" value="true"/>\n'
    props += ' </properties>\n'
    body = [f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="isometric" renderorder="right-down"
 width="{width}" height="{height}" tilewidth="192" tileheight="96" infinite="0" backgroundcolor="#141812">
{props} <tileset firstgid="1" name="grassland" tilewidth="192" tileheight="96" tilecount="1" columns="1">
  <image source="../../../../flare-game/mods/fantasycore/images/tilesets/tileset_grassland.png" width="1" height="1"/>
 </tileset>''']
    for i, kind in enumerate(order, 1):
        body.append(f' <layer id="{i}" name="{kind}" width="{width}" height="{height}">\n  <data encoding="csv">')
        body.append(csv(layers[kind]))
        body.append('  </data>\n </layer>')
    body.append('</map>\n')
    open(path, 'w', encoding='utf-8').write('\n'.join(body))


def update_zones():
    z = json.load(open(ZONES, encoding='utf-8'))
    z['world']['size'] = [KEEP_W + ADD_W, H]
    zones = [zz for zz in z['zones'] if zz['id'] not in ('orla_do_bosque', 'seara_leste')]
    zones.append({
        'id': 'orla_do_bosque',
        'name': {'pt': 'Orla do Bosque', 'en': 'Woods Edge'},
        'map': 'mundo',
        'kind': 'hunt',
        'biome': 'forest',
        'level': [2, 5],
        'origin': [98, 12],
        'size': [FOREST_W, ZONE_H],
        'build': 'nao',
        'danger': 2,
        'invasion': False,
        'resources': {'common': ['logs', 'stone', 'iron_ore', 'copper_ore'], 'rare': []},
        'layout_cell': [13, 22],
        'world_origin': [768 + 98, 1408 + 12],
        'note': {
            'pt': 'Continuação leste da mata, ainda na célula floresta (13,22). Sem chefe. As duas brechas em x=97, y=15 e y=17 são a entrada.',
            'en': 'East continuation of the woods, still on forest cell (13,22). No boss. The two gaps at x=97, y=15 and y=17 are the entrance.',
        },
        'chunks': [{
            'id': 'trilha',
            'name': {'pt': 'Trilha Leste', 'en': 'East Track'},
            'rect': [98, 12, FOREST_W, ZONE_H],
            'build': 'nao',
            'danger': 2,
            'invasion': False,
            'spawns': [
                {'monster': 'goblin', 'count': [3, 6], 'level': 4},
                {'monster': 'goblin_runner', 'count': [1, 3], 'level': 3},
                {'monster': 'goblin_spearman', 'count': [1, 2], 'level': 4},
            ],
        }],
    })
    zones.append({
        'id': 'seara_leste',
        'name': {'pt': 'Seara a Leste', 'en': 'East Fields'},
        'map': 'mundo',
        'kind': 'hunt',
        'biome': 'plains',
        'level': [6, 6],
        'origin': [128, 12],
        'size': [ADD_W - FOREST_W, ZONE_H],
        'build': 'aberta',
        'danger': 2,
        'invasion': True,
        'resources': {
            'common': ['logs', 'stone', 'iron_ore', 'copper_ore'],
            'rare': ['silver_ore', 'leather_hide'],
        },
        'layout_cell': [14, 22],
        'world_origin': [768 + 128, 1408 + 12],
        'unlock': {'kind': 'always'},
        'note': {
            'pt': 'Primeiro campo aberto a leste da mata, célula de planície (14,22). Sem chefe. Aberto desde o começo: é o passo seguinte da fatia inicial, não o portão do bioma inteiro.',
            'en': 'First open field east of the woods, plains cell (14,22). No boss. Open from the start: it is the next step of the starter slice, not the gate for the whole biome.',
        },
        'chunks': [{
            'id': 'seara',
            'name': {'pt': 'Seara', 'en': 'Fields'},
            'rect': [128, 12, ADD_W - FOREST_W, ZONE_H],
            'build': 'aberta',
            'danger': 2,
            'invasion': True,
            'spawns': [
                {'monster': 'goblin', 'count': [3, 5], 'level': 6},
                {'monster': 'goblin_spearman', 'count': [2, 4], 'level': 6},
                {'monster': 'skeleton', 'count': [2, 3], 'level': 6},
            ],
        }],
    })
    z['zones'] = zones
    with open(ZONES, 'w', encoding='utf-8') as f:
        json.dump(z, f, ensure_ascii=False, indent=2)
        f.write('\n')


def preview(layers):
    from PIL import Image, ImageDraw, ImageFont
    bg, ob, col = layers['background'], layers['object'], layers['collision']
    # Mostra a borda leste antiga (16 colunas) e a extensão.
    x0 = KEEP_W - 16
    x1 = KEEP_W + ADD_W
    tw = 10
    pad = 16
    header = 48
    w = (x1 - x0) * tw + pad * 2
    h = H * tw + header + 36
    im = Image.new('RGB', (w, h), (22, 24, 28))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf', 16)
    font_s = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-Regular.ttf', 12)
    for y in range(H):
        for x in range(x0, x1):
            if col[y][x]:
                color = (36, 72, 44) if x >= KEEP_W else (28, 56, 36)
            elif bg[y][x] in DIRT or 32 <= bg[y][x] <= 47:
                color = (176, 142, 86)
            elif bg[y][x] == 0:
                color = (18, 20, 18)
            else:
                color = (92, 140, 70) if x < KEEP_W else (116, 164, 82)
            if x == KEEP_W:
                color = (220, 200, 140)
            px = pad + (x - x0) * tw
            py = header + y * tw
            d.rectangle([px, py, px + tw - 1, py + tw - 1], fill=color)
    d.text((pad, 8), 'Trilha Leste — encosta no Bosque sem mover a fatia 98×60', fill=(236, 232, 220), font=font)
    d.text((pad, 28), 'Esquerda: mapa atual. Faixa clara: emenda. Direita: mata (30) e seara (18). Sem chefe.', fill=(180, 176, 164), font=font_s)
    im.save(PREVIEW)


def main():
    header, layers, order = load_txt(MAP)
    # Guarda as 98 colunas originais para o teste.
    original = {k: [row[:KEEP_W] for row in v] for k, v in layers.items()}
    ext = build_extension()
    layers = stitch(layers, ext)
    for kind in order:
        assert all(row[:KEEP_W] == original[kind][y] for y, row in enumerate(layers[kind]))
        assert len(layers[kind][0]) == KEEP_W + ADD_W
    # As brechas continuam abertas dos dois lados.
    assert layers['collision'][15][97] == 0 and layers['collision'][15][98] == 0
    assert layers['collision'][17][97] == 0 and layers['collision'][17][98] == 0
    write_txt(MAP, header, layers, order, title='Mundo — Vila, Bosque e Trilha Leste')
    write_tmx(TMX, layers, order, KEEP_W + ADD_W, H,
              'Mundo — Vila, Bosque e Trilha Leste', '43,1', continuous=True)
    write_piece(ext)
    update_zones()
    preview(layers)
    print('mundo', KEEP_W + ADD_W, 'x', H)
    print('piece', PIECE_TXT)
    print('preview', PREVIEW)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Confere uma casa em camadas (ART_SPEC seção 5) e gera uma prancha de revisão.

    python3 build/check_house.py art/buildings/plains/plains_cabin_01

Saída: <pasta>/_check.png com
  1. exterior   = back + front + door_closed + roof
  2. interior   = back + props + front_low + door_open (o que o jogador vê dentro)
  3..n. cada camada sozinha, sobre xadrez, com a planta (losangos) desenhada
e um relatório no terminal: tamanhos e âncora iguais, pixels soltos fora da
planta, altura da front_low e da porta em relação ao personagem (140 px no master).
"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw

TW, TH = 192, 96          # tile do master
CHAR_H = 140              # personagem de pé no master (70 px no jogo)


def diamond(cx, cy):
    return [(cx, cy - TH // 2), (cx + TW // 2, cy), (cx, cy + TH // 2), (cx - TW // 2, cy)]


def tile_center(ax, ay, i, j):
    return ax + (i - j) * TW // 2, ay + (i + j) * TH // 2


def checker(size, s=16):
    im = Image.new('RGBA', size, (60, 60, 60, 255))
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], s):
        for x in range(0, size[0], s):
            if (x // s + y // s) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(80, 80, 80, 255))
    return im


def outline(im, h):
    d = ImageDraw.Draw(im)
    ax, ay = h['anchor']
    w, dpt = h['size']
    for j in range(dpt):
        for i in range(w):
            d.polygon(diamond(*tile_center(ax, ay, i, j)), outline=(255, 0, 255, 160))
    d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], outline=(255, 255, 0, 255), width=2)


def main(folder):
    h = json.load(open(os.path.join(folder, 'house.json'), encoding='utf-8'))
    ax, ay = h['anchor']
    w, dpt = h['size']
    L = {k: Image.open(os.path.join(folder, v)).convert('RGBA') for k, v in h['layers'].items()}
    probs = []
    sizes = {k: im.size for k, im in L.items()}
    if len(set(sizes.values())) != 1:
        probs.append(f'camadas com tamanhos diferentes: {sizes}')
    for need in ('back', 'front', 'front_low', 'roof', 'door_closed', 'door_open'):
        if need not in L:
            probs.append(f'falta a camada {need}')
    size = next(iter(L.values())).size

    # máscara da planta (com folga de meio tile para beiral e degrau)
    foot = Image.new('L', size, 0)
    fd = ImageDraw.Draw(foot)
    for j in range(-1, dpt + 1):
        for i in range(-1, w + 1):
            fd.polygon(diamond(*tile_center(ax, ay, i, j)), fill=255)
    # tudo que está acima da planta (paredes e telhado sobem) também conta como dentro
    top = min(tile_center(ax, ay, 0, 0)[1], 0)
    for x in range(size[0]):
        col = [foot.getpixel((x, y)) for y in range(size[1])]
        if 255 in col:
            last = len(col) - 1 - col[::-1].index(255)
            for y in range(0, last):
                foot.putpixel((x, y), 255)
    for k, im in L.items():
        a = im.split()[3].point(lambda v: 255 if v > 16 else 0)
        out_of = ImageChops.subtract(a, foot)
        stray = out_of.histogram()[255]
        if stray > 50:
            probs.append(f'{k}: {stray} pixels fora da planta (sujeira ou peça no lugar errado)')

    def opaque_height(im):
        bb = im.split()[3].point(lambda v: 255 if v > 32 else 0).getbbox()
        return (bb[3] - bb[1]) if bb else 0

    # a planta tem de caber na imagem e bater com o desenho
    corners = {'norte': (ax, ay - TH // 2),
               'leste': (tile_center(ax, ay, w - 1, 0)[0] + TW // 2, tile_center(ax, ay, w - 1, 0)[1]),
               'sul': (tile_center(ax, ay, w - 1, dpt - 1)[0], tile_center(ax, ay, w - 1, dpt - 1)[1] + TH // 2),
               'oeste': (tile_center(ax, ay, 0, dpt - 1)[0] - TW // 2, tile_center(ax, ay, 0, dpt - 1)[1])}
    for k, (x, y) in corners.items():
        if not (0 <= x < size[0] and 0 <= y < size[1]):
            probs.append(f'a quina {k} da planta ({x},{y}) fica fora da imagem {size}: âncora errada ou imagem pequena')
    # nada pode encostar na borda (sinal de render cortado)
    for k, im in L.items():
        bb = im.split()[3].point(lambda v: 255 if v > 16 else 0).getbbox()
        if bb and (bb[0] <= 1 or bb[1] <= 1 or bb[2] >= size[0] - 1 or bb[3] >= size[1] - 1):
            probs.append(f'{k}: o desenho encosta na borda da imagem {bb} (render cortado)')
    # o chão da back deve ocupar a planta: compara as pontas do desenho com as quinas
    if 'back' in L:
        bb = L['back'].split()[3].point(lambda v: 255 if v > 16 else 0).getbbox()
        if bb:
            dx_l, dx_r, dy_b = bb[0] - corners['oeste'][0], bb[2] - corners['leste'][0], bb[3] - corners['sul'][1]
            print(f'back vs planta: esquerda {dx_l:+}px, direita {dx_r:+}px, base {dy_b:+}px')
            if max(abs(dx_l), abs(dx_r), abs(dy_b)) > 60:
                probs.append(f'a back não bate com a planta (esq {dx_l:+}, dir {dx_r:+}, base {dy_b:+} px): confira anchor e size no house.json')

    # altura da front_low e da front: a low deve ter ~20% da front
    if 'front' in L and 'front_low' in L:
        hf, hl = opaque_height(L['front']), opaque_height(L['front_low'])
        # a parede sobe a partir da linha da planta; mede a parte acima do chão
        floor_y = tile_center(ax, ay, w - 1, dpt - 1)[1] + TH // 2
        def above(im):
            bb = im.split()[3].point(lambda v: 255 if v > 32 else 0).getbbox()
            return floor_y - bb[1] if bb else 0
        ra = above(L['front_low']) / max(1, above(L['front']))
        print(f'front: {hf}px de altura, front_low: {hl}px; parte acima do chão low/front = {ra:.2f}')
        if ra > 0.45:
            probs.append(f'front_low alta demais ({ra:.0%} da front; o alvo é ~20%)')
    if 'door_closed' in L:
        hd = opaque_height(L['door_closed'])
        print(f'porta: {hd}px = {hd / CHAR_H:.2f}× o personagem ({CHAR_H}px no master)')
        if hd < 1.2 * CHAR_H:
            probs.append('porta menor que 1,2× o personagem')

    # prancha
    def comp(keys):
        im = checker(size)
        for k in keys:
            if k in L:
                im.alpha_composite(L[k])
        return im
    props = Image.new('RGBA', size, (0, 0, 0, 0))
    panels = [('exterior', comp(['back', 'front', 'door_closed', 'roof'])),
              ('interior', comp(['back', 'front_low', 'door_open']))]
    for k in ('back', 'front', 'front_low', 'roof', 'door_closed', 'door_open'):
        if k in L:
            im = comp([k]); outline(im, h); panels.append((k, im))
    sc = 0.5
    pw, ph = int(size[0] * sc), int(size[1] * sc)
    cols = 3
    sheet = Image.new('RGBA', (pw * cols, (ph + 20) * ((len(panels) + cols - 1) // cols)), (30, 30, 30, 255))
    d = ImageDraw.Draw(sheet)
    for n, (name, im) in enumerate(panels):
        x, y = (n % cols) * pw, (n // cols) * (ph + 20)
        sheet.paste(im.resize((pw, ph)), (x, y + 20))
        d.text((x + 6, y + 4), name, fill=(255, 220, 120, 255))
    out = os.path.join(folder, '_check.png')
    sheet.save(out)
    print('prancha:', out)
    if probs:
        print('\nPROBLEMAS:'); [print(' -', p) for p in probs]; sys.exit(1)
    print('\nOK')


if __name__ == '__main__':
    main(sys.argv[1])

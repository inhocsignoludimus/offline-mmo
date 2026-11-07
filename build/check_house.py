#!/usr/bin/env python3
"""Confere uma casa em camadas (ART_SPEC seção 5) e gera uma prancha de revisão.

    python3 build/check_house.py art/buildings/plains/plains_cabin_01

Saída: <pasta>/_check.png com
  1. exterior   = back + front + door_closed + roof
  2. interior   = back + props + front_low + door_open (o que o jogador vê dentro)
  3..n. cada camada sozinha, sobre xadrez, com a planta (losangos) desenhada
e um relatório no terminal: tamanhos e âncora iguais, pixels soltos fora da
planta, altura da front_low e da porta em relação ao personagem (140 px no master).

A front_low é a parede da frente cortada no rodapé (cerca de 20% da altura,
ART_SPEC seção 5). A altura conta por coluna, em cima da linha da fachada
(sul e leste), não a partir da quina sul. A quina sul é o ponto mais baixo
da planta: numa fachada de N tiles a linha do chão sobe 48 px por tile, e
somar isso ao topo do desenho infla o rodapé (uma sill de 20% numa frente
de 5 tiles lia ~58%).
"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw

TW, TH = 192, 96          # tile do master
CHAR_H = 140              # personagem de pé no master (70 px no jogo)
# Fração da parede normal (acima da linha da fachada) a partir da qual o
# rodapé está alto demais. 20–30% é o alvo; 0.40 ainda rejeita um corte
# real de ~40% (num desenho encostado na planta isso é 0.40; com a face
# do tronco um pouco para dentro da linha, um corte de 40% lê ~0.45).
SILL_MAX = 0.40
SILL_MIN_COVER = 0.70     # as duas frentes, não um toco perto da porta
WALL_BAND = 520           # px acima da linha da planta em que a parede pode subir
GROUND_SLACK = 36         # a face do tronco pode passar um pouco da quina
MIN_WALL_PX = 100         # abaixo disso a coluna é vão de porta, não parede
MIN_FACADE_COLS = 48


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


def _corners(ax, ay, w, dpt):
    west_c = tile_center(ax, ay, 0, dpt - 1)
    south_c = tile_center(ax, ay, w - 1, dpt - 1)
    east_c = tile_center(ax, ay, w - 1, 0)
    west = (west_c[0] - TW // 2, west_c[1])
    south = (south_c[0], south_c[1] + TH // 2)
    east = (east_c[0] + TW // 2, east_c[1])
    north = (ax, ay - TH // 2)
    return {'norte': north, 'leste': east, 'sul': south, 'oeste': west}


def _line_y(p, q, x):
    if q[0] == p[0]:
        return None
    t = (x - p[0]) / (q[0] - p[0])
    if t < -0.02 or t > 1.02:
        return None
    return p[1] + t * (q[1] - p[1])


def _alpha(im, thr=32):
    ch = im.split()[3]
    # binariza uma vez; o resto é varredura de coluna
    return ch.point(lambda v, t=thr: 255 if v > t else 0).tobytes(), im.size[0], im.size[1]


def _top(raw, w, h, x, y0, y1):
    if x < 0 or x >= w:
        return None
    y0 = 0 if y0 < 0 else h - 1 if y0 >= h else int(y0)
    y1 = 0 if y1 < 0 else h - 1 if y1 >= h else int(y1)
    if y1 < y0:
        return None
    for y in range(y0, y1 + 1):
        if raw[y * w + x]:
            return y
    return None


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2]


def facade_sill(front, low, anchor, size):
    """Altura do rodapé / parede normal, por fachada da frente.

    Cada item: n_front, n_low, cov, med_ratio (None se não houver parede).
    `med_ratio` usa as colunas da altura normal (percentil 30, para o
    oitão não puxar a parede para cima e esconder um rodapé alto).
    """
    ax, ay = anchor
    w, dpt = size
    c = _corners(ax, ay, w, dpt)
    fr, fw, fh = _alpha(front)
    lr, lw, lh = _alpha(low)
    out = {}
    for name, p, q in (('sul', c['oeste'], c['sul']), ('leste', c['leste'], c['sul'])):
        rows = []
        n_front = 0
        x0 = int(min(p[0], q[0])) + 6
        x1 = int(max(p[0], q[0])) - 6
        for x in range(x0, x1 + 1):
            yg = _line_y(p, q, x)
            if yg is None:
                continue
            tf = _top(fr, fw, fh, x, yg - WALL_BAND, yg + GROUND_SLACK)
            if tf is None:
                continue
            Hf = yg - tf
            if Hf < MIN_WALL_PX:
                continue
            n_front += 1
            tl = _top(lr, lw, lh, x, yg - WALL_BAND, yg + GROUND_SLACK)
            if tl is None:
                continue
            Hl = yg - tl
            if Hl < 8:
                continue
            rows.append((Hf, Hl))
        if n_front < MIN_FACADE_COLS or not rows:
            out[name] = {'n_front': n_front, 'n_low': len(rows), 'cov': 0.0, 'med_ratio': None}
            continue
        ordered = sorted(Hf for Hf, _ in rows)
        h_ref = ordered[max(0, int(len(ordered) * 0.30))]
        normal = [Hl / Hf for Hf, Hl in rows if Hf <= h_ref * 1.12]
        if not normal:
            normal = [Hl / Hf for Hf, Hl in rows]
        out[name] = {
            'n_front': n_front,
            'n_low': len(rows),
            'cov': len(rows) / n_front,
            'med_ratio': _median(normal),
        }
    return out


def sill_problems(stats):
    probs = []
    for name, s in stats.items():
        if s['n_front'] < MIN_FACADE_COLS:
            continue
        if s['cov'] < SILL_MIN_COVER:
            probs.append(
                f'front_low não cobre a fachada {name} ({s["cov"]:.0%} das colunas da parede; '
                f'as duas frentes precisam do rodapé)')
            continue
        r = s['med_ratio']
        if r is not None and r > SILL_MAX:
            probs.append(
                f'front_low alta demais na fachada {name} ({r:.0%} da parede normal; o limite é {SILL_MAX:.0%}). '
                f'A altura é medida acima da linha dessa fachada, não a partir da quina sul')
    return probs


def evaluate(folder):
    """Devolve (problemas, linhas de relatório). Não grava a prancha."""
    h = json.load(open(os.path.join(folder, 'house.json'), encoding='utf-8'))
    ax, ay = h['anchor']
    w, dpt = h['size']
    L = {k: Image.open(os.path.join(folder, v)).convert('RGBA') for k, v in h['layers'].items()}
    probs = []
    info = []
    sizes = {k: im.size for k, im in L.items()}
    if len(set(sizes.values())) != 1:
        probs.append(f'camadas com tamanhos diferentes: {sizes}')
    for need in ('back', 'front', 'front_low', 'roof', 'door_closed', 'door_open'):
        if need not in L:
            probs.append(f'falta a camada {need}')
    size = next(iter(L.values())).size

    # máscara da planta (com folga de um tile para beiral e degrau)
    foot = Image.new('L', size, 0)
    fd = ImageDraw.Draw(foot)
    for j in range(-1, dpt + 1):
        for i in range(-1, w + 1):
            fd.polygon(diamond(*tile_center(ax, ay, i, j)), fill=255)
    # tudo que está acima da planta (paredes e telhado sobem) também conta como dentro
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
    corners = _corners(ax, ay, w, dpt)
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
            dx_l = bb[0] - corners['oeste'][0]
            dx_r = bb[2] - corners['leste'][0]
            dy_b = bb[3] - corners['sul'][1]
            info.append(f'back vs planta: esquerda {dx_l:+}px, direita {dx_r:+}px, base {dy_b:+}px')
            if max(abs(dx_l), abs(dx_r), abs(dy_b)) > 60:
                probs.append(f'a back não bate com a planta (esq {dx_l:+}, dir {dx_r:+}, base {dy_b:+} px): confira anchor e size no house.json')

    if 'front' in L and 'front_low' in L:
        stats = facade_sill(L['front'], L['front_low'], (ax, ay), (w, dpt))
        bits = []
        for name, s in stats.items():
            if s['med_ratio'] is None:
                bits.append(f'{name}: sem parede mensurável ({s["n_front"]} col)')
            else:
                bits.append(f'{name}: {s["med_ratio"]:.2f} (cobertura {s["cov"]:.0%}, {s["n_low"]}/{s["n_front"]} col)')
        info.append('front_low / parede normal, acima da linha da fachada: ' + '; '.join(bits))
        probs.extend(sill_problems(stats))
    if 'door_closed' in L:
        hd = opaque_height(L['door_closed'])
        info.append(f'porta: {hd}px = {hd / CHAR_H:.2f}× o personagem ({CHAR_H}px no master)')
        if hd < 1.2 * CHAR_H:
            probs.append('porta menor que 1,2× o personagem')
    return probs, info, h, L


def write_sheet(folder, h, L):
    size = next(iter(L.values())).size

    def comp(keys):
        im = checker(size)
        for k in keys:
            if k in L:
                im.alpha_composite(L[k])
        return im

    panels = [('exterior', comp(['back', 'front', 'door_closed', 'roof'])),
              ('interior', comp(['back', 'front_low', 'door_open']))]
    for k in ('back', 'front', 'front_low', 'roof', 'door_closed', 'door_open'):
        if k in L:
            im = comp([k])
            outline(im, h)
            panels.append((k, im))
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
    return out


def main(folder):
    probs, info, h, L = evaluate(folder)
    for line in info:
        print(line)
    print('prancha:', write_sheet(folder, h, L))
    if probs:
        print('\nPROBLEMAS:')
        for p in probs:
            print(' -', p)
        sys.exit(1)
    print('\nOK')


if __name__ == '__main__':
    main(sys.argv[1])

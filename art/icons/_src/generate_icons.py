#!/usr/bin/env python3
"""Generate dark painted 128px icons for offline-mmo (skills, scrolls, potions,
reagents, the 37 missing items, and ore/ingot/log resources).

Sources: game-icons.net SVGs (CC-BY 3.0) via jsdelivr, recolored/shaded to match
TCoM item icons; potions/scrolls/ores/ingots drawn procedurally.
"""
from __future__ import annotations
import json, os, re, hashlib, urllib.request
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import cairosvg

ROOT = Path('/workspace/offline-mmo')
OUT = ROOT / 'art' / 'icons'
CACHE = Path('/workspace/offline-mmo-art/work/icons_gen/svg_cache')
CACHE.mkdir(parents=True, exist_ok=True)
SIZE = 128

# ---------- SVG fetch + paint ----------
CDN = 'https://cdn.jsdelivr.net/gh/game-icons/icons@master/{author}/{name}.svg'

def fetch_svg(author: str, name: str) -> Path:
    p = CACHE / f'{author}__{name}.svg'
    if not p.exists():
        url = CDN.format(author=author, name=name)
        req = urllib.request.Request(url, headers={'User-Agent': 'offline-mmo-icon-gen/1'})
        with urllib.request.urlopen(req, timeout=30) as r:
            p.write_bytes(r.read())
    return p

def svg_mask(svg_path: Path, render=256) -> np.ndarray:
    svg = svg_path.read_text(encoding='utf-8')
    svg = re.sub(r'<path d="M0 0h512v512H0z"/>', '', svg, count=1)
    # force white fill on remaining paths that lack fill
    svg = svg.replace('fill="#fff"', 'fill="#ffffff"')
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=render, output_height=render)
    arr = np.array(Image.open(BytesIO(png)).convert('RGBA')).astype(np.float32)
    a = arr[:, :, 3] / 255.0
    bright = arr[:, :, 0] / 255.0
    # white glyph on transparent → mask
    mask = np.clip(a * np.maximum(bright, (a > 0.05).astype(np.float32)), 0, 1)
    # if mostly dark-on-transparent (no white fill), use alpha alone
    if mask.mean() < 0.01 and a.mean() > 0.01:
        mask = a
    return mask

def paint_mask(mask: np.ndarray, tint=(120, 110, 95), size=SIZE, seed=0) -> Image.Image:
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    light = np.clip(1.28 - (xx * 0.42 + yy * 0.68) / h, 0.32, 1.38)
    a8 = (np.clip(mask, 0, 1) * 255).astype(np.uint8)
    aimg = Image.fromarray(a8, 'L')
    # soft inner bevel
    er = np.array(aimg.filter(ImageFilter.MinFilter(5))).astype(np.float32) / 255.0
    dil = np.array(aimg.filter(ImageFilter.MaxFilter(3))).astype(np.float32) / 255.0
    hi = np.clip(mask - er, 0, 1)
    lo = np.clip(dil - mask, 0, 1)
    shade = light + hi * 0.45 - lo * 0.25
    out = np.zeros((h, w, 4), np.float32)
    tr, tg, tb = tint
    out[:, :, 0] = np.clip(tr * shade, 0, 255)
    out[:, :, 1] = np.clip(tg * shade, 0, 255)
    out[:, :, 2] = np.clip(tb * shade, 0, 255)
    rng = np.random.default_rng(seed if seed else (tr * 3 + tg * 5 + tb))
    grain = rng.normal(0, 7.5, (h, w))
    m = mask > 0.04
    for c in range(3):
        ch = out[:, :, c]
        ch[m] = np.clip(ch[m] + grain[m], 0, 255)
        out[:, :, c] = ch
    out[:, :, 3] = mask * 255
    im = Image.fromarray(out.astype(np.uint8), 'RGBA').resize((size, size), Image.Resampling.LANCZOS)
    return im

def from_game_icon(author, name, tint, seed=0) -> Image.Image:
    return paint_mask(svg_mask(fetch_svg(author, name)), tint, seed=seed)

# ---------- procedural: potion ----------
def draw_potion(liquid, cork=(90, 60, 35), glass=(160, 155, 145), greater=False) -> Image.Image:
    s = SIZE
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # bottle body
    cx, top, bot = s // 2, 28, 110
    if greater:
        body = [(cx - 28, 48), (cx + 28, 48), (cx + 32, 100), (cx + 22, bot), (cx - 22, bot), (cx - 32, 100)]
        neck = [(cx - 10, 28), (cx + 10, 28), (cx + 12, 48), (cx - 12, 48)]
    else:
        body = [(cx - 22, 50), (cx + 22, 50), (cx + 26, 98), (cx + 18, bot), (cx - 18, bot), (cx - 26, 98)]
        neck = [(cx - 8, 30), (cx + 8, 30), (cx + 10, 50), (cx - 10, 50)]
    # shadow body
    d.polygon([(x + 2, y + 2) for x, y in body], fill=(20, 18, 15, 90))
    d.polygon(body, fill=(*glass, 230))
    # liquid fill lower 60%
    ly0 = 62 if not greater else 60
    liquid_poly = [(x, max(y, ly0)) for x, y in body]
    # rebuild liquid as clipped body below ly0
    d.polygon([
        (body[0][0], ly0), (body[1][0], ly0), body[2], body[3], body[4], body[5]
    ], fill=(*liquid, 240))
    # glass highlight
    d.line([(cx - 14, 55), (cx - 16, 95)], fill=(255, 255, 255, 70), width=3)
    d.polygon(neck, fill=(140, 135, 125, 240))
    # cork
    d.rectangle([cx - 9, 18, cx + 9, 32], fill=(*cork, 255))
    d.rectangle([cx - 7, 16, cx + 7, 22], fill=(cork[0] + 20, cork[1] + 15, cork[2] + 10, 255))
    # soft edge
    return _grain(im, seed=sum(liquid))

def draw_bandage(heavy=False) -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (210, 200, 175) if not heavy else (180, 165, 140)
    d.rounded_rectangle([30, 40, 98, 88], radius=6, fill=(*col, 255))
    d.rounded_rectangle([34, 44, 94, 84], radius=4, fill=(col[0] - 25, col[1] - 25, col[2] - 25, 255))
    for y in (52, 64, 76):
        d.line([(38, y), (90, y)], fill=(150, 140, 120, 200), width=2)
    if heavy:
        d.ellipse([52, 54, 76, 74], fill=(140, 50, 45, 220))
    return _grain(im, 11)

def draw_scroll(circle: int) -> Image.Image:
    # circle tint colors — muted but distinct; strong only as accent ribbon
    colors = {
        1: (160, 150, 130),   # parchment plain
        2: (120, 140, 110),   # pale green
        3: (100, 125, 150),   # steel blue
        4: (140, 110, 130),   # dusty violet
        5: (150, 115, 80),    # amber
        6: (130, 90, 90),     # dried blood
        7: (90, 110, 120),    # verdigris
        8: (100, 85, 120),    # deep indigo
    }
    accent = {
        1: (180, 160, 90), 2: (70, 130, 70), 3: (60, 110, 170), 4: (130, 70, 140),
        5: (190, 120, 40), 6: (160, 45, 40), 7: (40, 140, 130), 8: (90, 50, 160),
    }
    parchment = colors[circle]
    ribbon = accent[circle]
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # rolled scroll
    d.ellipse([22, 30, 42, 98], fill=(parchment[0] - 30, parchment[1] - 30, parchment[2] - 30, 255))
    d.rectangle([32, 34, 96, 94], fill=(*parchment, 255))
    d.ellipse([86, 30, 106, 98], fill=(parchment[0] + 15, parchment[1] + 10, parchment[2], 255))
    # text lines
    for i, y in enumerate((48, 58, 68, 78)):
        d.line([(42, y), (88, y)], fill=(90, 80, 65, 160), width=2)
    # wax seal / ribbon by circle
    d.ellipse([55, 70, 78, 93], fill=(*ribbon, 255))
    d.ellipse([60, 74, 73, 87], fill=(ribbon[0] + 30, ribbon[1] + 20, ribbon[2] + 20, 200))
    # circle numeral tick marks on seal
    d.text((61, 76), str(circle), fill=(20, 15, 10, 230))
    return _grain(im, circle * 17)

def draw_ore(tint) -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # irregular rock chunks
    chunks = [
        [(40, 50), (70, 35), (95, 55), (85, 90), (45, 95), (30, 70)],
        [(55, 40), (80, 30), (100, 50), (90, 70), (60, 65)],
        [(35, 70), (55, 60), (70, 80), (50, 100), (28, 88)],
    ]
    for i, poly in enumerate(chunks):
        shade = tuple(max(0, c - i * 18) for c in tint)
        d.polygon(poly, fill=(*shade, 255))
        # sparkle speck
        d.ellipse([poly[1][0], poly[1][1], poly[1][0] + 6, poly[1][1] + 6],
                  fill=(min(255, tint[0] + 60), min(255, tint[1] + 50), min(255, tint[2] + 40), 200))
    return _grain(im, sum(tint))

def draw_ingot(tint) -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # stacked bars
    for i, y0 in enumerate((38, 58, 78)):
        shade = tuple(max(0, min(255, c - i * 12 + 10)) for c in tint)
        d.polygon([(28, y0 + 18), (48, y0), (108, y0), (88, y0 + 18)], fill=(*shade, 255))
        top = tuple(min(255, c + 35) for c in shade)
        d.polygon([(48, y0), (108, y0), (100, y0 - 8), (40, y0 - 8)], fill=(*top, 255))
        side = tuple(max(0, c - 40) for c in shade)
        d.polygon([(28, y0 + 18), (88, y0 + 18), (100, y0), (40, y0 - 8)], fill=(*side, 180))
    return _grain(im, sum(tint) + 3)

def draw_log() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bark = (90, 60, 35)
    d.ellipse([18, 40, 48, 88], fill=(bark[0] - 20, bark[1] - 15, bark[2] - 10, 255))
    d.rectangle([33, 42, 100, 86], fill=(*bark, 255))
    d.ellipse([85, 40, 115, 88], fill=(210, 185, 140, 255))  # cut face
    # rings
    d.ellipse([92, 50, 108, 78], outline=(160, 130, 90, 220), width=2)
    d.ellipse([97, 58, 103, 70], outline=(140, 110, 70, 200), width=1)
    for x in (45, 60, 75):
        d.line([(x, 48), (x + 3, 80)], fill=(60, 40, 25, 160), width=2)
    return _grain(im, 42)

def draw_boards() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, y in enumerate((36, 56, 76)):
        c = (160 - i * 15, 120 - i * 10, 70 - i * 5)
        d.rectangle([24, y, 104, y + 16], fill=(*c, 255))
        d.line([(30, y + 4), (98, y + 4)], fill=(c[0] + 30, c[1] + 20, c[2] + 10, 180), width=1)
    return _grain(im, 43)

def draw_coin() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([28, 28, 100, 100], fill=(180, 150, 50, 255))
    d.ellipse([36, 36, 92, 92], fill=(220, 185, 60, 255))
    d.ellipse([48, 48, 80, 80], outline=(140, 110, 30, 255), width=3)
    return _grain(im, 99)

def draw_bread() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([24, 48, 104, 96], fill=(170, 120, 60, 255))
    d.ellipse([30, 40, 98, 80], fill=(200, 155, 80, 255))
    for x in (45, 64, 82):
        d.arc([x - 8, 48, x + 8, 68], 200, 340, fill=(140, 95, 45, 200), width=2)
    return _grain(im, 7)

def draw_meat() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(40, 40), (90, 35), (100, 70), (70, 100), (35, 85)], fill=(120, 70, 45, 255))
    d.polygon([(50, 48), (80, 45), (85, 65), (60, 80)], fill=(90, 50, 35, 230))
    return _grain(im, 8)

def draw_deed() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([30, 24, 98, 104], fill=(210, 195, 160, 255))
    d.rectangle([36, 30, 92, 98], outline=(120, 100, 70, 255), width=2)
    for y in (45, 55, 65, 75):
        d.line([(42, y), (86, y)], fill=(100, 85, 60, 180), width=2)
    d.polygon([(70, 80), (95, 70), (95, 100)], fill=(160, 50, 45, 230))  # seal ribbon
    return _grain(im, 55)

def draw_hide() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(35, 40), (70, 28), (100, 45), (95, 95), (40, 100), (25, 70)], fill=(120, 85, 50, 255))
    d.polygon([(45, 50), (75, 42), (85, 70), (55, 80)], fill=(90, 60, 35, 200))
    return _grain(im, 61)

def draw_cloth_bolt() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([30, 40, 98, 70], fill=(160, 155, 145, 255))
    d.rectangle([30, 55, 98, 95], fill=(140, 135, 125, 255))
    d.ellipse([30, 80, 98, 110], fill=(120, 115, 105, 255))
    d.line([(40, 60), (40, 90)], fill=(200, 195, 185, 180), width=3)
    return _grain(im, 62)

def draw_arrow_icon() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(30, 95), (95, 35)], fill=(130, 100, 60, 255), width=4)
    d.polygon([(95, 35), (100, 50), (85, 40)], fill=(150, 150, 155, 255))
    d.polygon([(30, 95), (40, 100), (35, 85)], fill=(180, 170, 140, 255))
    return _grain(im, 63)

def draw_bolt() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(35, 90), (92, 40)], fill=(70, 70, 75, 255), width=5)
    d.polygon([(92, 40), (100, 52), (85, 48)], fill=(160, 160, 165, 255))
    d.rectangle([32, 88, 42, 98], fill=(90, 60, 40, 255))
    return _grain(im, 64)

def draw_chest() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([28, 50, 100, 100], fill=(110, 75, 40, 255))
    d.rectangle([28, 40, 100, 58], fill=(130, 90, 50, 255))
    d.rectangle([58, 60, 70, 72], fill=(180, 150, 50, 255))
    d.line([(30, 58), (98, 58)], fill=(60, 40, 20, 200), width=2)
    return _grain(im, 70)

def draw_bed() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([25, 55, 103, 95], fill=(100, 70, 40, 255))
    d.rectangle([30, 45, 98, 70], fill=(160, 150, 140, 255))
    d.rectangle([30, 45, 55, 62], fill=(180, 170, 160, 255))  # pillow
    return _grain(im, 71)

def draw_table() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(24, 55), (104, 55), (95, 70), (33, 70)], fill=(130, 95, 55, 255))
    d.rectangle([40, 70, 50, 100], fill=(100, 70, 40, 255))
    d.rectangle([78, 70, 88, 100], fill=(100, 70, 40, 255))
    return _grain(im, 72)

def draw_pants(tint=(90, 90, 100)) -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(40, 30), (88, 30), (92, 55), (70, 55), (75, 105), (55, 105), (58, 55), (36, 55)], fill=(*tint, 255))
    return _grain(im, sum(tint))

def draw_sandals() -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([30, 55, 95, 95], fill=(100, 70, 40, 255))
    d.arc([40, 45, 85, 75], 200, 340, fill=(140, 100, 60, 255), width=4)
    return _grain(im, 73)

def draw_greaves(metal=True) -> Image.Image:
    im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (130, 130, 135) if metal else (80, 80, 90)
    d.rectangle([40, 30, 60, 100], fill=(*c, 255))
    d.rectangle([68, 30, 88, 100], fill=(*(max(0, x - 15) for x in c), 255))
    d.ellipse([38, 25, 62, 40], fill=(min(255, c[0] + 30),) * 3 + (255,))
    d.ellipse([66, 25, 90, 40], fill=(min(255, c[0] + 20),) * 3 + (255,))
    return _grain(im, 74 if metal else 75)

def _grain(im: Image.Image, seed: int) -> Image.Image:
    arr = np.array(im).astype(np.float32)
    rng = np.random.default_rng(seed & 0xFFFFFFFF)
    grain = rng.normal(0, 6, arr.shape[:2])
    a = arr[:, :, 3] > 10
    for c in range(3):
        ch = arr[:, :, c]
        ch[a] = np.clip(ch[a] + grain[a], 0, 255)
        arr[:, :, c] = ch
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')

# ---------- catalog ----------
# skill -> (author, icon_name, tint_rgb)
SKILLS = {
    'swordsmanship': ('lorc', 'broadsword', (130, 125, 115)),
    'mace_fighting': ('lorc', 'spiked-mace', (120, 115, 110)),
    'fencing': ('lorc', 'plain-dagger', (140, 140, 145)),
    'archery': ('lorc', 'bowman', (120, 100, 70)),
    'tactics': ('lorc', 'battle-gear', (110, 100, 90)),
    'wrestling': ('lorc', 'punch', (140, 100, 80)),
    'parrying': ('lorc', 'checked-shield', (120, 120, 130)),
    'magery': ('lorc', 'wizard-staff', (100, 90, 130)),
    'evaluating_intelligence': ('lorc', 'brain', (130, 110, 140)),
    'meditation': ('lorc', 'yoga', (100, 120, 130)),
    'resisting_spells': ('lorc', 'shield-reflect', (90, 110, 130)),
    'blacksmithing': ('lorc', 'anvil', (120, 115, 110)),
    'carpentry': ('lorc', 'circular-sawblade', (130, 100, 70)),
    'tailoring': ('lorc', 'needle-drill', (140, 120, 100)),
    'alchemy': ('lorc', 'standing-potion', (90, 130, 100)),
    'tinkering': ('lorc', 'gears', (130, 125, 100)),
    'cooking': ('lorc', 'bowl-spiral', (160, 120, 70)),
    'mining': ('lorc', 'mining', (110, 100, 90)),
    'lumberjacking': ('lorc', 'wood-axe', (120, 95, 65)),
    'fishing': ('lorc', 'fishing-hook', (80, 110, 130)),
    'stealth': ('lorc', 'cloak-dagger', (70, 75, 80)),
    'hiding': ('lorc', 'robe', (70, 70, 85)),
    'snooping': ('lorc', 'locked-chest', (120, 110, 80)),
    'lockpicking': ('lorc', 'padlock', (140, 130, 100)),
    'animal_taming': ('lorc', 'wolf-head', (130, 100, 70)),
    'veterinary': ('lorc', 'bandage-roll', (140, 90, 90)),
    'healing': ('lorc', 'bleeding-heart', (140, 80, 80)),
    'anatomy': ('lorc', 'skeleton-inside', (150, 100, 100)),
    'camping': ('lorc', 'campfire', (160, 100, 50)),
    'tracking': ('lorc', 'footprint', (100, 110, 80)),
    'herding': ('lorc', 'hound', (150, 145, 130)),
    'musicianship': ('lorc', 'lyre', (140, 110, 70)),
    'provocation': ('lorc', 'music-spell', (150, 90, 70)),
    'peacemaking': ('lorc', 'peace-dove', (130, 140, 150)),
    'inscription': ('lorc', 'quill', (100, 90, 80)),
    'detecting_hidden': ('lorc', 'burning-eye', (120, 120, 90)),
    'poisoning': ('lorc', 'poison-bottle', (80, 130, 70)),
    'bowcraft_fletching': ('lorc', 'arrow-flights', (120, 100, 70)),
}

# fallbacks if an icon name 404s
SKILL_FALLBACKS = {
    'boxing-glove-surprise': ('lorc', 'punch'),
    'high-shot': ('lorc', 'archery-target'),
    'needle-drill': ('lorc', 'sewing-needle'),
    'cooked-meal': ('lorc', 'hot-meal'),
    'health-normal': ('lorc', 'hearts'),
    'peace-dove': ('lorc', 'dove'),
    'quill-ink': ('lorc', 'quill'),
    'arrow-dunk': ('lorc', 'arrow-flight'),
    'dog-bowl': ('lorc', 'sitting-dog'),
    'yoga': ('lorc', 'meditation'),
    'hidden': ('lorc', 'invisible'),
    'sing': ('lorc', 'musical-notes'),
    'mining': ('lorc', 'stone-pile'),
    'anatomy': ('lorc', 'skeleton'),
    'lock-picking': ('lorc', 'padlock-open'),
}

POTION_COLORS = {
    'heal_potion': (160, 50, 50),
    'greater_heal_potion': (190, 40, 40),
    'mana_potion': (50, 80, 170),
    'refresh_potion': (200, 170, 50),
    'greater_refresh_potion': (220, 180, 40),
    'cure_potion': (60, 150, 70),
    'greater_cure_potion': (40, 170, 60),
    'poison_potion': (90, 140, 40),
    'strength_potion': (160, 90, 40),
    'agility_potion': (50, 140, 120),
    'night_sight_potion': (80, 60, 140),
}

ORE = {
    'iron_ore': (90, 90, 95),
    'copper_ore': (160, 100, 55),
    'silver_ore': (170, 175, 185),
    'gold_ore': (180, 150, 50),
}
INGOT = {
    'iron_ingot': (120, 120, 125),
    'copper_ingot': (180, 110, 60),
    'silver_ingot': (190, 195, 205),
    'gold_ingot': (210, 175, 55),
}

REAGENTS = {
    'incense': ('lorc', 'perfume-bottle', (140, 110, 70)),
    'saltpeter': ('lorc', 'sands-of-time', (190, 190, 185)),
    'myrrh': ('lorc', 'bottle-vapors', (100, 70, 50)),
    'quicklime': ('lorc', 'stone-crafting', (210, 205, 190)),
}
REAGENT_FALLBACKS = {
    'incense': ('lorc', 'smoke-bomb'),
    'powder': ('lorc', 'sandstorm'),
    'bottle-vapors': ('lorc', 'perfume-bottle'),
    'powder-bag': ('lorc', 'sack'),
}

TOOLS = {
    'sewing_kit': ('lorc', 'sewing-needle', (140, 120, 100)),
    'fishing_pole': ('lorc', 'fishing-net', (100, 80, 55)),
    'mortar_pestle': ('lorc', 'bowl-spiral', (130, 120, 110)),
    'tinker_tools': ('lorc', 'screwdriver', (130, 125, 110)),
    'shovel': ('lorc', 'spade', (120, 110, 90)),
}
TOOL_FALLBACKS = {
    'fishing-pole': ('lorc', 'fishing-hook'),
    'mortar': ('lorc', 'pestle-mortar'),
    'screwdriver': ('lorc', 'gears'),
    'spade': ('lorc', 'trowel'),
}

def try_icon(author, name, tint, fallbacks_map=None):
    try:
        return from_game_icon(author, name, tint)
    except Exception as e:
        print(f'  miss {author}/{name}: {e}')
        if fallbacks_map and name in fallbacks_map:
            a2, n2 = fallbacks_map[name]
            print(f'  fallback -> {a2}/{n2}')
            return from_game_icon(a2, n2, tint)
        # last resort: generic gem
        return from_game_icon('lorc', 'crowned-skull', tint)

def save(im: Image.Image, *parts):
    path = OUT.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path

def main():
    produced = {}  # key -> relative path under art/icons

    print('=== skills ===')
    for sid, (author, name, tint) in SKILLS.items():
        im = try_icon(author, name, tint, SKILL_FALLBACKS)
        save(im, 'skills', f'{sid}.png')
        produced[sid] = f'skills/{sid}.png'
        print(' ', sid)

    print('=== spell scrolls (8 circles) ===')
    for c in range(1, 9):
        key = f'scroll_c{c}'
        save(draw_scroll(c), 'spells', f'{key}.png')
        produced[key] = f'spells/{key}.png'
        print(' ', key)

    print('=== reagents ===')
    for rid, (author, name, tint) in REAGENTS.items():
        im = try_icon(author, name, tint, {name: REAGENT_FALLBACKS.get(name, ('lorc', 'sacks'))})
        # also try reagent-specific fallbacks by id
        try:
            pass
        except Exception:
            pass
        save(im, 'reagents', f'{rid}.png')
        produced[rid] = f'reagents/{rid}.png'
        print(' ', rid)

    print('=== potions ===')
    for pid, col in POTION_COLORS.items():
        greater = pid.startswith('greater_')
        save(draw_potion(col, greater=greater), 'items', f'{pid}.png')
        produced[pid] = f'items/{pid}.png'
        print(' ', pid)
    save(draw_bandage(False), 'items', 'bandage.png'); produced['bandage'] = 'items/bandage.png'
    save(draw_bandage(True), 'items', 'greater_bandage.png'); produced['greater_bandage'] = 'items/greater_bandage.png'

    print('=== resources ===')
    save(draw_log(), 'resources', 'logs.png'); produced['logs'] = 'resources/logs.png'
    save(draw_boards(), 'resources', 'boards.png'); produced['boards'] = 'resources/boards.png'
    for k, t in ORE.items():
        save(draw_ore(t), 'resources', f'{k}.png'); produced[k] = f'resources/{k}.png'
    for k, t in INGOT.items():
        save(draw_ingot(t), 'resources', f'{k}.png'); produced[k] = f'resources/{k}.png'

    print('=== remaining of the 37 ===')
    save(draw_bread(), 'items', 'bread.png'); produced['bread'] = 'items/bread.png'
    save(draw_meat(), 'items', 'dried_meat.png'); produced['dried_meat'] = 'items/dried_meat.png'
    save(draw_hide(), 'items', 'leather_hide.png'); produced['leather_hide'] = 'items/leather_hide.png'
    save(draw_hide(), 'items', 'cut_leather.png'); produced['cut_leather'] = 'items/cut_leather.png'  # same base, darker via tint later
    # darken cut_leather
    cl = paint_mask(np.array(Image.open(OUT/'items'/'cut_leather.png').convert('L')).astype(np.float32)/255.0,
                    (100, 70, 40), seed=12)
    # simpler: redraw
    im = draw_hide()
    arr = np.array(im).astype(np.float32)
    arr[:, :, 0] *= 0.75; arr[:, :, 1] *= 0.7; arr[:, :, 2] *= 0.65
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA').save(OUT/'items'/'cut_leather.png')
    save(draw_cloth_bolt(), 'items', 'cloth_bolt.png'); produced['cloth_bolt'] = 'items/cloth_bolt.png'
    save(draw_arrow_icon(), 'items', 'arrow.png'); produced['arrow'] = 'items/arrow.png'
    save(draw_bolt(), 'items', 'crossbow_bolt.png'); produced['crossbow_bolt'] = 'items/crossbow_bolt.png'
    save(draw_chest(), 'items', 'wooden_chest.png'); produced['wooden_chest'] = 'items/wooden_chest.png'
    save(draw_bed(), 'items', 'simple_bed.png'); produced['simple_bed'] = 'items/simple_bed.png'
    save(draw_table(), 'items', 'wooden_table.png'); produced['wooden_table'] = 'items/wooden_table.png'
    save(draw_deed(), 'items', 'deed_plains_cabin.png'); produced['deed_plains_cabin'] = 'items/deed_plains_cabin.png'
    save(draw_deed(), 'items', 'deed_smithy.png'); produced['deed_smithy'] = 'items/deed_smithy.png'
    save(draw_coin(), 'items', 'gold_coin.png'); produced['gold_coin'] = 'items/gold_coin.png'
    save(draw_pants((85, 85, 95)), 'items', 'cloth_pants.png'); produced['cloth_pants'] = 'items/cloth_pants.png'
    save(draw_sandals(), 'items', 'cloth_sandals.png'); produced['cloth_sandals'] = 'items/cloth_sandals.png'
    save(draw_greaves(True), 'items', 'chain_greaves.png'); produced['chain_greaves'] = 'items/chain_greaves.png'
    save(draw_greaves(True), 'items', 'plate_legs.png'); produced['plate_legs'] = 'items/plate_legs.png'
    # plate slightly brighter
    pl = Image.open(OUT/'items'/'plate_legs.png').convert('RGBA')
    a = np.array(pl).astype(np.float32)
    a[:, :, :3] = np.clip(a[:, :, :3] * 1.15, 0, 255)
    Image.fromarray(a.astype(np.uint8), 'RGBA').save(OUT/'items'/'plate_legs.png')

    print('=== tools ===')
    for tid, (author, name, tint) in TOOLS.items():
        im = try_icon(author, name, tint, TOOL_FALLBACKS)
        save(im, 'items', f'{tid}.png')
        produced[tid] = f'items/{tid}.png'
        print(' ', tid)

    # leather_hide already; ensure cut_leather key
    produced['cut_leather'] = 'items/cut_leather.png'

    meta = {'produced': produced, 'size': SIZE}
    (Path('/workspace/offline-mmo-art/work/icons_gen') / 'produced.json').write_text(json.dumps(meta, indent=2))
    print(f'DONE {len(produced)} icons')

if __name__ == '__main__':
    main()

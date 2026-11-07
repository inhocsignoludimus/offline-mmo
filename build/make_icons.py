#!/usr/bin/env python3
"""Ícones para os itens que ainda não têm (antes apareciam como quadrado com iniciais).
Fontes: a folha do TCoM (mesmo estilo dos ícones que já existem) e a folha de ícones do Flare
(images/icons/icons.png, CC-BY-SA; fundo preto vira transparente). Variantes de material ganham tinta
(bronze, ferro negro, pele, linho...). Acrescenta linhas em engine/dev_assets/tcom/icons.webp/json.
    python3 build/make_icons.py --flare <flare-game>
Rodar de novo depois de importar os ícones do TCoM.
"""
import argparse, json, os
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TC = os.path.join(ROOT, 'engine', 'dev_assets', 'tcom')
TINT = {'bronze': '#c47a34', 'negro': '#3c4450', 'pele': '#8a6a48', 'linho': '#e6dcc4', 'vermelho': '#a83434', 'roxo': '#6a3a8a',
        'azul': '#34508e', 'verde': '#4a7a3a', 'ouro': '#d8b040', 'branco': '#f2f0e8', 'areia': '#c8a870', 'amarelo': '#d8c050',
        'aco': '#a6aeb8', 'escuro': '#3a3028', 'ambar': '#e09030', 'cinza': '#8c8c8c', 'cedro': '#a0583a'}
# item -> (fonte, chave, tinta)   T = folha do TCoM (chave do mapa), F = índice na folha do Flare
MAP = {
    'falchion': ('T', 'cimitarra_1', None), 'arming_sword': ('T', 'espada_1', None), 'sabre': ('T', 'cimitarra_0', None),
    'cutlass': ('F', 97, None), 'cleaver': ('T', 'faca_1', None), 'broadaxe': ('F', 118, None), 'war_axe': ('T', 'acha_1', None),
    'double_axe': ('F', 119, None), 'maul': ('F', 103, None), 'morning_star': ('F', 110, None), 'flail': ('T', 'maca_1', 'escuro'),
    'war_fork': ('T', 'lanca_1', None), 'halberd': ('F', 123, None), 'pike': ('T', 'lanca_0', None), 'javelin': ('T', 'lanca_0', 'pele'),
    'shortbow': ('F', 113, None), 'composite_bow': ('F', 114, None), 'arbalest': ('T', 'besta', 'escuro'), 'wand': ('F', 105, None),
    'scepter': ('F', 107, None), 'scythe': ('T', 'acha_0', 'escuro'), 'throwing_knife': ('T', 'faca_0', None), 'bardiche': ('F', 123, 'escuro'),
    'glaive': ('T', 'lanca_1', 'aco'),
    'leather_sleeves': ('F', 138, None), 'leather_leggings': ('F', 147, None), 'leather_cap': ('F', 144, None), 'padded_coif': ('T', 'capuz', 'linho'),
    'chain_sleeves': ('F', 154, None), 'scale_hauberk': ('T', 'loriga', 'bronze'), 'brigandine': ('T', 'jaque', 'escuro'), 'bascinet': ('T', 'elmoPontudo', None),
    'spangenhelm': ('T', 'elmoNasal', 'bronze'), 'leather_gorget': ('T', 'capelo', 'pele'), 'plate_gorget': ('T', 'capelo', 'aco'),
    'templar_cuirass': ('T', 'sobreveste', None), 'sergeant_cuirass': ('T', 'couracaTurca', 'escuro'), 'studded_gloves': ('T', 'luvasCouro', 'escuro'),
    'studded_leggings': ('F', 147, 'escuro'), 'studded_sleeves': ('F', 138, 'escuro'), 'fur_boots': ('F', 176, None), 'fur_cloak': ('F', 193, 'pele'),
    'scale_coif': ('T', 'capelo', 'bronze'), 'bronze_helm': ('T', 'elmoNasal', 'bronze'), 'blackiron_hauberk': ('T', 'loriga', 'negro'),
    'iron_gauntlets': ('T', 'manoplas', None), 'mail_chausses': ('F', 155, None), 'bedouin_vest': ('T', 'gibao', 'areia'),
    'lamellar_sleeves': ('F', 154, 'bronze'), 'bronze_cuirass': ('T', 'couracaTurca', 'bronze'), 'hide_tunic': ('T', 'couroCozido', None),
    'chain_mantle': ('T', 'cotaSemMangas', None),
    'templar_mantle': ('T', 'sobreveste', 'branco'), 'linen_shirt': ('F', 129, 'linho'), 'linen_pants': ('F', 131, 'linho'), 'wool_tunic': ('T', 'gambesao', 'cinza'),
    'wool_pants': ('F', 131, 'cinza'), 'smith_apron': ('T', 'jaque', 'pele'), 'bedouin_sleeves': ('F', 138, 'areia'), 'bedouin_skirt': ('F', 139, 'areia'),
    'monk_robe': ('T', 'habito', None), 'straw_hat': ('T', 'turbante', 'amarelo'), 'wizard_hat': ('F', 184, None), 'silk_robe': ('F', 185, 'roxo'),
    'desert_cloak': ('F', 193, 'areia'), 'linen_gloves': ('F', 130, 'linho'), 'sash': ('T', 'cinturao', 'vermelho'), 'linen_coif': ('T', 'capuz', 'linho'),
    'tabard': ('T', 'sobreveste', 'azul'), 'villager_dress': ('F', 139, 'vermelho'), 'scarf': ('T', 'keffiyeh', None), 'bandana': ('T', 'turbante', 'vermelho'),
    'fur_hat': ('F', 144, 'pele'),
    'tower_shield': ('T', 'amendoa_2', None), 'oval_shield': ('F', 122, None), 'pavise': ('T', 'amendoa_0', 'escuro'),
    'bronze_ring': ('F', 201, 'bronze'), 'signet_ring': ('T', 'sinete', None), 'amber_ring': ('F', 207, 'ambar'), 'coral_necklace': ('F', 213, None),
    'pearl_necklace': ('F', 215, 'branco'), 'bead_necklace': ('F', 212, None), 'iron_circlet': ('F', 202, None), 'sapphire_ring': ('F', 204, None),
    'ruby_ring': ('F', 207, None), 'torque': ('T', 'cinturao', 'ouro'),
    'dates': ('T', 'bread', 'escuro'), 'figs': ('T', 'bread', 'roxo'), 'cheese': ('T', 'bread', 'amarelo'), 'roasted_meat': ('T', 'dried_meat', None),
    'cooked_fish': ('T', 'dried_meat', 'cinza'), 'flatbread': ('T', 'bread', 'areia'), 'ale': ('F', 82, None), 'wine': ('F', 64, None), 'water_flask': ('F', 83, None),
    'bronze_ingot': ('T', 'copper_ingot', 'bronze'), 'blackiron_ore': ('T', 'iron_ore', 'negro'), 'blackiron_ingot': ('T', 'iron_ingot', 'negro'),
    'oak_logs': ('T', 'logs', None), 'cedar_logs': ('T', 'logs', 'cedro'), 'oak_boards': ('T', 'boards', None), 'cedar_boards': ('T', 'boards', 'cedro'),
    'thick_leather': ('T', 'cut_leather', 'escuro'), 'wyrm_hide': ('T', 'leather_hide', 'verde'), 'fur_bundle': ('T', 'leather_hide', 'pele'),
    'linen_bolt': ('T', 'cloth_bolt', 'linho'), 'silk_bolt': ('T', 'cloth_bolt', 'roxo'), 'wool_bolt': ('T', 'cloth_bolt', 'cinza'),
    'feather': ('T', 'arrow', 'branco'), 'arrow_shaft': ('T', 'arrow', 'pele'), 'nails': ('T', 'tinker_tools', 'cinza'), 'empty_bottle': ('F', 83, 'cinza'),
    'stone': ('T', 'iron_ore', 'cinza'),
    'lockpick': ('F', 226, None), 'saw': ('T', 'tinker_tools', None), 'tongs': ('T', 'tinker_tools', 'escuro'), 'scribe_pen': ('F', 224, None),
    'crook': ('F', 104, None), 'lute': ('F', 225, 'ambar'), 'fletching_kit': ('T', 'sewing_kit', 'pele'), 'scissors': ('T', 'sewing_kit', 'cinza'),
    'wooden_chair': ('T', 'wooden_table', 'cedro'), 'wooden_stool': ('T', 'wooden_table', 'pele'), 'candle': ('T', 'incense', 'amarelo'), 'anvil': ('F', 101, 'escuro'),
    'loom': ('T', 'wooden_table', 'linho'), 'bookshelf': ('F', 225, None), 'barrel': ('T', 'wooden_chest', 'cedro'), 'crate': ('T', 'wooden_chest', 'pele'),
    'cooking_pot': ('T', 'mortar_pestle', 'escuro'), 'small_forge': ('T', 'deed_smithy', None),
    'deed_forest_hut': ('T', 'deed_plains_cabin', 'verde'), 'deed_market_stall': ('T', 'deed_plains_cabin', 'ambar'),
}


def tint(im, hexc, k=0.7):
    rgb = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    a = im.getchannel('A')
    g = ImageOps.grayscale(im.convert('RGB'))
    col = ImageOps.colorize(g, black=tuple(c // 6 for c in rgb), white=tuple(min(255, c + 90) for c in rgb), mid=rgb).convert('RGBA')
    out = Image.blend(im.convert('RGBA'), col, k); out.putalpha(a); return out


def flare_icon(sheet, idx, T):
    c = sheet.crop(((idx % 8) * 64, (idx // 8) * 64, (idx % 8) * 64 + 64, (idx // 8) * 64 + 64)).convert('RGBA')
    px = c.load()
    for y in range(64):
        for x in range(64):
            r, g, b, al = px[x, y]
            m = max(r, g, b)
            px[x, y] = (r, g, b, min(al, max(0, (m - 10) * 7)))
    c = c.crop((3, 3, 61, 61)).resize((T - 12, T - 12), Image.LANCZOS)
    out = Image.new('RGBA', (T, T)); out.paste(c, (6, 6), c); return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--flare', required=True); a = ap.parse_args()
    meta = json.load(open(os.path.join(TC, 'icons.json')))
    sheet = Image.open(os.path.join(TC, 'icons.webp')).convert('RGBA')
    flare = Image.open(os.path.join(a.flare, 'mods', 'fantasycore', 'images', 'icons', 'icons.png')).convert('RGBA')
    T, cols, M = meta['tam'], meta['cols'], meta['mapa']
    items = json.load(open(os.path.join(ROOT, 'data', 'items', 'base.json')))['items']
    todo = [i for i in items if i.get('icon') and i['icon'] not in M and i['id'] in MAP]
    falta = [i['id'] for i in items if i.get('icon') and i['icon'] not in M and i['id'] not in MAP]
    base_n = max(c + r * cols for c, r in M.values()) + 1
    rows = (base_n + len(todo) + cols - 1) // cols
    out = Image.new('RGBA', (cols * T, rows * T)); out.paste(sheet.crop((0, 0, cols * T, min(sheet.height, rows * T))), (0, 0))
    for k, it in enumerate(todo):
        src, key, tn = MAP[it['id']]
        if src == 'T':
            c, r = M[key]; im = sheet.crop((c * T, r * T, c * T + T, r * T + T))
        else:
            im = flare_icon(flare, key, T)
        if tn: im = tint(im, TINT[tn])
        n = base_n + k; c, r = n % cols, n // cols
        out.paste(im, (c * T, r * T)); M[it['icon']] = [c, r]
    meta['rows'], meta['h'] = rows, rows * T
    out.save(os.path.join(TC, 'icons.webp'), 'WEBP', quality=90, method=6)
    json.dump(meta, open(os.path.join(TC, 'icons.json'), 'w'), separators=(',', ':'))
    print(f'{len(todo)} ícones novos, folha {out.size}; ainda sem ícone: {falta}')


if __name__ == '__main__':
    main()

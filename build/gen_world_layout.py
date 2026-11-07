#!/usr/bin/env python3
"""Gera a grelha grossa de Aelória e os JSON que a acompanham.

O contrato que a engine lê é o JSON, não este script. Rode de novo
se a pintura mudar:

    python3 build/gen_world_layout.py

Não mexe em engine/ nem na fatia autoral art/maps/mundo.txt.
Lochport e Bosque da Vila continuam com origin/size/chunks de hoje;
ganham só o carimbo de onde entram no mapa de 2048.
"""
import json
import os
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
DOCS = os.path.join(ROOT, 'docs')

W = H = 32
CELL = 64
STAMP = (768, 1408)  # célula (12, 22); Porto do Trigo / Lochport


def load(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


def save(name, obj):
    path = os.path.join(DATA, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return path


BIOME_CHAR = {
    'north': 'N', 'mountains': 'M', 'forest': 'F', 'plains': 'P',
    'swamp': 'S', 'ruins': 'R', 'outremer': 'O', 'coast': 'C',
}
CHAR_BIOME = {v: k for k, v in BIOME_CHAR.items()}

COMMON = ['logs', 'stone', 'iron_ore', 'copper_ore']
RARE = {
    'plains': ['silver_ore', 'leather_hide'],
    'forest': ['silver_ore', 'oak_logs', 'leather_hide'],
    'mountains': ['silver_ore', 'gold_ore', 'blackiron_ore', 'cedar_logs'],
    'north': ['silver_ore', 'fur_bundle', 'gold_ore'],
    'swamp': ['silver_ore', 'saltpeter', 'myrrh'],
    'outremer': ['silver_ore', 'gold_ore', 'myrrh', 'incense'],
    'ruins': ['silver_ore', 'blackiron_ore', 'gold_ore', 'quicklime'],
    'coast': ['silver_ore', 'saltpeter', 'cedar_logs'],
}
SAFE_SUPPRESS = sorted({x for xs in RARE.values() for x in xs})

POOL = {
    'plains': [
        (1, ['goblin_runner', 'goblin']),
        (4, ['goblin', 'goblin_spearman', 'skeleton']),
        (8, ['goblin_elite', 'skeleton', 'skeleton_archer']),
        (12, ['skeleton_archer', 'wyvern', 'goblin_elite']),
    ],
    'forest': [
        (1, ['goblin_runner', 'goblin']),
        (5, ['goblin_shaman', 'goblin', 'skeleton']),
        (8, ['goblin_elite', 'goblin_shaman', 'skeleton']),
        (12, ['goblin_elite', 'skeleton']),
    ],
    'mountains': [
        (2, ['goblin']),
        (8, ['goblin_elite', 'hobgoblin', 'skeleton']),
        (11, ['hobgoblin_archer', 'skeleton_knight', 'boulder']),
        (14, ['minotaur', 'wyvern_air', 'boulder']),
    ],
    'north': [
        (6, ['frozen_zombie', 'antlion_freezer']),
        (10, ['skeleton_mage_ice', 'frozen_zombie', 'wyvern_air']),
        (14, ['wyvern_air_boss', 'skeleton_mage_ice', 'antlion_freezer']),
    ],
    'swamp': [
        (3, ['zombie_rotting', 'zombie', 'antlion_hatchling']),
        (8, ['zombie', 'zombie_dark', 'skeleton']),
        (12, ['zombie_dark', 'antlion', 'wyvern_water']),
    ],
    'outremer': [
        (2, ['antlion_hatchling', 'skeleton']),
        (6, ['fire_ant', 'antlion_spitter', 'skeleton']),
        (11, ['antlion', 'antlion_armored', 'skeleton_mage_fire']),
        (15, ['wyvern_fire', 'antlion_armored']),
    ],
    'ruins': [
        (3, ['skeleton', 'zombie']),
        (8, ['skeleton_knight', 'skeleton_mage', 'zombie_ghost']),
        (12, ['necromancer_apprentice', 'skeleton_knight_boss', 'zombie_dark']),
        (16, ['necromancer', 'skeleton_mage_high_boss', 'minotaur']),
    ],
    'coast': [
        (2, ['goblin', 'skeleton']),
        (8, ['skeleton_archer', 'goblin', 'wyvern_water']),
        (12, ['wyvern_air', 'wyvern_water', 'skeleton_archer']),
    ],
}

VENDORS = [
    'ferreiro', 'alfaiate', 'mago', 'alquimista', 'acougueiro',
    'estalajadeiro', 'carpinteiro', 'arqueiro', 'banqueiro',
]
FULL_SERVICES = [
    'bank', 'healer', 'trainer', 'contract_board', 'moon_portal', 'stall_market',
]


def paint():
    g = [['~'] * W for _ in range(H)]

    def land(x, y):
        if y >= 30 or x <= 0 or x >= 31:
            return False
        if y == 0 and (x < 5 or x > 25):
            return False
        if y == 1 and (x < 3 or x > 27):
            return False
        if y >= 29 and (x < 4 or x > 28):
            return False
        if x == 1 and y >= 20:
            return False
        if x == 1 and y <= 2:
            return False
        return True

    for y in range(H):
        for x in range(W):
            if land(x, y):
                g[y][x] = 'P'

    def setb(x, y, ch):
        if 0 <= x < W and 0 <= y < H and g[y][x] != '~':
            g[y][x] = ch

    def rect(x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                setb(x, y, ch)

    rect(2, 0, 30, 5, 'N')
    rect(2, 6, 12, 16, 'F')
    rect(23, 8, 30, 17, 'R')
    rect(17, 18, 26, 25, 'S')
    rect(25, 18, 30, 28, 'O')
    rect(18, 18, 24, 24, 'S')
    rect(8, 17, 17, 25, 'P')
    for y in range(5, 17):
        cx = 14 + (y - 5) // 2
        width = 3 if 7 <= y <= 12 else 2
        for dx in range(-width, width + 1):
            setb(cx + dx, y, 'M')
    rect(16, 6, 22, 10, 'M')
    rect(23, 6, 30, 7, 'N')
    setb(13, 22, 'F')  # Bosque da Vila, dedo de floresta junto a Porto do Trigo
    for y in range(26, 30):
        for x in range(W):
            if g[y][x] in 'PF':
                g[y][x] = 'C'
    for y in range(28, 30):
        for x in range(W):
            if g[y][x] == 'O':
                g[y][x] = 'C'
    for y in range(H):
        if g[y][29] != '~' and g[y][30] == 'P':
            g[y][30] = g[y][29]
        if y <= 5 and g[y][1] == 'P':
            g[y][1] = 'N'
    return g


def monsters_for(biome, level):
    if level <= 0:
        return []
    chosen = []
    for min_lv, ids in POOL[biome]:
        if min_lv <= level:
            chosen = ids
    return list(chosen)


def resources_for(biome, zone, water, extra=None):
    if water:
        return {'common': [], 'rare': []}
    if zone in ('city', 'frontier'):
        return {'common': list(COMMON), 'rare': []}
    rare = list(RARE[biome])
    if extra:
        for item in extra:
            if item not in rare:
                rare.append(item)
    return {'common': list(COMMON), 'rare': rare}


def main():
    biomes = load('lore/biomes.json')
    city_names = {}
    for b in biomes['biomes']:
        for c in b['cities']:
            city_names[c['id']] = c['name']
    bosses_doc = {b['id']: b for b in load('names/bosses.json')['bosses']}
    grid = paint()

    # id, cell, biome char esperado, papel, capital?, raio de fronteira, serviços, vendedores
    # Serviços completos: capitais, o porto-rio inicial e o bazar de Acre.
    spec = [
        ('gelomarca', (20, 3), 'N', 'honor_hunt', True, 1, FULL_SERVICES, VENDORS),
        ('pedralta', (18, 10), 'M', 'forge_ore', True, 1, FULL_SERVICES, VENDORS),
        ('folhaverde', (7, 13), 'F', 'timber_herb', True, 1, FULL_SERVICES, VENDORS),
        ('aurelia', (14, 18), 'P', 'crown_commerce', True, 1, FULL_SERVICES, VENDORS),
        ('lodoalto', (22, 20), 'S', 'reagent_fish', True, 1, FULL_SERVICES, VENDORS),
        ('templo_selo', (27, 14), 'R', 'faith_seal', True, 1, FULL_SERVICES, VENDORS),
        ('aelia_sancta', (28, 23), 'O', 'faith_caravan', True, 1, FULL_SERVICES, VENDORS),
        ('san_marco', (5, 27), 'C', 'port_arsenal', True, 1, FULL_SERVICES, VENDORS),
        ('porto_trigo', (12, 22), 'P', 'grain_river', False, 1, FULL_SERVICES, VENDORS),
        ('acre_livre', (16, 27), 'C', 'bazaar', False, 1, FULL_SERVICES, VENDORS),
        ('vila_rena', (9, 2), 'N', 'fur_hamlet', False, 1,
         ['healer', 'stall_market'], ['estalajadeiro', 'acougueiro']),
        ('posto_invernal', (24, 4), 'N', 'winter_watch', False, 1,
         ['healer'], ['estalajadeiro', 'arqueiro']),
        ('mina_ferro', (17, 11), 'M', 'ore_village', False, 1,
         ['stall_market'], ['ferreiro', 'carpinteiro', 'estalajadeiro']),
        ('castelo_pico', (20, 7), 'M', 'pass_keep', False, 1,
         ['healer'], ['arqueiro', 'estalajadeiro', 'ferreiro']),
        ('mosteiro_vento', (15, 9), 'M', 'route_abbey', False, 1,
         ['healer', 'trainer'], ['mago', 'estalajadeiro']),
        ('mosteiro_musgo', (5, 15), 'F', 'herb_abbey', False, 1,
         ['healer', 'trainer'], ['mago', 'alquimista', 'estalajadeiro']),
        ('acampamento_machado', (10, 12), 'F', 'timber_camp', False, 1,
         [], ['carpinteiro', 'estalajadeiro']),
        ('vila_cruzada', (16, 17), 'P', 'veteran_hamlet', False, 1,
         ['healer'], ['ferreiro', 'estalajadeiro']),
        ('castelo_linden', (15, 20), 'P', 'road_keep', False, 1,
         ['healer'], ['ferreiro', 'arqueiro', 'estalajadeiro']),
        ('porto_lodo', (20, 23), 'S', 'mire_landing', False, 1,
         [], ['acougueiro', 'alquimista', 'estalajadeiro']),
        ('oasis_qasr', (27, 26), 'O', 'caravan_oasis', False, 1,
         ['stall_market', 'healer'], ['estalajadeiro', 'alfaiate', 'acougueiro', 'mago']),
        ('castelo_montgisard', (26, 21), 'O', 'desert_keep', False, 1,
         ['healer'], ['ferreiro', 'arqueiro', 'estalajadeiro']),
        ('fort_amir', (29, 20), 'O', 'sultanate_fort', False, 1,
         ['healer'], ['ferreiro', 'arqueiro', 'estalajadeiro']),
        ('acampamento_espólio', (24, 13), 'R', 'relic_camp', False, 1,
         ['stall_market'], ['mago', 'estalajadeiro']),
        ('faro_bizantino', (24, 28), 'C', 'lighthouse', False, 1,
         [], ['estalajadeiro', 'mago']),
    ]
    for sid, (x, y), ch, *_rest in spec:
        got = grid[y][x]
        if got != ch:
            raise SystemExit(f'bioma errado em {sid} ({x},{y}): queria {ch}, grade tem {got}')
        if sid not in city_names:
            raise SystemExit(f'cidade {sid} não está em biomes.json')

    settlements = []
    for sid, cell, ch, role, capital, radius, services, vendors in spec:
        settlements.append({
            'id': sid,
            'name': city_names[sid],
            'cell': list(cell),
            'biome': CHAR_BIOME[ch],
            'role': role,
            'capital': capital,
            'radius': radius,
            'services': list(services),
            'vendors': list(vendors),
            'safe': True,
        })
    by_id = {s['id']: s for s in settlements}
    occupied = {tuple(s['cell']): s['id'] for s in settlements}

    def dist(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def nearest_safe(x, y):
        best = None
        best_d = 99
        for s in settlements:
            d = dist((x, y), tuple(s['cell']))
            if d < best_d:
                best, best_d = s, d
        return best, best_d

    # Chefes. A célula preferida vale se estiver no bioma e fora do raio seguro.
    boss_specs = [
        ('rei_formiga', 'outremer', (30, 27), 16, ['antlion', 'antlion_armored', 'fire_ant'], None, ['wyrm_hide']),
        ('serpe_de_fogo', 'outremer', (30, 25), 16, ['wyvern_fire', 'antlion_armored'], None, ['wyrm_hide']),
        ('fantasma_cruzado', 'outremer', (30, 21), 12, ['skeleton_knight', 'skeleton_mage_fire'], 'crusader_ghost', []),
        ('chefe_goblin', 'plains', (10, 19), 6, ['goblin_elite', 'goblin_spearman'], None, []),
        ('matilha_cinzenta', 'plains', (18, 24), 8, ['goblin_elite', 'skeleton'], 'wolf', ['leather_hide']),
        ('aranha_da_clareira', 'forest', (3, 9), 10, ['goblin_shaman', 'goblin'], 'spider_giant', []),
        ('coracao_do_bosque', 'forest', (4, 7), 14, ['goblin_elite', 'skeleton'], 'treant', []),
        ('urso_negro', 'forest', (11, 16), 12, ['goblin_elite', 'goblin_shaman'], 'dire_bear', ['leather_hide']),
        ('senhor_do_pantano', 'swamp', (24, 24), 14, ['zombie_dark', 'antlion', 'wyvern_water'], 'bog_lurker', []),
        ('sombra_do_miasma', 'swamp', (25, 22), 12, ['zombie_dark', 'zombie'], None, []),
        ('minotauro_do_pico', 'mountains', (22, 12), 15, ['minotaur', 'hobgoblin', 'boulder'], None, []),
        ('elemental_de_pedra', 'mountains', (21, 13), 14, ['boulder', 'hobgoblin_archer'], 'rock_elemental', []),
        ('gigante_do_gelo', 'north', (25, 1), 16, ['antlion_freezer', 'skeleton_mage_ice', 'wyvern_air'], 'frost_giant', ['fur_bundle']),
        ('jarl_morto', 'north', (7, 1), 14, ['frozen_zombie', 'skeleton_mage_ice'], 'wight', []),
        ('necromante_caduco', 'ruins', (26, 10), 16, ['necromancer', 'skeleton_mage'], None, []),
        ('guardiao_da_cripta', 'ruins', (29, 11), 14, ['skeleton_knight_boss', 'skeleton_mage'], None, []),
        ('corsario_vermelho', 'coast', (9, 28), 12, ['skeleton_archer', 'goblin', 'wyvern_water'], 'sea_raider', []),
        ('caranguejo_colossal', 'coast', (27, 29), 14, ['wyvern_water', 'skeleton'], 'crab_giant', []),
    ]

    def snap_boss(bid, biome, prefer, level):
        x, y = prefer
        def ok(xx, yy):
            if not (0 <= xx < W and 0 <= yy < H):
                return False
            if CHAR_BIOME.get(grid[yy][xx]) != biome:
                return False
            if (xx, yy) in occupied:
                return False
            if any(dist((xx, yy), tuple(b['cell'])) < 2 for b in bosses):
                return False
            _s, d = nearest_safe(xx, yy)
            # Fora da faixa de fronteira (raio 1). Pode encostar no aberto.
            return d >= 2
        if ok(x, y):
            return (x, y)
        for rad in range(1, 8):
            for yy in range(y - rad, y + rad + 1):
                for xx in range(x - rad, x + rad + 1):
                    if max(abs(xx - x), abs(yy - y)) != rad:
                        continue
                    if ok(xx, yy):
                        print(f'chefe {bid} saiu de {prefer} para {(xx, yy)}')
                        return (xx, yy)
        raise SystemExit(f'sem célula para chefe {bid} perto de {prefer}')

    bosses = []
    for bid, biome, prefer, level, mons, request, extra in boss_specs:
        if bid not in bosses_doc and bid != 'wyvern_air_boss':
            if bid not in bosses_doc:
                raise SystemExit(f'chefe {bid} não está em bosses.json')
        cell = snap_boss(bid, biome, prefer, level)
        bosses.append({
            'id': bid,
            'name': bosses_doc[bid]['name'],
            'biome': biome,
            'cell': list(cell),
            'level': level,
            'monsters': mons,
            'requested_monster': request,
            'rare_extra': extra,
            'monster_in_data': bosses_doc[bid].get('monster'),
        })
        occupied[tuple(cell)] = 'boss:' + bid

    # wyvern da clareira autoral não ocupa a célula inteira.
    # Crista de ar: chefe que já é monstro, sem ficha em bosses.json.
    air_cell = snap_boss('wyvern_air_boss', 'mountains', (19, 6), 18)
    bosses.append({
        'id': 'wyvern_air_boss',
        'name': {'pt': 'Serpe da Crista', 'en': 'Ridge Wyvern'},
        'biome': 'mountains',
        'cell': list(air_cell),
        'level': 18,
        'monsters': ['wyvern_air_boss', 'wyvern_air'],
        'requested_monster': None,
        'rare_extra': ['wyrm_hide'],
        'monster_in_data': 'wyvern_air_boss',
        'named_in_bosses_json': False,
    })
    occupied[tuple(air_cell)] = 'boss:wyvern_air_boss'

    boss_at = {tuple(b['cell']): b for b in bosses}
    RESERVED = {(13, 22)}  # Bosque da Vila

    zone = [['sea' if grid[y][x] == '~' else 'open' for x in range(W)] for y in range(H)]
    owner = [[None] * W for _ in range(H)]

    for s in settlements:
        x, y = s['cell']
        zone[y][x] = 'city'
        owner[y][x] = s['id']
    for s in settlements:
        cx, cy = s['cell']
        for y in range(H):
            for x in range(W):
                if grid[y][x] == '~':
                    continue
                if (x, y) in RESERVED or (x, y) in boss_at:
                    continue
                if zone[y][x] == 'city':
                    continue
                if dist((x, y), (cx, cy)) <= s['radius'] and zone[y][x] != 'frontier':
                    zone[y][x] = 'frontier'
                    owner[y][x] = s['id']
    for b in bosses:
        x, y = b['cell']
        zone[y][x] = 'boss'
        owner[y][x] = b['id']
    zone[22][13] = 'open'
    owner[22][13] = 'bosque_da_vila'

    # Estradas (4 direções) e rios antes de promover a estrada segura.
    def step_cost(x, y):
        ch = grid[y][x]
        return {'P': 1, 'C': 1, 'F': 1.4, 'S': 2.2, 'R': 2, 'O': 1.6, 'N': 1.7, 'M': 2.6}[ch]

    def astar(a, b):
        start, goal = tuple(a), tuple(b)
        q = deque([start])
        prev = {start: None}
        cost = {start: 0}
        while q:
            x, y = q.popleft()
            if (x, y) == goal:
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < W and 0 <= yy < H) or grid[yy][xx] == '~':
                    continue
                ncost = cost[(x, y)] + step_cost(xx, yy)
                if ncost < cost.get((xx, yy), 1e9):
                    cost[(xx, yy)] = ncost
                    prev[(xx, yy)] = (x, y)
                    q.append((xx, yy))
        if goal not in prev:
            raise SystemExit(f'sem estrada {a} -> {b}')
        path = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    road_defs = [
        ('estrada_do_gelo', {'pt': 'Estrada do Gelo', 'en': 'Ice Road'},
         ['gelomarca', 'pedralta']),
        ('trilha_das_folhas', {'pt': 'Trilha das Folhas', 'en': 'Leaf Trail'},
         ['pedralta', 'folhaverde', 'aurelia']),
        ('estrada_real', {'pt': 'Estrada Real', 'en': 'Royal Road'},
         ['pedralta', 'aurelia', 'porto_trigo', 'acre_livre']),
        ('caminho_do_selo', {'pt': 'Caminho do Selo', 'en': 'Seal Road'},
         ['pedralta', 'templo_selo', 'aelia_sancta']),
        ('rota_das_caravanas', {'pt': 'Rota das Caravanas', 'en': 'Caravan Road'},
         ['lodoalto', 'aelia_sancta', 'oasis_qasr']),
        ('via_litoranea', {'pt': 'Via Litorânea', 'en': 'Coast Road'},
         ['san_marco', 'porto_trigo', 'acre_livre', 'faro_bizantino']),
        ('ramal_da_rena', {'pt': 'Ramal da Rena', 'en': 'Reindeer Spur'},
         ['gelomarca', 'vila_rena']),
        ('ramal_invernal', {'pt': 'Ramal Invernal', 'en': 'Winter Spur'},
         ['gelomarca', 'posto_invernal']),
        ('ramal_da_mina', {'pt': 'Ramal da Mina', 'en': 'Mine Spur'},
         ['pedralta', 'mina_ferro']),
        ('ramal_do_pico', {'pt': 'Ramal do Pico', 'en': 'Peak Spur'},
         ['pedralta', 'castelo_pico']),
        ('ramal_do_vento', {'pt': 'Ramal do Vento', 'en': 'Wind Spur'},
         ['pedralta', 'mosteiro_vento']),
        ('ramal_do_musgo', {'pt': 'Ramal do Musgo', 'en': 'Moss Spur'},
         ['folhaverde', 'mosteiro_musgo']),
        ('ramal_do_machado', {'pt': 'Ramal do Machado', 'en': 'Axe Spur'},
         ['folhaverde', 'acampamento_machado']),
        ('ramal_cruzado', {'pt': 'Ramal Cruzado', 'en': 'Crusader Spur'},
         ['aurelia', 'vila_cruzada']),
        ('ramal_de_linden', {'pt': 'Ramal de Linden', 'en': 'Linden Spur'},
         ['aurelia', 'castelo_linden']),
        ('ramal_do_lodo', {'pt': 'Ramal do Lodo', 'en': 'Mire Spur'},
         ['lodoalto', 'porto_lodo']),
        ('ramal_de_montgisard', {'pt': 'Ramal de Montgisard', 'en': 'Montgisard Spur'},
         ['aelia_sancta', 'castelo_montgisard']),
        ('ramal_de_amir', {'pt': 'Ramal de Amir', 'en': 'Amir Spur'},
         ['aelia_sancta', 'fort_amir']),
        ('ramal_do_espolio', {'pt': 'Ramal do Espólio', 'en': 'Spoil Spur'},
         ['templo_selo', 'acampamento_espólio']),
        ('atalho_do_brejo', {'pt': 'Atalho do Brejo', 'en': 'Bog Cut'},
         ['aurelia', 'lodoalto']),
    ]
    roads = []
    road_cells = set()
    for rid, name, stops in road_defs:
        cells = []
        for a, b in zip(stops, stops[1:]):
            path = astar(by_id[a]['cell'], by_id[b]['cell'])
            if cells and path:
                path = path[1:]
            cells.extend(path)
        roads.append({'id': rid, 'name': name, 'between': stops, 'cells': [list(c) for c in cells]})
        road_cells.update(cells)

    # Estrada entre duas zonas seguras, a até 3 células de uma cidade, vira fronteira.
    for (x, y) in road_cells:
        if grid[y][x] == '~' or zone[y][x] in ('city', 'boss'):
            continue
        if (x, y) in RESERVED:
            continue
        s, d = nearest_safe(x, y)
        if d <= 2 and zone[y][x] == 'open':
            zone[y][x] = 'frontier'
            owner[y][x] = s['id']

    rivers = [
        ('fiorde_palido', {'pt': 'Fiorde Pálido', 'en': 'Pale Fjord'}, 'fjord',
         [(20, 0), (20, 1), (20, 2), (21, 3)]),
        ('rio_da_coroa', {'pt': 'Rio da Coroa', 'en': 'Crown River'}, 'river',
         [(16, 10), (16, 11), (16, 12), (16, 13), (15, 14), (15, 15), (15, 16),
          (15, 17), (14, 18), (14, 19), (13, 20), (13, 21), (12, 22), (12, 23),
          (13, 24), (14, 25), (15, 26), (16, 27)]),
        ('braco_do_brejo', {'pt': 'Braço do Brejo', 'en': 'Bog Arm'}, 'river',
         [(14, 18), (16, 18), (18, 19), (20, 20), (22, 20), (23, 21), (24, 22)]),
        ('uede_de_qasr', {'pt': 'Uede de Qasr', 'en': 'Qasr Wadi'}, 'wadi',
         [(26, 24), (27, 25), (27, 26)]),
    ]
    river_cells = set()
    river_out = []
    for rid, name, kind, cells in rivers:
        kept = []
        for x, y in cells:
            if 0 <= x < W and 0 <= y < H and grid[y][x] != '~':
                kept.append([x, y])
                river_cells.add((x, y))
        river_out.append({'id': rid, 'name': name, 'kind': kind, 'cells': kept})

    # Casas de guilda e vagas de simulados.
    guild_home = {
        'OCV': 'aelia_sancta', 'CMG': 'castelo_montgisard', 'ASH': 'fort_amir',
        'BQ': 'oasis_qasr', 'MDA': 'acre_livre', 'RSM': 'san_marco',
        'GI': 'gelomarca', 'JG': 'gelomarca', 'CDF': 'folhaverde',
        'LN': 'acampamento_machado', 'MP': 'pedralta', 'FL': 'mina_ferro',
        'SB': 'lodoalto', 'GS': 'templo_selo', 'EL': 'acampamento_espólio',
        'FI': 'porto_trigo', 'NMB': 'aurelia',
    }
    # Caos sem casa na fronteira segura: acampam no aberto, perto do tema.
    guild_wild = {
        'CG': ('coast', (9, 28), 'open'),
        'CDO': ('ruins', (26, 10), 'dangerous'),
        'SKC': ('ruins', (28, 12), 'open'),
    }

    def frontier_cells(sid):
        out = []
        for y in range(H):
            for x in range(W):
                if zone[y][x] == 'frontier' and owner[y][x] == sid:
                    out.append((x, y))
        out.sort(key=lambda p: (0 if p in road_cells else 1, p[1], p[0]))
        return out

    sim_slots = [[0] * W for _ in range(H)]
    guild_hall = [[None] * W for _ in range(H)]
    slot_cap = {}
    for s in settlements:
        if s['capital']:
            slot_cap[s['id']] = 6
        elif s['id'] in ('porto_trigo', 'acre_livre'):
            slot_cap[s['id']] = 4
        else:
            slot_cap[s['id']] = 2

    for tag, sid in guild_home.items():
        cells = frontier_cells(sid)
        if not cells:
            raise SystemExit(f'sem fronteira para a guilda {tag} em {sid}')
        # Uma casa de guilda por fronteira; se duas guildas dividem a cidade, células diferentes.
        used = {tuple(p) for p in cells if guild_hall[p[1]][p[0]]}
        pick = next(p for p in cells if p not in used)
        guild_hall[pick[1]][pick[0]] = tag
        sim_slots[pick[1]][pick[0]] = 1

    for tag, (biome, prefer, want_zone) in guild_wild.items():
        px, py = prefer
        found = None
        for rad in range(0, 6):
            for y in range(py - rad, py + rad + 1):
                for x in range(px - rad, px + rad + 1):
                    if not (0 <= x < W and 0 <= y < H):
                        continue
                    if CHAR_BIOME.get(grid[y][x]) != biome:
                        continue
                    if zone[y][x] not in ('open', 'dangerous'):
                        continue
                    if guild_hall[y][x]:
                        continue
                    found = (x, y)
                    break
                if found:
                    break
            if found:
                break
        if not found:
            raise SystemExit(f'sem célula selvagem para guilda {tag}')
        guild_hall[found[1]][found[0]] = tag
        sim_slots[found[1]][found[0]] = 1

    for s in settlements:
        need = slot_cap[s['id']]
        have = sum(1 for x, y in frontier_cells(s['id']) if sim_slots[y][x])
        for x, y in frontier_cells(s['id']):
            if have >= need:
                break
            if sim_slots[y][x]:
                continue
            sim_slots[y][x] = 1
            have += 1

    # Aberto ao longo da estrada: 2 vagas por bioma. Perigoso: 1 por bioma.
    for kind, per in (('open', 2), ('dangerous', 1)):
        for biome in CHAR_BIOME.values():
            n = 0
            for y in range(H):
                for x in range(W):
                    if n >= per:
                        break
                    if zone[y][x] != kind or CHAR_BIOME.get(grid[y][x]) != biome:
                        continue
                    if (x, y) not in road_cells or sim_slots[y][x] or guild_hall[y][x]:
                        continue
                    sim_slots[y][x] = 1
                    n += 1

    # Nível, perigo, construção, invasão.
    BIAS = {'north': 2, 'ruins': 2, 'outremer': 2, 'swamp': 1, 'mountains': 1}
    cells = []
    for y in range(H):
        row = []
        for x in range(W):
            ch = grid[y][x]
            water = ch == '~'
            biome = 'coast' if water else CHAR_BIOME[ch]
            z = zone[y][x]
            if water:
                z = 'open'
            binfo = boss_at.get((x, y))
            if (x, y) in RESERVED:
                level, danger, build, invasion = 4, 2, 'nao', False
                mons = ['goblin', 'goblin_runner', 'goblin_spearman', 'skeleton']
                res = resources_for('forest', 'frontier', False)
            elif water:
                level, danger, build, invasion = 0, 1, 'nao', False
                mons, res = [], resources_for(biome, 'open', True)
            elif z == 'city':
                level, danger, build, invasion = 0, 1, 'proibido', False
                mons, res = [], resources_for(biome, 'city', False)
            elif z == 'frontier':
                level, danger, build, invasion = 1, 1, 'fronteira', False
                mons, res = [], resources_for(biome, 'frontier', False)
            elif z == 'boss':
                level = binfo['level']
                danger, build, invasion = 5, 'nao', False
                mons = list(binfo['monsters'])
                res = resources_for(biome, 'boss', False, binfo['rare_extra'])
            else:
                _near, dsett = nearest_safe(x, y)
                cap = min(
                    (s for s in settlements if s['capital']),
                    key=lambda s: dist((x, y), tuple(s['cell'])),
                )
                dcap = dist((x, y), tuple(cap['cell']))
                # Vila não amansa o bioma: só a porta (até 2 células) fica mansa.
                # Longe da capital, o chão é perigoso.
                if dsett <= 2:
                    z = 'open'
                    level = min(10, 4 + dsett + BIAS.get(biome, 0))
                    danger = 2
                elif dcap >= 5:
                    z = 'dangerous'
                    level = min(18, 12 + min(6, dcap - 5) + BIAS.get(biome, 0))
                    danger = 4
                else:
                    z = 'open'
                    level = min(10, 4 + dcap + BIAS.get(biome, 0))
                    danger = 2 if level <= 7 else 3
                build, invasion = 'aberta', True
                mons = monsters_for(biome, level)
                res = resources_for(biome, z, False)
                zone[y][x] = z
            cell = {
                'biome': biome,
                'zone': z,
                'level': level,
                'danger': danger,
                'build': build,
                'invasion': invasion,
                'road': (x, y) in road_cells,
                'river': (x, y) in river_cells,
                'water': water,
                'resources': res,
                'monsters': mons,
            }
            if owner[y][x] and z in ('city', 'frontier'):
                cell['settlement'] = owner[y][x]
            if binfo:
                cell['boss'] = binfo['id']
                if binfo.get('requested_monster'):
                    cell['requested_monster'] = binfo['requested_monster']
            if guild_hall[y][x]:
                cell['guild_hall'] = guild_hall[y][x]
            if sim_slots[y][x]:
                cell['sim_slots'] = sim_slots[y][x]
            if (x, y) == (12, 22):
                cell['authored'] = ['lochport']
                cell['city_id'] = 'porto_trigo'
            if (x, y) == (13, 22):
                cell['authored'] = ['bosque_da_vila']
                cell['feature'] = 'bosque_da_vila'
            if z == 'city':
                cell['city_id'] = owner[y][x]
            row.append(cell)
        cells.append(row)

    # Regiões de zones.json, uma por papel de jogo.
    def nm(pt, en):
        return {'pt': pt, 'en': en}

    def span(points):
        if not points:
            return None
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return [min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1]

    regions = []

    def add_region(rid, name, points, **extra):
        if not points:
            return
        biomes_here = sorted({CHAR_BIOME[grid[y][x]] if grid[y][x] != '~' else 'coast' for x, y in points})
        levels = [cells[y][x]['level'] for x, y in points]
        dangers = [cells[y][x]['danger'] for x, y in points]
        sample = cells[points[0][1]][points[0][0]]
        reg = {
            'id': rid,
            'name': name,
            'biomes': biomes_here,
            'zone': sample['zone'],
            'build': sample['build'],
            'danger': [min(dangers), max(dangers)] if min(dangers) != max(dangers) else min(dangers),
            'level': [min(levels), max(levels)] if min(levels) != max(levels) else min(levels),
            'invasion': sample['invasion'],
            'resources': sample['resources'],
            'cells': [list(p) for p in points],
            'cell_span': span(points),
        }
        reg.update(extra)
        regions.append(reg)

    for s in settlements:
        x, y = s['cell']
        add_region(
            'city_' + s['id'], s['name'], [(x, y)],
            settlement=s['id'], capital=s['capital'], role=s['role'],
            services=s['services'], vendors=s['vendors'],
            unlock={'kind': 'always'},
        )
        pts = frontier_cells(s['id'])
        unlock = {'kind': 'always'} if s['id'] in ('porto_trigo', 'aurelia') else {'kind': 'visit', 'city': s['id']}
        add_region(
            'frontier_' + s['id'],
            nm(f"Fronteira de {s['name']['pt']}", f"{s['name']['en']} Frontier"),
            pts, settlement=s['id'], unlock=unlock,
            sim_slots=sum(sim_slots[y][x] for x, y in pts),
        )

    for biome in ['outremer', 'plains', 'forest', 'swamp', 'mountains', 'north', 'ruins', 'coast']:
        cap = next(s for s in settlements if s['biome'] == biome and s['capital'])
        camp_monster = monsters_for(biome, 6)[:1] or monsters_for(biome, 10)[:1]
        deep_monster = monsters_for(biome, 12)[:1] or camp_monster
        combat = [
            'swordsmanship', 'mace_fighting', 'axe_fighting', 'fencing',
            'archery', 'wrestling', 'magery', 'tactics',
        ]
        open_pts = [(x, y) for y in range(H) for x in range(W)
                    if zone[y][x] == 'open' and not cells[y][x]['water']
                    and cells[y][x]['biome'] == biome and (x, y) not in RESERVED]
        dang_pts = [(x, y) for y in range(H) for x in range(W)
                    if zone[y][x] == 'dangerous' and cells[y][x]['biome'] == biome]
        add_region(
            biome + '_open',
            nm(f"Aberto — {biome}", f"Open — {biome}"),
            open_pts,
            unlock={
                'kind': 'any',
                'camp': {'id': 'camp_' + biome, 'monster': camp_monster[0], 'count': [4, 6]},
                'skill_min': 35,
                'skill_any': combat,
                'reputation': {'city': cap['id'], 'min': 15},
            },
        )
        add_region(
            biome + '_dangerous',
            nm(f"Perigoso — {biome}", f"Dangerous — {biome}"),
            dang_pts,
            unlock={
                'kind': 'any',
                'requires_region': biome + '_open',
                'camp': {'id': 'camp_' + biome + '_fundo', 'monster': deep_monster[0], 'count': [3, 5]},
                'skill_min': 50,
                'skill_any': combat,
                'reputation': {'city': cap['id'], 'min': 40},
            },
        )

    add_region(
        'bosque_da_vila',
        nm('Bosque da Vila', 'Village Woods'),
        [(13, 22)],
        feature='bosque_da_vila',
        same_as_zone='bosque_da_vila',
        unlock={'kind': 'always'},
        note={
            'pt': 'Fatia de caça já desenhada. Sem lote e sem invasão. A serpe fica na clareira, não na célula inteira.',
            'en': 'Authored hunt slice. No lot and no invasion. The wyvern sits in the clearing, not on the whole cell.',
        },
    )
    sea_pts = [(x, y) for y in range(H) for x in range(W) if cells[y][x]['water']]
    add_region(
        'mar_de_san_marco',
        nm('Mar de San Marco', 'San Marco Sea'),
        sea_pts, water=True, unlock={'kind': 'always'},
    )
    for b in bosses:
        x, y = b['cell']
        extra = {
            'boss': b['id'],
            'monsters': b['monsters'],
            'unlock': {'kind': 'always'},
        }
        if b.get('requested_monster'):
            extra['requested_monster'] = b['requested_monster']
        if b['id'] == 'guardiao_da_cripta':
            extra['dungeon_entrance'] = 'cripta_familia'
        if b['id'] == 'rei_formiga':
            extra['dungeon_entrance'] = 'formigueiro'
        add_region('boss_' + b['id'], b['name'], [(x, y)], **extra)

    # Portais da lua. Cubo entre capitais; pedras locais nas vilas que já existiam.
    cube = {
        'aurelia': ['folhaverde', 'pedralta', 'san_marco'],
        'folhaverde': ['aurelia', 'gelomarca', 'lodoalto'],
        'pedralta': ['aurelia', 'gelomarca', 'templo_selo'],
        'gelomarca': ['folhaverde', 'pedralta', 'aelia_sancta'],
        'san_marco': ['aurelia', 'lodoalto', 'templo_selo'],
        'lodoalto': ['folhaverde', 'san_marco', 'aelia_sancta'],
        'templo_selo': ['pedralta', 'san_marco', 'aelia_sancta'],
        'aelia_sancta': ['gelomarca', 'lodoalto', 'templo_selo'],
    }
    portals = []
    for cid, phases in cube.items():
        nm_ = city_names[cid]
        portals.append({
            'id': 'portal_' + cid,
            'name': nm(f"Portal de {nm_['pt']}", f"{nm_['en']} Portal"),
            'city': cid,
            'phases': phases,
            'kind': 'moon',
            'network': 'capital',
        })
    local = [
        ('portal_porto_trigo', 'porto_trigo', ['aurelia', 'san_marco', 'folhaverde']),
        ('portal_acre_livre', 'acre_livre', ['san_marco', 'aelia_sancta', 'aurelia']),
        ('portal_castelo_montgisard', 'castelo_montgisard', ['aelia_sancta', 'oasis_qasr', 'aurelia']),
        ('portal_oasis_qasr', 'oasis_qasr', ['aelia_sancta', 'castelo_montgisard', 'acre_livre']),
        ('portal_mosteiro_musgo', 'mosteiro_musgo', ['folhaverde', 'aurelia', 'acampamento_machado']),
    ]
    for pid, cid, phases in local:
        nm_ = city_names[cid]
        portals.append({
            'id': pid,
            'name': nm(f"Portal de {nm_['pt']}", f"{nm_['en']} Portal"),
            'city': cid,
            'phases': phases,
            'kind': 'moon',
            'network': 'local',
        })

    # Invasões.
    mix = {
        'plains': {
            2: [['goblin', 4], ['goblin_runner', 2]],
            3: [['goblin', 4], ['goblin_spearman', 3], ['skeleton', 2]],
            4: [['goblin_elite', 2], ['goblin_spearman', 4], ['skeleton_archer', 3], ['wyvern', 1]],
        },
        'forest': {
            2: [['goblin', 3], ['goblin_runner', 2]],
            3: [['goblin_shaman', 2], ['goblin', 4], ['skeleton', 2]],
            4: [['goblin_elite', 2], ['goblin_shaman', 2], ['skeleton', 4]],
        },
        'mountains': {
            2: [['goblin', 4], ['skeleton', 2]],
            3: [['hobgoblin', 3], ['goblin_elite', 3], ['skeleton', 2]],
            4: [['hobgoblin_archer', 3], ['minotaur', 1], ['boulder', 2], ['skeleton_knight', 2]],
        },
        'north': {
            2: [['frozen_zombie', 3], ['antlion_freezer', 2]],
            3: [['frozen_zombie', 4], ['skeleton_mage_ice', 2], ['antlion_freezer', 2]],
            4: [['wyvern_air', 1], ['skeleton_mage_ice', 2], ['frozen_zombie', 5], ['antlion_freezer', 3]],
        },
        'swamp': {
            2: [['zombie_rotting', 3], ['antlion_hatchling', 2]],
            3: [['zombie', 4], ['zombie_rotting', 2], ['skeleton', 2]],
            4: [['zombie_dark', 3], ['antlion', 2], ['wyvern_water', 1], ['zombie', 4]],
        },
        'outremer': {
            2: [['antlion_hatchling', 3], ['skeleton', 2]],
            3: [['fire_ant', 3], ['antlion_spitter', 2], ['skeleton', 2]],
            4: [['antlion', 2], ['antlion_armored', 1], ['skeleton_mage_fire', 2], ['wyvern_fire', 1]],
        },
        'ruins': {
            2: [['skeleton', 4], ['zombie', 2]],
            3: [['skeleton_knight', 2], ['skeleton_mage', 2], ['zombie_ghost', 2]],
            4: [['necromancer_apprentice', 1], ['skeleton_knight_boss', 1], ['zombie_dark', 3], ['minotaur', 1]],
        },
        'coast': {
            2: [['goblin', 3], ['skeleton', 2]],
            3: [['skeleton_archer', 3], ['goblin', 3], ['wyvern_water', 1]],
            4: [['wyvern_air', 1], ['wyvern_water', 1], ['skeleton_archer', 4], ['skeleton', 3]],
        },
    }
    announce = {
        'plains': (
            'Berrante em {place}: uma manada desce do campo.',
            'A horn at {place}: a pack is coming off the fields.',
        ),
        'forest': (
            'Tambor no {place}: o bosque solta a matilha.',
            'A drum at {place}: the wood lets the pack loose.',
        ),
        'mountains': (
            'Pedra rolando em {place}: a serra desce para o portão.',
            'Stone rolling at {place}: the ridge is coming for the gate.',
        ),
        'north': (
            'Vento cortante em {place}: o gelo caminha.',
            'A cutting wind at {place}: the ice is walking.',
        ),
        'swamp': (
            'Sino abafado em {place}: o brejo sobe pelas estacas.',
            'A muffled bell at {place}: the bog is climbing the stilts.',
        ),
        'outremer': (
            'Poeira em {place}: a areia traz a coluna.',
            'Dust at {place}: the sand is bringing a column.',
        ),
        'ruins': (
            'Sino rachado em {place}: os ossos acharam a cerca.',
            'A cracked bell at {place}: the bones have found the fence.',
        ),
        'coast': (
            'Concha em {place}: a maré sobe armada.',
            'A shell-horn at {place}: the tide is coming armed.',
        ),
    }
    every = {2: [480, 720], 3: [240, 420], 4: [150, 240]}
    warning = {2: 180, 3: 120, 4: 90}
    size = {2: [4, 7], 3: [8, 12], 4: [12, 18]}
    rewards = {
        2: {'gold': [25, 50], 'items': {'logs': [3, 6], 'stone': [3, 6]},
            'chance': [['bandage', 0.6, [1, 3]], ['heal_potion', 0.25, [1, 1]]]},
        3: {'gold': [40, 80], 'items': {'logs': [4, 8], 'stone': [4, 8], 'iron_ingot': [1, 2]},
            'chance': [['heal_potion', 0.4, [1, 1]], ['cure_potion', 0.2, [1, 1]]]},
        4: {'gold': [70, 120], 'items': {'logs': [6, 10], 'stone': [6, 10], 'iron_ingot': [1, 3]},
            'chance': [['heal_potion', 0.5, [1, 2]], ['greater_bandage', 0.3, [1, 1]]]},
    }
    hordes = []
    for biome, by_d in mix.items():
        for danger, comp in by_d.items():
            pt, en = announce[biome]
            hordes.append({
                'id': f'{biome}_d{danger}',
                'biome': biome,
                'danger': danger,
                'zone': 'open' if danger < 4 else 'dangerous',
                'every_min': every[danger],
                'clock': 'owner_online',
                'warning_s': warning[danger],
                'size': size[danger],
                'composition': comp,
                'announce': {'pt': pt, 'en': en},
                'rewards': rewards[danger],
            })

    invasions = {
        'version': 1,
        'pvp': False,
        'rules': {
            'frontier_invaded': False,
            'city_invaded': False,
            'boss_arena_invaded': False,
            'water_invaded': False,
            'requires_zone': ['open', 'dangerous'],
            'requires_build': ['aberta'],
            'requires_piece_kinds': ['wall', 'gate'],
            'min_pieces': 4,
            'clock': 'owner_online',
            'not_during_boss_event': True,
            'prefer_far_from_city': True,
            'one_active_per_base': True,
        },
        'protected': {
            'deed': True,
            'home_chest': True,
            'bank': True,
            'equipped': True,
        },
        'loss': {
            'wall_fraction_max': {'2': 0.2, '3': 0.3, '4': 0.45},
            'chests_looted_max': {'2': 0, '3': 1, '4': 1},
            'offline': {
                'loot_chests': False,
                'wall_fraction_max': 0.15,
                'repair_to_bank': True,
                'note': {
                    'pt': 'Quem está fora não perde o baú da casa. No máximo umas paredes racham, e a pedra ou o toro do conserto já está no banco.',
                    'en': 'An offline owner does not lose the home chest. A few walls crack at most, and the stone or logs to fix them are already in the bank.',
                },
            },
        },
        'targets': [
            {'id': 'gate', 'pieces': ['gate_wood', 'gate_iron'], 'priority': 1},
            {'id': 'door', 'pieces': ['door_wood', 'door_iron'], 'priority': 2},
            {'id': 'wall', 'pieces': ['wall_wood', 'wall_stone'], 'priority': 3},
            {'id': 'fence', 'pieces': ['fence_wood', 'fence_stone'], 'priority': 4},
            {'id': 'chest', 'pieces': ['wooden_chest'], 'priority': 5, 'skip_role': 'home_chest'},
        ],
        'defenses': [
            {'piece': 'fence_wood', 'tier': 1, 'exists': True, 'role': 'delay'},
            {'piece': 'wall_wood', 'tier': 1, 'exists': True, 'role': 'wall'},
            {'piece': 'fence_stone', 'tier': 2, 'exists': True, 'role': 'delay'},
            {'piece': 'wall_stone', 'tier': 2, 'exists': True, 'role': 'wall'},
            {'piece': 'gate_iron', 'tier': 3, 'exists': True, 'role': 'choke'},
            {'piece': 'door_iron', 'tier': 3, 'exists': True, 'role': 'choke'},
            {
                'piece': 'tower_stone', 'tier': 3, 'exists': False, 'role': 'range',
                'stand_in': 'Uma sala 1×1 de wall_stone com gate_iron conta como reduto até a peça existir.',
            },
        ],
        'sim': {
            'cosmetic': True,
            'repairs_self': True,
            'chat_ctx': 'raid_call',
            'note': {
                'pt': 'Casa de simulado racha e é consertada sozinha. Serve de conversa no chat, não de prejuízo.',
                'en': 'A simulated homestead cracks and repairs itself. It is chat, not a loss.',
            },
        },
        'hordes': hordes,
    }

    # Eventos novos, só com monstro que já existe. Os da floresta inicial ficam.
    events_doc = load('events.json')
    have = {e['id'] for e in events_doc['events']}
    new_events = [
        ('rei_formiga_dunas', 'rei_formiga', 'antlion', 'boss_rei_formiga', 'outremer', [50, 80], 18,
         [['antlion_hatchling', 4], ['fire_ant', 3], ['antlion_spitter', 2]],
         'O {boss} abriu as dunas!', '{boss} has opened the dunes!'),
        ('serpe_de_fogo_dunas', 'serpe_de_fogo', 'wyvern_fire', 'boss_serpe_de_fogo', 'outremer', [90, 150], 20,
         [['fire_ant', 4]],
         'A {boss} cobriu as dunas de cinza!', '{boss} has covered the dunes in ash!'),
        ('minotauro_passo', 'minotauro_do_pico', 'minotaur', 'boss_minotauro_do_pico', 'mountains', [40, 70], 18,
         [['hobgoblin', 3], ['boulder', 1]],
         'O {boss} fechou o passo!', '{boss} has closed the pass!'),
        ('necromante_cidadela', 'necromante_caduco', 'necromancer', 'boss_necromante_caduco', 'ruins', [45, 75], 18,
         [['skeleton', 4], ['skeleton_mage', 2]],
         'O {boss} acendeu a cidadela!', '{boss} has lit the citadel!'),
        ('guardiao_cripta_familiar', 'guardiao_da_cripta', 'skeleton_knight_boss', 'boss_guardiao_da_cripta', 'ruins', [35, 60], 15,
         [['skeleton', 4], ['skeleton_archer', 2]],
         'O {boss} despertou na cripta familiar!', '{boss} has woken in the family crypt!'),
        ('sombra_torre_miasma', 'sombra_do_miasma', 'zombie_dark', 'boss_sombra_do_miasma', 'swamp', [40, 70], 16,
         [['zombie', 4], ['zombie_rotting', 3]],
         'A {boss} subiu da torre!', '{boss} has risen from the tower!'),
        ('chefe_goblin_seara', 'chefe_goblin', 'goblin_elite', 'boss_chefe_goblin', 'plains', [25, 45], 12,
         [['goblin', 5], ['goblin_spearman', 2]],
         'O {boss} juntou a seara!', '{boss} has rallied the fields!'),
        ('serpe_da_crista', 'wyvern_air_boss', 'wyvern_air_boss', 'boss_wyvern_air_boss', 'mountains', [80, 140], 20,
         [['wyvern_air', 1]],
         'A {boss} pousou na crista!', '{boss} has landed on the ridge!'),
    ]
    for eid, boss, monster, table, biome, every_e, dur, adds, pt, en in new_events:
        if eid in have:
            continue
        reg = 'boss_' + (boss if boss != 'wyvern_air_boss' else 'wyvern_air_boss')
        events_doc['events'].append({
            'id': eid,
            'boss': boss,
            'monster': monster,
            'place': {'region': reg, 'biome': biome, 'poi': reg},
            'every_min': every_e,
            'duration_min': dur,
            'contest': 'guild_damage',
            'announce': {'pt': pt, 'en': en},
            'adds': adds,
            'rewards': {'table': table, 'top_damage': 3 if dur < 18 else 5},
            'notes': 'Disputa de guilda por dano. Sem alvo entre jogadores.',
        })

    # world_layout
    counts = {}
    for y in range(H):
        for x in range(W):
            counts[cells[y][x]['zone'] if not cells[y][x]['water'] else 'water'] = \
                counts.get(cells[y][x]['zone'] if not cells[y][x]['water'] else 'water', 0) + 1
    layout = {
        'version': 1,
        'map': 'mundo',
        'continent': {'id': 'aeloria', 'name': nm('Aelória', 'Aeloria')},
        'cells': [W, H],
        'cell_tiles': [CELL, CELL],
        'tile_size': [W * CELL, H * CELL],
        'origin': 'north_west',
        'y_axis': 'south',
        'tile_px': {'runtime': [96, 48], 'master': [192, 96]},
        'authored_stamp': {
            'file': 'art/maps/mundo.txt',
            'slice_size': [98, 60],
            'tile_origin': list(STAMP),
            'cell': [12, 22],
            'zones': ['lochport', 'bosque_da_vila'],
            'note': {
                'pt': 'Não regenerar esta fatia. origin/chunks em zones.json continuam locais a ela.',
                'en': 'Do not regenerate this slice. origin/chunks in zones.json stay local to it.',
            },
        },
        'dungeons': {
            'status': 'undecided',
            'rule': {
                'pt': 'O mapa de cima continua um só. Se uma masmorra existir, é exceção vertical: entra num tile e volta no mesmo tile.',
                'en': 'The overworld stays one map. If a dungeon exists later, it is a vertical exception: enter on a tile and return to that same tile.',
            },
            'entrances': [
                {'id': 'cripta_familia', 'boss': 'guardiao_da_cripta'},
                {'id': 'formigueiro', 'boss': 'rei_formiga'},
                {'id': 'mina_ferro_boca', 'settlement': 'mina_ferro'},
            ],
        },
        'resource_rules': {
            'gather_nodes_now': {'tree': ['logs'], 'rock': ['stone', 'iron_ore', 'copper_ore', 'silver_ore']},
            'safe_zones_suppress': SAFE_SUPPRESS,
            'rare_not_in_gathering_yet': [
                'gold_ore', 'blackiron_ore', 'oak_logs', 'cedar_logs', 'fur_bundle',
                'wyrm_hide', 'leather_hide', 'incense', 'myrrh', 'saltpeter', 'quicklime',
            ],
        },
        'housing': {
            'lot_limit': 1,
            'frontier_footprint': [12, 12],
            'open_footprint': [20, 20],
            'dangerous_footprint': [28, 28],
            'min_gap_tiles': {'frontier': 10, 'open': 16, 'dangerous': 14},
            'decay_warn_days': 7,
            'decay_crumble_days': 14,
            'decay_contents': 'bank',
        },
        'settlements': [{k: v for k, v in s.items() if k != 'radius'} | {'cell': s['cell']} for s in settlements],
        'bosses': [{k: v for k, v in b.items() if k != 'rare_extra'} for b in bosses],
        'roads': roads,
        'rivers': river_out,
        'rows': cells,
    }

    # zones.json — só acrescenta. A fatia 98×60 e os chunks ficam.
    zones = load('zones.json')
    world = zones['world']
    world['design_size'] = [W * CELL, H * CELL]
    world['chunk'] = [CELL, CELL]
    world['layout_cells'] = [W, H]
    world['layout'] = 'world_layout.json'
    world['authored_stamp'] = list(STAMP)
    world['continent'] = layout['continent']
    for z in zones['zones']:
        if z['id'] == 'lochport':
            z['city_id'] = 'porto_trigo'
            z['build'] = 'proibido'
            z['danger'] = 1
            z['invasion'] = False
            z['resources'] = {'common': list(COMMON), 'rare': []}
            z['services'] = list(FULL_SERVICES)
            z['vendors'] = list(VENDORS)
            z['role'] = 'grain_river'
            z['layout_cell'] = [12, 22]
            z['world_origin'] = [STAMP[0] + z['origin'][0], STAMP[1] + z['origin'][1]]
        elif z['id'] == 'bosque_da_vila':
            z['build'] = 'nao'
            z['danger'] = 2
            z['invasion'] = False
            z['resources'] = resources_for('forest', 'open', False)
            z['layout_cell'] = [13, 22]
            z['world_origin'] = [STAMP[0] + z['origin'][0], STAMP[1] + z['origin'][1]]
            for ch in z['chunks']:
                ch['build'] = 'nao'
                ch['invasion'] = False
                if ch['id'] == 'clareira_do_fundo':
                    ch['danger'] = 3
                else:
                    ch['danger'] = 2
    zones['regions'] = regions

    save('world_layout.json', layout)
    save('invasions.json', invasions)
    save('portals.json', {'version': 1, 'portals': portals})
    save('zones.json', zones)
    save('events.json', events_doc)
    write_png(layout, os.path.join(DOCS, 'world_layout.png'))

    # Resumo para o documento.
    print('COUNTS', counts)
    print('REGIONS', len(regions))
    print('SIM_SLOTS', sum(sim_slots[y][x] for y in range(H) for x in range(W)))
    print('GUILD_HALLS', sum(1 for y in range(H) for x in range(W) if guild_hall[y][x]))
    print('BOSSES')
    for b in bosses:
        print(f"  {b['id']:24} {b['cell']} {b['biome']} req={b['requested_monster']}")
    print('CITIES')
    for s in settlements:
        print(f"  {s['id']:24} {s['cell']} {s['biome']} capital={s['capital']} role={s['role']}")
    land = sum(1 for y in range(H) for x in range(W) if not cells[y][x]['water'])
    fr = counts.get('frontier', 0) + counts.get('city', 0)
    print(f'LAND {land} SAFE {fr} ({100*fr/land:.1f}%)')


def write_png(layout, path):
    from PIL import Image, ImageDraw, ImageFont
    cell_px = 26
    pad = 18
    legend_w = 430
    header = 56
    footer = 28
    mw = W * cell_px
    mh = H * cell_px
    img = Image.new('RGB', (pad + mw + 16 + legend_w + pad, header + mh + footer), (22, 24, 28))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-Regular.ttf', 13)
    font_s = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-Regular.ttf', 11)
    font_b = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf', 18)
    font_m = ImageFont.truetype('/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf', 12)
    colors = {
        'north': (186, 206, 216),
        'mountains': (122, 116, 110),
        'forest': (42, 96, 54),
        'plains': (122, 164, 70),
        'swamp': (86, 98, 54),
        'ruins': (108, 92, 112),
        'outremer': (196, 150, 92),
        'coast': (210, 190, 142),
    }
    sea = (42, 92, 122)
    ox, oy = pad, header
    rows = layout['rows']
    for y in range(H):
        for x in range(W):
            c = rows[y][x]
            col = sea if c['water'] else colors[c['biome']]
            if c['zone'] == 'frontier' and not c['water']:
                col = tuple(min(255, int(col[i] * 0.72 + 255 * 0.28)) for i in range(3))
            if c['zone'] == 'dangerous':
                col = tuple(int(col[i] * 0.72) for i in range(3))
            if c['zone'] == 'boss':
                col = tuple(min(255, int(col[i] * 0.55 + (150, 42, 36)[i] * 0.45)) for i in range(3))
            x0, y0 = ox + x * cell_px, oy + y * cell_px
            draw.rectangle([x0, y0, x0 + cell_px - 1, y0 + cell_px - 1], fill=col)
            if c['zone'] == 'city':
                m = 7
                draw.rectangle([x0 + m, y0 + m, x0 + cell_px - m, y0 + cell_px - m], outline=(240, 220, 160), width=2)
            if c.get('boss'):
                cx, cy = x0 + cell_px // 2, y0 + cell_px // 2
                draw.polygon([(cx, cy - 6), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)], fill=(220, 60, 48))
    for y in range(H):
        for x in range(W):
            c = rows[y][x]
            x0, y0 = ox + x * cell_px, oy + y * cell_px
            cx, cy = x0 + cell_px // 2, y0 + cell_px // 2
            if c['road'] and not c['water']:
                for dx, dy in ((1, 0), (0, 1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H and rows[yy][xx]['road'] and not rows[yy][xx]['water']:
                        draw.line([cx, cy, cx + dx * cell_px, cy + dy * cell_px], fill=(92, 64, 36), width=2)
            if c['river']:
                for dx, dy in ((1, 0), (0, 1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H and rows[yy][xx]['river']:
                        draw.line([cx, cy, cx + dx * cell_px, cy + dy * cell_px], fill=(64, 156, 198), width=2)
    for y in range(H):
        for x in range(W):
            c = rows[y][x]
            x0, y0 = ox + x * cell_px, oy + y * cell_px
            if c['zone'] == 'city':
                m = 7
                draw.rectangle([x0 + m, y0 + m, x0 + cell_px - m, y0 + cell_px - m], outline=(240, 220, 160), width=2)
            if c.get('boss'):
                cx, cy = x0 + cell_px // 2, y0 + cell_px // 2
                draw.polygon([(cx, cy - 6), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)], fill=(220, 60, 48))
    draw.text((pad, 14), 'Aelória — 32×32 células, 64×64 tiles', fill=(236, 232, 220), font=font_b)
    draw.text((pad, 36), 'Norte em cima. 1 célula = 64 tiles. Losango de jogo 96×48.', fill=(180, 176, 164), font=font_s)
    # Legenda
    lx = ox + mw + 16
    draw.text((lx, header), 'Biomas', fill=(236, 232, 220), font=font_m)
    labels = [
        ('north', 'Norte Gelado'), ('mountains', 'Pedra Alta'), ('forest', 'Bosque Sombrio'),
        ('plains', 'Planícies'), ('swamp', 'Miasma'), ('ruins', 'Ruínas'),
        ('outremer', 'Outremer'), ('coast', 'Costa'), 
    ]
    yy = header + 22
    for key, lab in labels:
        draw.rectangle([lx, yy, lx + 14, yy + 14], fill=colors[key])
        draw.text((lx + 20, yy - 1), lab, fill=(220, 216, 206), font=font_s)
        yy += 18
    draw.rectangle([lx, yy, lx + 14, yy + 14], fill=sea)
    draw.text((lx + 20, yy - 1), 'Mar de San Marco', fill=(220, 216, 206), font=font_s)
    yy += 26
    draw.text((lx, yy), 'Zona', fill=(236, 232, 220), font=font_m)
    yy += 20
    for lab, col in (
        ('Cidade (não constrói)', (240, 220, 160)),
        ('Fronteira clara', (210, 206, 170)),
        ('Perigoso escurecido', (70, 68, 64)),
        ('Chefe (losango)', (220, 60, 48)),
    ):
        draw.rectangle([lx, yy, lx + 14, yy + 14], fill=col)
        draw.text((lx + 20, yy - 1), lab, fill=(220, 216, 206), font=font_s)
        yy += 18
    yy += 8
    draw.text((lx, yy), 'Cidades', fill=(236, 232, 220), font=font_m)
    yy += 18
    for s in layout['settlements']:
        if not s['capital'] and s['id'] not in ('porto_trigo', 'acre_livre'):
            continue
        mark = '●' if s['capital'] else '○'
        draw.text((lx, yy), f"{mark} {s['name']['pt']}  {s['cell'][0]},{s['cell'][1]}", fill=(210, 206, 196), font=font_s)
        yy += 15
    yy += 6
    draw.text((lx, yy), 'Chefes', fill=(236, 232, 220), font=font_m)
    yy += 18
    for b in layout['bosses']:
        req = ' *' if b.get('requested_monster') else ''
        draw.text((lx, yy), f"{b['name']['pt']}{req}  {b['cell'][0]},{b['cell'][1]}", fill=(210, 206, 196), font=font_s)
        yy += 14
    draw.text((pad, header + mh + 8), 'Estrada em marrom. Rio em azul. * chefe ainda sem o monstro pedido. Fatia Lochport/Bosque na célula 12,22.', fill=(160, 156, 146), font=font_s)
    img.save(path, 'PNG')
    print('PNG', path)


if __name__ == '__main__':
    main()

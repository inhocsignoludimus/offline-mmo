#!/usr/bin/env python3
"""Confere as referências entre os arquivos de data/ (rode antes de abrir PR).

    python3 build/check_data.py

Sai com código 1 e lista o que estiver quebrado: item, magia, monstro,
tabela de loot, cor ou camada do TCoM citados que não existem.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data')


def J(p, default=None):
    p = os.path.join(D, p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


bad = []
B = J('items/base.json', {'items': []})['items']
items = {i['id'] for i in B}
if len(items) != len(B):
    bad.append('base.json: ids repetidos')
reag = {r['id'] for r in J('magic/reagents.json', {'reagents': []})['reagents']}
spells = {s['id'] for s in J('magic/spells.json', {'spells': []})['spells']}
hues = {h['id'] for h in J('hues.json', {'hues': []})['hues']}
mons = {m['id'] for m in J('monsters.json', {'monsters': []})['monsters']}
bosses = {b['id'] for b in J('names/bosses.json', {'bosses': []})['bosses']}
lt = J('loot.json', {'tables': {}}); tables = lt.get('tables', lt)
lj = os.path.join(ROOT, 'engine/dev_assets/tcom/layers.json')
layers = set(json.load(open(lj))) if os.path.exists(lj) else None
STATS = {'dmg_pct', 'dmg_flat', 'armor_pct', 'armor_flat', 'str', 'dex', 'int', 'hp', 'mana', 'stam', 'regen_hp',
         'regen_mana', 'regen_stam', 'res_fire', 'res_cold', 'res_poison', 'res_energy', 'hit_chance', 'def_chance',
         'swing_speed', 'luck', 'durability', 'skill'}

for i in B:
    if layers is not None and i.get('sprite_layer') and i['sprite_layer'] not in layers:
        bad.append(f"item {i['id']}: sprite_layer {i['sprite_layer']} não existe no TCoM importado")
for s in J('magic/spells.json', {'spells': []})['spells']:
    e = s['effect']
    if e['type'] == 'create_item' and e.get('id') not in items | reag:
        bad.append(f"magia {s['id']}: cria {e.get('id')}, que não é item")
    for r in s.get('reagents', {}):
        if r not in reag:
            bad.append(f"magia {s['id']}: reagente {r} não existe")
for m in J('monsters.json', {'monsters': []})['monsters']:
    for s in m.get('spells') or []:
        if s not in spells:
            bad.append(f"monstro {m['id']}: magia {s} não existe")
    t = (m.get('loot') or {}).get('table')
    if t and t not in tables:
        bad.append(f"monstro {m['id']}: tabela de loot {t} não existe")
    if m.get('hue') and m['hue'] not in hues:
        bad.append(f"monstro {m['id']}: cor {m['hue']} não existe")
uniques = {u['id'] for u in J('items/uniques.json', {'uniques': []})['uniques']}
for k, v in tables.items():
    for e in v:
        x = e[0]
        if x.startswith('base:') or x.startswith('raro:'):
            iid = x.split(':', 1)[1]
            if iid not in items | reag:
                bad.append(f'loot {k}: {e[0]} não é item')
        elif x.startswith('unique:'):
            uid = x.split(':', 1)[1]
            if uid not in uniques:
                bad.append(f'loot {k}: unique {uid} não existe')
        elif x not in ('gold', 'reagent') and x not in items | reag:
            bad.append(f'loot {k}: {e[0]} não é item')
A = J('items/affixes.json', {'prefix': [], 'suffix': []})
for a in A.get('prefix', []) + A.get('suffix', []):
    st = a['stat'].split(':')[0]
    if st not in STATS:
        bad.append(f"afixo {a['id']}: stat {a['stat']} desconhecido")
    if st == 'skill' and a['stat'].split(':')[1] not in {s['id'] for s in J('skills.json', {'skills': []})['skills']}:
        bad.append(f"afixo {a['id']}: skill {a['stat']} não existe")
for s in J('items/sets.json', {'sets': []})['sets']:
    for p in s['pieces']:
        if p['base'] not in items: bad.append(f"set {s['id']}: base {p['base']} não existe")
        if p.get('hue') and p['hue'] not in hues: bad.append(f"set {s['id']}: cor {p['hue']} não existe")
for u in J('items/uniques.json', {'uniques': []})['uniques']:
    if u['base'] not in items: bad.append(f"único {u['id']}: base {u['base']} não existe")
    if u.get('hue') and u['hue'] not in hues: bad.append(f"único {u['id']}: cor {u['hue']} não existe")
    if u.get('source') and u['source'] not in mons | bosses: bad.append(f"único {u['id']}: source {u['source']} não é monstro nem chefe")
for v in J('npcs/vendors.json', {'vendors': []})['vendors']:
    for s, _ in v['sells']:
        if s not in items | reag: bad.append(f"vendedor {v['id']}: vende {s}, que não é item")
    sx = v.get('sex', 'm')
    for l in v.get('look', []):
        if layers is not None and f'{sx}/{l}' not in layers: bad.append(f"vendedor {v['id']}: camada {sx}/{l} não existe")
for e in J('events.json', {'events': []})['events']:
    if e['boss'] not in bosses | mons: bad.append(f"evento {e['id']}: chefe {e['boss']} não existe")
    for a, _ in e.get('adds', []):
        if a not in mons: bad.append(f"evento {e['id']}: monstro {a} não existe")


# chat/lines.json — sem contextos de PvP
Lj = J('chat/lines.json')
if Lj:
    banned_ctx = {'pk_warning', 'kill_other'}
    for ln in Lj.get('lines', []):
        if ln.get('ctx') in banned_ctx:
            bad.append(f"linha {ln.get('id')}: ctx {ln.get('ctx')} removido (sem PvP)")
# gathering.json (coleta simples)
G = J('gathering.json')
if G:
    skills = {s['id'] for s in J('skills.json', {'skills': []})['skills']}
    for n in G.get('nodes', []):
        if n.get('skill') not in skills:
            bad.append(f"gathering node {n.get('id')}: skill {n.get('skill')} não existe")
        for y in n.get('yields', []):
            if y.get('item') not in items:
                bad.append(f"gathering node {n.get('id')}: item {y.get('item')} não existe")
        t = n.get('time_s')
        if t is not None and not (1.0 <= float(t) <= 2.0):
            bad.append(f"gathering node {n.get('id')}: time_s {t} fora de 1–2 s")
    for st in G.get('stations', []):
        if st.get('skill') and st['skill'] not in skills:
            bad.append(f"gathering station {st.get('id')}: skill {st.get('skill')} não existe")
        t = st.get('time_s')
        if t is not None and not (1.0 <= float(t) <= 2.0):
            bad.append(f"gathering station {st.get('id')}: time_s {t} fora de 1–2 s")
        for r in st.get('recipes', []):
            for bag in ('in', 'out'):
                for k in (r.get(bag) or {}):
                    if k not in items:
                        bad.append(f"gathering recipe {r.get('id')}: {bag} {k} não é item")
# building.json (peças do modo construção)
Bld = J('building.json')
if Bld:
    BOARD_IDS = {'boards', 'oak_boards', 'cedar_boards'}
    KINDS = {'floor', 'wall', 'door', 'window', 'fence', 'gate', 'roof'}
    for p in Bld.get('pieces', []):
        if p.get('kind') not in KINDS:
            bad.append(f"building {p.get('id')}: kind {p.get('kind')} inválido")
        cost = p.get('cost') or {}
        if len(cost) != 1:
            bad.append(f"building {p.get('id')}: cost deve ter exatamente 1 recurso (log OU ingot/stone)")
        for k in cost:
            if k in BOARD_IDS:
                bad.append(f"building {p.get('id')}: não pode custar tábua ({k})")
            if k not in items:
                bad.append(f"building {p.get('id')}: cost {k} não é item")
# abilities.json (habilidades físicas estilo D2)
Ab = J('abilities.json')
if Ab:
    skills = {s['id'] for s in J('skills.json', {'skills': []})['skills']}
    EFFECT_TYPES = {s['effect']['type'] for s in J('magic/spells.json', {'spells': []})['spells']}
    WEAPONS = {'sword', 'bow', 'mace', 'spear', 'axe'}
    for a in Ab.get('abilities', []):
        if a.get('weapon') not in WEAPONS:
            bad.append(f"ability {a.get('id')}: weapon {a.get('weapon')} inválida")
        if a.get('skill') not in skills:
            bad.append(f"ability {a.get('id')}: skill {a.get('skill')} não existe")
        e = a.get('effect') or {}
        if e.get('type') not in EFFECT_TYPES:
            bad.append(f"ability {a.get('id')}: effect.type {e.get('type')} não é tipo de magia")
        b = e.get('base')
        if not (isinstance(b, list) and len(b) == 2):
            bad.append(f"ability {a.get('id')}: effect.base deve ser [min,max]")
# zones.json
Z = J('zones.json')
if Z:
    mons_ids = {m['id'] for m in J('monsters.json', {'monsters': []})['monsters']}
    for z in Z.get('zones', []):
        for ch in z.get('chunks', []) or []:
            if ch.get('boss') and ch['boss'] not in mons_ids | {b['id'] for b in J('names/bosses.json', {'bosses': []})['bosses']}:
                bad.append(f"zone {z.get('id')} chunk {ch.get('id')}: boss {ch.get('boss')} não existe")
            for s in ch.get('spawns', []) or []:
                if s.get('monster') not in mons_ids:
                    bad.append(f"zone {z.get('id')} chunk {ch.get('id')}: monstro {s.get('monster')} não existe")
# events.json / portals.json — sem alvos PvP
Ev = J('events.json')
if Ev:
    for e in Ev.get('events', []):
        # já checado boss/adds abaixo no bloco legado; reforço: sem campos de PvP
        for k in ('target_player', 'pk', 'pvp', 'kill_player'):
            if k in e:
                bad.append(f"evento {e.get('id')}: campo PvP {k} proibido")
Po = J('portals.json')
if Po:
    for p in Po.get('portals', []):
        if p.get('pvp') is True:
            bad.append(f"portal {p.get('id')}: pvp não permitido")


# boards obsoletos: fora de loot
for k, v in tables.items():
    for e in v:
        if 'board' in e[0]:
            bad.append(f'loot {k}: {e[0]} é tábua obsoleta')

Po = J('portals.json')
if Po:
    for p in Po.get('portals', []):
        if p.get('kind') == 'road':
            bad.append(f"portal {p.get('id')}: kind road removido (mapa único)")
        if p.get('pvp') is True:
            bad.append(f"portal {p.get('id')}: pvp não permitido")

Z = J('zones.json')
if Z:
    mons_ids = {m['id'] for m in J('monsters.json', {'monsters': []})['monsters']}
    boss_ids = {b['id'] for b in J('names/bosses.json', {'bosses': []})['bosses']}
    wmap = (Z.get('world') or {}).get('map')
    for z in Z.get('zones', []):
        if wmap and z.get('map') and z['map'] != wmap:
            bad.append(f"zone {z.get('id')}: map {z.get('map')} != world.map {wmap}")
        if z.get('connects'):
            bad.append(f"zone {z.get('id')}: connects removido (mapa contínuo, sem exits)")
        for ch in z.get('chunks', []) or []:
            if ch.get('boss') and ch['boss'] not in mons_ids | boss_ids:
                bad.append(f"zone {z.get('id')} chunk {ch.get('id')}: boss {ch.get('boss')} não existe")
            for s in ch.get('spawns', []) or []:
                if s.get('monster') not in mons_ids:
                    bad.append(f"zone {z.get('id')} chunk {ch.get('id')}: monstro {s.get('monster')} não existe")

Ev = J('events.json')
if Ev:
    for e in Ev.get('events', []):
        for k in ('target_player', 'pk', 'pvp', 'kill_player'):
            if k in e:
                bad.append(f"evento {e.get('id')}: campo PvP {k} proibido")
        rt = (e.get('rewards') or {}).get('table')
        if rt and rt not in tables:
            bad.append(f"evento {e.get('id')}: tabela de loot {rt} não existe")

for s in J('magic/spells.json', {'spells': []})['spells']:
    if 'words' in s:
        bad.append(f"magia {s['id']}: campo words removido (sem palavras de poder)")

# --- mundo contínuo: grelha, regiões, invasões (PvE) ---
BIOMES = {b['id'] for b in J('lore/biomes.json', {'biomes': []})['biomes']}
CITIES = {}
for b in J('lore/biomes.json', {'biomes': []})['biomes']:
    for c in b.get('cities', []):
        CITIES[c['id']] = b['id']
GUILD_TAGS = {g['tag'] for g in J('names/guilds.json', {'guilds': []})['guilds']}
SKILLS = {s['id'] for s in J('skills.json', {'skills': []})['skills']}
PIECES = {p['id'] for p in J('building.json', {'pieces': []}).get('pieces', [])}
REAG = reag
ZONES_OK = {'city', 'frontier', 'open', 'dangerous', 'boss'}
BUILD_OK = {'proibido', 'fronteira', 'aberta', 'nao'}
SERVICES_OK = {'bank', 'healer', 'trainer', 'contract_board', 'moon_portal', 'stall_market'}
BANNED = ('britain', 'magincia', 'yew', 'minoc', 'trinsic', 'moonglow', 'trammel', 'felucca', 'ilshenar')


def banned_in(label, obj):
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for word in BANNED:
        if word in blob:
            bad.append(f'{label}: nome proibido "{word}"')


WL = J('world_layout.json')
if WL:
    banned_in('world_layout', WL)
    if WL.get('cells') != [32, 32] or WL.get('cell_tiles') != [64, 64]:
        bad.append(f"world_layout: cells/cell_tiles {WL.get('cells')} {WL.get('cell_tiles')}")
    if WL.get('tile_size') != [2048, 2048]:
        bad.append(f"world_layout: tile_size {WL.get('tile_size')}")
    rows = WL.get('rows') or []
    if len(rows) != 32 or any(len(r) != 32 for r in rows):
        bad.append('world_layout: a grade não é 32×32')
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            where = f'célula {x},{y}'
            if c.get('biome') not in BIOMES:
                bad.append(f'world_layout {where}: bioma {c.get("biome")}')
            if c.get('zone') not in ZONES_OK:
                bad.append(f'world_layout {where}: zone {c.get("zone")}')
            if c.get('build') not in BUILD_OK:
                bad.append(f'world_layout {where}: build {c.get("build")}')
            dng = c.get('danger')
            if not isinstance(dng, int) or not 1 <= dng <= 5:
                bad.append(f'world_layout {where}: danger {dng}')
            for m in c.get('monsters') or []:
                if m not in mons:
                    bad.append(f'world_layout {where}: monstro {m} não existe')
            if c.get('boss') and c['boss'] not in bosses | mons:
                bad.append(f'world_layout {where}: chefe {c.get("boss")} não existe')
            if c.get('requested_monster') and c['requested_monster'] in mons:
                bad.append(f'world_layout {where}: {c["requested_monster"]} já existe, não é pedido')
            sid = c.get('city_id') or (c.get('settlement') if c.get('zone') == 'city' else None)
            if c.get('zone') == 'city' and c.get('city_id') not in CITIES:
                bad.append(f'world_layout {where}: city_id {c.get("city_id")}')
            if c.get('guild_hall') and c['guild_hall'] not in GUILD_TAGS:
                bad.append(f'world_layout {where}: guild_hall {c.get("guild_hall")}')
            for bucket in ('common', 'rare'):
                for it in (c.get('resources') or {}).get(bucket) or []:
                    if it not in items | REAG:
                        bad.append(f'world_layout {where}: recurso {it}')
            rare = (c.get('resources') or {}).get('rare') or []
            safe = c.get('zone') in ('city', 'frontier') or c.get('feature') == 'bosque_da_vila'
            if safe and rare:
                bad.append(f'world_layout {where}: recurso raro em zona segura')
            if c.get('water') or c.get('zone') in ('city', 'frontier', 'boss'):
                if c.get('invasion'):
                    bad.append(f'world_layout {where}: invasão em zona que não se invade')
            if c.get('zone') == 'city' and c.get('build') != 'proibido':
                bad.append(f'world_layout {where}: cidade tem de ser build proibido')
            if c.get('zone') == 'frontier' and c.get('build') != 'fronteira':
                bad.append(f'world_layout {where}: fronteira com build {c.get("build")}')
            if c.get('zone') == 'boss' and c.get('build') != 'nao':
                bad.append(f'world_layout {where}: arena de chefe não pode construir')
            if c.get('water') and c.get('build') != 'nao':
                bad.append(f'world_layout {where}: água não constrói')
            if not isinstance(c.get('road'), bool) or not isinstance(c.get('river'), bool):
                bad.append(f'world_layout {where}: road/river precisam ser bool')

if Z:
    banned_in('zones', Z)
    w = Z.get('world') or {}
    if w.get('map') != 'mundo' or w.get('size') != [98, 60] or w.get('continuous') is not True:
        bad.append(f"zones.world fatia autoral mudou: {w.get('map')} {w.get('size')} continuous={w.get('continuous')}")
    if w.get('design_size') != [2048, 2048]:
        bad.append(f"zones.world design_size {w.get('design_size')}")
    byz = {zz['id']: zz for zz in Z.get('zones', [])}
    lo = byz.get('lochport') or {}
    bo = byz.get('bosque_da_vila') or {}
    if lo.get('origin') != [0, 0] or lo.get('size') != [50, 60]:
        bad.append('lochport: origin/size da fatia autoral mudou')
    if lo.get('build') != 'proibido' or lo.get('invasion') is not False:
        bad.append('lochport: cidade sem build proibido ou com invasão')
    if bo.get('origin') != [50, 12] or bo.get('size') != [48, 36]:
        bad.append('bosque_da_vila: origin/size da fatia autoral mudou')
    expect_chunks = {
        'entrada': [50, 22, 14, 16],
        'cripta': [66, 16, 14, 12],
        'clareira_do_fundo': [84, 22, 12, 16],
    }
    got_chunks = {c.get('id'): c.get('rect') for c in bo.get('chunks') or []}
    if got_chunks != expect_chunks:
        bad.append(f'bosque_da_vila: chunks mudaram {got_chunks}')
    if bo.get('build') != 'nao' or bo.get('invasion') is not False:
        bad.append('bosque_da_vila: caça autoral não é lote e não é invadida')
    regs = Z.get('regions') or []
    if not regs:
        bad.append('zones: falta regions')
    seen = {}
    rids = set()
    for r in regs:
        rid = r.get('id')
        if rid in rids:
            bad.append(f'região {rid} repetida')
        rids.add(rid)
        if r.get('build') not in BUILD_OK:
            bad.append(f'região {rid}: build {r.get("build")}')
        inv = r.get('invasion')
        if not isinstance(inv, bool):
            bad.append(f'região {rid}: invasion não é bool')
        if r.get('zone') in ('city', 'frontier') and inv:
            bad.append(f'região {rid}: invasão em zona segura')
        for v in r.get('vendors') or []:
            if v not in {vv['id'] for vv in J('npcs/vendors.json', {'vendors': []})['vendors']}:
                bad.append(f'região {rid}: vendedor {v}')
        for s in r.get('services') or []:
            if s not in SERVICES_OK:
                bad.append(f'região {rid}: serviço {s}')
        u = r.get('unlock') or {}
        for sk in u.get('skill_any') or []:
            if sk not in SKILLS:
                bad.append(f'região {rid}: skill {sk}')
        camp = (u.get('camp') or {}).get('monster')
        if camp and camp not in mons:
            bad.append(f'região {rid}: acampamento {camp}')
        rep = (u.get('reputation') or {}).get('city')
        if rep and rep not in CITIES:
            bad.append(f'região {rid}: reputação em {rep}')
        if u.get('kind') == 'visit' and u.get('city') not in CITIES:
            bad.append(f'região {rid}: visit {u.get("city")}')
        if u.get('requires_region') and u['requires_region'] not in {x.get('id') for x in regs}:
            bad.append(f'região {rid}: requires_region {u.get("requires_region")}')
        for it in (r.get('resources') or {}).get('common', []) + (r.get('resources') or {}).get('rare', []):
            if it not in items | REAG:
                bad.append(f'região {rid}: recurso {it}')
        if r.get('zone') in ('city', 'frontier') and (r.get('resources') or {}).get('rare'):
            bad.append(f'região {rid}: raro em zona segura')
        for xy in r.get('cells') or []:
            if not (isinstance(xy, list) and len(xy) == 2):
                bad.append(f'região {rid}: célula {xy}')
                continue
            x, y = xy
            seen.setdefault((x, y), []).append(rid)
            if WL and 0 <= x < 32 and 0 <= y < 32:
                cell = WL['rows'][y][x]
                if cell.get('biome') not in (r.get('biomes') or []):
                    bad.append(f'região {rid}: bioma da célula {x},{y} não bate')
                if cell.get('build') != r.get('build'):
                    bad.append(f'região {rid}: build da célula {x},{y} não bate')
                if cell.get('invasion') != r.get('invasion'):
                    bad.append(f'região {rid}: invasion da célula {x},{y} não bate')
                if not cell.get('water') and cell.get('zone') != r.get('zone'):
                    bad.append(f'região {rid}: zone da célula {x},{y} não bate')
    if WL and len(seen) != 32 * 32:
        bad.append(f'zones.regions não cobrem a grade ({len(seen)} células)')
    for xy, ids_ in seen.items():
        if len(ids_) != 1:
            bad.append(f'célula {xy} em mais de uma região: {ids_}')

IV = J('invasions.json')
if IV:
    banned_in('invasions', IV)
    if IV.get('pvp') is not False:
        bad.append('invasions: pvp tem de ser false')
    if IV.get('rules', {}).get('frontier_invaded') is not False:
        bad.append('invasions: fronteira não pode ser invadida')
    for h in IV.get('hordes') or []:
        if h.get('biome') not in BIOMES:
            bad.append(f"horda {h.get('id')}: bioma")
        if h.get('danger') not in (2, 3, 4):
            bad.append(f"horda {h.get('id')}: danger {h.get('danger')}")
        if h.get('zone') not in ('open', 'dangerous'):
            bad.append(f"horda {h.get('id')}: zone {h.get('zone')}")
        if h.get('clock') != 'owner_online':
            bad.append(f"horda {h.get('id')}: relógio tem de ser owner_online")
        for m, _n in h.get('composition') or []:
            if m not in mons:
                bad.append(f"horda {h.get('id')}: monstro {m}")
        rew = h.get('rewards') or {}
        for it in (rew.get('items') or {}):
            if it not in items:
                bad.append(f"horda {h.get('id')}: recompensa {it}")
        for ch in rew.get('chance') or []:
            if ch[0] not in items:
                bad.append(f"horda {h.get('id')}: chance {ch[0]}")
    for dfn in IV.get('defenses') or []:
        if dfn.get('exists') and dfn.get('piece') not in PIECES:
            bad.append(f"invasions defesa {dfn.get('piece')} marcada como existente e não está em building.json")
    for t in IV.get('targets') or []:
        for p in t.get('pieces') or []:
            if p not in PIECES and p not in items:
                bad.append(f"invasions alvo {t.get('id')}: peça {p}")

if Po:
    banned_in('portals', Po)
    for p in Po.get('portals', []):
        if p.get('kind') != 'moon':
            bad.append(f"portal {p.get('id')}: kind {p.get('kind')} (só moon)")
        if p.get('city') not in CITIES:
            bad.append(f"portal {p.get('id')}: cidade {p.get('city')}")
        phases = p.get('phases') or []
        if len(phases) != 3:
            bad.append(f"portal {p.get('id')}: fases {phases}")
        for dest in phases:
            if dest not in CITIES:
                bad.append(f"portal {p.get('id')}: fase {dest} não é cidade")

CT = J('contracts.json')
if CT:
    banned_in('contracts', CT)
    if CT.get('pvp') is not False:
        bad.append('contracts: pvp tem de ser false')
    board_cities = set()
    if Z:
        for r in Z.get('regions') or []:
            if 'contract_board' in (r.get('services') or []):
                board_cities.add(r.get('settlement'))
    seen_orders = set()
    for o in CT.get('orders') or []:
        if o.get('id') in seen_orders:
            bad.append(f"contrato {o.get('id')} repetido")
        seen_orders.add(o.get('id'))
        if o.get('city') not in CITIES:
            bad.append(f"contrato {o.get('id')}: cidade {o.get('city')}")
        elif board_cities and o.get('city') not in board_cities:
            bad.append(f"contrato {o.get('id')}: {o.get('city')} não tem contract_board")
        ask = o.get('ask') or {}
        if len(ask) != 1:
            bad.append(f"contrato {o.get('id')}: um pedido casual pede um item só")
        for it, n in ask.items():
            if it not in items | REAG:
                bad.append(f"contrato {o.get('id')}: item {it}")
            if not isinstance(n, int) or n < 1 or n > 30:
                bad.append(f"contrato {o.get('id')}: quantidade {n} fora do casual (1–30)")
        if not (isinstance(o.get('gold'), list) and len(o['gold']) == 2):
            bad.append(f"contrato {o.get('id')}: gold [min,max]")
        if not isinstance(o.get('reputation'), int) or not 1 <= o['reputation'] <= 3:
            bad.append(f"contrato {o.get('id')}: reputation fora de 1–3")
    stall = CT.get('stall') or {}
    if stall.get('item') and stall['item'] not in items:
        bad.append(f"contracts stall: {stall.get('item')} não é item")
    if stall.get('counts_as_lot') is not False:
        bad.append('contracts stall: a banca não gasta o lote da base')

if Ev:
    region_ids = {r.get('id') for r in (Z or {}).get('regions') or []}
    zone_ids = {zz.get('id') for zz in (Z or {}).get('zones') or []}
    for e in Ev.get('events', []):
        place = e.get('place') or {}
        if place.get('region') and place['region'] not in region_ids:
            bad.append(f"evento {e.get('id')}: região {place.get('region')}")
        if place.get('zone') and place['zone'] not in zone_ids:
            bad.append(f"evento {e.get('id')}: zone {place.get('zone')}")
        if not place.get('region') and not place.get('zone'):
            bad.append(f"evento {e.get('id')}: sem zone nem region")

print(f'{len(items)} itens, {len(spells)} magias, {len(mons)} monstros, {len(tables)} tabelas, {len(hues)} cores')
if bad:
    print('\nPROBLEMAS:'); [print(' -', b) for b in bad]; sys.exit(1)
print('OK')

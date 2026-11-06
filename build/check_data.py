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
for k, v in tables.items():
    for e in v:
        x = e[0]
        if x.startswith('base:'):
            x = x[5:]
        if x not in ('gold', 'reagent') and x not in items | reag:
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

print(f'{len(items)} itens, {len(spells)} magias, {len(mons)} monstros, {len(tables)} tabelas, {len(hues)} cores')
if bad:
    print('\nPROBLEMAS:'); [print(' -', b) for b in bad]; sys.exit(1)
print('OK')

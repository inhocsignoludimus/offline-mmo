# DATA_SCHEMA — dados de texto (Ludimus → engine)

Todos os arquivos ficam em `data/`, em **JSON UTF-8**, e cada um é um objeto com `"version": 1` no topo. IDs em `snake_case` e únicos dentro do arquivo. Textos que aparecem para o jogador vêm sempre em **pt e en**: `{"pt": "...", "en": "..."}`.

Variáveis aceitas dentro dos textos (a engine troca na hora): `{player}` (você), `{name}` (quem fala), `{target}` (outro jogador), `{guild}`, `{tag}`, `{item}`, `{place}`, `{boss}`, `{price}`, `{skill}`, `{n}`.

---

## data/chat/personalities.json
```json
{ "version": 1,
  "personalities": [
    { "id": "novato",      "desc": "pergunta tudo, erra muito, agradece",        "typo": 0.15, "caps": 0.05, "emoji": 0.2 },
    { "id": "farmador",    "desc": "focado em xp/loot, fala pouco",               "typo": 0.05, "caps": 0.0,  "emoji": 0.05 },
    { "id": "pvper",       "desc": "provoca, desafia, se gaba no PvE/boss",         "typo": 0.08, "caps": 0.3,  "emoji": 0.1 },
    { "id": "comerciante", "desc": "WTS/WTB, negocia, anuncia preço",              "typo": 0.03, "caps": 0.2,  "emoji": 0.0 },
    { "id": "roleplayer",  "desc": "fala como personagem medieval, nunca gíria",   "typo": 0.0,  "caps": 0.0,  "emoji": 0.0 },
    { "id": "troll",       "desc": "zoa, reclama do servidor, spam leve",          "typo": 0.2,  "caps": 0.4,  "emoji": 0.3 }
  ] }
```
`typo`, `caps` e `emoji` são probabilidades de 0 a 1. A engine aplica erros de digitação, CAIXA ALTA e emotes de texto (`:)`, `kkk`, `xD`) por cima das frases.

## data/chat/lines.json
```json
{ "version": 1,
  "lines": [
    { "id": "nov_greet_01", "p": ["novato"], "ctx": "greet", "ch": "local",
      "text": { "pt": "oi gente alguem sabe onde fica o banco de {place}?", "en": "hi guys anyone know where the bank in {place} is?" } },
    { "id": "com_wts_01", "p": ["comerciante"], "ctx": "trade_sell", "ch": "global",
      "text": { "pt": "WTS {item} {price}gp pm", "en": "WTS {item} {price}gp pm" } }
  ] }
```
* `p`: lista de personalidades que podem usar a frase.
* `ch`: `global`, `local`, `guild`, `whisper` ou `party`.
* `ctx` (contextos que a engine dispara): `greet`, `bye`, `idle`, `lfg` (procura grupo), `trade`, `trade_sell`, `trade_buy`, `trade_haggle`, `help_ask`, `help_give`, `thanks`, `brag`, `insult`, `complain_server`, `death_self`, `hunt` (convite/rota de caça PvE), `boss_spawn` (chefe/evento apareceu), `loot_drop` (loot comum no chão), `loot_rare`, `guild_recruit`, `guild_war_declare`, `guild_war_taunt`, `raid_call`, `raid_win`, `raid_wipe`, `reply_friend` (quem gosta de você responde), `reply_enemy` (quem te odeia responde), `reply_neutral`. **Sem PvP:** `pk_warning` e `kill_other` foram removidos; guerra de guilda = disputa por chefe/evento.
* Meta: frases curtas, como num chat de MMO (até cerca de 80 caracteres), com cobertura de todos os `ctx` ativos.

## data/names/players.json
```json
{ "version": 1,
  "players": [
    { "name": "xXCruzadoXx", "style": "gamer", "sex": "m" },
    { "name": "Lirael",      "style": "fantasia", "sex": "f" },
    { "name": "Balduino IV", "style": "rp_historico", "sex": "m" }
  ] }
```
`style`: `gamer`, `fantasia`, `rp_historico`, `br_zoeira`, `simples` ou `numero` (ex.: `Pedro1987`). Nomes de até 16 caracteres.

## data/names/guilds.json
```json
{ "version": 1,
  "guilds": [
    { "name": "Ordem da Cruz Vermelha", "tag": "OCV", "motto": {"pt": "...", "en": "..."},
      "style": "rp", "align": "ordem", "colors": ["#b8302a", "#e8e0d0"] }
  ] }
```
`tag` com 2 a 4 letras. `align`: `ordem`, `neutro` ou `caos` (o caos tende a disputa agressiva de chefes/eventos).

## data/items/base.json
```json
{ "version": 1,
  "items": [
    { "id": "longsword", "name": {"pt": "Espada Longa", "en": "Longsword"}, "type": "weapon", "slot": "hand1",
      "skill": "swordsmanship", "dmg": [8, 14], "speed": 2.5, "weight": 6, "value": 120, "material": "iron",
      "icon": "longsword", "sprite_layer": "m/longsword", "desc": {"pt": "...", "en": "..."} },
    { "id": "lorigao", "name": {"pt": "Lorigão", "en": "Hauberk"}, "type": "armor", "slot": "torso",
      "armor": 18, "weight": 15, "value": 300, "material": "iron", "sprite_layer": "m/lorigao" }
  ] }
```
* `type`: `weapon`, `armor`, `shield`, `clothing`, `jewelry`, `consumable`, `reagent`, `resource`, `tool`, `furniture`, `deed` ou `misc`.
* `slot`: `head`, `neck`, `torso`, `arms`, `hands`, `legs`, `feet`, `cloak`, `hand1`, `hand2`, `ring` ou `none`.
* `sprite_layer`: o nome da camada do TCoM que veste o item (veja a lista de camadas em `CAMADAS_ANIM`, no `jogo.js` do TCoM). Deixe `null` se ainda não existir a camada.
* `icon`: o nome do ícone. Se ele não existir, a engine usa um genérico e registra o que falta.
* `obsolete: true` — item mantido por compatibilidade (ex.: `boards`), fora de loot/receitas/construção.

## data/items/affixes.json
```json
{ "version": 1,
  "prefix": [ { "id": "cruel", "name": {"pt": "Cruel", "en": "Cruel"}, "applies": ["weapon"], "stat": "dmg_pct", "range": [10, 25], "tier": 2 } ],
  "suffix": [ { "id": "do_urso", "name": {"pt": "do Urso", "en": "of the Bear"}, "applies": ["weapon", "armor"], "stat": "str", "range": [3, 8], "tier": 2 } ] }
```
`stat`: `dmg_pct`, `dmg_flat`, `armor_pct`, `armor_flat`, `str`, `dex`, `int`, `hp`, `mana`, `stam`, `regen_hp`, `regen_mana`, `res_fire`, `res_cold`, `res_poison`, `regen_stam`, `res_energy`, `hit_chance`, `def_chance`, `swing_speed`, `luck`, `durability` ou `skill:<id>` (ex.: `skill:magery`). Os níveis (`tier`) vão de 1 a 5.

## data/magic/spells.json e data/magic/reagents.json
```json
{ "version": 1,
  "spells": [
    { "id": "mind_blast", "name": {"pt": "Rajada Mental", "en": "Mind Blast"}, "circle": 5, "mana": 14,
      "reagents": {"black_pearl": 1, "mandrake_root": 1, "nightshade": 1, "sulfurous_ash": 1},
      "target": "mobile", "effect": {"type": "damage", "element": "cold", "base": [10, 20], "scales": ["magery", "int"]},
      "icon": "mind_blast", "desc": {"pt": "...", "en": "..."} } ] }
```
`target`: `self`, `mobile`, `ground`, `item` ou `none`. `effect.type`: `damage`, `heal`, `buff`, `debuff`, `summon`, `teleport`, `field`, `reveal` ou `create_item`. Os reagentes ficam em `reagents.json`, no mesmo formato de `items` (com `type: "reagent"`). **Os nomes de magias devem ser nossos**, e não copiados do Ultima Online. Campo `words` removido (sem palavras de poder).

## data/lore/biomes.json (+ um `.md` por bioma, com o texto longo)
```json
{ "version": 1,
  "biomes": [
    { "id": "outremer", "name": {"pt": "Outremer", "en": "Outremer"}, "climate": "deserto",
      "factions": ["reino_de_jerusalem", "beduinos"], "monsters": ["antlion", "fire_ant", "jackal", "hyena", "wyvern_fire"],
      "cities": [ { "id": "jerusalem", "name": {"pt": "Jerusalém", "en": "Jerusalem"}, "type": "capital", "desc": {"pt": "...", "en": "..."} } ],
      "summary": {"pt": "...", "en": "..."} } ] }
```
`type` da cidade: `capital`, `cidade`, `vila`, `castelo`, `porto`, `mosteiro`, `acampamento` ou `ruina`. Os monstros usam os IDs dos inimigos do Flare (`antlion`, `goblin`, `skeleton`, `zombie`, `minotaur`, `wyvern_*`...) ou IDs novos, avisando qual modelo falta.

## art/buildings/<bioma>/<id>/house.json
```json
{ "version": 2, "id": "plains_cabin_01", "size": [5, 4],
  "anchor": [384, 512],
  "layers": { "back": "back.png", "front": "front.png", "front_low": "front_low.png",
              "roof": "roof.png", "door_closed": "door_closed.png", "door_open": "door_open.png" },
  "walls": [[0,0],[1,0],[2,0],[3,0],[4,0],[0,1],[4,1],[0,2],[4,2],[0,3],[1,3],[3,3],[4,3]],
  "doors": [[2,3]],
  "props": [[1,1,"bed_r0"],[3,1,"chest_r2"]],
  "interior": [[1,1],[3,2]] }
```
* `size`: largura (x) e profundidade (y) da planta em tiles. A casa ocupa os tiles `[0,0]` a `[w-1, h-1]` a partir de onde for colocada no mapa.
* `anchor`: `ox, oy` em pixels do master, iguais para todas as camadas — o centro do losango do tile `[0,0]`.
* `layers`: os arquivos das camadas (ver a seção 5 do `ART_SPEC.md`). A engine ordena por `size`; não precisa de `sort_y`.
* `walls`: tiles bloqueados, `[x, y]`.
* `doors`: `[x, y]` de cada porta. O tile da porta bloqueia quando fechada.
* `interior`: o retângulo `[x0, y0]` a `[x1, y1]` que conta como "dentro" da casa (esconde o telhado e troca `front` por `front_low`).

## data/items/rarity.json, sets.json e uniques.json — faixas do TCoM

As **5 faixas de raridade** são fixas na engine:

| Faixa | Cor do nome | Afixos |
|---|---|---|
| `comum` | branco | 0 |
| `refinado` | azul | 1 a 2 |
| `raro` | amarelo | 3 a 4, mais um nome sorteado |
| `conjunto` | verde | peça de um set |
| `lendario` | laranja | único, com nome e efeito fixos |

`rarity.json` só traz os pesos de queda por nível de monstro:

```json
{ "version": 1, "drop": [ { "level": [1, 10], "comum": 70, "refinado": 22, "raro": 6, "conjunto": 1.5, "lendario": 0.5 } ],
  "rare_names": { "first": [{"pt": "Lamento", "en": "Lament"}], "second": [{"pt": "da Aurora", "en": "of Dawn"}] } }
```

`sets.json`:

```json
{ "version": 1, "sets": [ { "id": "vigia_de_jafa", "name": {"pt": "Vigia de Jafa", "en": "Warden of Jaffa"},
  "pieces": [ {"base": "nasal_helm", "hue": "areia", "affixes": [["armor_pct", 10]]} ],
  "bonus": { "2": [["def_chance", 5]], "4": [["skill:parrying", 10], ["res_fire", 10]] } } ] }
```

`uniques.json`:

```json
{ "version": 1, "uniques": [ { "id": "dente_do_alfa", "base": "longsword", "name": {"pt": "Dente do Alfa", "en": "Alpha's Fang"},
  "hue": "brasa", "level": 40, "affixes": [["dmg_pct", 60], ["res_fire", 20]], "effect": "burn_on_hit",
  "source": "dragon_alpha_fire", "lore": {"pt": "...", "en": "..."} } ] }
```

* `effect` é opcional e serve para efeitos especiais que a engine implementa. Peça novos efeitos no PR.
* `source` é o chefe ou monstro que solta o item.

## data/hues.json

```json
{ "version": 1, "hues": [ { "id": "azul_real", "name": {"pt": "Azul-real", "en": "Royal Blue"}, "hex": "#2a4fd8", "group": "comum" },
  { "id": "brasa", "name": {"pt": "Brasa", "en": "Ember"}, "hex": "#ff5a1a", "group": "raro", "glow": true } ] }
```

* `group` diz onde a cor aparece: `comum` (loja e tintura), `raro` (só loot), `evento` ou `material` (a cor do minério ou do couro).
* `glow: true` faz a peça brilhar de leve.

## data/monsters.json

```json
{ "version": 1, "monsters": [ { "id": "dragon_young_fire", "name": {"pt": "Dragão Jovem de Fogo", "en": "Young Fire Dragon"},
  "art": "dragon", "stage": "young", "hue": "brasa", "scale": 1.0, "level": 25,
  "hp": [180, 220], "mana": 80, "str": 120, "dex": 70, "int": 60, "armor": 30,
  "dmg": [12, 20], "speed": 1.1, "range": 1, "resist": {"fire": 80, "cold": -20},
  "skills": {"wrestling": 70, "magery": 40}, "spells": ["spark_dart"], "special": ["breath_fire"],
  "behavior": "aggressive", "aggro": 8, "flee_hp": 0, "pack": [1, 1],
  "biomes": ["outremer", "mountains"], "spawn_weight": 2,
  "loot": {"gold": [80, 160], "table": "dragon_young", "rarity_bonus": 1},
  "tame": null, "corpse_items": ["leather_hide"] } ] }
```

* **`art`:** o id da folha.
  * Monstros do Flare usam o nome de lá (`goblin`, `skeleton`, `wyvern_fire`…).
  * Monstros novos usam o de `art/monsters/<id>`.
  * Dragões de degraus diferentes usam a mesma arte, com `scale` e `hue` diferentes.
* **`behavior`:** `passive` (bicho), `defensive`, `aggressive` ou `coward`.
* **`tame`:** `{"skill": 60}` para os que dá para domar.
* **Tabelas de loot:** `data/loot.json` → pesos por entrada.
  * `base:<id>` — sorteia faixa pelo `rarity.json`.
  * `raro:<id>` — item na faixa raro (chefes garantem ≥1).
  * `unique:<id>` — chance do único (`uniques.json`).
  * `gold`, `reagent`.
  * Tabelas `boss_<chefe>`: mais ouro, `raro:*` garantido, chance de `unique:*`.

## data/npcs/vendors.json

```json
{ "version": 1, "vendors": [ { "id": "ferreiro", "name": {"pt": "Ferreiro", "en": "Blacksmith"}, "look": ["ferreiro_tunica", "cloth_pants", "leather_boots", "martelo"],
  "sells": [ ["longsword", 1.0], ["nasal_helm", 1.0], ["iron_ingot", 1.2] ], "buys": ["weapon", "armor", "shield", "iron_ore"],
  "trains": ["blacksmithing", "mining"], "lines": {"pt": ["Boa lâmina, bom preço."], "en": ["Good blade, fair price."]} } ] }
```

* `sells`: `[id, multiplicador do preço]`.
* `buys`: os tipos de item ou ids que a loja compra, pela metade do `value`.
* `look`: camadas do TCoM.

## data/events.json e data/portals.json

Eventos = chefes por região (`contest: guild_damage`). Sem PvP.

```json
{ "version": 1, "events": [ { "id": "wyvern_clareira", "boss": "wyvern", "monster": "wyvern",
  "place": {"zone": "bosque_da_vila", "chunk": "clareira_do_fundo"},
  "every_min": [40, 70], "duration_min": 18, "contest": "guild_damage",
  "rewards": {"table": "boss_wyvern", "top_damage": 5} } ] }
```

Portais: **só** `kind: "moon"` (cidade↔cidade no mesmo mapa). Sem `road`/troca de mapa.

```json
{ "version": 1, "portals": [
  { "id": "portal_aurelia", "city": "aurelia", "kind": "moon",
    "phases": ["aelia_sancta", "porto_trigo", "folhaverde"] }
] }
```

* Recompensas de evento/chefe usam tabelas `boss_<id>` em `loot.json`
  (garantem `raro:<item>`, chance de `unique:<id>`, mais ouro).


## data/gathering.json

Coleta simples (sem PvP). Árvore → `logs` (serve direto na construção). Rocha → minérios com chance por nível de `mining`. Forja: 2 minérios → 1 lingote.

```json
{ "version": 1,
  "nodes": [
    { "id": "tree", "skill": "lumberjacking", "tool": "axe", "time_s": 1.5,
      "yields": [ { "item": "logs", "amount": [1, 3], "min_skill": 0 } ] },
    { "id": "rock", "skill": "mining", "tool": "pickaxe", "time_s": 1.8,
      "yields": [ { "item": "iron_ore", "chance_by_skill": [[0, 0.7], [40, 0.55]], "amount": [1, 2] } ] }
  ],
  "stations": [
    { "id": "forge", "skill": "blacksmithing", "time_s": 2.0,
      "recipes": [ { "id": "smelt_iron", "in": {"iron_ore": 2}, "out": {"iron_ingot": 1}, "min_skill": 0 } ] }
  ] }
```
* `time_s`: 1 a 2 segundos.
* `chance_by_skill`: lista `[nível_mínimo, chance]` (a engine usa o maior nível ≤ skill do jogador).
* Rocha: `stone` com `always: true` + minérios por chance.
## data/building.json

Peças do modo construção. Cada peça custa **só** `logs` **ou** só `stone`/`iron_ingot` — nunca tábua (`boards`).

```json
{ "version": 1,
  "pieces": [
    { "id": "wall_wood", "name": {"pt": "Parede de Madeira", "en": "Wood Wall"},
      "kind": "wall", "material": "wood", "cost": {"logs": 4}, "size": [1, 1] }
  ] }
```
* `kind`: `floor`, `wall`, `door`, `window`, `fence`, `gate`, `roof`.
* `cost`: exatamente um recurso.
## data/abilities.json

Habilidades físicas estilo Diablo 2, por tipo de arma (teclas 1–9 junto com magias). O `effect` usa os **mesmos** `type` de `spells.json` (`damage`, `heal`, `buff`, `debuff`, …) e `base` sempre `[min, max]`.

```json
{ "version": 1,
  "abilities": [
    { "id": "whirlwind_strike", "name": {"pt": "Golpe Giratório", "en": "Whirlwind Strike"},
      "weapon": "sword", "skill": "swordsmanship", "min_level": 40,
      "stamina": 18, "cooldown_s": 8, "target": "self",
      "effect": {"type": "damage", "element": "physical", "base": [12, 20], "scales": ["swordsmanship", "str"], "aoe": 2},
      "icon": "whirlwind_strike", "desc": {"pt": "...", "en": "..."} }
  ] }
```
* `weapon`: `sword`, `bow`, `mace`, `spear`, `axe`.
* `skill` / `min_level`: skill que libera e nível mínimo.
* Campos extras no effect (`aoe`, `dash`, `pierce`, `projectiles`, `range`) são dicas pra engine.
## data/zones.json

Mundo **contínuo** (um único mapa). `chunks` são regiões desse mapa, não mapas separados. Sem `connects`/exits entre áreas.

```json
{ "version": 1,
  "world": { "map": "mundo", "size": [98, 60], "continuous": true },
  "zones": [
    { "id": "lochport", "map": "mundo", "kind": "village", "origin": [0, 0], "size": [50, 60] },
    { "id": "bosque_da_vila", "map": "mundo", "kind": "hunt", "origin": [50, 12], "size": [48, 36],
      "chunks": [
        { "id": "entrada", "rect": [50, 22, 14, 16],
          "spawns": [ {"monster": "goblin", "count": [3, 6], "level": 1} ] }
      ] }
  ] }
```
* `origin` / `chunks[].rect`: coordenadas do mapa único (`world.map`).
* Fonte do mapa: `art/maps/<map>.txt` (+ `src/<map>.tmx`). JSON em `engine/dev_assets/flare/` é gerado pelo build.
* `world.size` é a fatia autoral já desenhada (hoje `[98, 60]`, Lochport + Bosque da Vila). O mundo alvo mora em `world.design_size` (`[2048, 2048]`), `world.chunk` (`[64, 64]`) e `world.layout` (`world_layout.json`). `world.authored_stamp` é o tile onde essa fatia entra no mapa grande. Não mover `origin` nem `chunks[].rect` da fatia: `world_origin` da zona é o carimbo já somado.
* Cada zona e cada chunk podem trazer `build`, `danger` (1–5), `invasion` (bool) e `resources`.

## data/world_layout.json — grelha grossa

32×32 células, cada uma 64×64 tiles. `(0,0)` é noroeste, Y cresce para o sul. O tile da célula `(x,y)` é `(x*64, y*64)`.

```json
{ "version": 1,
  "map": "mundo",
  "cells": [32, 32], "cell_tiles": [64, 64], "tile_size": [2048, 2048],
  "rows": [ [ { "biome": "plains", "zone": "city", "level": 0, "danger": 1,
    "build": "proibido", "invasion": false, "road": true, "river": false, "water": false,
    "resources": {"common": ["logs", "stone"], "rare": []}, "monsters": [],
    "city_id": "aurelia" } ] ] }
```

* `biome`: um id de `data/lore/biomes.json`. Água usa `coast` com `water: true`.
* `zone`: `city`, `frontier`, `open`, `dangerous` ou `boss`.
* `build`: `proibido` (cidade), `fronteira` (lote pequeno, sem invasão), `aberta` (lote depois de abrir a região) ou `nao` (água, arena, caça desenhada).
* `level`: nível de monstro da célula. `danger`: 1 a 5.
* `resources.rare` fica vazio em `city`, `frontier` e no Bosque da Vila. Prata inclusive.
* `requested_monster`, quando existe, é um id que **ainda não** está em `monsters.json`.
* `sim_slots` e `guild_hall` dizem onde o simulado mora. A tag tem de existir em `guilds.json`.
* `roads[]`, `rivers[]`, `settlements[]`, `bosses[]` e `housing` são o índice. A célula continua a ser a verdade do tile.
* `dungeons.status` é `undecided`. Entrada futura volta para o mesmo tile. Não é troca de mapa.

## data/zones.json — regions[]

Além das zonas da fatia, `regions` cobre as 1024 células, cada célula numa região só.

```json
{ "id": "frontier_aurelia", "name": {"pt": "Fronteira de Aurélia", "en": "Aurelia Frontier"},
  "biomes": ["plains"], "zone": "frontier", "build": "fronteira",
  "danger": 1, "level": 1, "invasion": false,
  "resources": {"common": ["logs", "stone", "iron_ore", "copper_ore"], "rare": []},
  "cells": [[13, 17], [14, 17]], "cell_span": [13, 17, 3, 3],
  "settlement": "aurelia",
  "unlock": {"kind": "always"} }
```

* `unlock.kind`: `always`, `visit` (exige `city`) ou `any`.
* `any`: basta o `camp` (id, `monster` que existe, `count`), **ou** `skill_min` em uma skill de `skill_any`, **ou** `reputation` (`city` + `min`).
* No perigoso, `requires_region` (o aberto do mesmo bioma) vem antes desse ou.
* `services` de uma cidade: `bank`, `healer`, `trainer`, `contract_board`, `moon_portal`, `stall_market`.
* `vendors`: ids de `data/npcs/vendors.json`.
* `danger` e `level` são um número ou `[min, max]` quando a região mistura células.

## data/invasions.json

Hordas PvE contra base em `open` ou `dangerous`. `pvp` é `false`. Fronteira, cidade, água e arena não entram. O relógio é `owner_online`.

```json
{ "version": 1, "pvp": false,
  "rules": {"frontier_invaded": false, "clock": "owner_online", "min_pieces": 4},
  "protected": {"deed": true, "home_chest": true, "bank": true, "equipped": true},
  "loss": {"wall_fraction_max": {"2": 0.2, "3": 0.3, "4": 0.45},
           "offline": {"loot_chests": false, "repair_to_bank": true}},
  "defenses": [ {"piece": "wall_stone", "exists": true, "role": "wall"},
                {"piece": "tower_stone", "exists": false, "role": "range"} ],
  "hordes": [ {"id": "plains_d2", "biome": "plains", "danger": 2, "zone": "open",
    "every_min": [480, 720], "warning_s": 180, "size": [4, 7], "clock": "owner_online",
    "composition": [["goblin", 4], ["goblin_runner", 2]],
    "announce": {"pt": "...", "en": "..."},
    "rewards": {"gold": [25, 50], "items": {"logs": [3, 6]}, "chance": [["bandage", 0.6, [1, 3]]]} } ] }
```

* `composition` lista `[monstro, peso]`. `size` é o total de cabeças.
* Peça com `exists: true` tem de estar em `building.json`. `tower_stone` é pedido (`exists: false`).
* Recompensa usa item que existe. Não é farm melhor que chefe.
* Offline não esvazia o baú da casa. O conserto vai para o banco.

## data/contracts.json

Quadro da cidade, envio da base e banca. `pvp` é `false`. Nada se perde no caminho.

```json
{ "version": 1, "pvp": false,
  "delivery": {"nearest_capital_fee": 0, "other_city_fee": [5, 15], "from": ["base_chest", "backpack"]},
  "stall": {"item": "deed_market_stall", "per_player": 1, "counts_as_lot": false, "where": "stall_market"},
  "orders": [ {"id": "aurelia_toros", "city": "aurelia", "ask": {"logs": 15},
    "gold": [35, 55], "reputation": 2} ] }
```

* A cidade do pedido tem `contract_board` na região.
* `ask` tem um item só (de `base.json` ou `reagents.json`), quantidade 1–30.
* `reputation` é 1–3, naquela cidade. Não cumprir não pune.
* A banca não gasta o lote único da base.

## data/portals.json — rede das capitais

Continua só `kind: moon`, três `phases`, cada uma uma cidade de `biomes.json`. `network: capital` liga as oito capitais nos dois sentidos. `network: local` é a pedra de vila (Porto do Trigo, Acre, Montgisard, Qasr, Musgo). Sem `road` e sem `pvp`.

## data/events.json — place.region

O evento antigo guarda `place.zone` (Bosque da Vila). O evento do mapa grande guarda `place.region`, um id de `zones.json` → `regions`. Os dois podem vir juntos. `contest` continua `guild_damage`.


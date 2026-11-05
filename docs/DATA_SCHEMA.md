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
    { "id": "pvper",       "desc": "provoca, desafia, se gaba",                    "typo": 0.08, "caps": 0.3,  "emoji": 0.1 },
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
* `ctx` (contextos que a engine dispara): `greet`, `bye`, `idle`, `lfg` (procura grupo), `trade_sell`, `trade_buy`, `trade_haggle`, `help_ask`, `help_give`, `thanks`, `brag`, `insult`, `complain_server`, `death_self`, `kill_other`, `loot_rare`, `guild_recruit`, `guild_war_declare`, `guild_war_taunt`, `raid_call`, `raid_win`, `raid_wipe`, `reply_friend` (quem gosta de você responde), `reply_enemy` (quem te odeia responde), `reply_neutral`, `pk_warning` (avisa sobre PK numa área).
* Meta da primeira rodada: 300 frases, com cerca de 50 por personalidade, todos os `ctx` cobertos pelo menos uma vez e frases curtas, como num chat de MMO (até cerca de 80 caracteres).

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
`tag` com 2 a 4 letras. `align`: `ordem`, `neutro` ou `caos` (o caos tende a PK e guerra).

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

## data/items/affixes.json
```json
{ "version": 1,
  "prefix": [ { "id": "cruel", "name": {"pt": "Cruel", "en": "Cruel"}, "applies": ["weapon"], "stat": "dmg_pct", "range": [10, 25], "tier": 2 } ],
  "suffix": [ { "id": "do_urso", "name": {"pt": "do Urso", "en": "of the Bear"}, "applies": ["weapon", "armor"], "stat": "str", "range": [3, 8], "tier": 2 } ] }
```
`stat`: `dmg_pct`, `dmg_flat`, `armor_pct`, `armor_flat`, `str`, `dex`, `int`, `hp`, `mana`, `stam`, `regen_hp`, `regen_mana`, `res_fire`, `res_cold`, `res_poison`, `res_energy`, `hit_chance`, `def_chance`, `swing_speed`, `luck`, `durability` ou `skill:<id>` (ex.: `skill:magery`). Os níveis (`tier`) vão de 1 a 5.

## data/magic/spells.json e data/magic/reagents.json
```json
{ "version": 1,
  "spells": [
    { "id": "mind_blast", "name": {"pt": "Rajada Mental", "en": "Mind Blast"}, "circle": 5, "mana": 14,
      "reagents": {"black_pearl": 1, "mandrake_root": 1, "nightshade": 1, "sulfurous_ash": 1},
      "target": "mobile", "effect": {"type": "damage", "element": "cold", "base": [10, 20], "scales": ["magery", "int"]},
      "words": "Por Corp Wis", "icon": "mind_blast", "desc": {"pt": "...", "en": "..."} } ] }
```
`target`: `self`, `mobile`, `ground`, `item` ou `none`. `effect.type`: `damage`, `heal`, `buff`, `debuff`, `summon`, `teleport`, `field`, `reveal` ou `create_item`. Os reagentes ficam em `reagents.json`, no mesmo formato de `items` (com `type: "reagent"`). **Os nomes de magias e as "palavras de poder" devem ser nossos**, e não copiados do Ultima Online.

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

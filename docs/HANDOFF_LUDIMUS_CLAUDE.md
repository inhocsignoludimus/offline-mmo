# Handoff Ludimus → Claude

Auditoria de 2026-11-07. `main` = `03615f1` (PR #34). Nada deste arquivo foi mergeado junto com arte. Não autoriza merge nem mudança de gameplay.

Ludimus entrega `art/`, `data/` e `CREDITOS.txt`. Claude entrega `engine/` e o que a engine gera em `engine/dev_assets/`. O Ludimus não regenera `engine/dev_assets/`.

`python3 build/check_data.py` na `main`: **251 itens, 64 magias, 36 monstros, 61 tabelas, 60 cores, OK.**

## Ordem

Não mergear daqui. Quando o Rodrigo mandar, nesta ordem:

1. Paperdoll: [#23](https://github.com/inhocsignoludimus/offline-mmo/pull/23), depois [#40](https://github.com/inhocsignoludimus/offline-mmo/pull/40). O 40 está em cima da branch do 23. Na `main` o diff do 40 misturaria o lote 1.
2. Mundo: [#36](https://github.com/inhocsignoludimus/offline-mmo/pull/36), depois [#37](https://github.com/inhocsignoludimus/offline-mmo/pull/37), depois [#38](https://github.com/inhocsignoludimus/offline-mmo/pull/38). 37 em cima do 36, 38 em cima do 37.
3. Casas [#39](https://github.com/inhocsignoludimus/offline-mmo/pull/39), grifo [#35](https://github.com/inhocsignoludimus/offline-mmo/pull/35) e monstros lote 1 [#24](https://github.com/inhocsignoludimus/offline-mmo/pull/24) não dependem uns dos outros. O 24 está 20 commits atrás da `main`; rebase antes de mergear. O 35 está em dia.

## Não mergear e não importar

| Coisa | Estado real |
|---|---|
| [#21](https://github.com/inhocsignoludimus/offline-mmo/pull/21) filhote e [#22](https://github.com/inhocsignoludimus/offline-mmo/pull/22) jovem | Abertos, 20 commits atrás da `main`. Cartoon rejeitado. **Não mergear.** |
| Hauberk do paperdoll | Não está em PR nenhum. Estudo recusado (ombros quadrados). **Não importar.** Continua na lista do que falta. |
| Armas lote 1 | Não há pacote nem PR. A passagem local foi rejeitada (mão aberta com a arma colada). O ajuste de empunhadura e o mapa visual de todos os ids de escudo vêm noutro pacote. **Não marcar como feito.** |
| Atlas próprio de cast que falhou | Não está no repositório. **Não importar.** |

## Já na main

- Ícones lote 1, [#31](https://github.com/inhocsignoludimus/offline-mmo/pull/31): `art/icons/` (101 arquivos no tree).
- Caça e zonas, [#32](https://github.com/inhocsignoludimus/offline-mmo/pull/32): `bosque_da_vila` 48×36 e `data/zones.json`.
- Eventos e portais, [#33](https://github.com/inhocsignoludimus/offline-mmo/pull/33). O #32 não é o PR de eventos.
- Passada 2 dos dados, [#34](https://github.com/inhocsignoludimus/offline-mmo/pull/34): mapa único `art/maps/mundo.txt` **98×60** (Vila + Bosque). `hero_pos=43,1`.
- Cabana `plains_cabin_01` v3, 5×4, porta em `[2,3]`. A v4 e a cabana 02 não estão na `main`.
- Combate, câmera, loot, vendedores, skills, magia em dados: PRs #1–#20 e #25–#30, já mergeados.
- A engine ainda abre o Lochport do Flare (`src/main.js` usa `DATA.maps.lochport`), não o `mundo.txt`. Os json em `engine/dev_assets/flare/` são gerados; a fonte editável é `art/maps/*.txt` e `src/*.tmx`.

## Abertos

### Paperdoll — #23, depois #40

#23, 109 arquivos, base `main`. Corpo, peles, cabelos, roupa e couro CC0; placa e templário CC-BY-SA 3.0 (Flare `plate_armor.blend`, referência visual `armadura_templario` do TCoM). Tela 300×480 RGBA. A engine ainda não lê `art/paperdoll/`.

Ids com camada: `cloth_pants`, `leather_boots`, `cloth_shirt`, `studded_leather` (+ `_fixed`), `leather_gloves`, `leather_hood`, `wool_cloak` (+ `_fixed`), `loriga`, `chain_greaves`, `nasal_helm`, `longsword`, `kite_shield`, `wooden_shield`, `plate_legs`, `plate_boots`, `plate_torso`, `plate_arms`, `plate_gloves`, `plate_gorget`, `greathelm`, `templar_cuirass` (hueable + `_fixed`), `templar_mantle` (item novo, slot `cloak`, `sprite_layer` null; 252 itens só depois deste merge).

`templar_cuirass` e `plate_torso` são o mesmo slot torso. Não empilhar. `greathelm_fixed` é elmo fechado arredondado, aproximação. O manto templário já vem recortado atrás do corpo; na ordem da engine a borda com a espaldeira é ~86 px (m) e ~48 px (f).

#40, 18 arquivos, base a branch do #23. Acrescenta `chain_coif` (só `_fixed`), `chain_gloves` (cinza + `_fixed`, mitene da v3), `chain_boots` (cinza + `_fixed`), `cloth_sandals` (só hueable). `chain_boots` e `cloth_sandals` dividem o slot dos pés. CC-BY-SA 3.0, bloco próprio. Coifa de `chain_coif.blend`. Botas e sandálias são topologia nova, não cópia de `chain_boots.blend` / `cloth_sandals.blend`. Limitações aceitas para publicar: pé da bota simples, tiras estreitas, sola atrás do corpo, coroa da coifa ~5 px mais alta, luvas sem remodelagem.

Ordem de pintura: corpo → cabelo → pernas → pés → tronco → braços → mãos → pescoço → manto → cabeça → arma → escudo. Hue em `<id>.png`; `<id>_fixed.png` não recebe hue. Detalhe em `art/paperdoll/README.md` desses PRs.

### Mundo — #36 → #37 → #38

2048×2048 é `world.design_size` no #36 (`docs/WORLD_DESIGN.md`, `data/world_layout.json`). Não é mapa desenhado. O #36 não mexe em `engine/`. `world.size` jogável continua `[98, 60]`.

#37: `art/maps/mundo.txt` passa a **146×60**. As 98 colunas velhas ficam. A trilha leste é a peça 48×36 em `(98, 12)`, `art/maps/trilha_leste.txt`. Sem chefe novo. Handoff: `docs/HANDOFF_TRILHA_LESTE.md` nesse PR.

#38: `art/maps/estrada_norte.txt` **64×72**, origem legada `[32, -72]`. Não edita `mundo.txt` e não empurra Lochport nem a trilha. Handoff: `docs/HANDOFF_ESTRADA_NORTE.md`.

Folhaverde é a célula `(7, 13)` na planta. Estes blocos não chegam lá. O próximo lance seria `legacy_y < -72`, para oeste, e ainda não existe.

### Casas — #39

`plains_cabin_01` v4 (porta passa a `[1, 3]`) e `plains_cabin_02` 4×4, palha, alpendre. `build/check_house.py` mede a `front_low` pela fachada, não pelo topo global. As duas casas passam o checker. Sem `engine/`.

Alpendre do 02: o deque sai ~88 px ao sul da planta (dentro da folga de 1 tile). `size` continua `[4, 4]`. Os esteios estão só na `front`, fora de `walls`: não têm colisão. No corte, esteios e viga somem; o deque fica. Quem pisa no deque é desenhado por cima da `front` inteira. Não meter o alpendre dentro do `size`.

### Grifo — #35

`art/monsters/griffin/griffin.png` + `griffin.json`, 256 quadros, CC0 Safirgreif. Não entra em `data/monsters.json` nem no atlas da engine. A engine reduz o master à metade.

### Monstros lote 1 — #24

Rato 0,3×, escorpião 0,5×, javali 0,6×, aranha gigante 0,7×. CC0 (rato, javali) e CC-BY-SA 4.0 (aranha, escorpião). Sem `cast`. Aberto e atrasado em relação à `main`. Não é rejeição.

## O que o Claude faz agora

1. **Mapa contínuo.** Ler `art/maps/mundo.txt` e o `.tmx`, e compor `estrada_norte` em `[32, -72]` sem somar esse deslocamento ao Lochport. Não regenerar `engine/dev_assets` no lugar do Ludimus. A fonte é o txt/tmx. O protótipo ainda abre o Lochport.
2. **Paperdoll.** Ligar as camadas dos #23 e #40. Testar de verdade o hue e o downscale 150×240. Frestas de contato da placa, borda do manto templário com a espaldeira, e o `greathelm` como aproximação ainda não foram vistos na engine.
3. **Casas.** Colisão e desenho do alpendre como no #39. Não tratar o deque como tile de `walls`.
4. **Escudos.** Só depois que o pacote de armas chegar. Hoje vários ids dividem a mesma `sprite_layer` do TCoM (`wooden_shield`, `kite_shield`, `heater_shield`, `tower_shield` e `pavise` usam `m/shield`; `round_shield` e `oval_shield` usam `m/escudo_redondo`). No paperdoll só existem `kite_shield_fixed` e `wooden_shield_fixed`. O mapa visual por id não está feito.
5. **Cast do jogador.** Usar o cast nativo do Flare: 4 quadros × 8 direções, corpo m/f, mais o VFX. A fonte do manto custom do TCoM não está no repo. Não importar o atlas próprio que falhou. Nos monstros do Flare já importados, `cast` também é 4×8 (conferido em `skeleton_mage`).

## Ainda não existe

Não fabricar: mundo 2048 desenhado, Folhaverde, hauberk, armas com empunhadura, mapa visual de todos os escudos, atlas de cast do jogador, `templar_mantle` na `main` (só no #23), grifo no `monsters.json`, paperdoll ligado na engine.

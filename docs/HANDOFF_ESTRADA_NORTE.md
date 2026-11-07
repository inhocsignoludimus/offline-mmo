# Handoff — Estrada Real ao norte (para a engine)

Terceiro bloco do mapa, depois da trilha leste. Não mexe em magia, casas nem vestíveis. Não foi mergeado.

## Ordem

1. PR #36 — desenho de Aelória, contra `main`.
2. PR #37 — trilha leste, contra o ramo do #36.
3. Esta PR — estrada norte, contra o ramo do #37.

## O que não se moveu

`art/maps/mundo.txt` e `src/mundo.tmx` não mudam de tamanho nem de tile. Continuam 146×60.

| Zona | origin | size |
| --- | --- | --- |
| `lochport` | `[0, 0]` | `[50, 60]` |
| `bosque_da_vila` | `[50, 12]` | `[48, 36]` |
| `orla_do_bosque` | `[98, 12]` | `[30, 36]` |
| `seara_leste` | `[128, 12]` | `[18, 36]` |

Os três chunks do bosque e o `wyvern` da clareira ficam onde estavam. Esta peça não tem chefe.

## Offset

O portão norte já existe no arquivo antigo: tiles andáveis em **x=41..44, y=0**. Para crescer para o norte sem empurrar essas linhas, a peça nova não entra em `mundo.txt`.

`world.pieces` em `data/zones.json`:

| id | arquivo | legacy_origin | size |
| --- | --- | --- | --- |
| `mundo` | `art/maps/mundo.txt` | `[0, 0]` | `[146, 60]` |
| `estrada_norte` | `art/maps/estrada_norte.txt` | `[32, -72]` | `[64, 72]` |

Tile legado = `legacy_origin` + tile dentro do arquivo. O carimbo do mundo continua `[768, 1408]` + tile legado. A peça encosta no lado norte de `mundo` (`abuts.legacy_y = 0`). Não há exit, não há teleporte, não há segundo mapa de jogo: é o mesmo mundo contínuo, em dois arquivos-fonte até o loader compor.

Arquivos: `art/maps/estrada_norte.txt` e `art/maps/src/estrada_norte.tmx`. Mesmo tileset grassland do Flare. Prévia: `docs/estrada_norte.png`.

## O que a peça é

Três retângulos, sem folga e sem sobreposição, cobrindo a peça inteira.

| Zona | Legado | Célula | Regra |
| --- | --- | --- | --- |
| `estrada_real_norte` | `[32, -72]` `[32, 72]` | `(12, 20)` e `(12, 21)`, fronteira | estrada, sem monstro, sem invasão, sem raro |
| `acostamento_norte` | `[64, -64]` `[32, 64]` | `(13, 21)`, fronteira | acostamento, igual |
| `campo_do_marco` | `[64, -72]` `[32, 8]` | `(13, 20)`, planície aberta, danger 2 | `goblin` e `goblin_spearman` nível 6 |

Recurso comum nos três: `logs`, `stone`, `iron_ore`, `copper_ore`. Raro só no campo: `silver_ore`, `leather_hide`. O campo abre desde já: é a primeira faixa aberta ao lado da estrada, não o portão do bioma inteiro.

A estrada de terra ocupa o legado x=41..44 de ponta a ponta e encontra o portão. Um pátio no meio é só o marco da estrada, não uma cidade. O campo no canto nordeste liga na estrada por um ramal.

## O que a engine faz

Não editar `engine/` nem `engine/dev_assets/` por causa disto.

Quando o loader passar a ler o mapa contínuo:

- compor `estrada_norte` com origem legada `[32, -72]` por cima do mesmo mundo de `mundo.txt`;
- não somar 72 ao `origin` de Lochport;
- spawns só no `campo_do_marco`;
- fronteira sem invasão;
- portais continuam só o da cidade (`kind: moon`), não esta estrada.

## Folhaverde

Folhaverde segue na célula `(7, 13)`, a noroeste. Esta peça é o lance norte a partir de Porto do Trigo, ainda na fronteira da Estrada Real. O próximo carimbo continua para o norte (`legacy_y < -72`) pela coluna x=12 até a curva oeste da Trilha das Folhas. Não colocar Folhaverde neste campo.

# Handoff — trilha leste (para a engine)

A fatia jogável cresceu para leste. Isto não é o PR do desenho de Aelória. Folhaverde **não** foi movida.

## O que entrou

| | |
| --- | --- |
| Mapa | `art/maps/mundo.txt` e `art/maps/src/mundo.tmx`, agora **146×60** |
| Peça | `art/maps/trilha_leste.txt` (+ `src/trilha_leste.tmx`), 48×36, embutida em `(98, 12)` |
| Zonas | `orla_do_bosque` e `seara_leste` em `data/zones.json` |
| Prévia | `docs/trilha_leste.png` |

As primeiras 98 colunas são as de antes, tile a tile. Lochport continua `[0, 0]` / `[50, 60]`. O Bosque da Vila continua `[50, 12]` / `[48, 36]`, com `entrada`, `cripta` e `clareira_do_fundo` nos mesmos `rect`. A clareira segue com o único `wyvern`. Esta extensão não tem chefe.

A estrada usa as duas brechas que já eram andáveis na coluna 97: **y=15** e **y=17**. Não se apagou árvore nenhuma do bosque.

## Onde isso fica no mundo de 2048

Carimbo da fatia: tile `[768, 1408]`, célula `(12, 22)`.

| Zona | Local | Tile no mundo | Célula | Bioma da planta |
| --- | --- | --- | --- | --- |
| `orla_do_bosque` | `[98, 12]` `[30, 36]` | `[866, 1420]` | `(13, 22)` floresta, `build: nao`, sem invasão | a mesma célula do Bosque da Vila |
| `seara_leste` | `[128, 12]` `[18, 36]` | `[896, 1420]` | `(14, 22)` planície aberta, danger 2, invasão sim | campo a leste da mata |

Spawns só com ids que já existem:

- orla: `goblin`, `goblin_runner`, `goblin_spearman` (nível 3–4)
- seara: `goblin`, `goblin_spearman`, `skeleton` (nível 6)

A seara abre desde o começo (`unlock: always`). É o passo ao lado da fatia inicial, não o portão do bioma inteiro. O raro dela é o da célula: `silver_ore` e `leather_hide`. A orla não tem raro.

## O que a engine precisa fazer

O protótipo ainda abre o Lochport do Flare (`src` / `build.py` carregam `lochport`, não `mundo`). Esta trilha não aparece no jogo até o loader usar `art/maps/mundo.txt` como o mapa contínuo, em pedaços de 64×64, sem troca de área.

Não há segundo mapa nem exit. `trilha_leste.txt` é a peça-fonte; o que se joga é o `mundo` já emendado.

Quando o loader existir:

- origem do mundo no tile `[768, 1408]` para esta fatia;
- chunks de 64×64;
- spawns lidos de `zones.json` (`orla_do_bosque`, `seara_leste`, e os três chunks antigos do bosque);
- não duplicar o `wyvern` da clareira.

## Folhaverde fica para o bloco seguinte

Na planta aprovada, Folhaverde é a célula `(7, 13)`, a noroeste. A Estrada Real sobe de Porto do Trigo pela coluna de células `x=12` (tiles de mundo com y **menor que 1408**) e a Trilha das Folhas dobra para oeste.

Este arquivo não cresce para o norte: inserir linhas em y=0 moveria todo `origin` e todo `rect` já aprovados. O próximo carimbo nessa direção é um pedaço novo colocado em tile de mundo, não uma edição do retângulo 98×60.

Não mover Folhaverde para leste para “encontrar” esta trilha. A trilha leste é o campo da célula `(14, 22)`.
